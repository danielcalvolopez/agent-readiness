#!/usr/bin/env python3
"""Force a fresh is-agentic scan, then print the report only if it is fresh.

The report API and `npx is-agentic` both serve the last stored snapshot, which
can be weeks old. This drives the same stream the site's "Rescan" button uses
(`force=1`), waits for the report API to catch up (it lags ~5 min), and
refuses any report whose scanned_at predates this run.

    python3 isagentic_scan.py https://www.example.com > isagentic.json

Takes 1-10 min. Exit 0 fresh report on stdout, 3 stale (scan did not reach
the report API in time), 1 other error.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://is-agentic.com"
SKEW_S = 120  # tolerate clock drift between this machine and the scanner
POLL_S, POLL_TRIES = 30, 20


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def is_fresh(scanned_at, started):
    return (started - parse_ts(scanned_at)).total_seconds() <= SKEW_S


def force_scan(target):
    q = urllib.parse.urlencode({"target": target, "force": "1"})
    req = urllib.request.Request(
        f"{BASE}/api/scan/stream?{q}",
        headers={"Accept": "text/event-stream",
                 "Referer": f"{BASE}/scan/{urllib.parse.urlparse(target).netloc}"})
    with urllib.request.urlopen(req, timeout=600) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            ev = json.loads(line[5:])
            if ev.get("type") == "scan_complete":
                return ev["result"]["scannedAt"]
            if ev.get("type") == "error":
                raise RuntimeError(f"scan error: {ev}")
    raise RuntimeError("stream ended without scan_complete")


def fetch_report(target):
    q = urllib.parse.urlencode({"url": target})
    with urllib.request.urlopen(f"{BASE}/api/v1/report?{q}", timeout=30) as r:
        return json.load(r)


def main(target):
    started = datetime.now(timezone.utc)
    try:
        forced_at = parse_ts(force_scan(target))
        # The report API lags the stream by ~5 min (measured 2026-09-21).
        for _ in range(POLL_TRIES):
            report = fetch_report(target)
            if parse_ts(report["scanned_at"]) >= forced_at:
                break
            time.sleep(POLL_S)
    except Exception as e:
        print(f"is-agentic forced scan failed: {e}", file=sys.stderr)
        return 1
    if not is_fresh(report["scanned_at"], started):
        print(f"STALE: scanned_at {report['scanned_at']} predates run start "
              f"{started.isoformat()}. Do not report this score.", file=sys.stderr)
        return 3
    json.dump(report, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
