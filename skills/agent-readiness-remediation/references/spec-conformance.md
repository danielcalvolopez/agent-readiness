# Spec conformance review — agent-readiness-remediation

Evidence date: 2026-09-07. This file is written **for the review subagent**
dispatched at phase 4.4 of `SKILL.md`. The dispatching agent does not need to
read it — pointing a subagent at this path is the whole handoff.

A correctness review asks "is this code wrong?" This is the other half: **"did
this run build what the plan said — all of it, and only it?"** A remediation
diff can be entirely bug-free and still ship with a `fix-now` check quietly
dropped, a fix nobody tested, a secret published into an llms.txt, or three
files refactored that no task asked for. Those are the findings this pass
exists to catch, and the agent that wrote the diff is the least able reader to
catch them.

---

## 0. Your job, and its limits

- **Review only. Do not edit, fix, stage, or commit anything.** You would be
  changing the diff you were asked to judge, and the next phase would verify
  something nobody reviewed. Report the finding; the dispatching agent fixes it.
- **Fresh eyes.** You were not present for the implementation. Do not
  reconstruct the implementer's reasoning and then accept it — judge the diff
  against the plan text as written.
- **Report only what §3's buckets cover.** A reviewer told to find gaps will
  always find some; chasing all of them produces defensive over-engineering.
  §6 says what to leave out.
- **An empty finding list is a valid, good result.** Never manufacture a
  finding to look thorough.

---

## 1. Inputs

Your dispatch prompt gives you: the **plan file path**, the **check IDs** in
your risk group, the **diff command** (a commit range, or the working tree when
the run is in announced edit-only mode), and the **repo root**.

If you were not given a plan file path, **stop and say so**. Reviewing against
a spec someone recited from memory is precisely the failure this phase exists
to prevent, and a review with no governing document is worth nothing. Do not
substitute the scanners' recommendation text, a commit message, or your own
sense of what agent-readiness ought to include.

**Anything else in your prompt is narrative, not evidence.** A correct dispatch
carries only the items above. If yours also describes what was built, why a
choice was made, or which parts are already fine, that is the implementer's
account of its own work — read it as a claim to check, never as a finding you
can skip. Go to the plan and the diff and derive the answer yourself; where your
reading and the account disagree, the artifacts win and the disagreement is
itself worth reporting. The same goes for the diff: if you were handed a summary
of the changes rather than a path or command that yields the real ones, say so
and ask for the diff — you cannot review what you have not seen.

---

## 2. Build the checklist from the plan, before you open the diff

Read the plan first. Reading the diff first anchors you to what was built and
makes an absent task nearly invisible — you cannot miss what you never knew to
look for.

The phase-3 plan carries four sections. Use them like this:

| Plan section | What you extract |
|---|---|
| **Scope** | the full classification table — which check IDs were `fix-now` (your checklist) and which were not (anything else is out of scope by definition) |
| **Tasks** | one entry per `fix-now` check ID, each naming the **observed baseline evidence** it answers and the playbook section it applies. This is the requirement list. |
| **Out of scope** | `accepted-gap`, `product-decision:declined`, `slow-moving` IDs. Work on any of these in the diff is a finding, not a bonus. |
| **Open questions** | blocking user inputs (postal address granularity, `Content-Signal` values, AI-crawler policy, policy copy). A task implemented while its gating input is still open is a finding. |

Write the checklist down before reading a single line of the diff: one row per
check ID in your group, with the baseline evidence it is supposed to answer.

Then read the diff.

---

## 3. The five buckets

Report findings in exactly these buckets. Nothing else is a finding.

### 3.1 Unimplemented plan tasks

A `fix-now` check ID in your group with no corresponding change in the diff.

Judge by the plan's task text, not by whether *something* related changed. A
task that says "add `Vary: Accept` to the markdown-negotiated routes" is not
satisfied by a route that returns markdown without the header. Partial
implementation is a finding — name which half is missing.

Check the inverse too: a task whose change exists but is unreachable (a file
written to a path the framework does not serve, a manifest not linked from
anywhere, a route defined but not exported).

### 3.2 Untested changes

**First establish whether the target has a test runner at all.** Look for the
lockfile's test dependency, a test script, an existing test directory. If there
is no runner, this bucket is not applicable — say that in one line and do not
report every change as untested.

Where there is a runner, the skill's phase-4 rule is: TDD wherever there is
testable logic, and static file content still gets an assertion. So:

- Behavior changes (content negotiation, error shapes, status codes, header
  logic) with no test exercising them → finding.
- Static discovery files (llms.txt, robots.txt, `.well-known` manifests, sitemap
  entries) with no assertion on their content → finding.
- A test that asserts the code was *called* rather than what it *produces* →
  finding, stated as such.

