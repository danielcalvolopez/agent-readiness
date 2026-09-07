# Next.js App Router playbook — agent-readiness-remediation

- **Evidence date:** 2026-09-01
- **Source branch:** the reference site `agent-readiness` (mined via `git show agent-readiness:<path>`; full commit-by-commit archaeology in `specs/001-agent-remediation-skill/evidence/reference-branch-recipes.md`)
- **Next.js version caveat:** recipes distilled from the reference branch on **Next 16.2.4** App Router; check `node_modules/next/dist/docs` in the target — `proxy.ts` replaced `middleware.ts` there. §9's `Vary` behaviour was separately measured on **Next 16.2.3** (2026-09-04) and differs from what the reference branch's recipe implies; version-specific header behaviour is re-verified per target, not assumed.
- **On mismatch, live scanner output wins over this file.**

Each section below names the check ID(s) it clears (identical to the IDs in
`references/check-contracts.md`), gives an imperative recipe with a condensed
code sketch (≤40 lines, the load-bearing shape — not a whole file), the
pitfalls that bit the reference branch, a verification command, and a
`source:` citation as its last line. Read a section's check IDs against
check-contracts.md before applying it — this file is a recipe book, that file
is the vocabulary of record.

---

## Check-ID index

**Read the section for every `fix-now` check ID before implementing any of
them.** Sections cross-reference each other and several answer more than one
check; skipping one and rediscovering its content mid-implementation is a
recorded failure of this file, not of the agent reading it.

| Check ID | Section(s) |
|---|---|
| `a2aAgentCard` | §15 |
| `agent-friendly-404` | §8 |
| `agent-instruction` | §5 |
| `agentSkills` | §14 |
| `agentic-search-specific` | §11, §18 |
| `ai-catalog` | §12 |
| `ai-crawler-access` | §3 |
| `api-schema-analysis` | §11 |
| `apiCatalog` | §12 |
| `ard` | §12 |
| `authMd` | §13 |
| `brand-search-accuracy` | §18 |
| `canonical-correctness` | §2 |
| `content-no-js` | §1 |
| `contentSignals` | §3 |
| `function-calling-compat` | §11 |
| `json-error-responses` | §10 |
| `json-ld` | §7 |
| `linkHeaders` | §12 |
| `llms-txt` | §5, §6 |
| `markdown-negotiation-vary` | §9 |
| `markdownNegotiation` | §9 |
| `mcp-server` | §16 |
| `mcpServerCard` | §16 |
| `metadata-completeness` | §2 |
| `openapi-spec` | §11 |
| `org-schema-completeness` | §7 |
| `public-api-docs` | §11 |
| `rate-limit-headers` | §17 |
| `robots-txt` | §3 |
| `robotsTxt` | §3 |
| `robotsTxtAiRules` | §3 |
| `sitemap` | §4 |
| `webMcp` | §16 |

Sections without a check ID of their own (§0, §18–19) cover foundations,
execution order, cross-cutting conventions, and checks with no recipe yet.
Read those too — they are not optional context.

---

## 0. Foundations — vitest + single site-config source of truth

**Checks:** infrastructure for every check below; no check ID of its own.

**Recipe:** Before touching any check, install vitest (ask the user first —
it is a new dependency) and create one `src/config/site.ts` that every
absolute URL in the codebase flows through: canonicals, sitemap, JSON-LD,
llms.txt, markdown bodies, and problem `type` URIs must all import from it,
never hardcode a host.

```ts
// src/config/site.ts
export const SITE_URL = "https://www.example.com"
export const SITE_NAME = "Example"
export const CONTACT_EMAIL = "hello@example.com"
export const ORG_SAME_AS = [
  "https://www.linkedin.com/company/example",
  "https://www.youtube.com/@example",
  // add only verified profiles — ask the user before listing one
]
export function absoluteUrl(path: string): string {
  return `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`
}
```

Configure vitest with `environment: "node"`, `include: ["src/__tests__/**/*.test.ts"]`,
and a `"@" → src/` alias. Put every test in a dedicated `src/__tests__/`
directory. Write each task test-first: failing test, implement, pass, commit.

**Pitfalls:**
- Determine the canonical host FIRST — check whether apex redirects to `www`
  (or vice versa) before writing anything. Every downstream artifact
  (canonicals, sitemap, JSON-LD, llms.txt) silently breaks if this is wrong.
- Mock any module a test imports that touches a CMS client or image asset
  (`vi.mock`) — do not let tests hit real network or build pipelines.

**Verification:** `pnpm test && pnpm build` — keep both green after every task.

source: 9b5663d, 2728477; agent-readiness:src/config/site.ts; evidence/reference-branch-recipes.md:14-43

---

## 1. `content-no-js` — server-rendered visible text ≥500 chars

**Recipe:** A `"use client"` page cannot export `metadata` and its text may
not reliably land in the raw HTML response. Split the page: move the
existing client component verbatim into `components/<Feature>/<Feature>Client.tsx`
(keep `"use client"` on it), accept `{children}`, and make `page.tsx` a thin
server component that exports `metadata` and renders real copy through it.

```tsx
// src/app/page.tsx — server component
import { FeatureClient } from "@/components/Feature/FeatureClient"
import { FeatureSummary } from "@/components/Feature/FeatureSummary"
export const metadata: Metadata = { alternates: { canonical: "/" } }
export default function Page() {
  return <FeatureClient><FeatureSummary /></FeatureClient>
}
```

Give `FeatureSummary` a `<section aria-label="…" className="sr-only">` with
≥2 `<h2>`s and ~2 paragraphs of real product prose (≥300 chars there; ≥500
chars total on the page). Never let the page's only `<h1>` live inside this
section — the primary hero owns the page `<h1>`.

**Pitfalls:**
- The client/server split is mandatory, not optional, wherever a page needs
  both interactivity and `metadata`.
- Prefer genuinely visible copy. If visible copy conflicts with the design
  (e.g. it fights a chat overlay), `sr-only` still clears this check because
  the text is present in server-rendered HTML — but only with guardrails:
  add tests asserting the section is **not** `display:none` and **not**
  `aria-hidden` (both hide text from parsers even though it is
  server-rendered), keeps ≥2 `<h2>`, and keeps ≥300 chars of real prose. Do
  not treat "no sr-only filler" as an absolute — treat it as "sr-only is
  acceptable only with these guardrail tests in place."
- Do not re-architect rendering when a page already server-renders — just add
  copy.

