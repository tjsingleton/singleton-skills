# Skills inventory and agent matrix

This document describes:

1. **What lives in this repository** — skills, certification status, and install routes.
2. **How agents discover skills** — discovery paths and which routes each host uses.
3. **What is installed globally on the authoring machine** — a point-in-time snapshot of third-party and personal skills outside this repo's installer.

Refresh the global snapshot with:

```bash
npx skills@latest list -g
just list target=all
```

Last snapshot: **2026-07-31**.

---

## Agent discovery matrix

Agents do not share one directory. The `npx skills` CLI treats `~/.agents/skills` as the **shared canonical store** and symlinks into several agent-specific trees.

| Agent | Primary discovery path | Also reads | Managed by singleton-skills installer | Typical third-party install target |
| --- | --- | --- | --- | --- |
| **Claude Code** | `~/.claude/skills/` | Native plugins (`/plugin install …`) | `target=claude` or `target=all` | `npx skills add … -a claude-code` |
| **Cursor** | `~/.agents/skills/` | `~/.cursor/skills/`, Cursor plugins | `target=shared` | `npx skills add … -a cursor` |
| **Codex** | `~/.agents/skills/` | `~/.codex/skills/`, Codex plugins | `target=shared` | `npx skills add … -a codex` |
| **Gemini CLI** | `~/.gemini/skills/` | `~/.agents/skills/` (symlinked) | — | `npx skills add … -a gemini` |
| **Hermes Agent** | `~/.hermes/skills/` | `~/.agents/skills/` (partial overlap) | — | Hermes-specific bundles |
| **OpenCode** | `~/.config/opencode/skills/` | `~/.agents/skills/` (symlinked) | — | `npx skills add … -a opencode` |
| **Antigravity CLI** | `~/.agents/skills/` | — | `target=shared` | `npx skills add … -g` |

### Install routes in this repository

| Route | Destination | Default `just install` set | Notes |
| --- | --- | --- | --- |
| **Shared** | `$SINGLETON_SHARED_SKILLS_DIR` → `~/.agents/skills` | `supported-skills.txt` only | Intended for Codex and Cursor |
| **Claude** | `$SINGLETON_CLAUDE_SKILLS_DIR` → `~/.claude/skills` | `supported-skills.txt` only | Explicit Claude Code route |
| **All targets** | Both shared and Claude | same | `just install target=all` |
| **Native plugins** | Host-managed Claude/Codex/Cursor plugin location | all skills under `skills/` | Do **not** combine with symlinks for the same skill |

Environment overrides:

- `SINGLETON_SHARED_SKILLS_DIR` — shared install root
- `SINGLETON_CLAUDE_SKILLS_DIR` — Claude install root

Ownership is tracked in `.singleton-skills-links.json` at each install root. Only links recorded there are removed by `just uninstall`.

The shared and Claude symlink routes are the portable-core routes. Native
plugins are deliberately broader, host-specific all-skills routes; their
presence does not certify every skill as portable. Enabling both routes in one
host can produce duplicate discovery.

### Native plugin IDs and migration

The marketplace and plugin IDs are both `singleton-skills`. This is a clean
break from the former Claude development marketplace ID
`singleton-skills-dev`: uninstall the old plugin, remove that marketplace, then
register the root checkout and install
`singleton-skills@singleton-skills`. Do not keep both marketplace IDs active.

`just register` is read-only and shell-neutral: it only prints the
`SINGLETON_SKILLS_PATH` export plus Claude Code, Codex, and Cursor registration
commands. The repository does not publish externally or mutate host or shell
configuration.

---

## Repository inventory

Skills defined in **singleton-skills** and their intended portability.

| Skill | Location | Portable-core | Intended hosts | Install set |
| --- | --- | --- | --- | --- |
| `git-triage` | `skills/git-triage/` | **Yes** — contract-tested | Claude Code, Codex, Cursor | `default` (`supported-skills.txt`) |
| `imessage-search` | `skills/imessage-search/` | **Yes** — contract-tested | Claude Code, Codex, Cursor | `default` |
| `dev-skill` | `skills/dev-skill/` | No | Native plugins; host-dependent | `all` |
| `learn-from-context` | `skills/learn-from-context/` | No | Native plugins; host-dependent | `all` |
| `new-skill` | `skills/new-skill/` | No | Native plugins; host-dependent | `all` |
| `project-onboard` | `skills/project-onboard/` | No | Native plugins; host-dependent | `all` |
| `organize-screenshots` | `skills/organize-screenshots/` | No | Native plugins; host-dependent | `all` |

