#!/usr/bin/env python3
"""Read-only agent-readiness probe. GET/HEAD only; never mutates the target.

    python3 scripts/probe.py https://example.com [/docs,/pricing,/about]

Stdlib only, no install. Exit 2 if the target is unreachable (a blocked
sandbox is not a bad website -- never report one as the other).
Evidence date 2026-09-04.
"""
import json, re, ssl, sys, urllib.request as U, urllib.error as E
UA = {"User-Agent": "agent-readiness-probe (+read-only audit)"}
def get(url, accept=None, method="GET"):
    h = dict(UA)
    if accept: h["Accept"] = accept
    try:
        r = U.urlopen(U.Request(url, headers=h, method=method), timeout=20,
                      context=ssl.create_default_context())
        return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read(2_000_000)
    except E.HTTPError as e:
        return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, (e.read(500_000) or b"")
    except Exception as e:
        return 0, {}, str(e).encode()

base = sys.argv[1].rstrip("/")
paths = sys.argv[2].split(",") if len(sys.argv) > 2 else ["/docs", "/pricing", "/about"]
st, hd, body = get(base)
html = body.decode("utf-8", "replace")
text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
        re.sub(r"(?is)<(script|style|noscript|svg|template)\b.*?</\1>", " ", html))).strip()
h1 = re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", html)

# content-no-js scores heading STRUCTURE, not the h1 count. Report every skip
# in one pass -- fixing only the first and re-running is a recorded failure.
heads = [(int(m.group(1)), re.sub(r"<[^>]+>", " ", m.group(2)).strip()[:60])
         for m in re.finditer(r"(?is)<h([1-6])[^>]*>(.*?)</h\1>", html)]
skips = [f"h{a[0]}->h{b[0]} before {b[1]!r}"
         for a, b in zip(heads, heads[1:]) if b[0] > a[0] + 1]

out = {
  "status": st,
  "resp_headers": hd,
  "text_chars": len(text),
  "html_bytes": len(body),
  "h1_count": len(h1),
  "h1_text": [re.sub(r"<[^>]+>", "", x).strip()[:120] for x in h1],
  "heading_sequence": [f"h{l}" for l, _ in heads],
  "heading_outline": heads,
  "heading_skips": skips,
  "content_efficiency_pct": round(100 * len(text) / max(1, len(body)), 2),
  "canonical": bool(re.search(r'rel=["\']canonical', html, re.I)),
  "html_lang": bool(re.search(r'<html[^>]*\blang\s*=', html, re.I)),
  "og_image": bool(re.search(r'property=["\']og:image', html, re.I)),
  "og_type": bool(re.search(r'property=["\']og:type', html, re.I)),
  "json_ld_blocks": len(re.findall(r'application/ld\+json', html, re.I)),
  "json_ld_types": re.findall(r'"@type"\s*:\s*"([^"]+)"', html)[:40],
  "service_desc": bool(re.search(r'rel=["\']service-desc', html, re.I)),
  "title": (re.search(r"(?is)<title[^>]*>(.*?)</title>", html) or [None, None])[1] if re.search(r"(?is)<title", html) else None,
}

mst, mhd, mbody = get(base, accept="text/markdown")
nst, _, _   = get(base, accept="application/vnd.nonexistent")
out["md_status"] = mst
out["md_content_type"] = mhd.get("content-type", "")
out["md_vary"] = mhd.get("vary", "")
out["md_vary_has_accept"] = "accept" in [t.strip().lower() for t in mhd.get("vary", "").split(",")]
out["md_body_head"] = mbody[:200].decode("utf-8", "replace")
out["unsupported_accept_status"] = nst

fst, fhd, fbody = get(base + "/__probe-does-not-exist-9f3a")
out["notfound_status"] = fst
out["notfound_content_type"] = fhd.get("content-type", "")
out["notfound_bytes"] = len(fbody)
out["notfound_links"] = len(re.findall(r"href=", fbody.decode("utf-8", "replace"), re.I))
fmst, fmhd, fmbody = get(base + "/__probe-does-not-exist-9f3a", accept="text/markdown")
out["notfound_md_content_type"] = fmhd.get("content-type", "")

out["interior"] = {}
for path in paths:
    s2, h2, b2 = get(base + path)
    d2 = b2.decode("utf-8", "replace")
    t2 = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ",
         re.sub(r"(?is)<(script|style|noscript|svg|template)\b.*?</\1>", " ", d2))).strip()
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', d2, re.I)
    ttl = re.search(r"(?is)<title[^>]*>(.*?)</title>", d2)
    out["interior"][path] = {
        "status": s2,
        "canonical": m.group(1) if m else None,
        "title": ttl.group(1).strip()[:140] if ttl else None,
        "h1": len(re.findall(r"(?is)<h1[^>]*>", d2)),
        "text_chars": len(t2),
        "efficiency_pct": round(100 * len(t2) / max(1, len(b2)), 2),
        "json_ld_blocks": len(re.findall(r'application/ld\+json', d2, re.I)),
    }

out["files"] = {}
for p in ["/robots.txt", "/llms.txt", "/llms-full.txt", "/sitemap.xml", "/openapi.json",
          "/openapi.yaml", "/.well-known/mcp/server-card.json", "/.well-known/ai-catalog.json",
          "/.well-known/api-catalog", "/server.json", "/agent-instructions.md",
          "/AGENTS.md", "/agents.md", "/pricing.md", "/.well-known/security.txt"]:
    s, h, b = get(base + p)
    is_shell = "text/html" in h.get("content-type", "") or b[:64].lstrip().lower().startswith(b"<!doctype html")
    out["files"][p] = {"status": s, "bytes": len(b), "content_type": h.get("content-type", ""),
                       "app_shell": is_shell, "head": b[:300].decode("utf-8", "replace") if not is_shell else ""}

out["reachable"] = st != 0
print(json.dumps(out, indent=2))
sys.exit(0 if out["reachable"] else 2)