**Verification:**
```bash
curl -s http://localhost:3000/ | python3 -c "import re,sys; h=sys.stdin.read(); t=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',re.sub(r'(?is)<(script|style|noscript|svg|template)\b.*?</\1>',' ',h))); print(len(t.strip()))"
# expect >=500
```

source: 20caf87, 2d86a6b, 06c1bcf; agent-readiness:src/app/page.tsx, src/components/Home/HomeSummary.tsx; evidence/reference-branch-recipes.md:46-75

---

## 2. `canonical-correctness` / `metadata-completeness` — metadataBase + per-page canonicals

**Recipe:**
1. Set `metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? SITE_URL)`
   in the root layout, importing `SITE_URL` from the site config — never
   duplicate the literal host string.
2. Give every static page `export const metadata = { alternates: { canonical: "/about" } }`
   (relative path; `metadataBase` resolves it).
3. Give every dynamic route the same field inside `generateMetadata`'s
   return value, e.g. `alternates: { canonical: `/news/${id}` }`.
4. Add a `metadata` export (title + canonical) to any page that lacks one.

**Pitfalls:**
- **Never set `alternates.canonical` in a shared layout.** An inherited
  canonical points every interior page at one URL and de-indexes the rest.
  Canonicals are per-page only — this is the single most-repeated pitfall in
  the source spec.
- Match the real redirect behavior. If apex 308-redirects to `www` (or the
  reverse), every generated absolute URL — canonical, sitemap, OG, JSON-LD,
  llms.txt — must use the same host, or checks fail subtly.
- `metadata-completeness` also requires `<html lang="…">`, `og:image`, and
  `og:type` present (presence only; value correctness of the canonical is
  the separate `canonical-correctness` check) — audit the root layout and
  any page-level `generateMetadata` overrides for all four together.

**Verification:**
```bash
for p in / /about /contact /case-studies /news; do
  echo -n "$p -> "; curl -s "http://localhost:3000$p" | grep -o '<link rel="canonical"[^>]*>' || echo MISSING
done
```

source: b945cc7, 2d86a6b; agent-readiness:src/app/layout.tsx; evidence/reference-branch-recipes.md:78-99

---

## 3. `robots-txt`/`robotsTxt` + `ai-crawler-access`/`robotsTxtAiRules` + `contentSignals` — AI-crawler-friendly robots.txt

**Recipe:** Serve `robots.txt` from a route handler, not Next's
`MetadataRoute.Robots` (`src/app/robots.ts`), because the built-in type
cannot express `Content-Signal:` lines.

```ts
// src/app/robots.txt/route.ts
import { absoluteUrl } from "@/config/site"
const AI_CRAWLERS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
  "Claude-SearchBot", "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended"]
// REQUIRED USER INPUT — do not ship these values without asking. `ai-train=yes`
// grants permission to train on the user's content: a licensing decision, not a
// header. Phase 2 collects all three (see SKILL.md, "Required business inputs").
const CONTENT_SIGNAL = "Content-Signal: search=<ask>, ai-input=<ask>, ai-train=<ask>"
const RULES = ["Allow: /", "Disallow: /api/", "Disallow: /md/"]
function group(userAgents: string[]) {
  return [...userAgents.map(ua => `User-Agent: ${ua}`), CONTENT_SIGNAL, ...RULES].join("\n")
}
export function GET(): Response {
  const body = [group(["*"]), group(AI_CRAWLERS), `Sitemap: ${absoluteUrl("/sitemap.xml")}`].join("\n\n")
  return new Response(`${body}\n`, { headers: { "content-type": "text/plain; charset=utf-8" } })
}
```

**Pitfalls:**
- If you don't need `Content-Signal:` lines, `src/app/robots.ts` is fine —
  migrate to the route-handler form the moment you do need them (this is
  exactly the migration the reference branch made).
- Add `Disallow: /md/` once markdown-negotiation routes exist (§9) — those
  `/md/*` paths are internal rewrite targets, not canonical URLs; without the
  disallow they become duplicate-content crawl targets.
- In `robots.ts` form, pass `disallow` as an array (`["/api/", "/md/"]`), not
  a string — tests and some crawlers care about the distinction.
- List every AI crawler named above for `ai-crawler-access`/`robotsTxtAiRules`
  credit; check separately whether CDN-level bot protection (e.g. Cloudflare
  "Block AI Scrapers"/Bot Fight Mode) silently overrides these rules —
  robots.txt correctness does not guarantee the CDN honors it.

**Verification:** `curl -s http://localhost:3000/robots.txt` → both `User-Agent` groups present, `Content-Signal:` lines present, `Sitemap: https://www.example.com/sitemap.xml` present.

source: a48a3df, 4cbfe56, 06c1bcf; agent-readiness:src/app/robots.txt/route.ts; evidence/reference-branch-recipes.md:102-130

---

## 4. `sitemap` — sitemap.xml with CMS content

**Recipe:**

```ts
// src/app/sitemap.ts
import { absoluteUrl } from "@/config/site"
export const STATIC_PATHS = ["/", "/about", "/contact", "/case-studies", "/news", /* … */]
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const news = await getNewsArticles(50)
  return [
    ...STATIC_PATHS.map(path => ({ url: absoluteUrl(path) })),
    ...news.map(a => ({ url: absoluteUrl(`/news/${a.id}`), lastModified: new Date(a.createdAt) })),
  ]
}
```

**Pitfalls:**
- Give dynamic CMS entries a **real** `lastModified` from their own
  `createdAt`/`updatedAt` field. Do not stamp static routes with
  `lastModified: new Date()` — a today-timestamp on every static page is
  noise, not a signal.
- Wire the CMS webhook to call `revalidatePath("/sitemap.xml")` too, or new
  content stays invisible in the sitemap until redeploy.
- Declare the sitemap in `robots.txt` (`Sitemap: <absolute-url>`).
- Keep news/list fetch limits identical across the sitemap, the markdown
  variants (§9), and the HTML page — a parity mismatch between surfaces
  reads as cloaking to a scanner or crawler.

**Verification:** `curl -s http://localhost:3000/sitemap.xml | head -20` → `<loc>` entries on the canonical host, `<lastmod>` present on dynamic entries.

source: 55ec931, 2d86a6b, 498d246; agent-readiness:src/app/sitemap.ts; evidence/reference-branch-recipes.md:133-161

---

## 5. `llms-txt` / `agent-instruction` — llms.txt with a "When to use this" section

**Recipe:** Serve a static `public/llms.txt` per llmstxt.org; Next serves
public-folder files as-is with a `text/plain` content type.