**Portable-core** means: listed in `supported-skills.txt`, covered by `tests/test_portable_conformance.py`, and intended for the shared + Claude symlink installer. Live cross-host smokes are still pending; see README support matrix.

### Installer state (authoring machine snapshot)

`just list target=all` on 2026-07-31:

| Skill | Supported | Shared (`~/.agents/skills`) | Claude (`~/.claude/skills`) | Owned by installer |
| --- | --- | --- | --- | --- |
| `git-triage` | yes | not installed | not installed | no |
| `imessage-search` | yes | not installed | installed (manual symlink) | no |
| `dev-skill` | no | not installed | installed (manual symlink) | no |
| `learn-from-context` | no | not installed | installed (manual symlink) | no |
| `new-skill` | no | not installed | installed (manual symlink) | no |
| `project-onboard` | no | not installed | installed (manual symlink) | no |

Five Claude skills symlink directly into this checkout but were **not** installed via `just install` (no provenance file, `owned=no`). `git-triage` is not installed on either route yet.

Recommended cleanup: run `just install target=all` once to replace manual symlinks with installer-owned links for the supported set, then decide whether uncertified skills should stay on the native plugin route instead.

---

## Global skills inventory (authoring machine snapshot)

Counts by discovery root on 2026-07-31:

| Root | Skill count | Role |
| --- | ---: | --- |
| `~/.agents/skills` | 61 | Shared canonical store (`npx skills -g`) |
| `~/.claude/skills` | 81 | Claude Code + symlinks/copies |
| `~/.codex/skills` | 63 | Codex-specific + shared symlinks |
| `~/.hermes/skills` | 53 | Hermes Agent |
| `~/.gemini/skills` | 32 | Gemini CLI (mostly shared symlinks) |
| `~/.config/opencode/skills` | 32 | OpenCode (mostly shared symlinks) |
| `~/.cursor/skills` | 0 | Empty; Cursor reads shared store |

**129** unique skill names appear across all roots (overlap from symlinks and agent-specific copies).

### By bundle

#### Matt Pocock (`mattpocock/skills`) — 22 skills

Installed in `~/.agents/skills`; Claude sees the same 22 via symlinks. Not present in Codex/Hermes/Gemini by default.

`ask-matt`, `code-review`, `codebase-design`, `diagnosing-bugs`, `domain-modeling`, `grill-me`, `grill-with-docs`, `grilling`, `handoff`, `implement`, `improve-codebase-architecture`, `prototype`, `research`, `resolving-merge-conflicts`, `setup-matt-pocock-skills`, `tdd`, `teach`, `to-spec`, `to-tickets`, `triage`, `wayfinder`, `writing-great-skills`

| Agent | Count |
| --- | ---: |
| Shared | 22 |
| Claude | 22 |
| Codex | 0 |
| Hermes | 1 (`research`) |
| Gemini / OpenCode | 0 |

#### Firecrawl — 32 skills

Canonical copy in `~/.agents/skills`; symlinked into Claude, Codex, Hermes, Gemini, and OpenCode.

Sources: `firecrawl/cli`, `firecrawl/skills`, `firecrawl/firecrawl-workflows`.

Core CLI skills: `firecrawl`, `firecrawl-scrape`, `firecrawl-search`, `firecrawl-crawl`, `firecrawl-map`, `firecrawl-agent`, `firecrawl-interact`, `firecrawl-download`, `firecrawl-monitor`, `firecrawl-parse`.

Build/integration: `firecrawl-build`, `firecrawl-build-interact`, `firecrawl-build-onboarding`, `firecrawl-build-scrape`, `firecrawl-build-search`, `firecrawl-research-index`.

Workflows (lead gen, research, QA, SEO, etc.): remaining `firecrawl-*` names.

| Agent | Count |
| --- | ---: |
| Shared, Claude, Codex, Hermes, Gemini, OpenCode | 32 each |

