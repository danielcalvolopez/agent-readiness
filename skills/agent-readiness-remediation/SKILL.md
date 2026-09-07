---
name: agent-readiness-remediation
description: >
  Use when the user wants agent-readiness work built rather than assessed —
  "make this project agent-ready", "get to 100 on is-agentic", "fix my
  agent-readiness score", "implement the audit's remediation plan", or "now
  fix it" / "ok, go ahead" / "apply those" straight after an agent-readiness
  audit. Also use when adding or repairing llms.txt, AGENTS.md, robots.txt
  AI-crawler rules, Content-Signal, sitemap, JSON-LD or trust-anchor pages,
  markdown content negotiation, agent-friendly 404s, RFC 9457 problem+json
  errors, OpenAPI discoverability, or .well-known agent manifests, with the
  intent to ship them. Requires a baseline from agent-readiness-audit first;
  this skill WRITES code. For assessing only — "audit my site", "how
  agent-ready is X?", "is my site AI-crawlable?", "check my llms.txt" — use
  agent-readiness-audit instead.
---

# Agent readiness remediation

Take a project from its measured baseline to its agreed target score, one
check ID at a time, with evidence for every claim.

This skill is the writing counterpart to `agent-readiness-audit`: that skill
scans and reports, this one implements. If the request is to assess, measure,
check, or report, use `agent-readiness-audit` instead — and never start fixing
inside an audit pass.

## Phases

| # | Phase | Gate |
|---|---|---|
| 1 | Baseline | **HARD** — no target-project file edits before a baseline exists |
| 2 | Scope | **HARD** — the user classifies every failed check before implementation |
| 3 | Plan | **Written to a file**; fixed risk order; one check ID per commit |
| 4 | Implement | Matching playbook > generic; target conventions win |
| 4.4 | Conformance review | **HARD** — fresh eyes diff the work against the plan file; review-only, findings closed before 4.5 |
| 4.5 | Preview gate | Predict the post-deploy score before merging; skipped only when there is no reachable preview **and** no usable deploy route, and the skip is announced |
| 5 | Verify | **HARD** — evidence per check + both scanners re-run + diff by check ID |
| 6 | Report | Every baseline issue classified |

Run them in order. None is satisfied by intending to do it later. Phase 4.5 is
the only one that may be skipped, only for the reason it names, and only with
the skip announced; phase 4.4 may be downgraded to a self-run pass but never
dropped. Every other phase is mandatory.

---

## Phase 1 — Baseline

> **HARD GATE: do not create, edit, or delete a single file in the target
> project until a dated baseline scan exists.**
> This holds for "trivial" additions — an llms.txt, a robots.txt line, a
> one-line canonical — and it holds when the user opens with "just add X
> now". A fix with no baseline cannot be verified, cannot be reported, and
> cannot be attributed to a score change. Speed is not an exemption; a small
> diff is not an exemption; being confident the check is failing is not an
> exemption.

1. **Take the path to a baseline artifact** —
   `agent-readiness-baseline-<host>-<date>.json`, written by the audit skill's
   step 5a. If you do not have one, invoke `agent-readiness-audit` against the
   target host to produce it, or accept one that is fresh (cache rules in
   [references/verification.md](references/verification.md) §2).

   A prose report is not a baseline. If all you were handed is a summary — even
   a detailed one, even one you wrote yourself a moment ago — the artifact is
   missing and the gate is not satisfied. Ask for the path, or re-run the audit
   to produce it.
2. Never implement scanning logic here. This skill consumes that artifact:
   `is_agentic`, `isitagentready` and `ora_catalog` raw, plus `mode`
   (`full` or `degraded`) and the audit's `plan[]` hints. Read `score`,
   `scanned_at` and `issues[]` from the raw scanner objects, never from a
   summary of them.
3. Record the baseline: both scanners' timestamps, the score, and the full
   `issues[]` list. Everything downstream is diffed against this.
4. If the user declines a baseline after you have explained the cost, you are
   not running this skill. Say that plainly, make no score claims, and do not
   silently proceed under the skill's name. One "just do it now" in an opening
   request is not that decision — refuse, and offer the audit first.

A session that cannot reach the network produces a `degraded` baseline. That
constrains what you may later claim (see Safety rules); it is never permission
to edit without a baseline.

---

## Phase 2 — Scope