```markdown
# Example

> One-paragraph summary of what the org/product is.

## When to use this
Use example.com when you are:
- <concrete agent job 1>
- <job with a fetchable URL: fetch https://www.example.com/data.json>
- Reaching the team programmatically: POST https://www.example.com/api/contact — see https://www.example.com/openapi.json.
Not the right place for: <explicit non-goals>.

## Pages
- [Home](https://www.example.com/): one-line description.

## Machine-readable
- [OpenAPI spec](https://www.example.com/openapi.json), [Sitemap](https://www.example.com/sitemap.xml)
- Markdown variants: main pages are also served as text/markdown via `Accept: text/markdown` (see §9).
```

**Pitfalls:**
- `agent-instruction` scores the literal `## When to use this` heading. It
  must name concrete jobs AND explicit non-goals — generic marketing copy
  scores zero even if the file otherwise looks complete.
- Every link must be absolute on the canonical host. Test it: every `](…)`
  match contains the full canonical origin, there are >5 links, the file
  starts with `# <Name>\n`, and has a `> ` blockquote summary.
- Advertise every new machine surface here as it ships (e.g. add the
  markdown-negotiation line the moment §9 exists) — llms.txt drifts stale
  fast otherwise.

**Verification:** `curl -sI /llms.txt | grep -i content-type` → `text/plain`; `curl -s /llms.txt | head -5` → starts `# <Name>`.

source: b8d79a6, b7ad499; agent-readiness:public/llms.txt; evidence/reference-branch-recipes.md:164-200

---

## 6. `llms-txt` (llms-full.txt variant) — full-content companion file

**Checks:** contributes to `llms-txt`'s own pass criteria (check-contracts.md
records its `observes` field as "`/llms.txt` (and `/llms-full.txt`)") — not a
separately named check ID.

**Recipe:** Serve `public/llms-full.txt` containing the llms.txt content plus
the full readable copy of every main page, concatenated:

```markdown
# Example

## Home
<verbatim copy from the homepage component>

## About
<verbatim copy from the about-page component>

## Developers
<verbatim copy from the developers-page component>
```

**Pitfalls:**
- Copy content verbatim from the live page components — do not paraphrase or
  summarize; a thinner llms-full than the HTML reads as a stale or
  low-effort variant.
- Keep it in sync manually whenever page copy changes — there is no
  build-time enforcement of this file, so add it to the PR checklist for any
  copy change on a page it includes.

**Verification:** `curl -sI /llms-full.txt | grep -i content-type` → `text/plain`; body length grows roughly with total page copy.

source: 33b1bec; agent-readiness:public/llms-full.txt; evidence/reference-branch-recipes.md:447-474

---

## 7. `json-ld` / `org-schema-completeness` — server-rendered @graph

**Recipe:** Build one `@graph` server-side and render it in the root layout.

```ts
// src/utils/jsonLd.ts
export function buildSiteGraph() {
  return {
    "@context": "https://schema.org",
    "@graph": [
      { "@type": "Organization", "@id": `${SITE_URL}/#organization`,
        name: SITE_NAME, url: SITE_URL, logo: absoluteUrl("/og/home.png"),
        sameAs: ORG_SAME_AS,   // >=3 VERIFIED profiles — ask the user, never guess
        contactPoint: { "@type": "ContactPoint", contactType: "customer support", email: CONTACT_EMAIL },
        ...(ORG_ADDRESS && { address: { "@type": "PostalAddress", ...ORG_ADDRESS } }) },
      { "@type": "WebSite", "@id": `${SITE_URL}/#website`, name: SITE_NAME, url: SITE_URL,
        publisher: { "@id": `${SITE_URL}/#organization` } },
    ],
  }
}
```

```tsx
// layout.tsx — escape "<" or CMS content can inject "</script>"
<script type="application/ld+json"
  dangerouslySetInnerHTML={{ __html: JSON.stringify(buildSiteGraph()).replace(/</g, "\\u003c") }} />
```

For article-type content add a per-article node (`headline`,
`mainEntityOfPage`, `datePublished`/`dateModified`, `author` resolved against
an `AUTHORS` registry by exact byline match, `publisher: { "@id": "…/#organization" }`),
rendered the same escaped way inside the article page.

**Pitfalls:**
- **Escape literal `<` characters as the six-character JSON escape sequence
  `\u003c`** (backslash, `u`, `0`, `0`, `3`, `c`) in the stringified JSON —
  matches the sketch's `.replace(/</g, "\\u003c")`. Unescaped CMS content
  can smuggle a literal `</script>` and break the page or inject markup.
  Add this in the same commit that ships JSON-LD, not as a follow-up.
- `org-schema-completeness` requires `contactPoint` **and** `address`
  **and** `sameAs` with ≥3 verified profiles — all three, not any one.
  `address` (`PostalAddress`) is usually the missing field. It is very
  commonly a **blocking user input** (a registered office address is rarely
  in the repo): ship with `ORG_ADDRESS = null` spread-omitted (see the
  sketch above) and record the gap in the commit message rather than
  fabricating an address or blocking the whole feature on it.
- `sameAs` entries must be profiles the user has explicitly confirmed as
  official — do not add a profile URL found by inference alone.
- Cross-reference nodes by `@id` (e.g. `"#organization"`) instead of
  duplicating the same object in multiple graph nodes.
- Only create a `Person` node from an exact registry match on the byline; an
  unmatched byline stays a plain string description, never a fabricated
  Person node.

**Verification:** `curl -s http://localhost:3000/ | grep -c 'application/ld+json'` → ≥1; paste the extracted JSON into https://validator.schema.org/ → zero errors.

source: 7c2a826, 2d86a6b, defe210, 0944dd8; agent-readiness:src/utils/jsonLd.ts, src/app/layout.tsx; evidence/reference-branch-recipes.md:203-245

---

## 8. `agent-friendly-404` — recovery links on the 404 page

**Recipe:** Add a recovery nav to the existing `not-found.tsx` — do not
replace the 404 with a 200 "not found" page.

```tsx
// src/app/not-found.tsx (addition)
<nav aria-label="Recovery links" className="mt-4 flex flex-col gap-1 text-sm">
  <Link href="/">Home</Link>
  <Link href="/news">Latest news</Link>
  <a href="/sitemap.xml">Sitemap (all pages)</a>
  <a href="/llms.txt">llms.txt (agent guide)</a>
</nav>
```