Untested failure paths are the headline finding of this review. "Handled but
untested" is how a fix regresses silently between runs.

### 3.3 Out-of-scope changes

Anything in the diff not traceable to a task in your group's plan entries.

Distinguish carefully, because remediation legitimately touches shared files:

- **In scope:** a supporting edit required to make a plan task work, and
  nothing beyond it — registering a new route, adding a config key the fix
  needs, exporting a helper the fix uses.
- **Finding:** unrelated files touched, renamed exports, reformatting, a
  drive-by refactor, a dependency added, a check worked on that the Scope table
  classified as anything other than `fix-now`, or work on an `Open questions`
  item whose answer never arrived.

Also check commit hygiene where the run is using commits: one check ID per
commit, each named for the check it clears. A commit mixing several check IDs
defeats per-check rollback and attribution — report it. In announced edit-only
mode, skip this and review the working tree as a single set.

These may all turn out to be fine. That is the user's call, not yours and not
the implementer's — flag them so a human decides.

### 3.4 Safety-rule violations — **blocking**

These outrank every other finding in this file. Lead your report with any of
them.

- **A secret on a public surface.** Credentials, tokens, private keys, or
  personal data written into any file the diff publishes. Discovery files
  amplify this class of leak by handing the whole corpus to every crawler in
  one fetch — read what the diff publishes, especially `llms.txt`,
  `llms-full.txt`, sitemaps, and OpenAPI examples. Name the file, path, and
  credential type; **redact the value**; recommend rotation.
- **An SEO dark pattern.** Keyword filler, hidden text, copy written for a
  scanner rather than a reader, or a page padded to clear a character count.
  `sr-only` content is acceptable only with guardrail tests asserting it is not
  `display:none`, not `aria-hidden`, and is real product prose — no guardrail
  test, no pass.
- **A dependency added without recorded approval.** Check the lockfile diff
  against the plan and any approval noted in it. This includes test runners and
  validation libraries a recipe implies.
- **A fabricated observation.** A postal address, a profile URL, a policy
  statement, or a business fact invented to fill a required field rather than
  supplied by the user.

### 3.5 Evidence-traceability gaps

The skill requires every fix to trace to an **observed failure in the baseline**
— a header, a status code, a character count, a specific missing file — not to
a scanner's generic recommendation prose.

Report a finding where:

- the plan task cites no baseline evidence, or cites recommendation text as if
  it were an observation;
- the change does not actually address the evidence cited (baseline observed a
  missing `Vary` header; the diff rewrote the page copy);
- the change is dramatically larger than the observed failure warrants — a
  whole subsystem built where the baseline recorded one absent file.

---

## 4. Safety rules — these bind you too

Restated because you cannot assume you arrived carrying them: secrets outrank the
score and are reported before anything else, with the value redacted; never
publish a secret anywhere, including into your own report; no dependency is
installed without explicit approval; no SEO dark patterns; and a thing you
could not observe is reported as unobserved, never as passing and never as
failing. On top of those, the rule from §0: **you do not edit the repo.**

---

## 5. Report shape

Return exactly this, and nothing else:

```markdown
## Conformance review — <risk group> — <plan filename>

### Safety violations (blocking)
- <what, file:line, redacted> — <required action>

### Unimplemented plan tasks
- <check-id> — plan task "<quoted>"; not found in diff. <file:line or "absent">

### Untested changes
- <check-id> — <file:line> implements it; no test covers <the behavior>.

### Out-of-scope changes
- <file:line> — <what changed> — no task in scope covers this; confirm or revert.

### Evidence-traceability gaps
- <check-id> — <what the baseline observed> vs <what the diff does>.

### Optional (non-blocking)
- <kept short, or omitted entirely>

### Verdict
<one line: conforms / N findings to close before the preview gate>
```

Omit any section with no findings rather than writing "none" under each.
Quote the plan's own words for a task; quote `file:line` for a change. A
finding a reader cannot locate in ten seconds will not get fixed.

---

## 6. Scope discipline — what is NOT a finding here

- **Bugs.** Wrong logic, unhandled inputs, races. Real, and someone else's
  pass — this review does not hunt them, and a bug report here crowds out the
  conformance findings the dispatcher is waiting on.
- **Nice-to-haves and hypotheticals.** Inputs the plan never mentioned, checks
  nobody scoped, hardening the baseline never asked for.
- **Style and taste.** Naming, formatting, file layout — unless the target's own
  documented conventions are violated, which is §3.3.
- **Anything the plan explicitly deferred.** `accepted-gap`,
  `product-decision:declined`, and `slow-moving` IDs were classified by the
  user. Re-opening one is not a review finding; it is the decision being
  overturned by an agent who was not asked.

If something outside these buckets genuinely matters, it goes in **Optional**,
in one line, and never in the verdict.