> **HARD GATE: the user classifies every failed check. You never self-accept
> a gap, and you never widen scope on your own judgment.**
> Deciding that a gap is "obviously fine", "not worth it", or "clearly not
> what they want" is the agent making a product decision it was not given.
> An unanswered check is unclassified, not accepted. The one sanctioned
> exception is explicit delegation — see **Delegation** below.

Load [references/check-contracts.md](references/check-contracts.md) and walk
every entry in the baseline's `issues[]` with the user. Assign exactly one
classification per check ID:

| Classification | Meaning |
|---|---|
| `fix-now` | Implement in this run |
| `product-decision:accepted` | User decided to build the product surface it needs |
| `product-decision:declined` | User decided not to build it → becomes `accepted-gap` |
| `accepted-gap` | Knowingly left failing, with the user's rationale recorded |
| `slow-moving` | Correct fix ships now; the check clears later via external lag |

Record each rationale in the user's own words where possible.

Product decisions, not code fixes — ask, never implement unasked: `cli-tool`
(publishing an official CLI/SDK), `mcp-server` / `mcpServerCard` / `webMcp`
(running an MCP surface), `a2aAgentCard`, `oauth-support` (operating an
authorization server), `onboarding-friction` (changing how customers sign up),
and the commerce family (`x402`, `mpp`, `ucp`, `acp`, `ap2`). Commerce checks are excluded from scoring on a
site with no commerce surface — never build a payments surface to clear one.
Externally-indexed checks (`brand-search-accuracy`, `agentic-search-specific`)
are `slow-moving`, not loop targets. Nothing leaves `accepted-gap` without a
new user decision.

**Ask the same questions every run.** A baseline with 18 failed checks is not
18 questions. Group them, and put the same four to the user each time so no run
reinvents the grouping and no input gets skipped because it did not come up:

| # | Group | What you are asking |
|---|---|---|
| 1 | **Product surfaces** | `cli-tool`, `mcp-server` / `mcpServerCard` / `webMcp`, `a2aAgentCard`, `oauth-support`, `onboarding-friction` — each needs a product that does not exist yet. One decision per surface, not per check. |
| 2 | **Commerce** | `x402`, `mpp`, `ucp`, `acp`, `ap2`. One question: does the site transact? A "no" excludes all five from scoring — it does not fail them. |
| 3 | **Static manifests** | llms.txt, sitemap, robots.txt, JSON-LD, `.well-known` files, trust-anchor pages. Pure additions; this is the group a blanket delegation can cover. |
| 4 | **Business inputs** | the values below, which no amount of reading the repo will tell you |

**Required business inputs** — collect these in Phase 2, before Phase 4 needs
them, because each one blocks a specific check:

- **`Content-Signal` values** (`search=`, `ai-input=`, `ai-train=`). **Ask
  explicitly; never default.** The playbook recipe ships
  `ai-train=yes` inline, which is the user granting permission to train on
  their content — a licensing decision, not a header. Get it in the user's own
  words and record it.
- **Postal address granularity** for `org-schema-completeness` — full street
  address, or city/country only. Publishing an address is a disclosure
  decision; ship with the field omitted and the gap recorded rather than
  inventing one.
- **AI-crawler policy** — which of the named crawlers are allowed. Do not
  assume the playbook's ten-crawler allow-list is what they want.
- **Legal/policy copy** for `trust-anchors` `/privacy`. You draft `/about` and
  `/contact` for approval; a privacy policy is the user's document, and padding
  one to clear a character count is the dark pattern the safety rules forbid.
- *Optional, not gating:* `sameAs` profile URLs. Worth publishing; **not**
  required by `org-schema-completeness` (corrected 2026-09-04 — see
  `check-contracts.md`). Do not block on it.

**Delegation.** If the user explicitly delegates in their own message —
"just handle it", "use your judgment", "I don't have time to go through every
line item" — that delegation classifies exactly one group: checks whose fix
is a Phase 3 step 1 discovery-surface addition may be marked `fix-now`, with
the user's delegating words recorded verbatim as the rationale for each.
Nothing else is covered: product-decision checks stay unclassified awaiting
the user, and Phase 3 step 2 (content negotiation) and step 3 (API error
shapes) still require a per-check answer before implementation — a blanket
"use your judgment" never authorizes behavior-changing code. Present the
complete classification table in the report either way, so every delegated
decision is visible for review.

---

