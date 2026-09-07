# Audit outputs — agent-readiness-audit

Loaded at step 5. Every audit run produces two files and both are required:
the machine-readable baseline artifact that remediation's Phase 1 consumes, and
the human report.

## The two outputs

**Every audit run produces two files. Both are required.**

## 5a. REQUIRED — the baseline artifact

`agent-readiness-baseline-<host>-<date>.json`, written next to the report. This
is the file remediation's Phase 1 consumes; a run that produces only prose
cannot be verified against later, because there is nothing to diff.

```json
{
  "host": "example.com",
  "scanned_at": "2026-09-04T11:26:47.711Z",
  "mode": "full",
  "targets": ["https://example.com", "https://docs.example.com"],
  "is_agentic": { "...": "raw API response, unedited" },
  "isitagentready": { "...": "raw API response, unedited" },
  "ora_catalog": { "...": "raw ora.ai/api/checks, or its sha256" },
  "plan": [
    { "check_id": "content-no-js", "tier": "essential",
      "est_delta": 8.0, "class_hint": "fix-now" }
  ]
}
```

Field rules:

- `mode` is `full` or `degraded`, matching step 0. A degraded run still writes
  this file — with the scanner objects present but `null` where a scanner could
  not be reached, never with a fabricated shape.
- The three scanner objects are stored **raw and unedited**. Tiers, weights and
  denominators are runtime data; summarising them here is how a stale tier gets
  hardcoded into a later run.
- `ora_catalog` is the `ora.ai/api/checks` snapshot (see step 2a). Store the
  full body, or its sha256 plus the path to a stored copy.
- `est_delta` is your estimate and is labelled as one. It is an ordering aid,
  never a forecast to report as a predicted score.
- `class_hint` is a *suggestion* for remediation's Phase 2. It never classifies
  anything — only the user does that.

## 5b. The report

Save to the output directory as `agent-readiness-<host>-<date>.md`:

0. **Escalations, if any** — leaked credentials or personal data, first, before the
   score. Values redacted, paths named. Omit the heading entirely when there is
   nothing to escalate; never pad it.
1. **Score line** — official score, grade, `scanned_at`, essential/recommended/bonus
   split. If no official report exists for this host, say that instead of a number.
2. **Method and fidelity** — full or degraded, what you calibrated against, and which
   checks were `not_verified` as a result. A reader must never mistake "not observable
   from here" for "failing".
3. **Failures** — one section per failed check: ID, tier, weight, observed evidence
   (quote the actual header/status/char count), the responsible file or config, the
   exact fix, and the verification command.
4. **Partials** — same, with what specifically is missing for full credit.
5. **Passing** — one line each. Do not pad.
6. **Not applicable / not verified** — kept separate from each other and from
   failures, each with a reason, so nobody "fixes" an excluded check.
7. **Ordered plan** — see ordering below, with an estimated point delta per item and
   the items that need a product decision or a credential called out separately.

Then present the file. Do not paste the whole report into chat.
