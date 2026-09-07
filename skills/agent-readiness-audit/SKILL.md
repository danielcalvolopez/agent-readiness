---
name: "agent-readiness-audit"
description: "Use when the user wants a site assessed for AI-agent readiness rather than changed — \"audit my site\", \"how agent-ready is X?\", \"is my site AI-crawlable / LLM-readable?\", \"why is my is-agentic score low?\", \"check my llms.txt\", or improving an Is Agentic / Ora / isitagentready score. Also use when checking AGENTS.md, robots.txt AI-crawler rules, Content-Signal, sitemap, JSON-LD, canonical correctness, trust-anchor pages, OpenAPI discoverability, markdown content negotiation (acceptmarkdown.com), agent-friendly 404s, or MCP discovery. Reports only — never edits the target codebase. To ship the fixes, use agent-readiness-remediation."
---

# Agent readiness audit

Scan a site, produce an evidence-backed report, and hand back a remediation plan
ordered by score impact.

## Non-negotiable: this skill reports, it does not write

**Never edit, create or delete files in the target site's codebase while running this
skill.** Not "as a convenience", not "since it's trivial". Output is a report plus a
remediation plan containing exact file contents to apply *later*, under a separate,
explicitly requested instruction.

Write only into a working/output directory. If the user asks you to apply fixes, that
is a new task: confirm scope first, work on a branch, one check ID per commit.

---

## Second rule: escalate what outranks the score

If the audit surfaces credentials, tokens, private keys or personal data on a public
page — especially in `llms.txt`, `llms-full.txt`, a sitemap or an OpenAPI example —
**lead the report with it and say so in your reply.** "Reports only" constrains what
you *change*, never what you *tell them*. Agent-readiness work actively amplifies this
class of leak: `llms-full.txt` hands the whole corpus to every crawler in one fetch.

Redact the values in anything you write. Name the file, the path and the credential
type. Recommend rotation before remediation of anything else.

---

## Workflow

### 0. Preflight — establish what you can actually observe

**Do this first, every time. It takes one call and determines the whole method.**

```bash
curl -s -o /dev/null -w "%{http_code}\n" --max-time 8 https://example.com/
```

- **A real status code** → full fidelity. Use `scripts/probe.py`. Go to step 1.
- **`000`, or the command is unavailable** → this machine has no outbound HTTPS
  (egress allowlists are the norm in CI sandboxes and agent runtimes, not an edge
  case). The scanner cannot run here. Switch to **degraded mode** below and say so
  in the report.

`scripts/probe.py` detects this itself: it emits `"reachable": false` and exits `2`
rather than a misleading set of zeros. A blocked sandbox is not a bad website —
never report one as the other.

**No egress → degraded mode.** Load
[references/degraded-mode.md](references/degraded-mode.md): which checks stay
observable, which become `not_verified` (never `failed`), and the
known-good-control calibration that stops you reporting present files as
missing.

### 1. Confirm scope

Ask — with `AskUserQuestion` if available, otherwise plainly in your reply — only what
you cannot infer:

- **Which origins?** Marketing site, docs site, app, API — each scores separately and
  needs its own report. `example.com` and `docs.example.com` are two targets.
- **Brand/product name** — needed for registry (`cli-tool`) and title checks.
- **`--min-score`** — the handoff threshold in step 7. Default 95; only ask if
  the user has implied a different bar.

**Discover the API origin rather than asking for it.** Sites routinely have a third
origin that gates four checks, and nobody thinks to mention it. Look for it in:
`llms.txt`, the docs search for "base URL" / "endpoint" / `curl`, `<link
rel="service-desc">`, homepage links matching `api.`/`developers.`, and the
`servers[]` block of any OpenAPI you find. Then pass it: `--api-base https://api.example.com`.

Then create a task list with one entry per target plus a verification step.

### 2. Get the authoritative scores — run BOTH scanners

Two independent scanners grade this, they disagree, and remediation's Phase 5
requires a diff from **both**. Running only is-agentic produces a baseline that
cannot verify a fix later.

Load [references/scanners.md](references/scanners.md) for both request shapes,
every response field, the cache semantics that decide when a re-scan is
meaningful, and the scoring models. The three things that bite if you skip it:

- **is-agentic `issues[]` carries only failed and partial checks.** A check's
  absence means it passed *or* was excluded, and you cannot tell which.