## Phase 3 — Plan

Order the `fix-now` set by risk, not by convenience. The order is fixed:

1. **Discovery surface** — robots.txt, sitemap, llms.txt, `.well-known`
   manifests, JSON-LD, canonicals, 404 page. Pure additions, lowest risk,
   clears the most checks fastest.
2. **Content negotiation** — markdown variants, `Vary`, `406`. Touches every
   page response, so it needs the test harness from step 1 in place.
3. **API error shapes LAST** — `json-error-responses` (RFC 9457
   problem+json), status/`Allow` behavior, rate-limit headers. This is the
   most behavior-sensitive change in the whole set.

> Before touching any API error shape, audit its consumers first. List every
> caller of each affected route — forms, widgets, SDKs, mobile clients,
> third-party integrations — and confirm they all live in this repo and can
> change in the same commit. If any consumer is outside the repo, that check
> is a coordination item for the user, not a quick edit.

**REQUIRED OUTPUT: a plan file.** The plan is a file, not a chat message. Write
it before Phase 4 begins, to the target's own plan directory if it has one
(`docs/plans/`, `docs/superpowers/plans/`, `.plans/` — detect, do not assume),
otherwise next to the baseline artifact in the output directory. Name it
`<date>-agent-readiness-<scope>.md`.

The plan carries, at minimum:

| Section | Contents |
|---|---|
| Scope | the **complete** Phase 2 classification table — every baseline check ID, its classification, and the user's rationale in their own words |
| Tasks | **one task per `fix-now` check ID**, in the risk order above, each naming the observed baseline evidence it answers and the playbook section it applies |
| Out of scope | `accepted-gap`, `product-decision:declined` and `slow-moving` IDs, each with its rationale, so nobody re-opens them mid-run |
| Open questions | the blocking user inputs (addresses, profile URLs, policy copy) with the tasks each one gates |

A plan that lives only in the conversation cannot be diffed against at Phase 6,
cannot survive a context reset, and cannot be reviewed by anyone else. Phase 6
reports against this file, so the run has no memory of the user's rationales
without it. Deadline pressure is not an exemption: the plan is where the
classification table stops being disposable, and it is the cheapest artifact
in the run.

**Commits.** On a git target: work on a branch, one check ID per commit,
commit named for the check it clears, with its test. If the target is not a
git repo, or the user has said no commits, switch to **edit-only mode** and
announce it: say explicitly that the one-check-per-commit guarantee is
suspended and that per-check attribution and rollback are therefore weaker.

Mark any check ID absent from `check-contracts.md` as `no-playbook` in the
plan (see Standing rules).

---

## Phase 4 — Implement

**Detect the target's stack before choosing a playbook.** Read the repo:
package manager (lockfile), test runner and test layout, language, routing
and config conventions, existing shared modules.

Load exactly one playbook:

- Next.js App Router target →
  [references/playbook-nextjs-app-router.md](references/playbook-nextjs-app-router.md)
- Anything else →
  [references/playbook-generic.md](references/playbook-generic.md)

**Read the playbook's Check-ID index first, then read the section for every
`fix-now` check ID before implementing any of them.** Sections cross-reference
each other and several cover more than one check. Reading them one at a time as
you reach each check is how a section that already answered the question gets
skipped and its content rediscovered halfway through — recorded from a real run
against §3.

Do not read or apply the Next.js playbook for a non-Next.js target. Its recipes
name framework-specific APIs and files; carrying them into a Django, Rails,
Astro, or static-hosting target produces instructions that cannot be followed.
Build those plans from the check contract plus the generic playbook, expressed
in the target's own conventions.

Rules while implementing:

- The target's conventions win over any example in a reference file. Adapt the
  recipe; do not import a foreign layout.
- Consult the target's own bundled framework docs before using any API whose
  name looks familiar — major versions rename and replace things.
- TDD wherever there is testable logic: write the failing test first, then the
  fix. Static file content still gets an assertion where the target has a test
  runner.
- Trace every fix to an observed failure in the baseline — a header, a status
  code, a character count, a specific missing file — not to a scanner's
  generic recommendation text.
- One check ID per commit, named for the check it clears, with its test (or
  per change-set in announced edit-only mode).
- Never install a dependency without explicit user approval (see Safety
  rules).

---

## Phase 4.4 — Conformance review