#### Other shared third-party — 7 skills

In `~/.agents/skills` only (plus partial Claude/Hermes overlap for readiness skills):

| Skill | Source |
| --- | --- |
| `agent-readiness-report` | openhands/skills |
| `improve-agent-readiness` | openhands/skills |
| `claude-md-improver` | anthropics/claude-plugins-official |
| `find-skills` | vercel-labs/skills |
| `humanizer` | blader/humanizer |
| `no-ai-slop` | petergyang/no-ai-slop |
| `web-perf` | cloudflare/skills |

#### Claude-only local skills — 16 entries

Real directories under `~/.claude/skills/`, not symlinked from shared:

**Reasoning methodology (14):** `adversarial-reasoning`, `breadth-of-thought`, `codebase-memory`, `confidence-check-skills`, `dialectical-reasoning`, `hypothesis-elimination`, `integrated-reasoning-v2`, `negotiated-decision-framework`, `parallel-execution`, `rapid-triage-reasoning`, `reasoning-handover-protocol`, `security-analysis-skills`, `self-reflecting-chain`, `tree-of-thoughts`

**Other:** `mcpproxy-operations`, `omc-learned` (not a valid skill — no `SKILL.md`)

**Homelab copies (also in Claude):** `dev-skill`, `imessage-search`, `learn-from-context`, `new-skill`, `project-onboard` — symlinked to singleton-skills checkout.

**Cruft:** `INTEGRATION_GUIDE.md` (loose file, not a skill)

#### Codex-only local skills — 29 entries

Under `~/.codex/skills/`, not in shared store. Includes OpenAI-shipped skills (`imagegen`, `playwright`, `pdf`, …), Vercel agent-skills (`vercel-react-best-practices`, …), and homelab ops skills (`brew-sync`, `runtime-status`, `yeet`, …).

#### Hermes-only local skills — 18 entries

Domain bundles under `~/.hermes/skills/` (`computer-use`, `dogfood`, `smart-home`, `yuanbao`, …) plus symlinked shared skills.

---

## Cross-agent availability summary

High-level view of which **bundles** appear in each agent's discovery tree:

| Bundle | Shared | Claude | Codex | Hermes | Gemini | OpenCode |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| Matt Pocock (22) | ● | ● | ○ | ◐ | ○ | ○ |
| Firecrawl (32) | ● | ● | ● | ● | ● | ● |
| Other shared third-party (7) | ● | ◐ | ◐ | ◐ | ○ | ○ |
| singleton-skills repo (7) | ○ | ● | ○ | ○ | ○ | ○ |
| Claude reasoning (14) | ○ | ● | ○ | ○ | ○ | ○ |
| Codex/OpenAI local (29) | ○ | ○ | ● | ○ | ○ | ○ |
| Hermes local (18) | ○ | ○ | ○ | ● | ○ | ○ |

Legend: ● present · ◐ partial overlap · ○ not present

---

## Related configuration elsewhere

| System | Skills management | Notes |
| --- | --- | --- |
| **homelab** | Project-local only | `.claude/skills/`, `skills-lock.json`, policy against global installs (`home/private_dot_claude/rules/third-party-skills.md`) |
| **singleton-skills** | Global personal skills (this repo) | Symlink installer + optional native plugins |
| **`npx skills`** | Global third-party installs | Writes to `~/.agents/skills`; use `skills-lock.json` per project for reproducibility |

---

## Maintenance checklist

1. **Certified portable skills** — keep `supported-skills.txt`, README matrix, and `tests/test_portable_conformance.py` in sync.
2. **Global inventory** — re-run `npx skills list -g` after add/remove; update the snapshot date in this file.
3. **Installer ownership** — prefer `just install` / `just uninstall` over hand-created symlinks so provenance stays accurate.
4. **YAML frontmatter** — quote or block-scalar any `description` containing `:` (see `firecrawl-build` fix); unquoted colons break `npx skills` parsing.
5. **Duplicate discovery** — do not enable the native Claude plugin and Claude symlinks for the same skill name.
6. **Cleanup candidates** — Claude reasoning sprawl (14 skills), `omc-learned/`, `INTEGRATION_GUIDE.md`, unused Firecrawl workflow skills.