- **Reports are cached ~6 h and the JSON API never launches a scan.** Always
  quote `scanned_at`.
- **isitagentready scores a `level`, not a percentage**, always scans fresh, and
  never counts `commerce` on a non-commerce site.

**Fetch the check catalog too, every run** — Ora publishes it, is-agentic does
not:

```bash
curl -s https://ora.ai/api/checks    # 200, no key. 125 checks as of 2026-09-04
```

Store the raw body in the baseline artifact's `ora_catalog` (step 5a) and diff
it against the last snapshot: it is the only way to tell "the scorer moved"
from "the site regressed". Field guide and the tier warning are in
`agent-readiness-remediation/references/check-contracts.md`, "The Ora catalog".

> The two scanners re-bucket each other's tiers on purpose. Never reconcile them
> into one number — report both, diff both.

### 3. Probe independently

The official report tells you *what* failed, rarely *where*. Reproduce each failure
yourself so the remediation plan can name the file to change.

**Only if preflight passed.** If there is no egress, skip to step 4 and use the
degraded-mode table — none of the code in this step will run.

Run the probe that ships with this skill. Stdlib only, read-only, ~10 s.
`scripts/probe.py` is **relative to this skill's own directory**, not to the
target project — resolve it from wherever this SKILL.md was loaded (typically
`~/.claude/skills/agent-readiness-audit/scripts/probe.py`):

```bash
SKILL_DIR=~/.claude/skills/agent-readiness-audit
python3 "$SKILL_DIR/scripts/probe.py" https://example.com
python3 "$SKILL_DIR/scripts/probe.py" https://example.com /docs,/pricing,/about
```

One JSON object covering: status and all response headers; `text_chars`,
`html_bytes` and `content_efficiency_pct` (`content-no-js`, `content-efficiency`);
`heading_sequence`, `heading_outline` and **every** `heading_skips` entry; canonical,
`html lang`, `og:image`, `og:type`, JSON-LD blocks and `@type` values; markdown
negotiation (`md_content_type`, `md_vary`, `md_vary_has_accept`,
`unsupported_accept_status`); the 404 probe including its markdown variant; a
per-interior-page block carrying each page's own canonical; and 15 machine-readable
paths with an `app_shell` flag.

Exit `0` reachable, `2` unreachable — usable directly as a CI gate.

**Discover the API origin and probe it separately.** A third origin gates
`openapi-spec`, `json-error-responses`, `api-schema-analysis` and
`function-calling-compat`. Run the probe against that origin too rather than
leaving those four unobserved.

**The app-shell trap.** SPAs answer `200` with the shell for *every* path. A `200` at
`/robots.txt` or `/llms.txt` proves nothing unless the content type is right and the
body is not HTML. The `app_shell` flag above exists for this; never count a probe
where it is true.

### 4. Reconcile

Build one table: check ID → official result → your local finding → the file or
config responsible. Where the two disagree, trust the official result for the score
and your probe for the diagnosis, and say so in the report.

**Known divergences — expect these, don't treat them as bugs:**

- **`robots-txt` / `ai-crawler-access`.** Is Agentic does not appear to penalise a
  *missing* robots.txt — nothing blocked reads as nothing wrong. The local scanner
  fails it. Both are defensible; the operational advice (publish one) holds either
  way. Report the absence as a finding, not as a score discrepancy.
- **`content-no-js`.** A partial result means one of two very different things.
  Check whether an `<h1>` and some prose are present in raw HTML: if yes, the page
  renders and is merely thin — the fix is copy, not architecture. Do not forward the
  official recommendation verbatim; it assumes a shell.
- **`json-error-responses`.** The detail string conflates "no API detected" with
  "API returns HTML errors". Confirm which before writing the fix.
- **`metadata-completeness` vs `canonical-correctness`.** The official check only
  verifies a canonical *exists*. A canonical pointing at the wrong page is worse than
  a missing one, because it is obeyed — every interior page canonicalising to the
  site root tells crawlers the docs and the homepage are the same document. Always
  fetch 2–3 interior pages and check where their canonical points.

Also worth running, since they catch things HTTP probing cannot:

- Chrome 150+ Lighthouse **Agentic Browsing** category — WebMCP tools, accessibility
  tree integrity, CLS, llms.txt.
- `https://validator.schema.org/` for JSON-LD.
- `https://acceptmarkdown.com` "Test a URL" for negotiation from a third-party edge.

### 5. Write the outputs