**Pitfalls:**
- Use `<Link>` only for in-app pages (`/`, `/news`); use plain `<a>` for
  non-page resources (`/sitemap.xml`, `/llms.txt`) — client-side prefetching
  is not meaningful for a static file.
- Preserve the real 404 **status code** — recovery links go in the body of
  the existing not-found response, never behind a 200.
- Full credit on this check also requires the markdown-negotiated 404 (§9):
  a request for an unknown path with `Accept: text/markdown` must still
  return 404, with a `text/markdown` body carrying the same recovery links.

**Verification:** `curl -s -o /dev/null -w "%{http_code}" /does-not-exist` → 404; `curl -s /does-not-exist | grep 'href="/llms.txt"'` → present.

source: 8dfd218, ec14151; agent-readiness:src/app/not-found.tsx; evidence/reference-branch-recipes.md:248-269

---

## 9. `markdown-negotiation-vary` / `markdownNegotiation` — Accept negotiation, Vary, 406, markdown 404

**Recipe — three layers.**

**(a)** Write a pure, fully unit-tested q-value-aware negotiation util first:

```ts
// src/utils/contentNegotiation.ts
const HTML_CAPABLE = new Set(["text/html", "text/*", "*/*"])
const SUPPORTED = new Set(["text/html", "text/markdown", "text/*", "*/*"])
export function prefersMarkdown(accept: string): boolean {
  // parse "type;q=0.x" entries; markdown wins when its q >= max(html-capable q); q=0 excludes a type
}
export function acceptsAnySupported(accept: string): boolean {
  // true for an empty header; false only when explicit types are listed and none of SUPPORTED has q > 0
}
```
Cover: a browser header (`text/html,…,*/*;q=0.8` → HTML), bare
`text/markdown` (→ markdown), a q-tie (`text/markdown,*/*;q=1` → markdown,
`>=` comparison), `text/markdown;q=0,text/html` (→ HTML), and empty/`*/*`
alone (→ HTML).

**(b)** Serve markdown from a route handler with a canonical `Link` header:

```ts
// src/app/md/[page]/route.ts
const { page } = await params
const markdown = await getPageMarkdown(page)
if (!markdown) return new Response(md404Body, { status: 404,
  headers: { "content-type": "text/markdown; charset=utf-8", vary: "Accept" } })
const path = page === "home" ? "/" : `/${page}`
return new Response(markdown, { status: 200, headers: {
  "content-type": "text/markdown; charset=utf-8",
  vary: "Accept",
  link: `<${absoluteUrl(path)}>; rel="canonical"`,
}})
```

