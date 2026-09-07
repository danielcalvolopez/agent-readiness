# Generic playbook — agent-readiness-remediation

- **Evidence date:** 2026-09-01
- **On mismatch, live scanner output wins over this file.**
- **Use this file when no framework-specific playbook matches the target
  repo's stack** — e.g. no sibling playbook covers the framework in use, or
  the target combines multiple services/stacks where no single
  framework-specific playbook covers the whole surface.
- **Follow the target repo's own conventions — detect package manager, test
  layout, and existing patterns before writing anything.** Read the repo
  first: what installs dependencies, where tests live and what runs them, how
  routes/handlers/config are structured, what already exists for shared
  constants (a site-config module, an env-var convention). Adapt every recipe
  below to what you find instead of importing a foreign layout.

Each section below names the check ID(s) it addresses (identical to the IDs
in `references/check-contracts.md`), states exactly what any stack must serve
to pass (status code, headers, content-type, body shape), gives adaptation
guidance across classes of hosting/serving capability, lists pitfalls that
hold regardless of framework, and ends with a `source:` citation as its last
line. Sections are grouped by family: static discovery files, server
behaviors, API behaviors, structured data, and OpenAPI. Read a section's check
IDs against `check-contracts.md` before applying it — that file is the
vocabulary of record; this file is a recipe book.

---

## Check-ID index

**Read the section for every `fix-now` check ID before implementing any of
them.** Sections cross-reference each other and several answer more than one
check; skipping one and rediscovering its content mid-implementation is a
recorded failure of this file, not of the agent reading it.

| Check ID | Section(s) |
|---|---|
| `a2aAgentCard` | §7 |
| `agent-friendly-404` | §10 |
| `agent-instruction` | §2 |
| `agentSkills` | §6 |
| `ai-catalog` | §5 |
| `ai-crawler-access` | §1 |
| `ap2` | §7 |
| `api-schema-analysis` | §16 |
| `api-versioning-policy` | §14 |
| `apiCatalog` | §5 |
| `ard` | §5 |
| `authMd` | §4 |
| `canonical-correctness` | §8 |
| `content-efficiency` | §9 |
| `content-no-js` | §9 |
| `contentSignals` | §1 |
| `function-calling-compat` | §16 |
| `json-error-responses` | §12, §13 |
| `json-ld` | §15 |
| `linkHeaders` | §5 |
| `llms-txt` | §2 |
| `markdown-negotiation-vary` | §11 |
| `markdownNegotiation` | §11 |
| `mcp-server` | §7 |
| `mcpServerCard` | §7 |
| `metadata-completeness` | §8 |
| `openapi-spec` | §16 |
| `org-schema-completeness` | §15 |
| `public-api-docs` | §16 |
| `rate-limit-headers` | §14 |
| `robots-txt` | §1 |
| `robotsTxt` | §1 |
| `robotsTxtAiRules` | §1 |
| `sitemap` | §3 |
| `trust-anchors` | §9 |
| `webMcp` | §7 |

Sections without a check ID of their own (§17–18) cover foundations,
execution order, cross-cutting conventions, and checks with no recipe yet.
Read those too — they are not optional context.

---

## 1. Static discovery files — `robots-txt` / `robotsTxt` + `ai-crawler-access` / `robotsTxtAiRules` + `contentSignals`

**Checks:** `robots-txt`, `ai-crawler-access`, `robotsTxt`, `robotsTxtAiRules`, `contentSignals`