> **HARD GATE: fresh eyes review the diff against the plan file before the
> preview gate. The agent that wrote the diff is not fresh eyes.**

Dispatch one review subagent per phase-3 risk group that produced changes —
independent work, so send them in one message and let them run concurrently.
Group 3 (API error shapes) gets its own review even when it holds one check.
Each prompt carries only: `Read <this skill>/references/spec-conformance.md and
follow it exactly`, the plan file path, that group's check IDs, the diff command
(commit range, or the working tree in edit-only mode), the repo root, the Safety
rules below restated verbatim, and `Review only — do not edit, fix, or commit.`

**Spawn each reviewer new; never continue an agent that has already touched this
run.** The prompt is that list and nothing else — no summary of what you built,
no reasoning for it, no note on which parts you believe are fine, and never your
own rendering of the diff in place of its path. Everything you add is context the
reviewer was supposed to derive for itself, and a reviewer reading your account
of the work is reviewing you, not the diff.

What comes back is not advisory. A safety violation blocks everything else, and
a published secret goes to the user first. An unimplemented plan task returns to
phase 4 for that check ID — it is not a footnote in the report. An untested
change gets its test, or a recorded reason the target cannot test it. An
out-of-scope change goes to the user to confirm or revert, never self-approved.
An evidence-traceability gap is re-traced to the baseline, or dropped.

No subagent capability in this session? Run the same protocol yourself as a
separate pass and say in the report that it was self-run — weaker evidence, and
the reader should know which they are reading.

---

## Phase 4.5 — Preview gate

Predict the post-deploy score while the branch is still cheap to change. Load
[references/preview-gate.md](references/preview-gate.md) for the discovery
commands and the measured host-drift data.

1. **Find the preview host yourself** — from the commit SHA via the platform's
   deployment status, the branch alias, the platform CLI, or by deploying the
   working tree (`npx vercel@latest deploy --yes`), which needs no commit,
   push or branch and works in edit-only mode.
2. **Confirm it answers `200` unauthenticated.** Anything else is
   `gate-unavailable`; lifting deployment protection is the user's call.
3. **Scan the per-commit URL**, not the branch alias, so the scanner's per-host
   cache never applies.
4. **Diff by check ID** against the production baseline, discount the
   preview-unreliable set, and check the tier denominators — a preview cannot
   speak for a check that is not eligible on that host.

> A preview predicts; production verifies. It never yields `fixed+verified`, and
> phase 5 runs in full regardless.

Skip this phase only when **both** are true: no reachable preview host, and no
usable deploy route to make one. Announce the skip and say which you checked.

"Nothing is pushed yet" is not a reason — route (d) deploys the working tree.
**"The working tree carries someone else's unfinished work" is a reason**: that
deploy would publish it. Ask the user; if they are not available, skip and
record why.

---

## Phase 5 — Verify

> **HARD GATE: no check is "fixed" until its own evidence command passes
> against the deployed host AND a fresh re-scan from BOTH scanners
> (is-agentic and isitagentready) shows its diff cleared.**
> A green local build is not evidence. A passing unit test is not evidence.
> "The recipe says this clears it" is not evidence.

Follow [references/verification.md](references/verification.md): per-check
evidence commands (§1), the two scanners' different re-scan semantics (§2),
the diff-by-check-ID rule (§3), degraded mode (§4), and the loop policy (§5).
Re-scan through the `agent-readiness-audit` skill or its tooling; never write
your own scanner, and never edit the audit skill itself.

Quote `scanned_at` / `scannedAt` on every scan you cite. Re-scan only after
the fix is deployed and live at the scanned host and the scanner's cache
window has passed — is-agentic serves an immutable snapshot until roughly 6
hours old, so an early re-scan reads as "no progress" when nothing was
measured at all. Loop on the diff, not on the raw score; terminate at a clean
diff or an explicit non-`fix-now` classification.

---

## Phase 6 — Report

Report **against the Phase 3 plan file** — its scope table is the list of check
IDs that must each end with an outcome, and its rationales are the ones quoted
here.

The report is a file with these five sections, in this order:

```markdown
# Agent-readiness remediation report — <host> — <date>

## Scores
| Scanner | Baseline score | Baseline scanned_at | Rescan score | Rescan scanned_at |

## Per-check outcomes
| Check ID | Scanner | Baseline result | Rescan result | Outcome | Notes |

## Accepted-gap rationales      <- the user's own words, quoted
## Slow-moving follow-ups       <- what shipped + re-check timescale
## not_verified checks          <- the reason each was unobservable
```

