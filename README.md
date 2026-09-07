# agent-readiness

Two paired skills for making a site legible to AI agents — one that measures, one
that builds. Both are self-contained: no plugin dependencies, no other skills, no
network service beyond the two public scanners and Ora's check catalogue.

| Skill | What it does |
|---|---|
| **agent-readiness-audit** | Scans a site, produces an evidence-backed report and a baseline artifact. Never edits the target. |
| **agent-readiness-remediation** | Takes that baseline to an agreed target score, one check ID at a time, with evidence for every claim. Writes code. |

They cover `llms.txt`, `AGENTS.md`, robots.txt AI-crawler rules, Content-Signal,
sitemaps, JSON-LD and Organization schema, trust-anchor pages, markdown content
negotiation, agent-friendly 404s, RFC 9457 `problem+json` errors, OpenAPI
discoverability and `.well-known` manifests.

## Install

```
/plugin marketplace add danielcalvolopez/agent-readiness
/plugin install agent-readiness@agent-readiness
```

Or copy `skills/agent-readiness-audit` and `skills/agent-readiness-remediation`
into `~/.claude/skills/` (or `~/.agents/skills/` for cross-runtime use). They are
plain directories with no build step.

## Use

Audit first — remediation requires a baseline artifact and refuses to run without
one:

```
audit acme.dev for agent readiness
```

Then, with that baseline in hand:

```
now fix it
```

## How remediation works

Six phases, three of them hard gates:

| # | Phase | Gate |
|---|---|---|
| 1 | Baseline | **HARD** — no file edits before a dated baseline exists |
| 2 | Scope | **HARD** — the user classifies every failed check |
| 3 | Plan | Written to a file; fixed risk order; one check ID per commit |
| 4 | Implement | Matching playbook > generic; target conventions win |
| 4.4 | Conformance review | **HARD** — fresh eyes diff the work against the plan |
| 4.5 | Preview gate | Predict the post-deploy score before merging |
| 5 | Verify | **HARD** — evidence per check + both scanners re-run |
| 6 | Report | Every baseline issue classified |

The design principles behind that shape:

- **No claim without evidence.** A check is `fixed+verified` only when its own
  evidence command passes against the deployed host *and* a fresh re-scan shows
  its diff cleared. A green local build is not evidence.
- **Product decisions belong to the user.** Building a CLI, running an MCP
  server, publishing a postal address or granting training permission are asked
  about, never assumed into scope.
- **Secrets outrank the score.** Discovery files hand your whole corpus to every
  crawler in one fetch, so the skills read what they are about to publish.
- **No SEO dark patterns.** No keyword filler, no text written for a scanner
  rather than a reader.

## Testing

Both hard-gate behaviours in Phase 4.4 were tested with subagents, RED/GREEN,
against a no-guidance control:

| Claim | Control | With skill |
|---|---|---|
| An independent review happens at all after implementation | 0/3 | 3/3 |
| A credential found in a diff is redacted rather than reprinted | 0/3 | 3/3 |

The control agents were not careless — each self-reviewed its own diff before
moving on. That substitution, author-checks-own-work, is what the gate exists to
prevent.

## Licence

MIT
