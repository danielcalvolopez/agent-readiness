# Verification procedure — agent-readiness-remediation

Evidence date: 2026-09-01. On mismatch, live scanner output wins over this
file.

This is the phase-5 procedure `SKILL.md` points at: a hard gate — "evidence
per check + both scanners re-run + diff by check ID" — that must clear before
phase 6 (Report). It assumes phase 1 already produced a `BaselineScan` and
phase 4 already produced commits classified `fix-now`; this file only covers
proving what changed. It does not re-derive check logic: pass criteria and
per-check `evidence_cmd`s live in `references/check-contracts.md`, and this
file never restates them.
(source: specs/001-agent-remediation-skill/contracts/skill-interface.md:26-37; specs/001-agent-remediation-skill/data-model.md:22-44,70-78)

---

## 1. Per-check evidence procedure

For every check with a `ScopeDecision` of `fix-now`, gather evidence in this
order:

1. **Open the check's row in `references/check-contracts.md`.** Each row
   follows the fixed schema — scanner, tier, weight, observes, pass,
   `evidence_cmd`, playbooks, source — under a `###` heading matching the
   check's own ID (e.g. `### content-no-js`, `### authMd`). Do not hand-roll a
   probe; the `evidence_cmd` is already the paste-able, runnable command for
   that exact check, with `$HOST` as its only substitution point.
2. **Run the `evidence_cmd` verbatim against the deployed target host** — the
   real production/staging domain the scanners will hit, never `localhost` —
   substituting `$HOST` (e.g. `HOST=example.com`). Some commands need live
   DNS/CDN behavior (`dnsAid`'s `dig` lookup, `ai-crawler-access`'s CDN-layer
   check) that a local build cannot reproduce.
3. **Capture the raw command output as the proof**, not the scanner's own
   `recommendation`/`details` text and not a paraphrase of what the fix should
   do. Quoting a tool's remediation prose as if it were observed evidence is
   exactly the failure mode the audit skill's reporting discipline forbids.