Every issue in the baseline ends the run with exactly one outcome:
`fixed+verified`, `not_verified` (with reason), `accepted-gap` (with the
user's rationale), or `slow-moving` (with a re-check timescale). Zero
unclassified checks, no fifth bucket.

Field rules — what each column may contain, what `fixed+verified` requires,
and how a preview column is allowed to appear — are in
[references/verification.md](references/verification.md) §6. Load it before
writing the report, not after.

---

## Standing rules

**Unknown checks.** A scan may return a check ID that `check-contracts.md`
does not cover — the scanners add checks. Look it up in the Ora catalog before
you say anything about it:

```bash
curl -s https://ora.ai/api/checks | jq '.checks[] | select(.id=="<check-id>")'
```

That returns the check's `recommendation`, `maxScore`, `tier`, `applicability`
and `specUrl`. Quote those as the catalog's words, with the fetch date. A miss,
or no network, changes nothing below.

Either way: never guess a recipe, a tier, a weight, or a pass criterion the
catalog did not answer. Surface the scanner's own `details`/`recommendation`
(is-agentic) or `message`/`evidence[]` (isitagentready) text as-is, mark it
`no-playbook`, and confirm the approach with the user before implementing — a
catalog hit is fix text, not a decision, and not the observed evidence this
target actually produced. Feed it back as a candidate addition to
`check-contracts.md` afterwards.

**Tiers and weights are runtime data.** Never hardcode a tier, a weight, or a
points-per-check figure. Read `issues[].tier` and `score_breakdown` from that
scan. isitagentready has no tiers or weights at all — only `pass` / `fail` /
`neutral` per check, with `neutral` excluded from denominators. Where a
reference file and live scanner output disagree, live output wins.

**Target-project rules.** Detect, never assume: package manager, test layout,
language, patterns. Git targets get a branch and per-check commits;
non-git or no-commit targets get announced edit-only mode.

---

## Safety rules

These bind every subagent this skill spawns. Restate them verbatim in any
subagent prompt: what a subagent inherits varies by harness and by what the
target repo installs, so never assume one arrived already carrying them.
Measured — a review subagent given none of this picked up a project-local skill
and followed that skill's report format unprompted, so "it inherits nothing" is
as wrong as "it inherits everything."

**Secrets outrank the score.** If you find credentials, tokens, private keys,
or personal data on a public surface, lead with it: name the file, path, and
credential type, redact the value, and recommend rotation *before* any other
remediation. Never publish a secret into a discovery file. `llms-full.txt`,
`llms.txt`, sitemaps, and OpenAPI examples amplify this class of leak by
handing the whole corpus to every crawler in one fetch — read what you are
about to publish before you publish it.

**No dependency installs without asking.** State what the library does, why it
beats the alternatives, and wait for explicit approval. This includes test
runners, MCP packages, and validation libraries a recipe implies.

**No SEO dark patterns.** Do not add keyword filler, hidden text, or copy
written for a scanner rather than a reader. Prefer genuinely visible,
server-rendered prose. `sr-only` content is acceptable only with guardrail
tests in place asserting it is not `display:none`, not `aria-hidden`, and is
real product prose — text hidden from parsers clears nothing and is a dark
pattern besides.

**Degraded-mode honesty.** A blocked sandbox is not a bad website — never
report one as the other. A check you could not observe is `not_verified`: it
is never `fixed` and never `failed`. Mark exactly the checks that were
actually unobservable, with the reason, and confirm the sandbox is genuinely
blocked (hit a known-reachable control host) before calling anything degraded.

---

## Red flags

If you catch yourself thinking any of these, stop — the thought is the
warning:

| Rationalization | Reality |
|---|---|
| "Just a quick fix before the audit — it's obviously missing" | Phase 1 gate. No baseline means no verifiable attribution and no report line. Size of the diff is irrelevant. |
| "I just ran the audit myself, so I already know the findings — I can start fixing" | The findings live in the baseline artifact. Carrying them in your head loses `scanned_at`, the raw tiers, and the denominators Phase 5 diffs against. Name the file. |
| "I'll accept this gap myself; the user wouldn't want it" | Phase 2 gate. Accepting a gap is a product decision reserved to the user. Unanswered ≠ accepted. |
| "The user said 'use your judgment', so everything is approved" | Delegation covers Phase 3 step 1 discovery additions only. Product surfaces, content negotiation, and API error shapes still get per-check answers. |
| "It's three static files — a written plan is ceremony I can skip" | The plan file is where the user's classification table and rationales become durable. Skip it and Phase 6 has no list to report against and no rationales to quote. Measured: an agent under deadline produced an ordered plan in chat only, and the next phase had to ask for the check IDs back. |
| "I built these commits straight from the plan, so of course they match it" | You are the reader least able to notice the task you silently dropped. Phase 4.4 dispatches someone who was not there. |
| "I'll summarise what I did so the reviewer has enough context" | That context is exactly what you withhold. Its value is deriving the story from the plan and the diff alone; hand it yours and you get your own blind spot back, in a second voice. |
| "The reviewer flagged an out-of-scope file, but it was needed" | Then the user confirms it. Phase 2's rule — the agent never widens scope on its own judgment — does not lapse because implementation already happened. |
| "The scanner is cached but it probably passed" | Nothing was measured. "Probably passed" is `not_verified`, not `fixed`. Wait out the cache window or force a fresh scan. |
| "This API error change is trivial" | It is the highest-blast-radius change in the set. Audit consumers first; it ships last. |
| "The Next.js recipe is close enough for this stack" | It is not. Use the check contract plus the generic playbook in the target's own idiom. |
| "I'll install this small dependency and mention it after" | Explicit approval first, every time. |
| "Local build is green, so the check is fixed" | Evidence is the check's own command against the deployed host, plus a re-scan diff. |
| "I'll write the report in whatever structure fits, then check the template" | The template is six lines, inline in Phase 6. Writing first and loading the rules afterwards is how a run ships a report with three required sections missing. |
| "No branch was pushed, so there's no preview to scan" | A working-tree deploy needs no commit, push or branch. Recorded verbatim from a run where the gate was skipped and the user had to ask for it. |
| "The tree is dirty with the user's WIP, but the gate is mandatory, so I'll deploy anyway" | A working-tree deploy publishes their unfinished work to a public URL. Ask first. Unreachable user means skip and say so — that skip is sanctioned. |
| "The build fails on a file I didn't touch, so their build is broken" | Check installed versions against the lockfile and re-install frozen first. Recorded verbatim from a run where node_modules had drifted and the misdiagnosis was reported to the user as a production blocker. |
| "The user said make it agent-ready, so MCP/CLI is in scope" | Product surfaces are asked about, never assumed into scope. |
| "This check ID isn't in the contracts, so there's nothing to tell the user yet" | Ora publishes all 125 checks. One `curl` returns its fix text, weight and applicability. Blocking the user on a lookup you did not run is not caution. |

---

## Dependencies

**None.** This skill and `agent-readiness-audit` are self-contained: everything
they need is in their own `references/` and `scripts/`. They require no plugin,
no other skill, and no network service beyond the two scanners and Ora's
catalog.

If you are tempted to add a `REQUIRED SUB-SKILL` line, write the thing it would
have given you into this file instead. A skill that silently stops working when
a plugin is absent is worse than a slightly longer skill.

The two skills reference **each other** — the audit hands over a baseline path,
and cites `agent-readiness-remediation/references/check-contracts.md` as the
single source of truth for check definitions. Install them as siblings.

---

## Reference files

| File | Load at |
|---|---|
| [references/check-contracts.md](references/check-contracts.md) | Phases 2–3 — both scanners' checks: what each observes, pass criteria, evidence command |
| [references/playbook-nextjs-app-router.md](references/playbook-nextjs-app-router.md) | Phase 4, Next.js App Router targets only |
| [references/playbook-generic.md](references/playbook-generic.md) | Phase 4, every other target |
| [references/spec-conformance.md](references/spec-conformance.md) | Phase 4.4 — read by the review subagent: checklist extraction, the five finding buckets, report shape |
| [references/preview-gate.md](references/preview-gate.md) | Phase 4.5 — preview URL discovery, reachability precondition, preview-unreliable checks, blind spots |
| [references/verification.md](references/verification.md) | Phase 5 — evidence, re-scan, diff, degraded mode, loop policy, report template |

Each carries an evidence date. Where a file and the live scanner disagree, the
live scanner wins — and the mismatch is worth reporting back.