**(c)** Negotiate in `proxy.ts` (Next 16's replacement for `middleware.ts`):

```ts
export const KNOWN_SEGMENTS = new Set(["about", "contact", "news", "md"])  // export for a segment-parity test
export default function proxy(request: NextRequest) {
  const accept = request.headers.get("accept") ?? ""
  const { pathname } = request.nextUrl
  if (NEGOTIATED_PATHS.has(pathname) && prefersMarkdown(accept)) {
    const url = request.nextUrl.clone()
    url.pathname = pathname === "/" ? "/md/home" : `/md${pathname}`
    const response = NextResponse.rewrite(url)
    response.headers.append("vary", "Accept")   // APPEND — see pitfalls
    return response
  }
  if (NEGOTIATED_PATHS.has(pathname) && accept && !acceptsAnySupported(accept)) {
    return new NextResponse("Not Acceptable. Supported content types: text/html, text/markdown.\n",
      { status: 406, headers: { "content-type": "text/plain; charset=utf-8", vary: "Accept" } })
  }
  const segment = pathname.split("/")[1]
  if (pathname !== "/" && segment && !KNOWN_SEGMENTS.has(segment) && prefersMarkdown(accept)) {
    return new NextResponse(NOT_FOUND_MD, { status: 404,             // unknown path + wants markdown
      headers: { "content-type": "text/markdown; charset=utf-8", vary: "Accept" } })
  }
  const response = NextResponse.next()
  response.headers.append("vary", "Accept")
  return response
}
export const config = { matcher: ["/((?!api|_next|.*\\..*).*)"] }
```

**Pitfalls (the densest cluster in the source material):**

- **Next 16 overwrites `Vary` on App Router page responses — appending does not
  work there.** Measured on **Next.js 16.2.3**, 2026-09-04. `.append("vary",
  "Accept")` in `proxy.ts` produces no `Vary: Accept` on the HTML page
  response, and `next.config.ts` `headers()` is overridden too — proven by a
  sibling `X-Frame-Options` in the same block landing while `Vary` did not. A
  control probe header set alongside it in `proxy.ts` *did* survive, so the
  proxy runs and its other headers stick: Next is specifically reclaiming
  `Vary` on page responses.

  | Response kind | `Vary: Accept` survives? |
  |---|---|
  | App Router **page** (HTML) | **no** — Next overwrites |
  | route handler (e.g. `/md/*`) | yes |
  | rewrite target | yes |
  | `406` from the proxy | yes |
  | `404` from the proxy | yes |

  **The check passes anyway.** `markdown-negotiation-vary` is scored on the
  **markdown** response's `Vary`, not the HTML one, and markdown is served by a
  route handler — which keeps the header. Do not re-architect page rendering
  chasing this.

  **If you need it on the HTML response** (a CDN caching both variants under
  one key is the real-world reason), it is an **edge/CDN rule**, not app code —
  add `Vary: Accept` at the CDN layer. Do not keep trying app-level approaches:
  `proxy.ts` append, `next.config.ts` headers, and per-route `headers()` were
  all measured failing on this version.

  Still call `.append(…)` rather than assigning: on the response kinds where it
  *does* land, Next sets `Vary: rsc, next-router-state-tree,
  next-router-prefetch, …` and overwriting that breaks client-side routing.
  Smoke-test navigation after adding the proxy either way.

  Re-verify on a version bump — this is version-specific behaviour, not a
  documented contract.
- The 406 body is plain text listing supported types; only fire 406 on page
  paths, never on assets or `/api/*` — exclude both in the matcher.
- The markdown 404 fires for **any** unknown path — a segment not in
  `KNOWN_SEGMENTS` — not only for the fixed `NEGOTIATED_PATHS` set; the
  sketch's unknown-segment branch runs after the negotiated-path checks so
  `curl -H "Accept: text/markdown" /does-not-exist` still gets a markdown
  404. It must preserve the real 404 status either way.
- Markdown must be real page content, never a stub — a thinner advertised
  variant than the HTML reads as cloaking. Keep copy verbatim and keep list
  counts (e.g. news article limits) in parity across markdown/HTML/sitemap.
- `/md/*` paths are internal rewrite targets: `Disallow: /md/` in
  robots.txt (§3), and every markdown response declares its canonical HTML
  URL via an RFC 8288 `Link: <…>; rel="canonical"` header.
- `KNOWN_SEGMENTS` drifts from the real route tree. Export it and add a
  **segment-parity test** comparing it against the actual `src/app`
  directory listing; update it the moment a new top-level route ships.
- Honor per-item external links in generated markdown (e.g. an article's own
  external URL should beat the internal page URL); always build URLs through
  `absoluteUrl()`, never a hardcoded host.
- **Test on a production build** (`pnpm build && pnpm start`) — proxy
  behavior under caching differs from `next dev`. After deploy, verify the
  CDN still returns `Vary: Accept` by fetching `/` as HTML then markdown, in
  both orders — each request must get its own variant, not a cached one.

**Verification:**
```bash
curl -sI -H "Accept: text/markdown" localhost:3000/                 # 200 text/markdown; vary includes Accept
curl -sI -H "Accept: text/html" localhost:3000/                     # text/html; vary includes Accept
curl -sI -H "Accept: text/html,text/markdown;q=0.5" localhost:3000/ # text/html (q-values honored)
curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/vnd.nonexistent" localhost:3000/  # 406
curl -s -H "Accept: text/markdown" -o /dev/null -w "%{http_code}" localhost:3000/does-not-exist   # 404, markdown body
```
Acceptance: acceptmarkdown.com "Test a URL" passes for `/`.

source: 8f15ced, e672160, 92bd3ce, a68edf0, 4cbfe56; agent-readiness:src/utils/contentNegotiation.ts, src/proxy.ts, src/app/md/[page]/route.ts; evidence/reference-branch-recipes.md:273-363

---

## 10. `json-error-responses` — RFC 9457 problem+json across `/api/*`

**Run this section LAST**, after every other section — see §19.

**Recipe:**

**(a)** One shared helper plus two companions:

```ts
// src/utils/problemResponse.ts
const PROBLEM_TYPE = "https://www.example.com/developers#errors"  // must dereference — see pitfalls
export function problemResponse({ status, code, title, detail, resolution, headers }): Response {
  return new Response(JSON.stringify({ type: PROBLEM_TYPE, title, status, code,
      ...(detail && { detail }), ...(resolution && { resolution }) }),
    { status, headers: { "content-type": "application/problem+json", ...headers } })
}
// parseJsonObject(request, resolution): 400 invalid_json for unparseable JSON
//   AND for valid-but-non-object JSON (null, "string", 42)
// methodNotAllowed(allowed, resolution?): 405 problem + `Allow` header
```
Field set: `{ type, title, status, code, detail?, resolution? }` — `code` is
a stable snake_case machine id; `resolution` tells the caller how to fix the
request.

**(b)** Catch-all JSON 404 for unknown API routes:

```ts
// src/app/api/[...notfound]/route.ts
export const GET = notFound, POST = notFound, PUT = notFound,
  PATCH = notFound, DELETE = notFound, HEAD = notFound, OPTIONS = notFound
function notFound() {
  return problemResponse({ status: 404, code: "unknown_endpoint", title: "Not Found",
    resolution: "Valid endpoints: GET /api/news, POST /api/contact. See https://www.example.com/openapi.json" })
}
```
Next matches concrete static segments before this catch-all, so existing
routes are unaffected.

**(c)** Apply per-route error contracts without touching success shapes:
missing/malformed body → 400 (never 500); upstream provider failure → 502
(genuine upstream failure, not the caller's fault); wrong HTTP method →
`methodNotAllowed([...])` (405 with `Allow`); rate-limited → 429 with
`Retry-After` + `X-RateLimit-Scope` (see §17). Strip unknown extra fields
rather than rejecting the request for them.

**Pitfalls:**
- **Sequence this section deliberately last.** It is the most
  behavior-sensitive change in the whole playbook: any UI that consumes
  these responses (a contact form, a chat widget) must be updated in the
  **same commit** as the route, e.g.:
  `try { const problem = await res.json(); if (typeof problem.detail === "string") text = problem.detail } catch { /* keep fallback copy */ }`.
- **Audit consumers before changing shapes**: `grep -rn "api/<route>" src --include="*.tsx" | grep -v app/api`
  to find every component that calls the route and how it parses errors.
- **400, never 500, for malformed/missing bodies.** Reserve 500 for genuine
  server bugs; an upstream provider failure is **502**, not 500 or 400.
- Valid JSON that isn't an object (`"string"`, `null`, `42`) is still 400 —
  `request.json()` succeeding is not sufficient validation.
- **The problem `type` URI must actually dereference.** Add a
  `<section id="errors">` to a real page (e.g. `/developers#errors`)
  documenting RFC 9457, the field set, and the `code` values — a `type` URI
  that 404s undermines the whole contract.
- Document and keep intentional exceptions rather than "fixing" them: a
  streaming endpoint may legitimately keep a `text/plain` success body; an
  endpoint that prefers availability over strictness may legitimately return
  `200 []` on an upstream read failure. Leave those alone, but write down why.
- Keep `openapi.json` in lockstep with every error-contract change — its
  error responses should reference the same `Problem` schema.

**Verification:**
```bash
curl -s -o /dev/null -w "%{http_code} %{content_type}\n" localhost:3000/api/nonexistent   # 404 application/problem+json
curl -s -X POST localhost:3000/api/contact | python3 -m json.tool                         # 400 invalid_json
curl -s -X POST -H "content-type: application/json" -d '{}' localhost:3000/api/contact    # 400 missing_fields
curl -s localhost:3000/api/chat | python3 -m json.tool                                    # 405 problem, Allow: POST
curl -s -o /dev/null -w "%{http_code}" localhost:3000/api/news                            # unaffected success path unchanged
```
Plus a manual UI smoke test of every consumer touched, including the
rate-limited path.

source: 10d6cef, b8ecee5, c1eea2b, 6fd1f6a, 63dc50b, 1817eba, 360fde5, ec14151; agent-readiness:src/utils/problemResponse.ts, src/app/api/[...notfound]/route.ts; evidence/reference-branch-recipes.md:366-415

---

## 11. `agentic-search-specific` / `openapi-spec` / `api-schema-analysis` / `function-calling-compat` / `public-api-docs` — developers page + OpenAPI 3.1 + service-desc

**Recipe:**
- Publish `public/openapi.json` as OpenAPI **3.1.0** with
  `servers: [{ "url": "https://www.example.com" }]`. Give every operation a
  unique `operationId` and a `description`, typed response schemas, and
  error responses expressed as `application/problem+json` referencing a
  shared `Problem` component schema (`{type,title,status,code,detail,resolution}`,
  required: `title`, `status`, `code`). Document the rate-limit header
  convention (§17) once in `info.description`.
- Build a `/developers` page: brand name in both `<title>` and `<h1>`, links
  to `openapi.json`, `llms.txt`, and `sitemap.xml`, an `#errors` section
  documenting the problem+json contract, and its own canonical. **Link to
  `/developers` from the homepage** — `public-api-docs` fails partial credit
  when the docs exist but aren't linked from the homepage.
- Emit a `rel="service-desc"` link via the Metadata API (Next 16 has no
  other documented way to emit an arbitrary-rel `<link>`):

```ts
// layout.tsx metadata
icons: { other: { rel: "service-desc", url: "/openapi.json", type: "application/json" } },
```
- List `/openapi.json` and `/developers` in `llms.txt` and `sitemap.xml`.

**Pitfalls:**
- A raw `<head>` tag for the service-desc link can fight the Metadata API —
  use `icons.other` and leave a comment explaining it intentionally hosts a
  non-icon link. Verify this against the target's own bundled Next docs
  (`node_modules/next/dist/docs/`) — the mechanism is not stable across
  majors.
- `agentic-search-specific` measures findability via search, not existence —
  it clears with indexing lag after a correct deploy. Do not churn on it;
  set that expectation with the user.
- For `api-schema-analysis`/`function-calling-compat`, "some `operationId`s,
  some typed schemas" only earns partial credit — every operation needs
  both, not most of them.

**Verification:**
```bash
curl -s localhost:3000/developers | grep -o "<title>[^<]*</title>"
curl -s localhost:3000/openapi.json | python3 -m json.tool > /dev/null
curl -s localhost:3000/ | grep -o 'rel="service-desc"'
curl -s localhost:3000/openapi.json | jq '[.paths[][] | {operationId, description}]'
```

source: 7719af2, 1817eba, 2d86a6b; agent-readiness:public/openapi.json, src/app/(inner)/developers/page.tsx, src/app/layout.tsx; evidence/reference-branch-recipes.md:418-444

---

## 12. `ai-catalog` / `ard` + `apiCatalog` + `linkHeaders` — bonus discovery signals

**Recipe:**
- **`public/.well-known/ai-catalog.json`** (an ARD manifest — same file
  satisfies is-agentic's `ai-catalog` and isitagentready's `ard`):
  `{ specVersion: "1.0", host: { displayName, identifier: "did:web:www.example.com", description, url, contact }, entries: [ { identifier, displayName, type, url, representativeQueries: [...] }, … ] }`
  — one entry per machine surface (OpenAPI, llms.txt, sitemap), each with
  `representativeQueries`.
- **`/.well-known/api-catalog`** route handler returning an RFC 9727 linkset:

```ts
const CATALOG = { linkset: [{ anchor: `${SITE_URL}/`,
  "service-desc": [{ href: absoluteUrl("/openapi.json"), type: "application/openapi+json" }],
  "service-doc":  [{ href: absoluteUrl("/developers"), type: "text/html" }] }] }
// served with content-type: application/linkset+json + Access-Control-Allow-Origin: *
```
- **Discovery `Link` headers** on `/` via `next.config.ts` `headers()` (for
  `linkHeaders`):

```
Link: </.well-known/api-catalog>; rel="api-catalog", </openapi.json>; rel="service-desc"; type="application/openapi+json", </llms.txt>; rel="describedby"; type="text/plain"
```

**Pitfalls:**
- **ARD requires the manifest to be CORS-readable**:
  `Access-Control-Allow-Origin: *` on `ai-catalog.json` via
  `next.config.ts headers()` — files served straight from `public/` cannot
  set their own headers.
- Unit-test `next.config.ts`'s `headers()` function directly (import the
  config, assert the rules) — cheap regression coverage with no server
  needed.
- `ai-catalog` (is-agentic, `/.well-known/ai-catalog.json`) and `apiCatalog`
  (isitagentready, RFC 9727 `/.well-known/api-catalog`) are different
  well-known paths and document shapes — do not conflate them into one file.

**Verification:** `curl -sI /` shows the `Link` header; `curl -sI /.well-known/ai-catalog.json` shows `access-control-allow-origin: *`; both files return 200.

source: 33b1bec, 06c1bcf; agent-readiness:public/.well-known/ai-catalog.json, src/app/.well-known/api-catalog/route.ts, next.config.ts; evidence/reference-branch-recipes.md:447-474

---

## 13. `authMd` — /auth.md agent registration discovery

**Recipe:** Serve `/auth.md` from a route handler (a dotted filename works
as an App Router segment) with `content-type: text/markdown; charset=utf-8`.
Required sections, each tested for presence: an H1 containing the literal
string "auth.md"; `## Agent audience` naming the API and linking the OpenAPI
spec URL; `## Registration`; `## Credential use`.

```ts
// src/app/auth.md/route.ts
const BODY = `# auth.md

## Agent audience
This describes programmatic access to the Example public API (see /openapi.json).

## Registration
Agents must register before use: email hello@example.com or POST /api/contact
to request access; no self-serve signup exists yet.

## Credential use
No credentials are issued for unauthenticated read endpoints. Send requests
without an Authorization header. Rate limits apply per client; honor
Retry-After on 429.`
export function GET(): Response {
  return new Response(BODY, { headers: { "content-type": "text/markdown; charset=utf-8" } })
}
```

**Pitfalls:**
- An unauthenticated public API has no OAuth metadata to point at — keep the
  document self-contained rather than referencing
  `/.well-known/oauth-authorization-server`.
- **2026-09-01 caveat — do not skip this.** The live isitagentready parser
  currently treats wording like "no registration required" / "no
  registration or API key is required" as a **fail**, even when the file
  exists, returns 200, and has the right content type, and even when the
  file follows every heading in this recipe exactly. If the target's
  `## Registration` section reads as "nothing to register," rewrite its
  prose to describe an actual registration or access-request flow (as in
  the sketch above) instead of stating there is none — this is a wording fix
  against an already-structurally-correct file, not a from-scratch build.
  Confirm current parser behavior against a live scan before declaring this
  check fixed; do not assume the structural recipe alone clears it.

**Verification:** `curl -s localhost:3000/auth.md` → 200 markdown, all four sections present; then run a live isitagentready scan and confirm `authMd` reads `pass`, not just that the file exists.

source: 5e8ae2d; agent-readiness:src/app/auth.md/route.ts, src/__tests__/authMd.test.ts; evidence/reference-branch-recipes.md:477-487

---

## 14. `agentSkills` — .well-known/agent-skills digest-verified discovery index

**Recipe:** Static files under `public/.well-known/agent-skills/`:

```json
// index.json
{ "$schema": "https://schemas.agentskills.io/discovery/0.2.0/schema.json",
  "skills": [{ "name": "example-api", "type": "skill-md",
    "description": "Query Example's public REST API …",
    "url": "/.well-known/agent-skills/example-api/SKILL.md",
    "digest": "sha256:<sha256 hex of the SKILL.md's exact bytes>" }] }
```
Each `SKILL.md`: YAML frontmatter (`name` kebab-case matching the index,
`description`), an H1, `## When to use this` (concrete jobs plus an explicit
"Not for:"), `## Endpoints`/`## How` with absolute URLs, `## Errors`
documenting the problem+json contract. Ship one skill per machine surface.

**Pitfalls:**
- The `digest` is the sha256 of the file's **exact bytes** — any later edit
  to a `SKILL.md` silently breaks it. Add a test that recomputes
  `createHash("sha256")` over `readFileSync(url)` and compares against the
  index — do not ship this pattern without that regression test.
- Agent-skills clients fetch cross-origin: set
  `Access-Control-Allow-Origin: *` on `/.well-known/agent-skills/:path*` via
  `next.config.ts headers()`.
- `name` must match `^[a-z0-9]+(-[a-z0-9]+)*$`; `url` must be root-relative
  under `/.well-known/agent-skills/`.

**Verification:** run the digest test; `curl -sI /.well-known/agent-skills/index.json` shows the CORS header.

source: af76e44, 7f69281; agent-readiness:public/.well-known/agent-skills/index.json, src/__tests__/agentSkills.test.ts; evidence/reference-branch-recipes.md:490-513

---

## 15. `a2aAgentCard` — A2A endpoint + agent-card.json

**Recipe:**
- Serve `public/.well-known/agent-card.json` (a2a-protocol.org v0.3.0):
  `{ protocolVersion: "0.3.0", name, version, description (states capabilities AND non-goals), url: ".../api/a2a", preferredTransport: "JSONRPC", supportedInterfaces: [...], provider, capabilities: {streaming:false, pushNotifications:false, stateTransitionHistory:false}, defaultInputModes/defaultOutputModes: ["text/plain"], skills: [{id, name, description, tags, examples}] }`
  with `Access-Control-Allow-Origin: *`.
- Implement `src/app/api/a2a/route.ts` as JSON-RPC 2.0 supporting only
  `message/send`, reusing the site's existing guardrailed system prompt.
  Map errors to **JSON-RPC error codes, not problem+json**: `-32700` parse
  error, `-32601` method not found (name the supported method), `-32602`
  invalid params (show the expected shape), `-32603` internal error.
  Non-POST → `methodNotAllowed(["POST"], "<example JSON-RPC body>")`.
  Rate-limit via the shared limiter (§17); success carries `RateLimit-*`
  headers.

**Pitfalls:**
- A2A is cross-origin by design — do not origin-gate it the way a
  same-site chat endpoint might be; rate limiting is the abuse control here,
  not CORS.
- Inside a JSON-RPC envelope, errors are JSON-RPC error objects.
  `application/problem+json` applies only at the transport level (a 429 or
  405 before the JSON-RPC body is even parsed).

**Verification:** POST a `message/send` envelope → a result message; an unsupported method → `-32601`; malformed JSON → `-32700` with `id: null`.

source: 7f69281; agent-readiness:src/app/api/a2a/route.ts, public/.well-known/agent-card.json; evidence/reference-branch-recipes.md:516-530

---

## 16. `mcp-server` / `mcpServerCard` + `webMcp` — MCP server + server-card + WebMCP

**Recipe:**
- Ask the user before installing `mcp-handler`, `zod`, and
  `@modelcontextprotocol/server` (new dependencies). Build `/mcp` as a
  streamable-HTTP MCP server with `createMcpHandler`, exposing read-only
  tools declared `annotations: { readOnlyHint: true }`, with `instructions`
  stating scope and out-of-scope. `export const dynamic = "force-dynamic"`;
  export `handler as GET`, a wrapped `POST`, and `handler as DELETE`.
- Serve `public/.well-known/mcp/server-card.json`:
  `{ serverInfo: {name, version}, description (with non-goals), url: ".../mcp", transport: { type: "streamable-http" }, capabilities: { tools: true } }`.
- For WebMCP (webmachinelearning.github.io/webmcp), define the same tools as
  `navigator.modelContext.registerTool` entries in a client util, and
  register them from a `"use client"` component mounted once in the root
  layout, inside `useEffect` — a no-op where `navigator.modelContext` does
  not exist.

**Pitfalls:**
- MCP tool calls can trigger paid model inference — route the handler
  through the same rate limiter as any other AI-backed endpoint: run
  `enforce()` first (429 problem+json on failure), and copy `RateLimit-*`
  headers onto the successful response by rebuilding it
  (`new Response(response.body, response)` then `headers.set`).
- Add the MCP route's segment (e.g. `mcp`) to the proxy's `KNOWN_SEGMENTS`
  (§9) — otherwise a markdown-preferring request to `/mcp` gets the proxy's
  404 instead of the MCP handler.
- A DNS-AID record (e.g. `_mcp._agents.<host>`) is a second, optional
  advertisement channel for MCP discovery — it is a DNS-zone action outside
  the application repo, not something this recipe can ship.

**Verification:** `curl -s /.well-known/mcp/server-card.json | python3 -m json.tool` → valid JSON; MCP client smoke test against `/mcp`; WebMCP has no reliable static probe — verify in a real browser, not curl.

source: 7f69281; agent-readiness:src/app/mcp/route.ts, public/.well-known/mcp/server-card.json, src/utils/webMcpTools.ts; evidence/reference-branch-recipes.md:533-547

---

## 17. `rate-limit-headers` — draft-ietf-httpapi-ratelimit-headers

**Recipe:** Extend the existing rate limiter's `enforce()` to also return
headers built from the most-constrained active window:

```ts
export function buildRateLimitHeaders(checks: RateCheck[], now = Date.now()) {
  if (checks.length === 0) return {}
  const most = checks.reduce((a, b) => (b.remaining < a.remaining ? b : a))
  return { "RateLimit-Limit": String(most.limit),
           "RateLimit-Remaining": String(Math.max(0, most.remaining)),
           "RateLimit-Reset": String(Math.max(0, Math.ceil((most.reset - now) / 1000))) }
}
```
Attach these headers to every success response
(`Response.json(body, { headers: gate.headers })`), and merge them into 429
problem responses alongside `Retry-After` (delta-seconds) and
`X-RateLimit-Scope` (the name of the exhausted window). Document the
convention once in `openapi.json`'s `info.description`.

**Pitfalls:**
- `RateLimit-Reset` is **delta-seconds from now, not an epoch timestamp** —
  a common source of off-by-a-decade bugs when copied from a different
  header convention.
- Report the most-constrained window when multiple limiters apply at once
  (e.g. per-minute and per-day) — never report a less-restrictive one.
- Documenting the convention in `openapi.json` without an observed live
  header on a real 429 response earns only partial credit — ship the
  headers before or in the same commit as the documentation.

**Verification:** `curl -sI -X POST localhost:3000/api/contact | grep -i ratelimit`; trigger a 429 and confirm `Retry-After` + `X-RateLimit-Scope` are present alongside `RateLimit-*`.

source: 7f69281; agent-readiness:src/lib/rate-limit.ts; evidence/reference-branch-recipes.md:550-568

---

## 18. IndexNow — supports `agentic-search-specific` / `brand-search-accuracy` (no dedicated check ID)

**Recipe:**
- Serve `public/{key}.txt` containing an IndexNow key (the key file is
  public by design — IndexNow authenticates via the matching file being
  reachable at the site root, not via secrecy).
- `pingIndexNow(paths)`: `POST https://api.indexnow.org/indexnow` with
  `{ host, key, urlList: paths.map(absoluteUrl) }`, entire call wrapped in
  try/catch — a failed ping must never break the caller, it only delays
  recrawl.
- Wire it into the CMS webhook: collect changed paths, `revalidatePath` each
  plus `/sitemap.xml`, then `await pingIndexNow(changedPaths)` — **await
  it**, so a serverless runtime cannot tear down the request before the ping
  lands.
- Before relying on it, confirm the site's canonical host is verified in
  Bing Webmaster Tools (often easiest via a Google Search Console import)
  and the sitemap is submitted — IndexNow supplements crawl speed, it does
  not replace basic indexing setup.

**Pitfalls:**
- Never let an IndexNow failure surface as an error to the CMS webhook
  caller or the end user — it is best-effort only.
- GPTBot is training-only, `ChatGPT-User` is user-initiated fetches, and
  `OAI-SearchBot` is the actual search surface — do not assume blocking or
  allowing one covers the others when reasoning about crawl behavior (§3).

**Verification:** trigger the CMS webhook against a staging entry and confirm a 200 from the IndexNow API in logs (best-effort — a failure here should not fail the webhook's own response).

source: 498d246; agent-readiness:src/utils/indexNow.ts, public/{key}.txt, src/app/api/revalidate/route.ts; evidence/reference-branch-recipes.md:572-580

---

## 19. Proven execution order + required user inputs

**Execution order (do not reorder without a reason — later phases build on
earlier infrastructure):**
1. **Discovery surface** (§0–§8, §11–§14, §18): pure additions plus one page
   split. Lowest risk, clears the most checks fastest.
2. **Markdown content negotiation** (§9): adds a proxy that touches every
   page response — needs the site config and test harness from §0 first.
3. **API problem+json** (§10) — **deliberately last**: the most
   behavior-sensitive change, since UI consumers (contact forms, chat
   widgets) must change in the same commit as the routes they call. Confirm
   every affected API route lives in the target repo (no external
   backend-team dependency) before starting.
4. **MCP / WebMCP / A2A / rate-limit headers** (§15–§17): layer onto the
   now-stable API surface and reuse its rate limiter and problem helper.

After each phase: `pnpm test && pnpm build` green, run the phase's curl
matrix against a **production build** (`pnpm build && pnpm start`, not
`next dev`), merge, deploy, then re-scan (`npx is-agentic <host> --json` or
the isitagentready `POST /api/scan`) and diff `issues[]`/`checks` by ID
against the dated baseline — quote `scanned_at`/`scannedAt` every time (see
check-contracts.md's re-scan semantics).

**Required user inputs (blocking asks — ship the surrounding feature with
the gap explicitly recorded rather than blocking on them):**
- Registered postal address for `Organization.address` (§7) — often nowhere
  in the repo; check a privacy policy or terms page before asking.
- Official social/profile URLs for `sameAs` (§7) — only list a profile the
  user has explicitly confirmed as official.
- Approval for every new dependency before installing it: vitest (§0), and
  later `mcp-handler`/`zod`/`@modelcontextprotocol/server` (§16) if MCP is
  in scope.
- Canonical-host confirmation (apex vs. `www`, §0) and execution-order
  preference are user decisions — do not assume either silently.

**Accepted gaps (do not "fix" these without a product decision):**
- A published CLI/SDK package (`cli-tool`) is a product decision, not a code
  fix — bonus signals (§12, §14) can cover the score gap instead.
- `brand-search-accuracy` moves over weeks via external signals (press,
  NAP consistency, `sameAs`) — never block a release on it.
- Commerce checks (`x402`, `mpp`, `ucp`, `acp`, `ap2`, and is-agentic's
  Payments layer) are `neutral`/excluded on any site with no commerce
  surface — do not build a payments surface just to clear them.
- `agentic-search-specific` clears with search-indexing lag after a correct
  `/developers`+OpenAPI deploy — re-scan later, do not churn immediately.

**Cross-cutting conventions worth reusing:**
- Trace every fix to an observed failure (a header, a status code, a char
  count, a specific file) from a dated baseline scan — not to a scanner's
  generic recommendation text.
- Consult the target's own bundled framework docs
  (`node_modules/next/dist/docs/`) before using any API whose name looks
  familiar — a major version can rename or replace it (middleware→proxy is
  exactly this kind of trap).
- Ship one check-clearing feature per commit, named after the check it
  clears, with a test. Budget a dedicated review-fix pass — on the reference
  branch, review-fix commits caught the highest-value pitfalls in this file
  (JSON-LD escaping, the canonical `Link` header on markdown routes, the
  robots `/md/` disallow, the segment-parity test, the dereferenceable
  `#errors` anchor, and the contact-route 405).

source: evidence/reference-branch-recipes.md:584-609