**Every audit run produces two files. Both are required.** Load
[references/outputs.md](references/outputs.md) for the field rules before
writing either.

**5a. REQUIRED — `agent-readiness-baseline-<host>-<date>.json`.** The file
remediation's Phase 1 consumes; a run that produces only prose cannot be
diffed against later.

```json
{ "host": "", "scanned_at": "", "mode": "full|degraded", "targets": [],
  "is_agentic": {}, "isitagentready": {}, "ora_catalog": {},
  "plan": [ { "check_id": "", "tier": "", "est_delta": 0, "class_hint": "" } ] }
```

Scanner objects go in **raw and unedited** — summarising them is how a stale
tier gets hardcoded into a later run. `est_delta` is labelled an estimate;
`class_hint` never classifies anything, because only the user does.

**5b. The report — `agent-readiness-<host>-<date>.md`**, these sections in
order:

```
0. Escalations (omit entirely if none)   4. Partials
1. Score line                            5. Passing
2. Method and fidelity                   6. Not applicable / not verified
3. Failures                              7. Ordered plan
```

Sections 4, 6 and 7 are the ones runs actually drop. Section 6 matters most: it
is what stops a reader mistaking "not observable from here" for "failing".

Then present the file. Do not paste the whole report into chat.

### 6. Verify

- Re-read the report against the raw probe JSON; every claim must trace to observed
  evidence, not to the recommendation text.
- If you wrote or changed scanner code, run `python3 -m unittest discover -s scripts`.
- After the user ships fixes, rescan and diff the two JSON reports by check ID.

### 7. Hand off — conditional

Evaluate this against the baseline artifact you just wrote, and say the result
out loud either way:

> **If** the is-agentic score is below `--min-score` (default **95**, the A+
> floor) **or** any check in `issues[]` carries an essential/required tier —
> **then** state which of the two conditions tripped, and offer to continue with
> `agent-readiness-remediation`, naming the **path to the baseline JSON**.
>
> Otherwise say the target is at or above the bar and no remediation run is
> indicated.

The two conditions are independent on purpose. A 96 with one required check
failing still trips the second one — a high aggregate hides exactly the failure
that matters most.

**Offer. Never invoke.** Do not start remediation, do not edit a file, and do
not treat "now fix it" as having pre-authorised it — that reply is the user
accepting the offer, and accepting the offer means *invoking the remediation
skill*, not improvising a fix here. This skill's report-only guarantee is the
reason it is safe to run against a site you do not own; an audit that sometimes
writes code is not that skill any more.

**Hand over the path, not a summary.** The remediation skill's Phase 1 consumes
the baseline artifact from step 5a. Prose does not survive the hop: point at the
file.

```
Score 76.0 (A) at 2026-09-04T11:26:47Z — below the 95 threshold, and 3
essential checks failed (content-no-js, agent-friendly-404,
markdown-negotiation-vary).

Baseline: ./agent-readiness-baseline-example.com-2026-09-04.json

Want me to continue with agent-readiness-remediation from that baseline? It
writes code, so it will walk the failed checks with you before touching
anything.
```

---

## Scoring model

In [references/scanners.md](references/scanners.md). Two rules you must not get
wrong without reading it: not-applicable checks are **excluded, not failed**, and
grades are assigned from the score **rounded half-up** — a 47.5 is a D that
rounds into C, and someone will notice.

## Remediation reference — see check-contracts.md

**One source of truth, and it is not this file.** Every check's tier, pass
criterion, evidence command and playbook lives in
`agent-readiness-remediation/references/check-contracts.md`, evidence-dated per
entry and covering **both** scanners. Read it there; do not restate it here.

This section used to carry a ~130-line parallel copy for is-agentic only. It
drifted, as duplicated references do, and the 002 review measured the cost:

| Claim it carried | Reality | Damage |
|---|---|---|
| `org-schema-completeness` needs `sameAs` with 3+ verified profiles | Ora's own recommendation names `contactPoint` and `address` only; a production preview cleared the check with one profile | an agent made confirmed-official profile URLs a **blocking** question to the user, for a requirement that does not exist |
| `trust-anchors` grouped under `json-ld`/`org-schema-completeness`, no criterion of its own | it is an independent check: `/about`, `/contact`, `/privacy`, ≥500 chars of visible text each | the heaviest trust check had no pass criterion an auditor could apply |
| `Vary: Accept` can simply be appended in Next.js | Next 16.2.3 overwrites `Vary` on App Router page responses | a recipe that silently does not work on the current major version |

