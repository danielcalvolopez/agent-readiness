# Check contracts — is-agentic.com & isitagentready.com

Evidence date: 2026-09-01. On mismatch, live scanner output wins over this file.

**is-agentic.com** (Is Agentic / Ora scanner, operated by Vercel Inc.) scores
0–100 across three pools: essential checks share an 80-point pool, recommended
checks share a 20-point pool, and bonus signals add up to 5 points without
becoming requirements. Each pool splits evenly across the checks eligible for
that site (not-applicable checks — e.g. no API, no OAuth, no MCP surface — are
excluded from the denominator, not failed), and a partial result earns
proportional credit. This equal-split rule is not stated in prose anywhere the
evidence checked; it is verified arithmetically against the reference site's own
report (10 passes + one 67% partial across 11 eligible essential checks:
`(10 + 0.67) × (80/11) = 77.60`, matching the observed 77.6/80). **That
77.6/80 figure is from the stale Aug-27 server-rendered snapshot, not the
current report** — the same evidence notes the server-rendered `/scan/<host>`
HTML page can lag the API (it still showed the Aug-27 97/100 snapshot while
the API returned the Sep-1 100/100 report); the arithmetic itself is what's
being verified here, not a claim about the reference site's present score. **Ora
publishes its full check catalog** — see "The Ora catalog" below — but the
*is-agentic report API* does not: its
`issues[]` array carries only failed or partial checks (`id`, `name`, `tier`,
`result`, `details`, `recommendation`) — passing checks can only be inferred
from `score_breakdown`'s `passing`/`total` counts per tier, never enumerated
by ID. Reports are immutable snapshots that refresh only when a visit finds
them older than roughly 6 hours; the API never launches a scan (404 if none is
stored yet), so verifying a fix means running `npx is-agentic <host> --json`
(or the report page's "Rescan" control) and quoting the fresh `scanned_at`
against the baseline's.

**isitagentready.com** (Cloudflare, Inc.'s Agent Readiness Scanner) has no
weighted numeric score model: every check resolves to `pass`, `fail`, or
`neutral` (informational or not-applicable, excluded from denominators),
grouped into five categories — `discoverability`, `contentAccessibility`,
`botAccessControl`, `discovery`, `commerce`. A percentage is computed
client-side per category and overall as `passes / (checks − neutrals) × 100`
across the four categories flagged `countInScore: true`; the response also
carries a server-side `level` (0–5, e.g. 5 "Agent-Native") whose formula is
not published. The `commerce` category (`x402`, `mpp`, `ucp`, `acp`, `ap2`)
never counts toward the score, pass or fail. There is no published cache or
documented rate limit: every `POST /api/scan {url, enabledChecks?}` runs a
fresh live scan and returns a new `scannedAt`.

Additional scoring context, evidenced but outside the pool math above: the
audit skill also quotes Ora's internal description of four check layers —
Discovery (20 pts, 15 checks), Access (30, 41), Usability (40, 56), Payments
(10, 6), totalling 118 checks — and a letter-grade scale (A+ 95–100, A 86–94,
B 70–85, C 48–69, D 28–47, F 0–27) for interpreting the rounded score. How
this four-layer breakdown reconciles with the essential/recommended/bonus
pools is **NOT VERIFIED**; treat both as descriptive framing of the same
underlying score, not two separate scores.
(source: evidence/scanner-docs.md:31-54,91-140,236-253; evidence/audit-skill-alignment.md:46-53)

Neither scanner has a check literally named for CORS headers; `CORS` and
`ratelimit`/`Retry-After` strings are absent from isitagentready's client
bundle and scan responses (grep-verified live, 2026-09-01). The rate-limit
response-header check belongs to is-agentic only (`rate-limit-headers`, see
below). (source: evidence/scanner-docs.md:227-235; specs/001-agent-remediation-skill/research.md:120-133)

---

## The Ora catalog — the machine source for is-agentic checks

Evidence date: 2026-09-04. `GET https://ora.ai/api/checks` → `200`, no key, no
rate limit observed.

```bash
curl -s https://ora.ai/api/checks
```

```json
{ "contractVersion": "...", "layers": [...], "checks": [ { "id": "...", ... } ] }
```

125 checks as of the snapshot — 29 `required`, 76 `recommended`, 20 `emerging`;
by layer: usability 62, accessibility 41, discovery 16, payments 6. Snapshot
stored at `specs/002-skill-review-and-standards/evidence/ora-api-checks-2026-09-04.json`.

Each check carries: `id`, `name`, `description`, `layer`, `maxScore`, `bonus`,
`applicability`, `appliesTo`, `tier`, `maturity`, `draft`, `beta`, `specUrl`,
`recommendation`.

**What each field is good for:**

| Field | Use it for | Do not use it for |
|---|---|---|
| `recommendation` | the fix text for a check this file has no `###` section for | overriding a `###` section that exists — those are evidence-dated against observed behaviour; the catalog is the vendor's prose |
| `specUrl` | standards anchoring; only 18 of 125 have one, and `null` means the check is a scanner opinion, not a ratified spec | proof that a check is standards-backed — read the status class first |
| `applicability` | exclusions. Values observed: `domain-only` (80), `api` (16), `mcp` (14), `all` (11), `mcp-app` (4) | anything on isitagentready, which has no such concept |
| `maxScore` / `tier` | Ora's own weighting; sizing a check the live scan did not classify | **the tier for scoring an is-agentic run** — see the warning below |

> **The catalog's `tier` is Ora's, not is-agentic's.** is-agentic re-buckets
> them. Measured 2026-09-04: Ora calls `markdown-negotiation-vary`
> recommended/`maxScore` 1 and `trust-anchors` required, while the same day's
> is-agentic report returned them as **essential** and **recommended**
> respectively. For scoring, tiers stay runtime data read from that scan's own
> `issues[].tier` and `score_breakdown`. Use the catalog `tier` only to size a
> check the live scan has not classified for you.

**Fetch it at audit time, store it with the baseline, diff it against the
evidence-dated snapshot.** A diff means the scorer's catalog moved — a different
event from a site regressing, and having both snapshots is the only way to tell
them apart afterwards.

---

## Status classes — what a check actually rests on

Every `###` entry carries a **`status:`** field. It answers a question the
scanners never do: *is this a standard, or is it one company's opinion?* That
distinction is what lets a future run tell **"the standard moved"** apart from
**"the scorer changed its mind"** — two events that look identical from a score
diff alone.

| Class | Meaning | What it implies |
|---|---|---|
| **`rfc`** | ratified RFC / W3C Recommendation | stable. If a check disagrees with the RFC, the scanner is wrong — say so and implement the RFC |
| **`ietf-wg-draft`** | IETF WG-adopted Internet-Draft, Standards Track | likely to land, syntax may still move. Safe to implement; re-verify on a version bump |
| **`individual-i-d`** | Internet-Draft with **no** WG adoption | one author's proposal. May expire. Implement only if the scorer requires it |
| **`w3c-cg-draft`** | W3C **Community** Group report | not a W3C Recommendation and not on the Rec track. A CG is any group of members, not a chartered WG |
| **`vendor-convention`** | published spec from one vendor or foundation | the majority of this file. Real and widely implemented, but nobody has ratified it |
| **`scanner-opinion`** | no external spec at all | the scorer's product judgement. `specUrl` is `null` in the Ora catalog. It can change without notice and there is nothing to appeal to |

Two traps this field exists to expose:

- **`contentSignals`** looks standards-backed because AIPREF is a real IETF WG.
  `Content-Signal:` itself is Cloudflare's convention, and the draft that
  defined it — `draft-romm-aipref-contentsignals-00` — is an **expired
  individual I-D**, not a WG document.
- **`mcpServerCard`** is checked by a scanner but the `.well-known` server card
  is **not in the ratified MCP spec**. SEP-2127 is an open PR, and the
  experimental repo hosting the card says outright it is "not an accepted or
  official MCP extension."

No ratified "agent readiness" standard exists — IETF, W3C, ISO and NIST were
all checked on 2026-09-04 and none defines it. What exists is ratified RFCs used
as building blocks, WG drafts above them, CG drafts above those, and vendor
conventions on top. Full survey with URLs and page dates:
`specs/002-skill-review-and-standards/evidence/standards-landscape-2026-09-04.md`.

---

## is-agentic checks

Tier/weight below are stated only where the evidence states them. Where a
check's tier or weight is not recorded here, the Ora catalog above carries
Ora's own `tier`/`maxScore` for it — but the value that scores an is-agentic run
is still read from that scan's `issues[].tier` and
`score_breakdown` at run time, and is never hardcoded (Principle/decision D1,
`specs/001-agent-remediation-skill/research.md:106-118`). Row schema per
check: scanner, tier, weight, observes, pass, evidence_cmd, playbooks, source.

`agent-readiness-audit/SKILL.md` line numbers below are as recorded inside
`evidence/audit-skill-alignment.md` (that file states its own line numbers
refer to the original, locally-uninstalled `SKILL.md`, not to itself).

### content-no-js
- **scanner:** is-agentic
- **tier:** essential — audit skill calls it "the heaviest single check"; live evidence confirms essential tier
- **weight:** runtime data (pool ÷ eligible-count; observed ≈7.27 pts for the reference site's 11-eligible essential set on 2026-09-01 — varies per site)
- **status:** `scanner-opinion` — no spec defines a 500-character floor or a heading-depth rule
- **observes:** raw (no-JS) HTML of the homepage
- **pass:** one `<h1>` and ≥500 chars of visible text in the raw HTML response, non-flat heading structure. Live evidence recorded a real partial: "780 chars with H1 but flat heading structure" → 67% credit on an earlier reference-site snapshot.
- **evidence_cmd:** `curl -s https://$HOST/ | python3 -c "import re,sys; h=sys.stdin.read(); t=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',re.sub(r'(?is)<(script|style|noscript|svg|template)\b.*?</\1>',' ',h))); print(len(t.strip()))"` (expect ≥500); cross-check against the scanner: `curl -s "https://is-agentic.com/api/v1/report?url=https%3A%2F%2F$HOST" | jq '.score_breakdown.essential'`
- **playbooks:** playbook-nextjs-app-router.md (recipe evidenced: `evidence/reference-branch-recipes.md:46-75`); playbook-generic.md (fallback)
- source: agent-readiness-audit/SKILL.md:L75,205-206,268-272,345-364 (via evidence/audit-skill-alignment.md:16); evidence/scanner-docs.md:65-67,160-167

### canonical-correctness
- **scanner:** is-agentic
- **tier:** essential (audit skill)
- **weight:** runtime data — not independently observed in live evidence
- **status:** `vendor-convention` — rel=canonical, long-standing web convention
- **observes:** the declared canonical of 2–3 interior pages
- **pass:** the canonical points at the page's own URL, never the root/shared-layout value
- **evidence_cmd:** `for p in /about /contact /case-studies /news; do echo -n "$p -> "; curl -s "https://$HOST$p" | grep -o '<link rel="canonical"[^>]*>' || echo MISSING; done`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:78-98`); playbook-generic.md
- source: agent-readiness-audit/SKILL.md:L68,229-233,273-277,366-376 (via evidence/audit-skill-alignment.md:17); evidence/reference-branch-recipes.md:78-98

### agent-friendly-404
- **scanner:** is-agentic
- **tier:** essential — audit skill states it directly; live evidence's own table marks the literal check ID itself "NOT VERIFIED" (the behavior was only confirmed via an npm README sample for a different site) but agrees on essential tier, same pool as `content-no-js`.
- **weight:** runtime data
- **status:** **`rfc`** — RFC 9110 status semantics
- **observes:** response for a nonexistent path
- **pass:** real HTTP 404/410, not `200` + app shell; body links `/llms.txt`, `/sitemap.xml`, docs, `/openapi.json`; markdown body under Accept negotiation for full credit
- **evidence_cmd:** `curl -s -o /dev/null -w "%{http_code}" https://$HOST/does-not-exist-xyz`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:248-269`); playbook-generic.md
- source: agent-readiness-audit/SKILL.md:L74,224-226,378-385 (via evidence/audit-skill-alignment.md:18); evidence/scanner-docs.md:68

### markdown-negotiation-vary
- **scanner:** is-agentic
- **tier:** essential (audit skill)
- **weight:** runtime data
- **status:** **`rfc`** — RFC 9110 (content negotiation), RFC 7763 (`text/markdown`)
- **observes:** response to `Accept: text/markdown` on negotiated page paths, and to an unsupported explicit `Accept`
- **pass:** four criteria — serves `text/markdown` for `Accept: text/markdown`; `Vary: Accept` is **appended**, never overwrites Next's own `Vary` values; `406` for a genuinely unsupported explicit type; q-values honored
- **evidence_cmd:** `curl -sI -H "Accept: text/markdown" https://$HOST/ | grep -i 'content-type\|vary'` and `curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/vnd.nonexistent" https://$HOST/`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:273-362`); playbook-generic.md
- **note:** distinct from isitagentready's own `markdownNegotiation` check below — same underlying behavior, different scanner/ID/scoring; one implementation typically satisfies both.
- source: agent-readiness-audit/SKILL.md:L73,216-221,387-395 (via evidence/audit-skill-alignment.md:19); evidence/reference-branch-recipes.md:273-362

### sitemap
- **scanner:** is-agentic
- **tier:** not stated — runtime data, read from `issues[].tier`
- **weight:** runtime data
- **status:** `vendor-convention` — sitemaps.org 0.9
- **observes:** `/sitemap.xml`
- **pass:** present, absolute URLs, real `lastmod`, declared in robots.txt
- **evidence_cmd:** `curl -s https://$HOST/sitemap.xml | head -20`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:133-161`); playbook-generic.md
- **note:** distinct from isitagentready's own `sitemap` check below.
- source: agent-readiness-audit/SKILL.md:L64,422-424 (via evidence/audit-skill-alignment.md:20); evidence/reference-branch-recipes.md:133-161

### llms-txt
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `vendor-convention` — llmstxt.org v2 — Answer.AI, self-described as open for community input
- **observes:** `/llms.txt` (and `/llms-full.txt`)
- **pass:** present and llmstxt.org-v2 compliant — required H1 naming the project, `>` blockquote summary, optional free markdown, H2-delimited link sections, absolute `.md`-linked entries with descriptions
- **evidence_cmd:** `curl -sI https://$HOST/llms.txt | grep -i content-type` and `curl -s https://$HOST/llms.txt | head -5`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:164-200`); playbook-generic.md
- source: agent-readiness-audit/SKILL.md:L64-65,410-418 (via evidence/audit-skill-alignment.md:21); evidence/scanner-docs.md:305-313; evidence/reference-branch-recipes.md:164-200

### agent-instruction
- **scanner:** is-agentic
- **tier:** recommended, same pool
- **weight:** runtime data
- **status:** `scanner-opinion` — AGENTS.md is a vendor convention with "no required fields"; the "When to use this" criterion is Ora’s
- **observes:** an agent-instruction file (llms.txt or a dedicated file, e.g. under `/.well-known/agent-skills/`)
- **pass:** explicit when-to-use guidance naming best-fit use cases; audit skill's version of the same check requires a literal `## When to use this` section naming concrete jobs, the exact endpoint, and what the site is *not* for — generic marketing copy scores zero. Currently partial on the reference site.
- **evidence_cmd:** `curl -s https://$HOST/llms.txt | grep -A6 "When to use"`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:164-200`); playbook-generic.md
- source: evidence/scanner-docs.md:75,163-167; agent-readiness-audit/SKILL.md:L66,419-421 (via evidence/audit-skill-alignment.md:22); evidence/reference-branch-recipes.md:164-200

### robots-txt
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** **`rfc`** — RFC 9309 Robots Exclusion Protocol
- **observes:** `/robots.txt`
- **pass:** published; note the audit skill's own caveat that is-agentic may not penalize outright absence of this file (its own citation is uncertain on that point)
- **evidence_cmd:** `curl -s https://$HOST/robots.txt`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:102-129`); playbook-generic.md
- **note:** distinct from isitagentready's own `robotsTxt` check below.
- source: agent-readiness-audit/SKILL.md:L64,262-266,422 (via evidence/audit-skill-alignment.md:23); evidence/reference-branch-recipes.md:102-129

### ai-crawler-access
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** **`rfc`** — RFC 9309 (the syntax); the AI-crawler UA list itself is vendor convention
- **observes:** named AI crawler `User-agent` rules in `/robots.txt`, plus whether CDN bot protection overrides them
- **pass:** the ten named crawlers allowed (GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-User, Claude-SearchBot, PerplexityBot, Perplexity-User, Google-Extended, Applebot-Extended) **and** CDN-level bot protection (e.g. Cloudflare "Block AI Scrapers"/Bot Fight Mode) checked separately so it does not silently override robots.txt
- **evidence_cmd:** `curl -s https://$HOST/robots.txt | grep -iA3 'gptbot\|claudebot\|perplexitybot'`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:102-129`); playbook-generic.md
- **note:** distinct from isitagentready's own `robotsTxtAiRules` check below — overlapping subject, separate scanner/ID.
- source: agent-readiness-audit/SKILL.md:L262,424-428 (via evidence/audit-skill-alignment.md:24); evidence/reference-branch-recipes.md:102-129

### openapi-spec
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `vendor-convention` — OpenAPI Specification v3.2.0 (Linux Foundation)
- **observes:** presence and linkage of an OpenAPI document
- **pass:** OpenAPI 3.1 at `/openapi.json`, linked from `<head>` via `rel="service-desc"`, from `/llms.txt`, and from `/.well-known/api-catalog`
- **evidence_cmd:** `curl -s https://$HOST/openapi.json | python3 -m json.tool > /dev/null && echo valid`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:418-443`); playbook-generic.md
- source: agent-readiness-audit/SKILL.md:L67,397-401 (via evidence/audit-skill-alignment.md:25); evidence/reference-branch-recipes.md:418-443

### json-error-responses
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** **`rfc`** — RFC 9457 Problem Details for HTTP APIs
- **observes:** API error responses, including unknown routes and wrong HTTP methods
- **pass:** RFC 9457 `application/problem+json` with a stable machine `code` and human `resolution`, on unknown routes and wrong methods too, not just documented success paths
- **evidence_cmd:** `curl -s -o /dev/null -w "%{http_code} %{content_type}\n" https://$HOST/api/nonexistent`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:366-414`); playbook-generic.md
- source: agent-readiness-audit/SKILL.md:L79,270-272,402-404 (via evidence/audit-skill-alignment.md:26); evidence/reference-branch-recipes.md:366-414; evidence/scanner-docs.md:315-323 (RFC 9457 field shape)

### api-schema-analysis
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `vendor-convention` — OpenAPI v3.2.0
- **observes:** the OpenAPI operation objects
- **pass:** every operation has a unique `operationId`, a `description`, typed parameters, and a response schema
- **evidence_cmd:** `curl -s https://$HOST/openapi.json | jq '[.paths[][] | {operationId, description}]'`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:418-443`); playbook-generic.md
- source: agent-readiness-audit/SKILL.md:L397,401-403 (via evidence/audit-skill-alignment.md:27); evidence/reference-branch-recipes.md:418-443

### function-calling-compat
- **scanner:** is-agentic
- **tier:** recommended, same pool
- **weight:** runtime data
- **status:** `vendor-convention` — OpenAPI v3.2.0
- **observes:** the same OpenAPI operation objects as `api-schema-analysis`
- **pass:** operations carry unique `operationId`s, typed schemas, and descriptions good enough for direct LLM tool-definition conversion. Live evidence recorded a real partial on the reference site: "4/4 operationIds, 2/4 typed schemas."
- **evidence_cmd:** `curl -s https://$HOST/openapi.json | jq '[.paths[][] | select(.operationId!=null)] | length'`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:418-443`); playbook-generic.md
- source: evidence/scanner-docs.md:73,165-166; agent-readiness-audit/SKILL.md:L397-404 (via evidence/audit-skill-alignment.md:28)

### json-ld
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `vendor-convention` — Schema.org (W3C CG vocabulary); no agent-specific types exist
- **observes:** server-rendered `<script type="application/ld+json">` blocks
- **pass:** at least one server-rendered JSON-LD block present (not client-injected)
- **evidence_cmd:** `curl -s https://$HOST/ | grep -c 'application/ld+json'`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:203-245`); playbook-generic.md
- source: agent-readiness-audit/SKILL.md:L76,430-432 (via evidence/audit-skill-alignment.md:29); evidence/reference-branch-recipes.md:203-245

### org-schema-completeness
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `vendor-convention` — Schema.org Organization
- **observes:** the `Organization` node inside the JSON-LD graph
- **pass:** `Organization` with `contactPoint` (`contactType` + email/phone) **and** `address` (`PostalAddress`). Both are required for full credit, not either/or. **`sameAs` is NOT required** (corrected 2026-09-04)
- **evidence_cmd:** `curl -s https://$HOST/ | grep -o '"@type":"Organization".*' | head -c 2000`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:203-245`); playbook-generic.md
- **correction (2026-09-04):** this entry previously required "`sameAs` with ≥3 real, verified profiles", inherited from the audit skill's inline reference. Two independent sources say otherwise. Ora's own `recommendation` for the check: *"Add Organization JSON-LD that includes both contactPoint (with email/phone and contactType) and address (PostalAddress). This lets AI verify your business legitimacy and answer contact queries."* — `sameAs` unmentioned. And a production preview scan cleared the check with a single profile present. The cost of the wrong fact is on record: an agent following it made confirmed-official social-profile URLs a **blocking** question to the user (`evidence/red-baselines-2026-09-04.md`, T1). `sameAs` is still worth publishing — it just does not gate this check
- source: ora.ai/api/checks 2026-09-04 (`evidence/ora-api-checks-2026-09-04.json`); `evidence/fixture-isagentic-preview.json`; superseded: agent-readiness-audit/SKILL.md:L76,430-435 (via evidence/audit-skill-alignment.md:30)

### trust-anchors
- **scanner:** is-agentic
- **tier:** recommended, same pool (live evidence) — tier NOT VERIFIED beyond that
- **weight:** runtime data
- **status:** `scanner-opinion` — no spec requires /about, /contact, /privacy at 500 chars
- **observes:** `/about`, `/contact`, `/privacy`
- **pass:** real pages exist at `/about`, `/contact` and `/privacy`, each independently carrying ≥500 chars of visible text. **Confirmed 2026-09-04** against Ora's own `recommendation`: *"Publish real /about, /contact, and /privacy pages with at least 500 characters of content each. These are the pages AI agents check to verify your business is legitimate before recommending you."* No open discrepancy — this entry is the only statement of the criterion anywhere in either skill.
- **evidence_cmd:** `for p in about contact privacy; do curl -s https://$HOST/$p | python3 -c "import sys,re; print(len(re.sub('<[^>]+>',' ',sys.stdin.read())))"; done`
- **playbooks:** playbook-generic.md (no framework-specific recipe evidenced; the audit skill's json-ld/org-schema recipe does not cover this literal check's criterion)
- source: ora.ai/api/checks 2026-09-04 (`evidence/ora-api-checks-2026-09-04.json`); evidence/scanner-docs.md:74

### metadata-completeness
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `vendor-convention` — OpenGraph + rel=canonical + html lang
- **observes:** four presence-only signals in the rendered `<head>`
- **pass:** exactly `<link rel="canonical">`, `<html lang="…">`, `og:image`, `og:type` all present (presence only — value correctness of the canonical is the separate `canonical-correctness` check)
- **evidence_cmd:** `curl -s https://$HOST/ | grep -oE '<link rel="canonical"[^>]*>|<html[^>]*lang="[^"]*"|og:image|og:type'`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:78-98`, canonical half); playbook-generic.md
- source: agent-readiness-audit/SKILL.md:L77,273-277,437-441 (via evidence/audit-skill-alignment.md:32)

### mcp-server
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `vendor-convention` — MCP spec 2026-07-28 (Agentic AI Foundation). The `.well-known` server card is NOT in the ratified spec — SEP-2127 is an open PR
- **observes:** `/.well-known/mcp/server-card.json` or `/server.json`
- **pass:** either file present
- **evidence_cmd:** `curl -s https://$HOST/.well-known/mcp/server-card.json | python3 -m json.tool > /dev/null && echo valid`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:533-547`); playbook-generic.md
- **note:** distinct from isitagentready's own `mcpServerCard` check below (same file typically satisfies both).
- source: agent-readiness-audit/SKILL.md:L237,443-445 (via evidence/audit-skill-alignment.md:33); evidence/reference-branch-recipes.md:533-547

### ai-catalog
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `vendor-convention` — ARD predecessor `/.well-known/ai-catalog.json`
- **observes:** `/.well-known/ai-catalog.json`
- **pass:** file present
- **evidence_cmd:** `curl -sI https://$HOST/.well-known/ai-catalog.json`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:447-473`); playbook-generic.md
- **note:** not the same spec as isitagentready's `apiCatalog` check (RFC 9727 `/.well-known/api-catalog`) — different well-known path, different document shape. It IS the same manifest as isitagentready's `ard` check below (see that entry).
- source: agent-readiness-audit/SKILL.md:L237,443-445 (via evidence/audit-skill-alignment.md:34); evidence/reference-branch-recipes.md:447-473

### cli-tool
- **scanner:** is-agentic
- **tier:** recommended, same pool
- **weight:** runtime data
- **status:** `scanner-opinion` — no spec requires a published CLI
- **observes:** npm, PyPI, or Homebrew registries
- **pass:** a real published package (a thin API wrapper exposing a `--json` flag suffices per the audit skill); `--offline-fixtures`/no-egress makes this not-applicable rather than failed
- **currently failing on the reference site** and accepted as an out-of-scope product decision on the reference branch, not a planned fix — bonus signals covered the score gap instead
- **evidence_cmd:** `curl -s https://registry.npmjs.org/<package-name>` or `npm view <package-name> version`
- **playbooks:** playbook-generic.md only — explicitly out of scope on the reference branch
- source: evidence/scanner-docs.md:70,165; agent-readiness-audit/SKILL.md:L167-168,443-448 (via evidence/audit-skill-alignment.md:35); evidence/reference-branch-recipes.md:594-598

### content-efficiency
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `scanner-opinion` — the 5% text-to-bytes ratio is Ora’s own threshold
- **observes:** ratio of visible text to total HTML bytes
- **pass:** visible text ≥5% of HTML bytes
- **evidence_cmd:** compare `curl -s https://$HOST/ | wc -c` against the visible-text byte count from the `content-no-js` extraction command above
- **playbooks:** playbook-nextjs-app-router.md (usually a byproduct of the `content-no-js` fix, `evidence/reference-branch-recipes.md:46-75`); playbook-generic.md
- source: agent-readiness-audit/SKILL.md:L75,207,450-454 (via evidence/audit-skill-alignment.md:36)

### agentic-search-specific
- **scanner:** is-agentic
- **tier:** recommended, same pool — live evidence flags the tier itself as NOT VERIFIED even though it lists it under "recommended"
- **weight:** runtime data
- **status:** `scanner-opinion` — externally-indexed judgement
- **observes:** developer-resource discoverability via search and internal linking
- **pass:** developer resources findable via search / listed in `/llms.txt`; audit skill's fuller version: product name in every docs `<title>`/`<h1>`, predictable URLs, everything present in llms.txt, `AGENTS.md` in the public repo. Findability, not existence — this check moves with search-indexing lag; do not churn waiting on it after a correct deploy.
- **evidence_cmd:** `curl -s https://$HOST/developers | grep -o "<title>[^<]*</title>"`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:418-443`); playbook-generic.md
- source: evidence/scanner-docs.md:77; agent-readiness-audit/SKILL.md:L69,456-459 (via evidence/audit-skill-alignment.md:37); evidence/reference-branch-recipes.md:418-443

### brand-search-accuracy
- **scanner:** is-agentic
- **tier:** recommended, same pool — live evidence flags the tier itself as NOT VERIFIED
- **weight:** runtime data
- **status:** `scanner-opinion` — externally-indexed judgement
- **observes:** whether a brand-name search surfaces the site's pages
- **pass:** name search surfaces the site's pages; audit skill's fuller framing: consistent NAP (name/address/phone), press links resolving to the apex canonical, no redirect chains. Moves over weeks via external signals — never blocks a release on it.
- **evidence_cmd:** no reliable direct probe; read the scanner's own finding: `curl -s "https://is-agentic.com/api/v1/report?url=https%3A%2F%2F$HOST" | jq '.issues[] | select(.id=="brand-search-accuracy")'`
- **playbooks:** playbook-generic.md only — this is an ongoing external-signal check, not a deploy
- source: evidence/scanner-docs.md:76; agent-readiness-audit/SKILL.md:L456,459-461 (via evidence/audit-skill-alignment.md:38); evidence/reference-branch-recipes.md:594-598

### https-and-transport
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** **`rfc`** — TLS / HSTS RFCs
- **observes:** transport-layer HTTP headers (header-dependent; audit skill lists it only in its degraded-mode "not checkable" table)
- **pass:** NOT VERIFIED — neither evidence file publishes an explicit pass criterion for this check
- **evidence_cmd:** `curl -sI https://$HOST/`
- **playbooks:** none evidenced — playbook-generic.md only, pending a concrete recipe
- source: agent-readiness-audit/SKILL.md:L78 (via evidence/audit-skill-alignment.md:39)

### bot-protection
- **scanner:** is-agentic
- **tier:** not stated — runtime data
- **weight:** runtime data
- **status:** `scanner-opinion` — Ora’s judgement about CDN behaviour
- **observes:** header/CDN-level bot-protection behavior (header-dependent; degraded-mode-only listing)
- **pass:** NOT VERIFIED — no explicit pass criterion published in either evidence file
- **evidence_cmd:** `curl -sI https://$HOST/ -H "User-Agent: GPTBot"`
- **playbooks:** none evidenced — playbook-generic.md only
- source: agent-readiness-audit/SKILL.md:L78 (via evidence/audit-skill-alignment.md:40)

### rate-limit-headers
- **scanner:** is-agentic
- **tier:** recommended, same pool
- **weight:** runtime data
- **status:** **`ietf-wg-draft`** — draft-ietf-httpapi-ratelimit-headers-11 (HTTPAPI WG, Standards Track)
- **observes:** RFC RateLimit response headers and `Retry-After` on a live `429` response
- **pass:** standard `RateLimit-*` headers and `Retry-After` observed on a live response and documented in the OpenAPI spec; documentation without a live observed header only earns partial credit
- **evidence_cmd:** `curl -sI -X POST https://$HOST/api/contact | grep -i ratelimit`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:550-568`); playbook-generic.md
- **note:** this is the same check the audit skill names `rate-limit-signalling` in its own degraded-mode table, where it states "no remediation recipe exists for it" in `SKILL.md` itself. The reference branch authored a working recipe independently (`playbook-nextjs-app-router.md` above); per D2 in research.md, ownership belongs to is-agentic, not isitagentready.
- source: evidence/scanner-docs.md:72,227-234; agent-readiness-audit/SKILL.md:L78 (via evidence/audit-skill-alignment.md:41); evidence/reference-branch-recipes.md:550-568; specs/001-agent-remediation-skill/research.md:120-133 (D2)

### api-versioning-policy
- **scanner:** is-agentic
- **tier:** recommended, same pool (weight observed ≈0.95 pts for the reference site's eligible set on 2026-09-01 — site-specific, not fixed)
- **weight:** runtime data
- **status:** **`rfc`** — RFC 9745 Deprecation header
- **observes:** URL-path or header API versioning plus deprecation signaling
- **pass:** `/v1/`-style URL-path versioning or header versioning declared in the OpenAPI spec, **and** documented deprecation signaling (`Sunset`/`Deprecation` header or a stated timeline). Currently failing on the reference site.
- **evidence_cmd:** `curl -s https://$HOST/openapi.json | jq '.servers, .info.description' | grep -i "v1\|deprecat"`
- **playbooks:** none evidenced — playbook-generic.md only
- **note:** not present in the audit skill's inventory — is-agentic-only, evidenced solely from live scan data.
- source: evidence/scanner-docs.md:69,165

### public-api-docs
- **scanner:** is-agentic
- **tier:** recommended, same pool
- **weight:** runtime data
- **status:** `vendor-convention` — OpenAPI v3.2.0
- **observes:** discoverability and homepage linkage of API documentation
- **pass:** API docs exist at a discoverable URL (`/docs`, `/api`, `/developers`) **and** are linked from the homepage. Live evidence recorded a real partial on the reference site: "found at /developers but not linked from homepage."
- **evidence_cmd:** `curl -s https://$HOST/ | grep -o 'href="/developers"'`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:418-443` — add the homepage link); playbook-generic.md
- **note:** not present in the audit skill's inventory — is-agentic-only.
- source: evidence/scanner-docs.md:71,165-166; evidence/reference-branch-recipes.md:418-443

### Payments checks (no published ID)
- **scanner:** is-agentic
- **tier:** described only as a named layer ("Payments", 10 pts / 6 checks) in Ora's internal four-layer breakdown quoted by the audit skill — **no per-check ID is published anywhere in the evidence**; do not invent one
- **weight:** runtime data
- **observes:** commerce/agentic-payment surface, only when one is positively identified
- **pass:** `/pricing.md`, JSON-LD `offers`, and an agentic payment protocol (x402 / AP2 / ACP) declared in the AI catalog — **only if agents should transact on the site**. No commerce surface → excluded from scoring, not failed; never "fix" this on a site with no commerce surface.
- **evidence_cmd:** `curl -s https://$HOST/pricing.md`
- **playbooks:** playbook-generic.md only — no framework-specific recipe evidenced (the reference site has no commerce surface)
- source: agent-readiness-audit/SKILL.md:L463-467 (via evidence/audit-skill-alignment.md:42); evidence/reference-branch-recipes.md:594-598

---

### oauth-support
- **scanner:** is-agentic
- **tier:** Ora catalog says `required`, `maxScore` 5 — **read the live scan's `issues[].tier` for scoring**; is-agentic re-buckets
- **weight:** runtime data (Ora `maxScore` 5 — the heaviest single check in the catalog)
- **status:** scanner-opinion for the check itself (`specUrl: null`); the artefacts it asks for are `rfc` — RFC 8414 authorization server metadata, RFC 9728 protected resource metadata
- **observes:** OAuth 2.0 support, **or** an explicitly open API needing no keys at all
- **pass:** Ora's description — *"Agents need a standard way to sign in. We check for OAuth 2.0, or an explicitly open API that needs no keys at all."* Its recommendation: *"Implement OAuth 2.0 for API authentication. Publish your authorization server metadata at /.well-known/oauth-authorization-server."*
- **evidence_cmd:** `curl -s -o /dev/null -w "%{http_code}\n" https://$HOST/.well-known/oauth-authorization-server`
- **playbooks:** playbook-generic.md §17 (`oauthDiscovery` / `oauthProtectedResource`)
- **note:** **product decision, never a code fix.** Publishing RFC 8414 metadata for an authorization server you do not operate is fabrication — a site that delegates login to a third-party IdP does not thereby have one to advertise. The second half of the criterion is the real option for most sites: an API that genuinely needs no keys, documented as such. If neither is true, this is `accepted-gap`, documented in `auth.md` (playbook-generic.md §4)
- source: ora.ai/api/checks 2026-09-04 (`evidence/ora-api-checks-2026-09-04.json`); RED evidence `evidence/red-baselines-2026-09-04.md` T1

### onboarding-friction
- **scanner:** is-agentic
- **tier:** Ora catalog says `recommended`, `maxScore` 2 — read the live scan's `issues[].tier` for scoring
- **weight:** runtime data
- **status:** scanner-opinion (`specUrl: null`) — no standard defines this; it is Ora's product judgement
- **observes:** whether an agent can go from discovery to a first successful API call with no human in the loop
- **pass:** Ora's recommendation — *"Offer a free tier or trial, self-serve API key generation, and a sandbox environment. Agents can't fill out 'contact sales' forms."*
- **evidence_cmd:** none automatable — this is a product-surface judgement. Read the scan's own `details` string for what it observed; is-agentic may return an empty `recommendation`
- **playbooks:** none — no code recipe exists, and one would be a product build
- **note:** **product decision.** It changes how customers sign up, so it is never covered by a blanket delegation (SKILL.md Phase 2). Size it from the scan's `score_breakdown` before proposing work: at `maxScore` 2 it is usually a fraction of what a single essential check is worth
- source: ora.ai/api/checks 2026-09-04 (`evidence/ora-api-checks-2026-09-04.json`); RED evidence `evidence/red-baselines-2026-09-04.md` T1

## isitagentready checks

Default presets (from the client bundle, live-verified): "All Checks" runs
every check **except** `a2aAgentCard` and `ap2` — though a bare `POST
/api/scan` without an explicit `enabledChecks` list still ran `a2aAgentCard`
server-side on 2026-09-01, so this exclusion is not fully reliable; "Content
Site" = `discoverability` + `contentAccessibility` + `botAccessControl` only;
"API / Application" = everything except `commerce` and `a2aAgentCard`/`ap2`.
There are no per-check tiers or weights anywhere on this scanner — every
check's `tier`/`weight` field below is "none (pass/fail/neutral only)"; do
not invent one. (source: evidence/scanner-docs.md:195-200)

### robotsTxt
- **scanner:** isitagentready
- **category:** discoverability
- **spec:** RFC 9309
- **tier / weight:** none (pass/fail/neutral)
- **status:** **`rfc`** — RFC 9309 Robots Exclusion Protocol
- **observes:** `GET /robots.txt`
- **pass:** exists, plain text, `200`, valid format
- **evidence_cmd:** `curl -s https://$HOST/robots.txt`
- **playbooks:** playbook-generic.md (`evidence/reference-branch-recipes.md:102-129`)
- source: evidence/scanner-docs.md:191,204

### sitemap
- **scanner:** isitagentready
- **category:** discoverability
- **spec:** (no external RFC cited; sitemap.xml convention)
- **tier / weight:** none
- **status:** `vendor-convention` — sitemaps.org 0.9
- **observes:** `sitemap.xml`
- **pass:** exists with valid structure; referenced from robots.txt
- **evidence_cmd:** `curl -s https://$HOST/sitemap.xml | head`
- **playbooks:** playbook-generic.md (`evidence/reference-branch-recipes.md:133-161`)
- source: evidence/scanner-docs.md:191,205

### linkHeaders
- **scanner:** isitagentready
- **category:** discoverability
- **spec:** RFC 8288
- **tier / weight:** none
- **status:** **`rfc`** — RFC 8288 Web Linking
- **observes:** HTTP `Link` response headers
- **pass:** agent-useful relations present — the reference site passes with `api-catalog`, `service-desc`, `describedby`
- **evidence_cmd:** `curl -sI https://$HOST/ | grep -i '^link:'`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:447-473`, `next.config.ts headers()`)
- source: evidence/scanner-docs.md:191,206

### dnsAid
- **scanner:** isitagentready
- **category:** discoverability
- **spec:** draft-mozleywilliams-dnsop-dnsaid; RFC 9460 (SVCB)
- **tier / weight:** none
- **status:** **`individual-i-d`** — draft-mozleywilliams-dnsop-dnsaid-02 — active but NO WG adoption
- **observes:** a DNS discovery record
- **pass:** discovery record found — the reference site passes at `_index._agents.the reference site`
- **evidence_cmd:** `dig +short SVCB _index._agents.$HOST` (a DNS record — not an HTTP probe)
- **playbooks:** none evidenced — this is a DNS-zone action outside the application repo, not a code recipe
- **note:** two different DNS-AID record names appear across the evidence — this check's own record is `_index._agents` (scanner-docs.md), while the MCP route's own code comment references a separate `_mcp._agents` record as its discovery channel (reference-branch-recipes.md). Treat them as two distinct advertisement channels under the same draft-dnsaid convention, not a typo of one another.
- source: evidence/scanner-docs.md:191,207; evidence/reference-branch-recipes.md:546

### markdownNegotiation
- **scanner:** isitagentready
- **category:** contentAccessibility
- **spec:** Cloudflare "Markdown for Agents" convention (acceptmarkdown.com)
- **tier / weight:** none
- **status:** **`rfc`** — RFC 9110 content negotiation, RFC 7763 `text/markdown`
- **observes:** response to `Accept: text/markdown`
- **pass:** "Site supports Markdown for Agents" — server responds `Content-Type: text/markdown; charset=utf-8` with `Vary: Accept`
- **evidence_cmd:** `curl -sI -H "Accept: text/markdown" https://$HOST/ | grep -i content-type`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:273-362` — same implementation satisfies is-agentic's `markdown-negotiation-vary` above)
- source: evidence/scanner-docs.md:191,208; evidence/scanner-docs.md:325-333 (acceptmarkdown.com spec detail)

### robotsTxtAiRules
- **scanner:** isitagentready
- **category:** botAccessControl
- **spec:** (robots.txt `User-agent` convention, no single RFC)
- **tier / weight:** none
- **status:** **`rfc`** — RFC 9309 (the syntax); the AI-crawler UA list is vendor convention
- **observes:** AI-crawler `User-agent` rules in robots.txt
- **pass:** explicit rules for AI bots — the reference site passes with gptbot, chatgpt-user, google-extended, perplexitybot, applebot-extended
- **evidence_cmd:** `curl -s https://$HOST/robots.txt | grep -iA2 gptbot`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:102-129`)
- source: evidence/scanner-docs.md:191,209

### contentSignals
- **scanner:** isitagentready
- **category:** botAccessControl
- **spec:** contentsignals.org; draft-romm-aipref-contentsignals
- **tier / weight:** none
- **status:** **`ietf-wg-draft`** — IETF AIPREF WG (draft-ietf-aipref-vocab-07 / -attach-05). NOTE: `Content-Signal:` itself is Cloudflare vendor convention — draft-romm-aipref-contentsignals-00 is an EXPIRED individual I-D, not a WG document
- **observes:** Content Signals policy line(s) in robots.txt
- **pass:** signals present
- **evidence_cmd:** `curl -s https://$HOST/robots.txt | grep -i content-signal`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:102-129`)
- source: evidence/scanner-docs.md:191,210

### webBotAuth
- **scanner:** isitagentready
- **category:** botAccessControl
- **spec:** IETF Web Bot Auth
- **tier / weight:** none
- **status:** **`ietf-wg-draft`** — draft-ietf-webbotauth-httpsig-protocol-00 (WEBBOTAUTH WG), over RFC 9421
- **observes:** a Web Bot Auth directory
- **pass:** **informational only** — absence resolves to `neutral`, not `fail`. Reference site.org is currently neutral on this check.
- **evidence_cmd:** `curl -s https://$HOST/.well-known/http-message-signatures-directory`
- **playbooks:** none evidenced — non-blocking by design
- source: evidence/scanner-docs.md:191,211,296-299

### apiCatalog
- **scanner:** isitagentready
- **category:** discovery
- **spec:** RFC 9727 (`/.well-known/api-catalog`); RFC 9264 linkset
- **tier / weight:** none
- **status:** **`rfc`** — RFC 9727 api-catalog, RFC 9264 Linkset
- **observes:** `/.well-known/api-catalog`
- **pass:** catalog found with ≥1 API listed
- **evidence_cmd:** `curl -s https://$HOST/.well-known/api-catalog`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:447-473`)
- source: evidence/scanner-docs.md:191,212

### oauthDiscovery
- **scanner:** isitagentready
- **category:** discovery
- **spec:** RFC 8414; OIDC Discovery
- **tier / weight:** none
- **status:** **`rfc`** — RFC 8414 OAuth 2.0 Authorization Server Metadata
- **observes:** `/.well-known/oauth-authorization-server`
- **pass:** metadata found. **Currently failing on the reference site** — no OAuth surface exists; treated as an accepted gap, not a bug, because the site's auth.md documents an unauthenticated public API by design.
- **evidence_cmd:** `curl -s https://$HOST/.well-known/oauth-authorization-server`
- **playbooks:** none evidenced — accepted gap on the reference site
- source: evidence/scanner-docs.md:191,213,286-299

### oauthProtectedResource
- **scanner:** isitagentready
- **category:** discovery
- **spec:** RFC 9728
- **tier / weight:** none
- **status:** **`rfc`** — RFC 9728 OAuth 2.0 Protected Resource Metadata
- **observes:** `/.well-known/oauth-protected-resource`
- **pass:** metadata found. **Currently failing on the reference site**, same accepted-gap rationale as `oauthDiscovery`.
- **evidence_cmd:** `curl -s https://$HOST/.well-known/oauth-protected-resource`
- **playbooks:** none evidenced — accepted gap on the reference site
- source: evidence/scanner-docs.md:191,214,286-299

### authMd
- **scanner:** isitagentready
- **category:** discovery
- **spec:** workos.com/auth-md convention (github.com/workos/auth.md)
- **tier / weight:** none
- **status:** `vendor-convention` — auth.md (WorkOS) — its own repo calls it "a reference implementation"
- **observes:** `GET /auth.md` with `Accept: text/markdown, text/plain`
- **pass:** the file must exist **and contain agent-registration markers**. The exact marker list is server-side and NOT VERIFIED.
- **2026-09-01 caveat (do not skip this):** the live parser currently treats wording like "no registration required" as a **fail**, even when the file exists, returns `200`, and has the right `Content-Type`. Reference site.org is failing this exact way right now: "auth.md exists but does not describe agent registration," even though its shipped file's `## Registration` section literally says "No registration or API key is required." A file structured per the reference recipe's headings alone (`# auth.md`, `## Agent audience`, `## Registration`, `## Credential use`) is **not sufficient** if the registration section's wording doesn't read as describing a registration flow — treat this as a same-day regression against the reference recipe, not a fresh implementation, and confirm current parser behavior against a live scan before declaring this check fixed.
- **evidence_cmd:** `curl -s https://$HOST/auth.md`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:477-487`) — flagged as needing a wording update, not a from-scratch build
- source: evidence/scanner-docs.md:191,215,286-299; specs/001-agent-remediation-skill/research.md:143-152 (D4); evidence/reference-branch-recipes.md:477-487

### mcpServerCard
- **scanner:** isitagentready
- **category:** discovery
- **spec:** MCP spec PR #2127
- **tier / weight:** none
- **status:** `vendor-convention` — MCP Server Card SEP-2127 — an OPEN PR labelled in-review; the experimental repo says "not an accepted or official MCP extension"
- **observes:** `/.well-known/mcp/server-card.json`
- **pass:** card found
- **evidence_cmd:** `curl -s https://$HOST/.well-known/mcp/server-card.json`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:533-547`)
- **note:** same file as is-agentic's `mcp-server` check above.
- source: evidence/scanner-docs.md:191,216

### a2aAgentCard
- **scanner:** isitagentready
- **category:** discovery — excluded from the bundle's default "All Checks" preset (though observed running server-side on a bare scan anyway)
- **spec:** a2a-protocol.org
- **tier / weight:** none
- **status:** `vendor-convention` — A2A Agent Card v1.0.0 (Linux Foundation)
- **observes:** `/.well-known/agent-card.json`
- **pass:** valid AgentCard structure; also checks the AP2 extension. Reference site.org passes: "Reference site Marketplace Assistant" v1.0.0.
- **evidence_cmd:** `curl -s https://$HOST/.well-known/agent-card.json`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:516-530`)
- source: evidence/scanner-docs.md:191,195-200,217

### agentSkills
- **scanner:** isitagentready
- **category:** discovery
- **spec:** cloudflare/agent-skills-discovery-rfc; agentskills.io
- **tier / weight:** none
- **status:** `vendor-convention` — Agent Skills (agentskills.io) + Cloudflare agent-skills-discovery-rfc v0.2.0, "Status: Draft"
- **observes:** `/.well-known/agent-skills/index.json`
- **pass:** valid JSON index; detects spec version, counts skills, validates entries. Reference site.org passes: `skillCount 2`, `specVersion 0.2.0`, `v2ValidEntries true`.
- **evidence_cmd:** `curl -s https://$HOST/.well-known/agent-skills/index.json | python3 -m json.tool`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:490-513`)
- source: evidence/scanner-docs.md:191,218

### webMcp
- **scanner:** isitagentready
- **category:** discovery
- **spec:** webmachinelearning.github.io/webmcp
- **tier / weight:** none
- **status:** **`w3c-cg-draft`** — WebMCP, W3C Web Machine Learning Community Group — a CG Draft Report, not a WG deliverable
- **observes:** tools registered via `navigator.modelContext` at runtime (client-side JS API — not directly curl-observable)
- **pass:** tools exposed; the reference site passes with `search_reference_news`, `ask_reference`
- **evidence_cmd:** no reliable static probe — this check requires a JS-executing browser context; `curl -s https://$HOST/ | grep -o 'registerTool'` is only a weak static proxy for "the registration code shipped," not proof the tools actually register at runtime
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:533-547`)
- source: evidence/scanner-docs.md:191,219

### ard
- **scanner:** isitagentready
- **category:** discovery
- **spec:** agenticresourcediscovery.org; ards-project/ard-spec
- **tier / weight:** none
- **status:** `vendor-convention` — ARD v0.91, "Status: Proposal" (ards-project)
- **observes:** an ARD capability manifest
- **pass:** manifest found — the reference site passes with 4 agentic resources listed
- **evidence_cmd:** `curl -s https://$HOST/.well-known/ai-catalog.json`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:447-473`)
- **note:** the reference implementation serves this from the same `/.well-known/ai-catalog.json` file that satisfies is-agentic's `ai-catalog` check above — one manifest, two scanners' checks.
- source: evidence/scanner-docs.md:191,220

### x402
- **scanner:** isitagentready
- **category:** commerce — **never counted toward the score**
- **spec:** x402.org
- **tier / weight:** none
- **status:** `vendor-convention` — x402 Foundation (Linux Foundation)
- **observes:** the x402 HTTP payment protocol
- **pass:** `neutral` on non-commerce sites (no commerce surface → not a fail)
- **evidence_cmd:** `curl -s https://$HOST/.well-known/x402`
- **playbooks:** none — accepted-gap by design whenever `isCommerce: false`
- source: evidence/scanner-docs.md:191,221,275-277

### mpp
- **scanner:** isitagentready
- **category:** commerce — never counted
- **spec:** mpp.dev; draft-payment-discovery-00
- **tier / weight:** none
- **status:** `vendor-convention` — MPP + draft-httpauth-payment-00, an individual I-D with no WG
- **observes:** MPP payment discovery
- **pass:** `neutral` on non-commerce sites
- **evidence_cmd:** `curl -s https://$HOST/.well-known/mpp`
- **playbooks:** none — accepted-gap by design
- source: evidence/scanner-docs.md:191,222

### ucp
- **scanner:** isitagentready
- **category:** commerce — never counted
- **spec:** ucp.dev
- **tier / weight:** none
- **status:** `vendor-convention` — UCP (Google-led consortium)
- **observes:** Universal Commerce Protocol profile
- **pass:** `neutral` on non-commerce sites
- **evidence_cmd:** `curl -s https://$HOST/.well-known/ucp`
- **playbooks:** none — accepted-gap by design
- source: evidence/scanner-docs.md:191,223

### acp
- **scanner:** isitagentready
- **category:** commerce — never counted
- **spec:** agenticcommerce.dev
- **tier / weight:** none
- **status:** `vendor-convention` — ACP (OpenAI + Stripe), status badge "Beta"
- **observes:** ACP discovery document
- **pass:** `neutral` on non-commerce sites
- **evidence_cmd:** `curl -s https://$HOST/.well-known/acp`
- **playbooks:** none — accepted-gap by design
- source: evidence/scanner-docs.md:191,224

### ap2
- **scanner:** isitagentready
- **category:** commerce — never counted; excluded from the default preset like `a2aAgentCard`
- **spec:** AP2 declaration nested inside the A2A Agent Card
- **tier / weight:** none
- **status:** `vendor-convention` — AP2 v0.2 (Google)
- **observes:** an AP2 declaration within `/.well-known/agent-card.json`
- **pass:** `neutral` on non-commerce sites
- **evidence_cmd:** `curl -s https://$HOST/.well-known/agent-card.json | jq '.ap2 // "absent"'`
- **playbooks:** playbook-nextjs-app-router.md (`evidence/reference-branch-recipes.md:516-530`, only if commerce is ever declared)
- source: evidence/scanner-docs.md:191,195-200,225

---

## Handling unknown checks

Both scanners evolve, and neither publishes a complete, stable catalog: this
file is an evidence-dated union, not a guarantee of completeness (D2,
`specs/001-agent-remediation-skill/research.md:120-133`). When a scan result
carries a check `id` that is not one of the `###` sections above:

1. **Look it up in the Ora catalog first.** One call, before you tell the user
   anything about the check:

   ```bash
   curl -s https://ora.ai/api/checks | jq '.checks[] | select(.id=="<check-id>")'
   ```

   A hit gives you `recommendation` (fix text), `maxScore` and `tier` (how heavy
   it is), `applicability` (whether it applies to this target at all) and
   `specUrl` (what standard, if any, it rests on). Report those as the catalog's
   words, attributed, with the fetch date. This is a lookup, not a licence to
   implement — the check stays `no-playbook` and step 5 still applies.

   A miss, or an unreachable catalog, falls through to step 2 unchanged.
   isitagentready has no equivalent endpoint; its unknown checks always fall
   through.
2. **Never guess a recipe silently.** Do not invent a check ID, a tier, a
   weight, or a pass criterion for anything the catalog did not answer.
3. **Surface the scanner's own text as-is** — its `details`/`recommendation`
   fields (is-agentic) or its check `message`/`evidence[]` entries
   (isitagentready) — instead of fabricating guidance.
4. **Mark it `no-playbook`** in the scope/plan output so it is visibly
   distinct from checks this file does cover — including when step 1 found it.
   A catalog hit supplies fix text; it does not supply the observed evidence,
   the target's file layout, or the user's decision.
5. **Confirm the approach with the user** before implementing a fix for it,
   per the skill-interface contract's audit-skill interop rule
   (`specs/001-agent-remediation-skill/contracts/skill-interface.md:60-63`).
6. Afterwards, feed the new check back as a candidate addition to this file
   (and, where relevant, to the `agent-readiness-audit` skill's own
   inventory) rather than forking a private, undocumented taxonomy.

**Weights and tiers are never hardcoded**, for known or unknown checks alike
(D1, `specs/001-agent-remediation-skill/research.md:106-118`). is-agentic's
`tier`/`weight` come from that scan's own `issues[].tier` and
`score_breakdown` at run time; isitagentready has no tier/weight concept at
all — only `pass`/`fail`/`neutral` per check, read from that scan's `checks`
object.
