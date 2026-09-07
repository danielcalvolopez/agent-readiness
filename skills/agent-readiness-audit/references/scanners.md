# Scanner APIs and scoring — agent-readiness-audit

Loaded at step 2. Both scanners' request shapes, response fields, cache
behaviour and scoring models. Evidence dates are per section; on mismatch, live
scanner output wins over this file.

## 2a. is-agentic (Vercel, powered by Ora)

The scorer most people are actually being graded on. Free, read-only, no key.

```bash
# Latest completed report as JSON — does NOT start a scan
curl -s "https://is-agentic.com/api/v1/report?url=https%3A%2F%2Fexample.com"

# CLI: renders a report, and starts a scan when none exists yet
npx is-agentic example.com --json
```

- Rate limit: 120 req / 60 s per IP. Errors are RFC 9457 `application/problem+json`
  with a stable `code`.
- **`report_not_found` (404) is the expected outcome for most non-apex hosts**, not an
  edge case. Reports are per-host: `example.com` having a score tells you nothing about
  `docs.example.com`. If no report exists, say so plainly — never infer a score from
  the apex — and either start one (`npx is-agentic docs.example.com`, or open
  `https://is-agentic.com/scan/<host>`) or proceed on local evidence alone.
- The `issues[]` array contains **only failed and partial checks** (that is the schema's
  `result` enum). A check's absence means it passed *or* was excluded — you cannot tell
  which, and you cannot enumerate passing checks from the API.
- Response fields: `score`, `score_label`, `scanned_at`, `eligible_checks`,
  `score_breakdown` (`essential` / `recommended` / `bonus`, each with
  `earned`/`available`/`passing`/`total`), and `issues[]` with
  `id`, `name`, `tier`, `result` (`failed` | `partial`), `details`, `recommendation`.
- Reports are cached ~6 h. A score can move because the site changed *or* because
  the methodology changed — always quote `scanned_at`.
- Also available as an MCP server at `https://is-agentic.com/mcp`
  (`is_agentic_get_report`, `is_agentic_get_methodology`, `is_agentic_get_developer_docs`).

**Fetch the check catalog too, every run.** Ora publishes it; is-agentic's
report API does not:

```bash
curl -s https://ora.ai/api/checks    # 200, no key. 125 checks as of 2026-09-04
```

Store the raw body in the baseline artifact's `ora_catalog` (step 5a) and diff
it against the last stored snapshot. It answers three things the report API
cannot: the fix text and weight for a check ID you have no contract for, which
checks are `applicability`-excluded for this target, and — via `specUrl` —
whether a check rests on a real spec or is a scanner opinion. A catalog diff
means the scorer moved, which is a different event from the site regressing;
you can only tell them apart if you kept both.

Field guide and the tier warning: `agent-readiness-remediation/references/check-contracts.md`,
"The Ora catalog". The catalog's `tier` is Ora's own and is **not** the tier
is-agentic scores with — that stays runtime data from `issues[].tier`.

## 2b. isitagentready.com

One call, no cache, ~30 s. It always scans fresh — there is no "fetch the last
report" endpoint and no cache window to wait out.

```bash
curl -s -X POST https://isitagentready.com/api/scan \
     -H 'content-type: application/json' \
     -d '{"url":"https://example.com"}'
```

It scores a **level**, not a percentage: `level` (int), `levelName`,
`nextLevel: {target, name, requirements[]}`. Per-check results live under
`checks.<category>.<checkId>` across five categories — `discoverability`,
`contentAccessibility`, `botAccessControl`, `discovery`, `commerce` — 22 checks
total. Each check is `pass` / `fail` / `neutral`; **`neutral` is excluded from
the denominator**, and there are no tiers and no weights.

`isCommerce` (bool) and `commerceSignals[]` decide whether the `commerce`
category counts at all. On a site with no commerce surface it never does —
report those five checks as not-applicable, never as failures.

Its methodology is not published. Treat the level model as observed behaviour
from the response, not as documented contract. Evidence:
`fixture-isitagentready-baseline.json` (2026-09-04).

> The two scanners disagree about the same site on purpose. is-agentic
> re-buckets Ora's tiers — measured 2026-09-04, Ora calls
> `markdown-negotiation-vary` recommended/maxScore 1 and `trust-anchors`
> required, while is-agentic reported them as essential and recommended
> respectively. Never reconcile them into one number. Report both, diff both.

---

## Scoring model (Is Agentic / Ora)

| Tier | Pool | Behaviour |
|---|---|---|
| essential | 80 | shared, weighted |
| recommended | 20 | shared, weighted |
| bonus | +5 max | additive only; absence never subtracts |

Not-applicable checks are **excluded**, not failed — API/OAuth/MCP/GraphQL/commerce
checks activate only when that surface is positively identified, so a marketing site
is not punished for having no API. Partial results earn proportional credit.

Ora's four layers: Discovery 20 (15 checks), Access 30 (41), Usability 40 (56),
Payments 10 (6) = 118 checks.

Grades: A+ 95–100, A 86–94, B 70–85, C 48–69, D 28–47, F 0–27. The published bands are
integers with gaps between them; the API returns fractional scores. Round half-up to
the nearest integer before assigning a letter, and quote the unrounded score alongside
it — a 47.5 is a D that rounds into C, and someone will notice.

---