4. **Where a check has no reliable static probe** (`check-contracts.md` says
   so explicitly — e.g. `webMcp`'s `navigator.modelContext` registration, or
   `brand-search-accuracy`'s external search-surface behavior), what the
   `evidence_cmd` actually does varies by check: for `brand-search-accuracy`
   it genuinely queries the scanner's own finding for that check ID instead
   of the target host (`check-contracts.md:307`); for `webMcp` it is only a
   weak static grep for the registration code shipping
   (`check-contracts.md:563`), not proof the tools register at runtime — real
   verification for `webMcp` is the scanner's own re-scan (§2), not this
   command. Run the given `evidence_cmd` as-is; do not invent a
   browser-driven substitute unless the target session actually has one.
5. Record each check's evidence output against its check ID — this becomes
   one row of the report table in §6, and the input to the diff in §3.

This section is deliberately a pointer, not a duplicate: `check-contracts.md`
carries the per-check `evidence_cmd` for all is-agentic and isitagentready
checks (over 30 rows across both scanners); nothing here should drift out of
sync with that file by being restated.
(source: references/check-contracts.md:61-73,376-386; specs/001-agent-remediation-skill/evidence/audit-skill-alignment.md:138)

### 1a. Getting a running build, when you need one

**Prefer the preview gate.** If a deploy CLI is authenticated, a working-tree
deploy (`preview-gate.md` §2 route d) gives you a real host with real headers
and no local environment to satisfy. Reach for `next start` / `rails s` /
equivalent only when there is no deploy route at all.

**A type or build error in a file you did not touch is a environment
diagnosis, not a finding.** Recorded rationalisation from a real run:

> "`pnpm build` fails on a file I didn't touch, so the build is broken on
> production."

It was not. `node_modules` had drifted from the lockfile — an SDK's bundled
types had moved under a caret range while the lockfile pinned the older one.
Before reporting a broken build, in this order:

```bash
# 1. what is actually installed vs what the lockfile pins
pnpm list <suspect-package> --depth 0        # or npm ls / yarn why
grep -A2 '"<suspect-package>"' <lockfile>

# 2. reconcile, then re-run the build
pnpm install --frozen-lockfile               # npm ci / yarn --immutable
```

Only if it still fails on untouched files is it a real pre-existing breakage —
and then it is the user's, reported as a blocker, not something to fix inside
an agent-readiness run. Confirm by stashing your changes and building clean.

**Never write a `.env` file into the target.** A run-time env validator will
refuse to boot without its variables; read the validator to learn which are
required and pass placeholders inline for the one command:

```bash
FOO_API_KEY=placeholder DATABASE_URL=postgres://localhost/x pnpm start
```

Writing a `.env` leaves credentials-shaped files in someone's repo, risks
overwriting a real one, and is not part of any fix.

---

## 2. Re-scan procedure

The two scanners behave differently enough that treating them the same way
will misread a cache hit as "the fix didn't work." Run both; read each by its
own rules.

### is-agentic.com

- Reports are **immutable snapshots**. The official documentation states:
  "Reports refresh only when a visit finds them older than 6 hours." Running
  a scan again immediately after a deploy returns the *same stored snapshot*
  — the deploy has not been observed yet, not failed.
- **The JSON API never launches a scan.** `GET
  https://is-agentic.com/api/v1/report?url=<url-encoded target>` only serves
  whatever is already cached, and returns a `report_not_found` (404) problem
  response if nothing has ever been scanned for that host. It cannot be used
  to force a fresh look.
- **The CLI launches a fresh scan when needed.** `npx is-agentic <domain>
  --json` (or the report page's "Rescan" control) is the one surface that
  actually starts a scan and waits for it. This is the command to run to
  verify a fix — not the raw API call.
- **Always quote `scanned_at` from both reports being compared** (baseline
  and rescan). A score that looks unchanged with an unchanged `scanned_at`
  timestamp is a cache hit, not a failed fix — do not act on it either way
  until `scanned_at` has actually advanced past the deploy time.
- Practical sequence: deploy the fix → confirm the deploy is live (not just
  merged) → wait until the baseline's `scanned_at` is more than ~6 hours old
  → run `npx is-agentic $HOST --json` → confirm the new `scanned_at` is later
  than both the deploy time and the baseline `scanned_at` before reading the
  score or `issues[]`.

### isitagentready.com

- There is **no documented cache** on this scanner. `POST
  https://isitagentready.com/api/scan` with body `{"url": "<target>",
  "enabledChecks": [...]?}` runs a genuinely live scan on every call and
  returns a fresh `scannedAt` (note the casing: isitagentready's field is
  `scannedAt`, camelCase — not the same spelling as is-agentic's snake_case
  `scanned_at`; do not conflate the two when quoting a timestamp).
- No cache-expiry wait is needed before re-scanning here — only wait for the
  fix to actually be deployed and live at the target host first. Whether any
  undocumented server-side caching or rate limiting exists is NOT VERIFIED;
  if a rescan looks suspiciously identical to the baseline immediately after
  a deploy, treat that as a reason to double-check the deploy went live
  before trusting the number.
(source: specs/001-agent-remediation-skill/evidence/scanner-docs.md:91-104,144-147,180-186,255-263; specs/001-agent-remediation-skill/evidence/audit-skill-alignment.md:72-84; specs/001-agent-remediation-skill/research.md:135-141)

---

## 3. Diff rule

Compare the rescan against the baseline **by check ID**, not by score alone —
the two scanners expose the diff differently.

### is-agentic

- `issues[]` lists **only failed or partial** checks (`id`, `name`, `tier`,
  `result` ∈ `failed`|`partial`, `details`, `recommendation`). Passing checks
  are never enumerated by ID in this array.
- A check ID present in the baseline's `issues[]` but **absent from the
  rescan's `issues[]`** is ambiguous on its own: it may have started passing,
  or it may have become **not-applicable** and been excluded from scoring
  entirely (not-applicable checks are excluded from the denominator, not
  failed — e.g. an API-surface check when no API exists).
- **Disambiguate using `eligible_checks` and `score_breakdown`:**
  1. Compare the check's tier `total` (eligible count) in
     `score_breakdown.<tier>` between baseline and rescan. If `total` dropped
     by one for that tier, the check was excluded as not-applicable — do not
     mark it `fixed+verified`.
  2. If `total` is unchanged but `passing` rose by one for that tier, the
     check now passes — that supports (but does not alone prove) treating it
     as fixed for that specific ID; confirm by re-running its own
     `evidence_cmd` (§1) if more than one check changed between scans, since
     the tier-level counters cannot distinguish which of several checks
     moved.
  3. The top-level `eligible_checks` field is the sum of `essential.total +
     recommended.total`; a change there without a corresponding `passing`
     change is the same excluded-not-fixed signal at the whole-report level.
  4. When the counters alone cannot resolve which check moved, fall back to
     the check's own `evidence_cmd` (§1) as the deciding evidence — never
     declare a check `fixed+verified` on `issues[]` absence alone.

### isitagentready

- There is no `issues[]` array here at all. Every check — passing or not —
  is nested under `checks.<category>.<checkId>`, each with a `status` of
  `pass`, `fail`, or `neutral`. Diff by walking this object and comparing
  `status` per check ID between baseline and rescan directly; a check is
  absent from this object only when the scan's own `enabledChecks`/preset
  omitted it (the default "All Checks" preset itself excludes
  `a2aAgentCard`/`ap2` from the bundle's own exclusion list, though a bare
  `POST` without an explicit `enabledChecks` has been observed running
  `a2aAgentCard` anyway). Always compare a baseline and rescan made with the
  **same preset/`enabledChecks`**; if a check is present in one scan's
  `checks` object and absent from the other, treat that absence as
  preset-excluded, never as a pass.
- The isitagentready-flavored version of the same trap is a **`fail` →
  `neutral` transition**, not a `fail` → `pass` one. `neutral` means
  informational-or-not-applicable and is excluded from the score exactly
  like an excluded is-agentic check — a check that flips to `neutral` was
  not "fixed," it stopped applying (e.g. `webBotAuth` is neutral whenever no
  Web Bot Auth directory is expected; commerce-family checks are neutral on
  any `isCommerce: false` site by design and never affect the score either
  way).
- Only a `fail` → `pass` transition counts as verified-fixed for this
  scanner — isitagentready has exactly three statuses (`pass`, `fail`,
  `neutral`); there is no `partial` state to reason about here the way
  is-agentic's `issues[].result` has one.
(source: specs/001-agent-remediation-skill/evidence/scanner-docs.md:105-140,236-284; references/check-contracts.md:376-386)

---

## 4. Degraded mode

Trigger: the session cannot reach the public internet (no-egress sandbox,
firewalled CI runner, or any environment where the preflight check in the
audit skill's tooling would report unreachable). This is common, not
exceptional, in CI sandboxes and agent runtimes.

Core rule, carried over from the audit skill and binding here without
exception: **"a blocked sandbox is not a bad website — never report one as
the other."** A check that cannot be observed from here is `not_verified`.
It is never `fixed`, and it is never `failed` either — "a degraded report
that presents `not_verified` as `failed` is worse than no report," and the
same logic runs the other direction: presenting `not_verified` as `fixed` is
worse than admitting the sandbox could not look.

Practical rules:

- **Never interpret a blocked probe as a regression.** If a fix's own
  `evidence_cmd` (§1) fails only because outbound HTTPS is unavailable — not
  because the target actually responded wrong — mark that check
  `not_verified` for this run, with the reason stated (`egress blocked`),
  and move on. Do not retry it into a false `failed`.
- **The split is per-check, not blanket.** Some evidence commands only need
  a plain page fetch (sitemap/llms.txt/robots.txt presence and content,
  canonical values on 2–3 interior pages, OpenAPI presence at a conventional
  path) and may still succeed even when broader egress is constrained.
  Others are unobservable the moment header-level or status-level access is
  missing: anything reading response headers or exact status codes
  (`markdown-negotiation-vary`'s `Vary`/`406` behavior, `agent-friendly-404`'s
  status code, `rate-limit-headers`, `https-and-transport`,
  `bot-protection`), anything needing the *raw* (no-JS) HTML byte stream
  (`content-no-js`, `content-efficiency`, `json-ld`,
  `org-schema-completeness`, `trust-anchors`, `metadata-completeness`'s
  `html lang`), and anything needing full request/response cycles
  (`json-error-responses`). Mark exactly the checks that were actually
  unobservable `not_verified`; do not mark the whole run degraded if some
  evidence still came through clean.
- **Calibrate before concluding "unreachable."** Before treating a check as
  degraded rather than genuinely failing, confirm the sandbox is really
  blocked and not just missing one specific route: hit a known-reachable
  control host first. Do not let a single failed fetch to `$HOST` alone
  stand in for "the sandbox has no egress."
- **A `not_verified` scan-tool exit state is not evidence of anything about
  the target site.** If the audit skill's own tooling reports
  `"reachable": false` / exits with its no-egress code, treat that purely as
  "this session could not check," never as a claim about the target's
  behavior, and never as a reason to revert or distrust the fix that was
  just implemented.
- This state feeds directly into the report template (§6): a check verified
  only via `not_verified` must appear in the report as `not_verified`, with
  its reason, not silently folded into `fixed+verified` or `accepted-gap`.
(source: specs/001-agent-remediation-skill/evidence/audit-skill-alignment.md:94-104,151; specs/001-agent-remediation-skill/data-model.md:42-44,75-77)

---

## 5. Loop policy

Re-scanning is not free and the two scanners punish naive looping in
different ways — is-agentic by returning a cached snapshot that looks like
"no progress," isitagentready by burning live scans against a target that
has not changed yet. The loop has two hard preconditions and one standing
exclusion.

**Only re-scan after both are true:**

1. **The fix is actually deployed and live** at the host being scanned — not
   merged, not built locally, not staged behind a preview URL the scanner
   cannot reach. A *reachable* preview host is a different thing: scanning one
   is phase 4.5's prediction step (`references/preview-gate.md`), and it never
   counts as this phase's re-scan.
2. **The relevant scanner's cache window has passed since the baseline
   scan.** For is-agentic that means the baseline's `scanned_at` is more
   than ~6 hours old, or the report page's "Rescan" control was used to force
   an immediate re-run instead of waiting. For isitagentready there is no
   documented cache, so precondition 2 is automatically satisfied once
   precondition 1 holds — do not add an artificial wait there.

Re-scanning before both hold does not produce a "didn't work" signal; it
produces a stale-snapshot or premature-deploy signal, and looping on it burns
cycles chasing a number that was never going to move. This is precisely what
phase 5's gate means by "loop until target or explicitly-accepted gaps;
respect scanner cache TTLs; don't chase search-indexing-lag checks" — the
loop target is the diff from §3, not the raw score, and it terminates at
either a clean diff or an explicit `ScopeDecision` other than `fix-now`, never
at an arbitrary retry count.

**Slow-moving checks are follow-ups with a timescale, not loop targets.**
`brand-search-accuracy` (whether a brand-name search surfaces the site's
pages) and `agentic-search-specific` (developer-resource discoverability via
search) both depend on external indexing and search-surface behavior that
moves over weeks after a correct deploy, independent of anything the
remediation skill can re-check sooner. Re-scanning repeatedly hoping to catch
these turning green wastes the cache budget on every other check in the same
report and will not shorten the actual indexing lag. Once their fix (if any)
has shipped and passed its own `evidence_cmd`, classify them `slow-moving` in
the report (§6) with a stated re-check timescale (weeks) instead of holding
phase 5 open for them.

**A mid-run rejection never stalls the loop.** If the user rejects a proposed
fix for a check at any point during the run, reclassify that check's
`ScopeDecision` from `product-decision:declined` to `accepted-gap` on the
spot, record their rationale verbatim, and continue looping on the remaining
`fix-now` checks — do not halt the whole run waiting on a check the user has
already declined.
(source: specs/001-agent-remediation-skill/research.md:55-57,135-141; references/check-contracts.md:291-299,301-309; specs/001-agent-remediation-skill/evidence/audit-skill-alignment.md:123)

---

## 6. Report template

The phase-6 `RemediationReport` must classify every issue from the baseline
scan — no check left unclassified — and must never present a `not_verified`
result as either `fixed` or `failed`. Use this shape:

```markdown
# Agent-readiness remediation report — <host> — <date>

## Scores

| Scanner        | Baseline score        | Baseline scanned_at (or scannedAt) | Rescan score           | Rescan scanned_at (or scannedAt) |
|----------------|------------------------|-------------------------------------|-------------------------|------------------------------------|
| is-agentic     | <score>/100 (<label>)  | <ISO timestamp>                     | <score>/100 (<label>)   | <ISO timestamp>                    |
| isitagentready | Level <N> "<levelName>", <pct>% | <ISO timestamp>            | Level <N> "<levelName>", <pct>% | <ISO timestamp>            |

## Per-check outcomes

| Check ID | Scanner | Baseline result | Rescan result | Outcome | Notes |
|---|---|---|---|---|---|
| <id> | is-agentic \| isitagentready \| both | failed/partial/pass/fail/neutral | failed/partial/pass/fail/neutral | fixed+verified \| not_verified \| accepted-gap \| slow-moving | evidence_cmd output or rationale |

## Accepted-gap rationales

For every check classified `accepted-gap`, quote the user's own decision
(`ScopeDecision.rationale`) rather than paraphrasing it — e.g. `cli-tool`:
"<verbatim reason the human gave for declining the product decision>". Also
cite that check's approximate score cost by pointing at the arithmetic in the
scan's own `score_breakdown`/`eligible_checks` output (e.g. "1 of 12
`recommended`-tier checks") — weights are runtime data, so never hardcode a
point value; derive it from the actual scan being reported on.

## Slow-moving follow-ups

For every check classified `slow-moving`, state what shipped and the
expected re-check timescale — e.g. `brand-search-accuracy`: fix deployed
<date>; re-check in 2–4 weeks, not before.

## not_verified checks

For every check classified `not_verified`, state the reason (egress
blocked, unobservable check type, sandbox could not reach target) — never
leave this silently merged into `accepted-gap` or `fixed+verified`.
```

Rules governing every field in the table above:

- **A phase-4.5 preview scan may add one `Preview result` column** to the
  per-check table, recording what the preview predicted beside what production
  showed. It adds no outcome value and replaces no column: a preview result is
  never `fixed+verified`. Where the two columns disagree, production is the
  finding, and the disagreement belongs in `preview-gate.md` §4 as a correction.
- **Outcome is exactly one of the four `RemediationReport` values**:
  `fixed+verified`, `not_verified`, `accepted-gap`, `slow-moving`. There is
  no fifth bucket and no check may be omitted — every ID that appeared in
  the baseline's failed/partial set (is-agentic `issues[]`) or as `fail` (
  isitagentready) must land in exactly one row.
- **`fixed+verified` requires both halves of the §3 diff and a passing §1
  `evidence_cmd` run** — a clean rescan diff alone, without the direct
  evidence command output, is not sufficient, and vice versa.
- **Quote timestamps, not vibes.** Both scanners' scores are dated
  measurements, not stable properties of the site — always show both
  `scanned_at`/`scannedAt` values so a reader can tell a genuine before/after
  from two reads of the same cached snapshot.
- **Never collapse `not_verified` into `failed` or into a passing state** in
  either direction; keep it a visibly distinct outcome exactly as §4
  requires.
- Present this as a file in the output/report location, not pasted
  piecemeal into chat — matching the audit skill's own reporting convention
  this skill inherits.
(source: specs/001-agent-remediation-skill/data-model.md:55-59,70-78; specs/001-agent-remediation-skill/contracts/skill-interface.md:37; specs/001-agent-remediation-skill/quickstart.md:78; specs/001-agent-remediation-skill/evidence/audit-skill-alignment.md:137-139)