**What any stack must serve:** `GET /robots.txt` → `200`, `Content-Type:
text/plain` (or `text/plain; charset=utf-8`), a body valid per RFC 9309
format. Include: a wildcard `User-agent: *` group; a second group naming the
ten AI crawlers the checks look for by exact literal token —
`GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, `ClaudeBot`, `Claude-User`,
`Claude-SearchBot`, `PerplexityBot`, `Perplexity-User`, `Google-Extended`,
`Applebot-Extended` — with `Allow: /`; one or more `Content-Signal:`
directive lines (contentsignals.org / draft-romm-aipref-contentsignals
convention — `search=`, `ai-input=`, `ai-train=`, each `yes` or `no`); and a
`Sitemap:` line pointing at the absolute canonical `sitemap.xml` URL.

> **The three `Content-Signal` values are a REQUIRED user input, never a
> default.** `ai-train=yes` grants permission to train on the user's content —
> a licensing decision they make, not one a recipe makes for them. Phase 2
> collects all three (SKILL.md, "Required business inputs").

**Adaptation:** on any static-file host, a plain-text `robots.txt` at the
site root is sufficient — no server logic required — as long as its content
never needs to vary per request or environment. Move to whatever
request-handling mechanism the stack offers (a route/handler, a small
function, an edge rule) only when the body needs environment-specific values
computed at request time, or the static host truly cannot serve a
`Content-Signal:` line format at all.

**Pitfalls:**
- List every named crawler using the canonical CamelCase token spellings from
  the crawler list above (`GPTBot`, `ClaudeBot`, …), for consistency with the
  reference implementation — whether matching is case-sensitive is NOT
  VERIFIED (evidence shows lowercase tokens passing `robotsTxtAiRules`, per
  `check-contracts.md:450`); missing one crawler from the allow group only
  earns partial credit on `ai-crawler-access` / `robotsTxtAiRules`.
- `Content-Signal:` values are a real policy decision (does this site permit
  AI training on its content?) — confirm the intended values with the user
  rather than defaulting every flag to `yes` without asking.
- CDN- or platform-level bot-protection settings (an "Block AI Scrapers"
  toggle, a bot-fight-mode default) can silently override an otherwise
  correct `robots.txt` — check that surface separately from the text file
  itself; a correct `robots.txt` does not guarantee the platform honors it.
- Determine the canonical host (apex vs. `www`, whichever the site actually
  redirects to) before writing the `Sitemap:` line — see §8.
- Once markdown-negotiation internal rewrite targets exist (§11), disallow
  their path prefix here — otherwise they become duplicate-content crawl
  targets alongside the canonical HTML page.

source: references/check-contracts.md:146-166,388-397,444-464; specs/001-agent-remediation-skill/evidence/scanner-docs.md:191,204,209-210

---

## 2. Static discovery files — `llms-txt` / `agent-instruction` (llms.txt and llms-full.txt)

**Checks:** `llms-txt`, `agent-instruction`

**What any stack must serve:** `GET /llms.txt` → `200`, a markdown file per
llmstxt.org's spec shape: it MUST begin with an H1 naming the project (`#
<Name>`), immediately followed by a `>` blockquote one-paragraph summary,
then optional free markdown, then zero-or-more H2-delimited sections of
markdown link lists (`- [name](absolute-url): notes`), with an optional final
"Optional" H2 marking skippable/secondary links. For `agent-instruction`
credit, include a literal `## When to use this` H2 naming concrete agent
use-cases AND explicit non-goals ("not the right place for…") — generic
marketing copy scores zero even if the rest of the file validates. Every link
must be a fully-qualified absolute URL on the canonical host. Serve
`/llms-full.txt` as a companion carrying the same content plus the full
verbatim readable copy of every main page (not a paraphrase), for the
full-content variant this check also considers.

**Adaptation:** any static-file host can serve both files verbatim from the
project's public/static root with zero server logic. Only add generation
logic (build-time templating, or a request-time route) when the content is
sourced from a CMS or otherwise changes independently of a deploy — in that
case, regenerate on the same content-change event that invalidates any other
cache, so the files don't drift stale relative to the live pages.

**Pitfalls:**
- The literal heading string `## When to use this` is what the check
  matches — equivalent prose under a different heading does not earn credit.
- A thin or paraphrased `llms-full.txt` relative to the live HTML reads as a
  stale or low-effort variant, not a genuine full-content companion.
- Relative links break some agent-side parsers; always build every URL from
  one shared canonical-host value, never a second hardcoded host string.
- Advertise every new machine-readable surface here the moment it ships (an
  OpenAPI document, an agent-skills index, markdown negotiation) — this file
  goes stale fast otherwise, and nothing enforces it at build time.

source: references/check-contracts.md:126-144; specs/001-agent-remediation-skill/evidence/scanner-docs.md:305-313

---

## 3. Static discovery files — `sitemap` / `sitemap`

**Checks:** `sitemap` (is-agentic), `sitemap` (isitagentready)

**What any stack must serve:** `GET /sitemap.xml` → `200`, a valid XML
sitemap, with absolute `<loc>` URLs on the canonical host, a real `<lastmod>`
value sourced from each entry's actual update timestamp (not a blanket
today-stamp), and its location declared via a `Sitemap:` line in `robots.txt`
(§1).

**Adaptation:** a static site generator can emit this file at build time with
no server logic at all. A stack with dynamic or CMS-backed content needs
either a request-time generator or a build regenerated by the same webhook
that invalidates content caches, so new or changed entries appear without
waiting for the next full deploy.

**Pitfalls:**
- Stamping every static URL with `lastModified: now()` at every build is
  noise, not a signal — only dynamic/CMS entries should carry a real,
  content-sourced `lastmod`.
- Keep list length/pagination limits for any repeated content type (news,
  articles, products) consistent across the sitemap, the HTML listing page,
  and any markdown/API variant of the same list — a count mismatch between
  surfaces reads as cloaking to a scanner or crawler, not as a bug.
- Declare the sitemap in `robots.txt`; a sitemap that exists but is
  undeclared there is harder for a crawler to discover at all.

source: references/check-contracts.md:115-124,399-408

---

## 4. Static discovery files — `authMd` (auth.md agent registration discovery)

**Checks:** `authMd`