Evidence: `agent-readiness-remediation/specs/002-skill-review-and-standards/evidence/`
— `session-review-2026-09-04.md` and `red-baselines-2026-09-04.md`.

**When you need a fix recipe for the report's step 5b section 7,** read the
check's entry in `check-contracts.md` and, for an ID it does not cover, the Ora
catalog (step 2a). What stays below is the part that is genuinely this skill's
job — diagnosis a scanner cannot do for you.

---

### Things no scanner catches — look with your own eyes

Spend two minutes on the rendered page before you finish. Recurring defects that score
perfectly and break every agent that arrives:

- **"Open in ChatGPT / Claude" buttons** whose prompt template interpolated a loading
  state or an undefined variable, so the agent is handed literal nonsense.
- **Copy-as-markdown buttons** that copy the nav chrome along with the article.
- **A `.md` variant that 404s** while `rel="alternate"` still advertises it.
- **Docs search** that requires JS and returns nothing to a crawler.


## Fix ordering

1. `content-no-js` — everything downstream reads the rendered HTML.
2. `agent-friendly-404` — stops agents believing in phantom URLs.
3. `canonical-correctness` — a wrong canonical actively de-indexes the pages agents need.
4. `robots-txt` / `ai-crawler-access` / CDN bot rules — stop blocking.
5. `sitemap`, `llms.txt`, `agent-instruction`, `json-ld`, `metadata-completeness` —
   pure additions, same-day, no behaviour risk.
6. `markdown-negotiation-vary` — middleware; test on staging, watch the `Vary` append.
7. `openapi-spec`, `json-error-responses`, schema quality — API workstream.
8. `mcp-server`, `ai-catalog`, `cli-tool` — product decisions.
9. `brand-search-accuracy` — ongoing, not a deploy.

Items 7–9 usually need a product decision or a credential. Surface them in the report
as decisions, not as tasks.

---

## Reporting rules

- Quote observed evidence, never the tool's recommendation, as proof. "`Vary: rsc,
  next-router-state-tree` — `Accept` absent" beats "Vary header is missing Accept".
- Give every claim a verification command the reader can paste.
- Separate *fix now* from *needs a decision*. Do not present shipping a CLI as a
  checkbox.
- State the scanner's blind spots: brand search, real agent journeys, and anything
  needing JS execution. The local score is a proxy; the Is Agentic number is the one
  being graded.
- Distinguish three things that look alike and are not: **failed** (observed, broken),
  **not applicable** (excluded from scoring), **not verified** (you could not observe
  it from here). Collapsing the third into the first is the fastest way to lose a
  reader's trust.

## What this file depends on

This skill is **not** self-contained, and stopped pretending to be on 2026-09-04.
It owns the scan, the probe, the reconciliation and the report. It does not own
check definitions or fix recipes:

| You need | Read |
|---|---|
| degraded-mode check lists and calibration | `references/degraded-mode.md` |
| scanner request/response shapes, cache rules, scoring models | `references/scanners.md` |
| baseline-artifact and report field rules | `references/outputs.md` |
| a check's tier, pass criterion, evidence command, playbook | `agent-readiness-remediation/references/check-contracts.md` |
| a check ID no contract covers | the Ora catalog, step 2a |
| framework-specific fix code | the remediation skill's playbooks — that skill applies them; this one only cites them |

`scripts/probe.py` ships with this skill. There is no separate toolkit to go
looking for and no inline fallback to keep in sync with it. It is stdlib-only,
so it runs wherever Python does; copy it into a target repo if you want it in
CI. Exit `0` reachable, `2` unreachable.

## Sources

- <https://is-agentic.com/methodology> · <https://is-agentic.com/docs> · <https://is-agentic.com/openapi.json>
- <https://ora.ai/methodology>
- <https://llmstxt.org> · <https://acceptmarkdown.com> · <https://agents.md>
- <https://ora.ai/api/checks> — the published check catalog (step 2a)
- <https://isitagentready.com> — second scanner (step 2b)
- <https://developer.chrome.com/docs/lighthouse/agentic-browsing/scoring> — the only
  grader that tests WebMCP at runtime. Deliberately **not** a measured scanner here:
  it needs a browser, which would make this skill unrunnable headless. Run it by hand
  when WebMCP is in scope (step 4).
