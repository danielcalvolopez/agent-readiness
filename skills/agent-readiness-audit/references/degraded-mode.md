# Degraded mode — agent-readiness-audit

Loaded from step 0 when preflight shows no outbound HTTPS. A blocked sandbox is
not a bad website; this file is how you keep those two apart in the report.

## Degraded mode: what a fetch tool can and cannot see

When you only have a page-fetch tool (no raw HTTP), you typically cannot set request
headers, read response headers, read status codes, or read raw HTML. That removes
about half the check list. Be precise about which half:

| Still checkable | Method |
|---|---|
| `sitemap`, `llms-txt`, `llms-full.txt`, `robots.txt` presence and content | fetch the path, read the body |
| `llms.txt` spec compliance | fetch and validate the text |
| `agent-instruction` | look for when-to-use guidance in the fetched text |
| `openapi-spec` | fetch the conventional paths |
| `canonical-correctness` | fetch 2–3 interior pages, compare declared canonical to the page's own URL |
| `agentic-search-specific` | read titles and headings |

| **Not** checkable — mark `not_verified`, never `failed` | Why |
|---|---|
| `markdown-negotiation-vary` | cannot send `Accept:` or read `Vary:` |
| `agent-friendly-404` | cannot read the status code |
| `content-no-js`, `content-efficiency` | cannot read raw HTML byte counts |
| `json-ld`, `org-schema-completeness`, `trust-anchors` | `<script>` blocks are stripped from rendered text |
| `metadata-completeness` (`html lang`) | not present in rendered output |
| `https-and-transport`, `bot-protection`, `rate-limit-signalling` | header-dependent |
| `json-error-responses` | needs status code and content type |

A degraded report is still worth writing. A degraded report that presents
`not_verified` as `failed` is worse than no report.

## Calibrate empty vs missing

A fetch tool returning *nothing* is ambiguous: the file may be absent, or the tool may
be refusing to render `text/plain`. **Fetch a known-good control before concluding
anything.**

```
fetch https://www.google.com/robots.txt     # renders? then text/plain works
fetch https://<target>/robots.txt           # still empty? genuinely absent
```

Do the same with a known-absent path to see what a 404 looks like through your tool.
Without this calibration you will report present files as missing. State in the report
that you calibrated, and how.