**What any stack must serve:** `GET /auth.md`, requested with `Accept:
text/markdown, text/plain` → `200`, `Content-Type: text/markdown;
charset=utf-8`, with a body containing: an H1 whose text includes the literal
string "auth.md"; a section naming the API and linking its machine-readable
description (e.g. the OpenAPI document); a registration/access-request
section; and a credential-use section. **2026-09-01 caveat, do not skip
this:** the live parser currently treats wording like "no registration
required" as a **fail** even when the file exists, returns `200`, has the
right content type, and structurally matches every required heading — word
the registration section as an actual access-request flow ("email X to
request access", "no credentials are issued for unauthenticated endpoints;
rate limits apply per client") rather than a bare negative statement.

**Adaptation:** serve this as a single static markdown file at the site root
if the hosting platform supports a dotted static filename as a route;
otherwise use whatever single-route mechanism the stack exposes (a function,
a small controller, a static-passthrough with a custom content type) — the
deliverable is only the `200 text/markdown` response and its body content,
not any particular routing mechanism.

**Pitfalls:**
- Structural correctness (every required heading present) is **not**
  sufficient on its own — wording is what the live parser actually scores.
  Confirm current parser behavior against a fresh live scan before declaring
  this check fixed; do not assume the structural recipe alone clears it.
- An unauthenticated public API has no OAuth metadata to point at — keep the
  document self-contained rather than referencing
  `/.well-known/oauth-authorization-server` if that surface doesn't exist
  (see §17).

source: references/check-contracts.md:510-520; specs/001-agent-remediation-skill/evidence/scanner-docs.md:215,286-299

---

## 5. Static discovery files — `.well-known` manifests (`ai-catalog` / `apiCatalog` / `ard` / `linkHeaders`)

**Checks:** `ai-catalog`, `apiCatalog`, `ard`, `linkHeaders`

**What any stack must serve — three related but distinct artifacts:**

**(a) `/.well-known/ai-catalog.json`** — an ARD-style manifest that satisfies
BOTH is-agentic's `ai-catalog` AND isitagentready's `ard` from the same file:
`{specVersion, host:{displayName, identifier:"did:web:<host>", description,
url, contact}, entries:[{identifier, displayName, type, url,
representativeQueries:[...]}]}`, one entry per machine-readable surface the
site ships (an OpenAPI document, llms.txt, sitemap, …). Must be served with
`Access-Control-Allow-Origin: *`.

**(b) `/.well-known/api-catalog`** — a **different** spec and path from (a):
RFC 9727 + RFC 9264 linkset, `Content-Type: application/linkset+json`, body
`{linkset:[{anchor:"<origin>/", "service-desc":[{href, type:"application/openapi+json"}],
"service-doc":[{href, type:"text/html"}]}]}`. Satisfies isitagentready's
`apiCatalog`.

**(c) Discovery `Link` response headers on `/`** (RFC 8288), satisfying
`linkHeaders`: a `Link:` header listing at minimum `rel="api-catalog"`,
`rel="service-desc"` (pointing at the OpenAPI document, typed
`application/openapi+json`), and `rel="describedby"` (pointing at
`llms.txt`).

**Adaptation:** (a) and (b) are plain JSON files — any static host serves
them. The CORS header on (a) and the `Link` header on (c) both require a
header-injection capability: on a fully static host with no custom-header
mechanism, this credit is genuinely blocked until a header-capable layer
(a CDN rule, an edge config, or a dynamic route) is added; on a server that
can set arbitrary response headers, add both at whatever layer the framework
exposes for response/header configuration.

**Pitfalls:**
- Never merge (a) and (b) into one file — different well-known path,
  different document shape, different scanner check.
- Without the CORS header on (a), an ARD client reading the JSON via
  cross-origin `fetch()` is blocked even though a same-origin `curl` request
  succeeds — this is exactly what the corresponding check is testing for.
- `linkHeaders`, `ai-catalog`/`ard`, and `apiCatalog` are three separate
  checks; passing one does not imply the others pass.

source: references/check-contracts.md:259-268,410-419,477-486,567-577; specs/001-agent-remediation-skill/evidence/scanner-docs.md:191,206,212,220

---

## 6. Static discovery files — `agentSkills` (agent-skills discovery index)

**Checks:** `agentSkills`

**What any stack must serve:** `GET /.well-known/agent-skills/index.json` →
`200`, valid JSON per the spec: `{"$schema":
"https://schemas.agentskills.io/discovery/0.2.0/schema.json", "skills":
[{name, type:"skill-md", description, url, digest:"sha256:<hex of the file's
exact bytes>"}]}`. Each referenced `SKILL.md` file: YAML frontmatter (`name`
in kebab-case matching the index, `description`), an H1, a `## When to use
this` section (concrete jobs plus an explicit "Not for:"), an endpoints/how
section with absolute URLs, and an errors section documenting the API's
error contract (§12). Ship one skill entry per machine-readable surface.

**Adaptation:** these are static files under `/.well-known/agent-skills/` —
any static host works, provided it can also attach
`Access-Control-Allow-Origin: *` to that path (agent-skills clients fetch it
cross-origin), via whichever header-configuration mechanism the platform
offers.

**Pitfalls:**
- `digest` is the sha256 of the referenced file's **exact bytes** — any
  later edit to a `SKILL.md` silently breaks it unless a test recomputes the
  hash over the live file and compares it against the index on every change.
- `name` must match `^[a-z0-9]+(-[a-z0-9]+)*$`; `url` must be root-relative
  under `/.well-known/agent-skills/`.

source: references/check-contracts.md:545-554; specs/001-agent-remediation-skill/evidence/scanner-docs.md:191,218

---

## 7. Static discovery files — agent card JSON (`mcp-server` / `mcpServerCard` / `a2aAgentCard` / `webMcp` / `ap2`)

**Checks:** `mcp-server`, `mcpServerCard`, `a2aAgentCard`, `webMcp`, `ap2`

**What any stack must serve:**

**(a) `/.well-known/agent-card.json`** (a2a-protocol.org): `{protocolVersion,
name, version, description (states capabilities AND explicit non-goals),
url:<A2A endpoint>, preferredTransport, supportedInterfaces, provider,
capabilities:{streaming, pushNotifications, stateTransitionHistory},
defaultInputModes/defaultOutputModes, skills:[{id, name, description, tags,
examples}]}`, `Access-Control-Allow-Origin: *`. Satisfies `a2aAgentCard`; an
optional nested AP2 declaration satisfies `ap2` only when the site actually
has a commerce surface (§17).

**(b) `/.well-known/mcp/server-card.json`**: `{serverInfo:{name, version},
description (with non-goals), url:<MCP endpoint>, transport:{type}, capabilities:{tools:true}}`.
Satisfies BOTH is-agentic's `mcp-server` and isitagentready's `mcpServerCard`
from one file.

**(c) `webMcp`** — tools registered via `navigator.modelContext` at runtime,
a client-side JS API call, not a static file. There is no reliable static/curl
probe for it; verify in a real browser.

**Adaptation:** (a) and (b) are plain JSON static files — any static host
serves them. The endpoints they reference (the `url` fields) implement live
protocol logic (JSON-RPC for A2A, MCP's protocol for the MCP endpoint) and
need whatever request-processing capability the stack has — a function, a
route handler, an equivalent — since that part is not a static response.

**Pitfalls:**
- A2A is deliberately cross-origin by design — rate limiting is the correct
  abuse control here, not an origin allowlist.
- Inside a JSON-RPC envelope, errors are JSON-RPC error objects (`-32700`
  parse error, `-32601` method not found, `-32602` invalid params, `-32603`
  internal error) — never `application/problem+json`. That media type only
  applies at the transport layer, e.g. a `429` or `405` returned before the
  JSON-RPC body is even parsed.
- Commerce-related checks (`ap2` here, and the whole commerce family in §17)
  resolve `neutral` on any site with no commerce surface — do not build one
  just to clear this check.

source: references/check-contracts.md:248-257,522-543,623-632; specs/001-agent-remediation-skill/evidence/scanner-docs.md:191,217-219

---

## 8. Server behaviors — `canonical-correctness` / `metadata-completeness` (canonical URLs + single host)

**Checks:** `canonical-correctness`, `metadata-completeness`

**What any stack must serve:** every interior page's rendered `<head>`
carries exactly one `<link rel="canonical" href="<the page's own absolute
URL>">` — never a value inherited from a shared layout or template that
points every page at the same URL. Every absolute URL emitted anywhere in the
app (canonical, sitemap, JSON-LD, llms.txt, markdown variants, problem-type
URIs, OpenAPI `servers`) must resolve to the **same** host — whichever one
the site's own redirect behavior treats as canonical (apex vs. `www`).
`metadata-completeness` additionally requires — presence only, not
value-correctness — an `<html lang="…">` attribute, an `og:image` tag, and
an `og:type` tag, all present in the rendered head.

**Adaptation:** determine the real redirect direction (does the apex
308-redirect to `www`, or the reverse?) before writing anything that
generates absolute URLs. Centralize that single host value in one place the
stack already uses for shared configuration (an env var, a constants module,
a site-config singleton) that every URL-producing code path imports — never
let two files hardcode the literal host string independently.

**Pitfalls:**
- Setting the canonical value once at a shared/layout/template level rather
  than per individual page is the single most-repeated mistake across every
  stack this pattern applies to — it silently de-indexes every page but the
  one the shared value points at.
- A canonical, sitemap, or JSON-LD entry generated against the wrong host
  (apex when the site redirects to `www`, or vice versa) fails subtly —
  the page still renders fine, only the machine-readable surface is wrong.

source: references/check-contracts.md:84-92,238-246; specs/001-agent-remediation-skill/evidence/reference-branch-recipes.md:78-98

---

## 9. Server behaviors — `content-no-js` / `content-efficiency` / `trust-anchors` (server-rendered visible text)

**Checks:** `content-no-js`, `content-efficiency`, `trust-anchors`

**What any stack must serve:** the raw HTTP response body for `/` (fetched
with **no** JavaScript execution — a plain HTTP client) must contain, after
stripping tags/scripts/styles/other non-text elements, **≥500 characters**
of visible text, at least one `<h1>`, and a non-flat heading structure (not
every heading at the same level). Visible text should also be **≥5% of the
total HTML response bytes** (`content-efficiency`). `/about`, `/contact`, and
`/privacy` (`trust-anchors`) each need the same treatment independently:
real, server-rendered pages with ≥500 chars apiece.

**Adaptation:** on any stack that can produce fully server-rendered or
statically pre-rendered HTML for its main pages, this is purely a content
gap, not a rendering-architecture gap — add real, crawlable prose to what
already renders. Only when a page is unavoidably client-render-only (a pure
SPA shell with genuinely no server-rendering or static-generation option
available) is a visually-hidden-but-DOM-present content block an acceptable
fallback — and only with guardrail tests asserting it is **not**
`display:none` and **not** `aria-hidden` (both hide text from the same
text-extraction step a scanner uses, even though the markup is technically
present in the response), keeps a genuine multi-level heading structure, and
carries real product prose rather than filler.

**Pitfalls:**
- Do not re-architect a page's rendering strategy when it already produces
  server or static HTML — just add copy.
- The visually-hidden fallback is a last resort for stacks with no
  server-rendering option at all, never a default first choice when real
  visible copy is achievable.
- The page's primary `<h1>` must live in the primary visible content, not
  buried inside a hidden filler section — a partial/flat-heading result (as
  opposed to a full pass) is exactly what happens when structure, not just
  character count, is wrong.

source: references/check-contracts.md:74-82,228-236,281-289; specs/001-agent-remediation-skill/evidence/reference-branch-recipes.md:46-75

---

## 10. Server behaviors — `agent-friendly-404` (recovery links + real 404 status)

**Checks:** `agent-friendly-404`

**What any stack must serve:** a request for a nonexistent path returns a
genuine HTTP `404` (or `410`) status — never `200` plus an in-app "not
found" shell — whose response body contains recovery links: at minimum a
link back to the home page, plus links to `/sitemap.xml`, `/llms.txt`, and
any other top-level discovery surfaces the site ships. The same request
repeated with `Accept: text/markdown` must **also** return a real 404, with a
`text/markdown` body carrying the same recovery links, for full credit (see
§11 for the negotiation half of this).

**Adaptation:** implement this at whatever layer the target stack uses for
"no route matched" — a catch-all/fallback route, a custom error page, or an
explicit not-found handler. The requirement is entirely about the response
shape (status code + body content), not any particular routing mechanism.

**Pitfalls:**
- Use real, in-app navigation for in-app pages and plain links for
  non-page static resources (a sitemap or `llms.txt` is not a client-routed
  page) — don't route a static-file link through client-side navigation.
- Never let a "friendlier" 404 page regress the actual status code to `200`
  in the process — verify the code with a headers-only request, not by
  eyeballing rendered content.

source: references/check-contracts.md:94-102; specs/001-agent-remediation-skill/evidence/reference-branch-recipes.md:248-269

---

## 11. Server behaviors — `markdown-negotiation-vary` / `markdownNegotiation` (content negotiation contract)

**Checks:** `markdown-negotiation-vary`, `markdownNegotiation`

**What any stack must serve — four criteria, satisfied by one
implementation for both scanners:**
1. A request with `Accept: text/markdown` to a negotiated page path returns
   `200` with `Content-Type: text/markdown; charset=utf-8` and a body that is
   real page content — a thinner variant than the HTML reads as cloaking, not
   as an optimization.
2. The response's `Vary` header has `Accept` **appended** to whatever
   variance signals the framework's own response pipeline already sets —
   never overwritten. Many server frameworks declare their own `Vary` values
   for their internal routing/caching machinery; replacing that value
   wholesale rather than adding to it breaks that machinery. Use whichever
   header-mutation API the stack offers that appends rather than reassigns.
3. A request with an explicit, genuinely unsupported `Accept` value returns
   `406 Not Acceptable` with a plain-text body listing the supported content
   types.
4. `Accept` parsing honors q-values: parse each `type;q=0.x` entry, exclude a
   type whose q is explicitly `0`, and — when both an HTML-capable type and
   `text/markdown` are offered — the higher (or tied) q wins, with a tie
   going to markdown when it's explicitly listed. An empty `Accept` header,
   or `*/*` alone, defaults to HTML.

**Adaptation:** this is the check where the choice of interception mechanism
matters most, and it splits sharply between **static hosting versus
middleware-capable servers**. On static hosting with no request-interception
layer at all, full negotiation across every route usually isn't achievable —
the practical fallback is a fixed, documented set of parallel markdown routes
(e.g. one markdown file per page) plus an explicit note that automatic
`Accept`-based negotiation isn't available on that surface. On a server whose
platform exposes a request-interception layer (whatever the target stack
calls its mechanism for running logic ahead of normal routing — read its own
current documentation for the exact API and name, since this differs sharply
between frameworks and changes across major versions of the same framework),
implement negotiation once at that layer so it applies uniformly to every
negotiated path before the router decides what to render. Whichever
mechanism applies, keep the actual q-value parsing logic in one small, pure,
fully unit-tested function with zero dependency on request/response types —
that function is 100% portable across frameworks and platforms.

**Pitfalls (the densest cluster in this family):**
- Unit-test the negotiation function directly: a typical browser Accept
  header (→ HTML), bare `text/markdown` (→ markdown), a q-tie (→ markdown
  wins when explicitly listed), `text/markdown;q=0,text/html` (→ HTML, `q=0`
  excludes it), and empty/`*/*` alone (→ HTML).
- Scope `406` to page/document paths only — never fire it on static assets
  or API routes, or a request for an image or a JSON API response gets
  incorrectly rejected.
- The unknown-path branch of the negotiation logic must still return a
  markdown-flavored 404 (§10) when the client explicitly wants markdown —
  don't let a working page-negotiation implementation silently fall through
  to a plain-HTML 404 on an unknown path.
- Internal rewrite-target paths that markdown variants live at (if the
  implementation uses parallel paths rather than true in-place negotiation)
  belong in the `robots.txt` disallow list (§1) — otherwise they become
  duplicate-content crawl targets next to the canonical HTML page.
- Every markdown response should declare its own canonical HTML URL via an
  RFC 8288 `Link: <…>; rel="canonical"` header, so an agent that fetched the
  markdown variant can still discover the "real" page URL.
- **Test the full negotiation flow against a production build/deployment,
  not a local dev server** — caching and header behavior under a CDN or
  production runtime commonly differs from a dev server. After deploying,
  confirm the CDN in front of the site actually returns distinct,
  `Vary: Accept`-respecting responses for HTML vs. markdown requests to the
  same URL, rather than serving one cached variant to both.
- Keep whatever "known route/segment" list the negotiation logic uses to
  decide known-vs-unknown paths synchronized with the real route tree — add
  a test comparing it against the actual routing structure so it can't
  silently drift as routes are added.
- Honor a more specific external link over an internal one where both exist
  (e.g. an article's own canonical external URL beating the site's internal
  page URL) when generating markdown link lists; build every URL through one
  shared absolute-URL helper, never a hardcoded host.

**Verification:**
```bash
curl -sI -H "Accept: text/markdown" https://$HOST/                 # 200 text/markdown; vary includes Accept
curl -sI -H "Accept: text/html" https://$HOST/                     # text/html; vary includes Accept
curl -sI -H "Accept: text/html,text/markdown;q=0.5" https://$HOST/ # text/html (q-values honored)
curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/vnd.nonexistent" https://$HOST/  # 406
curl -s -H "Accept: text/markdown" -o /dev/null -w "%{http_code}" https://$HOST/does-not-exist   # 404, markdown body
```
Acceptance: acceptmarkdown.com's "Test a URL" tool passes for `/`.

source: references/check-contracts.md:104-113,433-442; specs/001-agent-remediation-skill/evidence/scanner-docs.md:325-333

---

## 12. API behaviors — `json-error-responses` (RFC 9457 problem+json shape)

**Checks:** `json-error-responses`

**What any stack must serve:** every API error response — including unknown
routes and wrong HTTP methods, not only documented failure paths on real
endpoints — uses `Content-Type: application/problem+json` with body
`{type, title, status, code, detail?, resolution?}`, where `type` is a URI
reference that **actually dereferences** to a real page documenting the
error taxonomy (a `type` that itself 404s undermines the whole contract),
`title` is a short, stable-per-type human summary, `status` matches this
response's HTTP status, `code` is a stable machine-readable snake_case
identifier, `detail` explains this specific occurrence, and `resolution`
tells the caller how to fix the request. Malformed or missing request bodies
return `400`, never `500` — reserve `500` for genuine server bugs, and use
`502` specifically for a genuine upstream/dependency failure. Valid JSON that
parses successfully but isn't an object (a bare string, `null`, a number) is
still a `400` — successful parsing alone is not sufficient request
validation.

**Adaptation:** implement one small, shared response-building helper (a
plain function taking status/code/title/detail/resolution and returning the
right status, headers, and body) and route every error path in the app
through it, regardless of what routing or handler mechanism the stack
provides — this is a data-shape and status-code contract, not something tied
to any particular server framework's request/response API.

**Pitfalls:**
- Audit every existing consumer of an endpoint (a form, a client SDK, a chat
  widget) before changing its error shape, and update the consumer in the
  **same** change as the route — a UI that assumed a different error body
  shape will silently show the wrong message or crash otherwise.
- Keep and explicitly document any deliberate exception (a streaming
  endpoint that must keep a `text/plain` success body, or an endpoint that
  intentionally prefers availability over strict correctness on an upstream
  read failure) rather than force-fitting every response into the contract.
- Keep the OpenAPI document's error schemas (§16) in lockstep with any
  change to the live error contract — a drifted spec is worse than no spec,
  since an agent may trust it over the live behavior it's actually calling.

source: references/check-contracts.md:178-186; specs/001-agent-remediation-skill/evidence/scanner-docs.md:315-323

---

## 13. API behaviors — `json-error-responses` continued (JSON 404 catch-all + 405 `Allow`)

**Checks:** `json-error-responses`

**What any stack must serve:** a request to an unmapped API path returns
`404` in the **same** `application/problem+json` shape as §12 — never a
generic HTML 404 page — with a `resolution` field listing the actual valid
endpoints (ideally pointing at the OpenAPI document). A request to a real
endpoint with an unsupported HTTP method returns `405`, in the same problem
shape, **with** a standard `Allow:` response header listing the methods that
route does support.

**Adaptation:** implement the unmapped-path case as whatever the target
stack's most general fallback/catch-all routing mechanism is (a wildcard
route, a default handler, an explicit "route not found" hook), scoped to the
API path prefix only so it never swallows the non-API 404 contract (§10),
which is a different shape entirely (HTML/markdown recovery links, not
problem+json).

**Pitfalls:**
- Verify existing, working API routes are unaffected after adding a
  catch-all — a badly-scoped or badly-ordered catch-all can shadow real
  routes depending on the target stack's specific route-matching order.
- Keep the `Allow` header value in sync with the actual set of methods a
  route implements — a copy-pasted static list drifts the moment a route
  gains or loses a method.

source: references/check-contracts.md:178-186; specs/001-agent-remediation-skill/evidence/reference-branch-recipes.md:366-414

---

## 14. API behaviors — `rate-limit-headers` / `api-versioning-policy`

**Checks:** `rate-limit-headers`, `api-versioning-policy`

**What any stack must serve:** successful (not only rejected) API responses
carry the standard `RateLimit-*` response headers (`RateLimit-Limit`,
`RateLimit-Remaining`, `RateLimit-Reset`) computed from the
**most-constrained** currently-active rate-limit window when more than one
applies at once (e.g. a per-minute and a per-day limiter — always report the
more restrictive one). `RateLimit-Reset` is **delta-seconds from now, not an
epoch timestamp** — a common source of off-by-a-decade bugs when the value
is copied from a different header convention. A genuine `429` additionally
carries `Retry-After` (delta-seconds) and a scope-identifying header naming
which limiter window was exhausted. Documenting the convention in the
OpenAPI spec without an actually-observed live header on a real response
earns only partial credit — ship the headers before or in the same change as
the documentation. Separately, API versioning must be signaled via a
URL-path convention (`/v1/...`) or a header, declared in the OpenAPI
document, **plus** documented deprecation signaling (a `Sunset` or
`Deprecation` response header, or at minimum a stated timeline in the docs)
— both together, not either alone.

**Adaptation:** wherever the stack's existing rate-limiting mechanism
already lives (a request-interception layer, a per-route guard, or an
external gateway/CDN feature), extend it to also compute and attach these
headers rather than only enforcing the limit silently — this is a
header-shape requirement layered onto whatever enforcement mechanism already
exists, not a new enforcement mechanism to build from scratch.

**Pitfalls:**
- Never report a less-restrictive limiter's numbers when a more-restrictive
  one is also active for the same request.
- Keep the rate-limit header convention and the versioning/deprecation
  convention both documented once, in the OpenAPI spec's description, so
  documentation can't drift from what's actually served.

source: references/check-contracts.md:331-351; specs/001-agent-remediation-skill/evidence/reference-branch-recipes.md:550-568

---

## 15. Structured data — `json-ld` / `org-schema-completeness`

**Checks:** `json-ld`, `org-schema-completeness`

**What any stack must serve:** at least one **server-rendered**
`<script type="application/ld+json">` block on the homepage — present in the
raw HTML response, never injected by client-side JavaScript after load —
containing an `Organization` node with `contactPoint`
(`{"@type":"ContactPoint", contactType, email or telephone}`) **and**
`address` (`{"@type":"PostalAddress", …}`) **and** `sameAs` listing **≥3**
real, independently verifiable profile URLs — all three required together,
not any one alone. A `WebSite` node (and, where applicable, a `Service`/
product node) should reference the `Organization` node by a shared `@id`
rather than duplicating its fields.

**Adaptation:** build the JSON-LD payload as a plain server-side function
returning a plain object, independent of any templating engine, and render
it into the server-generated HTML output using whatever mechanism the stack
provides for emitting raw markup into a response — the object-building logic
itself has zero framework dependency and is fully portable.

**Pitfalls:**
- **Escape literal `<` characters** in the stringified JSON as the
  six-character JSON escape sequence (backslash, `u`, `0`, `0`, `3`, `c`)
  before embedding it in an HTML script tag — unescaped user- or
  CMS-sourced content can smuggle a literal `</script>` and either break
  the page or inject markup. Ship this escape in the same change that
  ships JSON-LD, not as a follow-up.
- A registered postal address is very often absent anywhere in the existing
  codebase — treat it as a **blocking user input**: ship the rest of the
  graph with the `address` field genuinely omitted (not fabricated) and
  record the gap explicitly, rather than inventing a placeholder address or
  blocking the whole feature on it.
- Every `sameAs` entry must be a profile URL the user has explicitly
  confirmed as official — never add one found only by inference.
- Cross-reference nodes by a shared `@id` instead of duplicating the same
  object across multiple graph nodes.
- Only create a `Person` node from an exact match against a maintained
  author/byline registry — an unmatched byline stays a plain string
  description, never a fabricated `Person` node.

source: references/check-contracts.md:208-226; specs/001-agent-remediation-skill/evidence/reference-branch-recipes.md:203-245

---

## 16. OpenAPI — `openapi-spec` / `api-schema-analysis` / `function-calling-compat` / `public-api-docs`

**Checks:** `openapi-spec`, `api-schema-analysis`, `function-calling-compat`, `public-api-docs`

**What any stack must serve:** a publicly reachable OpenAPI document
(commonly at `/openapi.json`) that declares OpenAPI version **3.1.0**, sets
`servers` to the real canonical origin, and gives **every** operation a
unique `operationId`, a `description`, typed parameters, and a typed
response schema — error responses expressed via the same
`application/problem+json` `Problem` component schema from §12
(`{type,title,status,code,detail,resolution}`, at minimum requiring
`title`/`status`/`code`). The document is linked from the homepage's
`<head>` via a `rel="service-desc"` link relation pointing at it, typed
`application/json` (or `application/openapi+json`). A discoverable
developer-facing docs page exists at a conventional path (`/docs`, `/api`,
or `/developers`) with the product name in both its `<title>` and its
`<h1>`, an errors section documenting the problem+json contract, and — this
is the part most often missed — an actual link **to** that docs page
**from** the homepage; existing-but-unlinked docs only earn partial credit.
The docs page, the OpenAPI document, and the developer docs path are all
also listed in `llms.txt` (§2) and `sitemap.xml` (§3).

**Adaptation:** emitting an arbitrary-relation `<link>` tag is where
frameworks differ most — most metadata/head-management APIs only special-case
a small fixed list of relations (icon, canonical, stylesheet, …) and
`service-desc` typically isn't one of them, so consult your framework's own
current documentation for how to emit an arbitrary `rel` value before
assuming any particular mechanism: some frameworks have a general-purpose
"other links" field for exactly this, others require falling back to a raw
tag written directly into whatever templating layer produces the document
head. This exact capability changes across major versions of many
frameworks, so verify against the target's bundled or linked docs rather
than assuming API stability.

**Pitfalls:**
- "Some operations have unique `operationId`s, some have typed schemas" only
  earns partial credit for `api-schema-analysis`/`function-calling-compat` —
  every single operation needs both, not most of them.
- Keep the OpenAPI document's error schemas in lockstep with any change to
  the live error contract (§12/§13) — see the pitfall there.
- `agentic-search-specific` (a separate check outside this section's scope)
  measures findability via search, not existence, and clears with indexing
  lag after a correct deploy — don't churn on it immediately after shipping
  the docs page.

source: references/check-contracts.md:168-176,188-206,353-362; specs/001-agent-remediation-skill/evidence/reference-branch-recipes.md:418-443

---

## 17. Checks with no code recipe yet (pending, informational, or accepted gaps)

Not every check in `references/check-contracts.md` maps to a buildable
recipe. Record these honestly instead of inventing a fix:

- **`https-and-transport`, `bot-protection`:** neither evidence file
  publishes an explicit pass criterion for these two is-agentic checks —
  don't build against a guessed criterion; read the actual scan's
  `issues[].details`/`recommendation` text before attempting a fix.
- **`dnsAid`:** a DNS discovery record at a fixed subdomain (draft-dnsaid
  convention) — a DNS-zone action outside any application repository, not a
  code change.
- **`webBotAuth`:** informational only on isitagentready — absence resolves
  to `neutral`, never `fail`; do not treat it as a required build.
- **`oauthDiscovery`, `oauthProtectedResource`:** expected failures on a
  site with no OAuth surface by design — an unauthenticated public API has
  nothing to publish at these paths; document that design choice (e.g. in
  `auth.md`, §4) rather than fabricating OAuth metadata to satisfy a check.
- **`cli-tool`:** a product decision (whether to publish an official
  CLI/SDK package), not a code fix — confirm scope with the user before
  treating it as in scope; a thin API wrapper exposing a `--json` flag is
  sufficient once the decision is made to build one.
- **`brand-search-accuracy`, `agentic-search-specific`:** both move over
  time via external signals (search indexing, press mentions, consistent
  name/address/phone, `sameAs` links) — a correct deploy is necessary but
  not sufficient, and re-checking immediately after deploying will show no
  change. Don't churn on these.
- **The commerce/Payments family** (`x402`, `mpp`, `ucp`, `acp`, `ap2`, and
  is-agentic's unnamed Payments layer): excluded from scoring entirely, pass
  or fail, on any site with no commerce/agentic-payment surface — never
  build a payments surface purely to clear these checks.

Whenever a scan result carries a check ID that isn't in
`check-contracts.md` at all, don't invent a recipe for that either: surface
the scanner's own `details`/`recommendation` (is-agentic) or
`message`/`evidence[]` (isitagentready) text as-is, mark it as having no
playbook, and confirm the approach with the user before implementing
anything — then feed the new check back as a candidate addition to
`check-contracts.md` rather than forking a private, undocumented taxonomy.

source: references/check-contracts.md:270-329,364-372,421-431,466-508,636-662

---

## 18. Cross-cutting conventions

- **Trace every fix to an observed failure** — a header, a status code, a
  char count, a specific scan result — from a dated baseline scan, not to a
  scanner's generic recommendation text alone.
- **Consult the target's own current, bundled or linked framework
  documentation** before using any API whose name looks familiar from a
  different stack or a different major version — names, availability, and
  behavior of request-interception layers, metadata/head APIs, and routing
  conventions all vary and change across versions.
- **Determine the canonical host and get explicit approval for every new
  dependency before writing code** — both are user decisions this file
  cannot make for you (§8, and any new test runner or library a recipe
  above implies installing).
- Ship one check-clearing change per commit or change-set, named after the
  check it clears, with a test — this keeps `git bisect`/review tractable
  and makes it easy to correlate a later re-scan's diff against a specific
  change.
- After any change, re-run the target's own test suite and build, run the
  section's verification commands against a **production build**, then
  re-scan and diff `issues[]`/`checks` by ID against the dated baseline —
  quote `scanned_at`/`scannedAt` every time (see `check-contracts.md`'s
  re-scan semantics).

source: references/check-contracts.md:1-58; specs/001-agent-remediation-skill/evidence/reference-branch-recipes.md:584-609
