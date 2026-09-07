# Preview gate — agent-readiness-remediation

Evidence date: 2026-09-03. Measured end-to-end against a Next.js App Router
target on Vercel, scanning a branch's own preview host with both scanners and
diffing it against the live production host the same hour. On mismatch, live
scanner output wins over this file.

Phase 4.5. Predict the post-deploy score while the branch is still cheap to
change. **A preview result is a prediction: it never yields `fixed+verified`
and never replaces phase 5.**

This file is deliberately short. It carries only what a 12-run pressure test
showed agents do *not* derive on their own — the discovery commands and the
measured host-drift data. Phase 5's gate and `verification.md` §2–§5 already
supply the discipline, and were shown to hold without any of it
(`specs/001-agent-remediation-skill/evidence/preview-gate-pressure-test.md`).

---

## 1. Preconditions

Run the gate when the target publishes a **public per-commit URL** for
non-production branches (Vercel, Netlify, Cloudflare Pages) and that host
answers unauthenticated.

> **"Nothing was pushed" is not a precondition failure.** Route (d) below
> deploys the working tree and needs no commit, push or branch. Recorded
> rationalisation from a real run: *"no branch was pushed, so no preview
> deployment exists to scan"* — the gate was skipped, and the user had to
> prompt for it. The gate is unavailable when there is **no reachable preview
> AND no deploy route** — a deploy route being an authenticated CLI *plus* a
> working tree it is safe to publish (see route (d)'s precondition).

Reachability check:

```bash
curl -sI --max-time 15 "https://$PREVIEW_HOST/" | head -1
```

`200` → proceed. A `302` to a login (`vercel.com/sso-api`), a `401`, or an HTML
password form → record `gate-unavailable: deployment protected` and go to
phase 5. Never scan a protected preview: both scanners would score the auth
wall, and a bypass secret cannot help because a third-party scanner sends
neither the header nor the cookie.

Lifting protection is the **user's decision** — it makes previews publicly
readable. On Vercel the free route is disabling Vercel Authentication for
previews on that project; a per-domain Deployment Protection Exception needs
Enterprise, or Pro with the Advanced Deployment Protection add-on.

---

## 2. Finding the preview URL

**Discover it; never ask the user to paste a URL.** Verified on a
GitHub + Vercel target.

**a. Exact commit (preferred)** — ties the scan to the commit under review:

```bash
SHA=$(git rev-parse HEAD)
REPO=$(git remote get-url origin | sed -E 's#.*[:/]([^/]+/[^/]+?)(\.git)?$#\1#')
DEP=$(gh api "repos/$REPO/deployments?sha=$SHA" \
        --jq '[.[]|select(.environment=="Preview")][0].id')
PREVIEW_URL=$(gh api "repos/$REPO/deployments/$DEP/statuses" \
        --jq '[.[]|select(.state=="success")][0].environment_url')
```

**b. Branch alias (fallback)** — `<project>-git-<branch-slug>-<team>.vercel.app`.
Read the project and team slug from the Vercel commit status rather than
guessing; the project slug often differs from the repo name:

```bash
gh api "repos/$REPO/commits/$SHA/statuses" \
  --jq '.[]|select(.context=="Vercel")|.target_url'   # vercel.com/<team>/<project>/<id>
```

**c. Platform CLI** — `vercel ls <project> --scope <team>`. Needs the CLI
authenticated; does not need the repo `vercel link`ed.

**d. Deploy the working tree (no git required)** — verified 2026-09-04. This is
the route for edit-only mode, an unpushed branch, a dirty tree, or a target that
is not a git repo at all:

```bash
npx vercel@latest deploy --yes          # prints the preview URL on stdout
```

It uploads the working tree as it stands. **No commit, no push, no branch, no
`vercel link` is needed**, and the resulting host is public and scannable like
any other preview. The `--yes` accepts the project-scope prompts; without it the
command blocks on interactive input and looks like a hang.

> **Precondition: a working-tree deploy publishes the working tree.**
> Everything uncommitted goes up — including work that is not yours. Before
> running it, check:
>
> ```bash
> git status --porcelain
> ```
>
> **Clean, or dirty only with your own remediation edits** → deploy.
>
> **Dirty with anyone else's in-flight work** → do **not** deploy it silently.
> Say what you found, name the files, and let the user choose: deploy anyway,
> stash their work first, or skip the gate. If they are not available to ask,
> **skipping is the correct outcome** — record `gate-unavailable: working tree
> carries unrelated uncommitted work` and go to phase 5. That is a sanctioned
> skip, not a rule violation.
>
> Measured 2026-09-04: in 5 of 5 runs on a tree carrying a user's half-finished
> refactor, agents independently refused to deploy it — and 3 of 5 then had to
> report the skip as *unsanctioned*, because this clause did not yet exist. They
> were right and the file was wrong.
>
> The same caution applies to what the deploy makes public. `llms.txt` and the
> sitemap hand a crawler the whole corpus in one fetch, so read what you are
> about to publish — a preview URL is public.

Notes measured on the same run:

- **Use `npx vercel@latest`, not a globally installed `vercel`.** An outdated
  global CLI fails in ways that read as auth or project errors rather than as a
  version problem.
- **Clean up `.vercel/`** afterwards if the deploy created one in a target repo
  that had none. It is a local link artifact, not part of the fix, and it should
  not ride along in a check's commit.
- **`NEXT_PUBLIC_APP_URL` and friends resolve from the project's preview
  environment**, which may point at a different branch's host than the one you
  just deployed. Check what the deployed page actually emits before reading an
  absolute-URL check off it — this compounds the blind spot in §5.

Confirm the deployment for the current HEAD is ready before scanning. A branch
alias serves the latest *ready* build, which mid-build is the previous commit.

---

## 3. Scan the per-commit URL, not the branch alias

is-agentic caches per host for ~6 h (`verification.md` §2). A per-commit host is
unique, so its first scan is always fresh — no cache wait on any iteration. A
branch alias is stable, so a second scan within the window replays the first
snapshot and reads as "no progress." Use the per-commit URL as the scan target
and the alias only for discovery.

isitagentready has no documented cache; either host works there.

---

## 4. Diff by check ID, and watch the denominator

Compare per check ID against the production baseline, never score to score.
Apply `verification.md` §3 unchanged. Three buckets: cleared on preview,
preview-unreliable (below), still failing (the finding the gate exists for).

These drifted between a production host and its own preview host in the same
hour with identical code. Read nothing into them either way:

| Check | Scanner | Production | Preview | Why |
|---|---|---|---|---|
| `dnsAid` | isitagentready | `pass` | `fail` | records live in the apex zone; a `*.vercel.app` host has no zone you control |
| `brand-search-accuracy` | is-agentic | pass | `failed` | external index has never seen the preview host |
| `agentic-search-specific` | is-agentic | pass | `partial` | same index dependency |
| `mcp-server` | is-agentic | pass | `partial` | registry/reputation evidence resolved against the domain |
| `cli-tool` | is-agentic | `failed` | excluded | package-registry lookup keyed to the brand domain |

> **The denominator rule.** Tier totals move between hosts: measured
> `essential.total` 11 on production against 10 on the preview, and
> `recommended.total` 21 against 22, same code. If `essential.total` differs
> from the baseline, an essential check is not eligible on the preview and the
> gate cannot speak for it — say so rather than reporting a clean tier. Which
> check was excluded is not knowable, since the API enumerates only failed and
> partial checks.

A corollary worth stating to the user: when an `accepted-gap` check drops out
of the preview denominator, the preview score sits **above** what production
can score while that gap stands. Closing a ticket on that number makes the next
production scan read as a regression.

---

## 5. Blind spots

- **Absolute URLs point at production.** Where the base URL is a constant or a
  build-time variable, the preview serves production canonicals, sitemap `<loc>`
  values and `og:url` — measured. So `canonical-correctness`, `sitemap` and
  `metadata-completeness` are reading production values on a preview, and a
  canonical regression on the branch can pass the gate. Verify those three at
  phase 5 regardless.
- **`X-Robots-Tag: noindex` is present and, as measured, unpenalised.** Vercel
  stamps it on every non-production deployment and it cannot be disabled on a
  `*.vercel.app` host. Both scanners still returned a full essential tier and a
  score of 100. Do not chase it.
- **Per-environment CDN and firewall rules.** If they differ between preview and
  production, `bot-protection`, `rate-limit-headers` and `ai-crawler-access` are
  preview-unreliable too. Not separately measured.

A green gate is evidence for the user's merge decision, not the decision. The
report's four outcomes in `verification.md` §6 are unchanged; a preview adds at
most a `Preview result` column beside what production actually showed.
