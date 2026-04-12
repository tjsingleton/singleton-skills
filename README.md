# singleton-skills

TJ Singleton's personal Claude Code skill library, structured as a Claude Code plugin.

## Structure

```
singleton-skills/
├── .claude-plugin/
│   ├── plugin.json       # Plugin manifest
│   └── marketplace.json  # Self-describing marketplace for local install
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md      # Skill definition + frontmatter
│       ├── scripts/      # Reusable helper scripts
│       └── evals/
│           └── evals.json
├── scripts/
│   └── new_skill.py      # Scaffold generator
├── AGENTS.md
├── justfile
└── README.md
```

## Installation

### Option A — Claude Code plugin (recommended)

Run once inside a Claude Code session:

```
/plugin marketplace add /path/to/singleton-skills
/plugin install singleton-skills@singleton-skills-dev
```

Skills are then available as `/singleton-skills:<skill-name>`.

### Option B — Symlinks (fallback)

```bash
just install
```

Symlinks each skill directory to `~/.claude/skills/<name>`, making skills available
as `/<skill-name>` in any Claude Code session.

### Register workspace env var

```bash
just register
```

Writes `SINGLETON_SKILLS_PATH` to `~/.zprofile`. Required for `/dev-skill` to locate
this repo when invoked from other projects.

## Skills

| Skill | Description |
|-------|-------------|
| `imessage-search` | Search and extract structured information from iMessages |
| `new-skill` | Scaffold a new skill following repo conventions |
| `dev-skill` | Full dev lifecycle: scaffold → iterate with evals → install |

## Creating a new skill

```bash
just new name=my-skill
```

Then edit `skills/my-skill/SKILL.md`. Run `/dev-skill iterate my-skill` inside Claude
to enter the skill-creator loop (write → eval → improve).

Install after editing:

```bash
just install
```

## Dev cycle

```
/dev-skill new <name>       # scaffold
/dev-skill iterate <name>   # skill-creator loop with evals
/dev-skill eval <name>      # run evals only
/dev-skill install          # symlink all skills
/dev-skill list             # show install status
```

`/dev-skill` is a global skill (symlinked during `just install`) — invoke it from any
Claude Code session, and it will scope its work to this repo.

## SKILL.md conventions

Every skill must have YAML frontmatter with at minimum:

```yaml
---
name: skill-name
description: >
  Use this skill whenever [trigger condition].
  Trigger on: [keyword list].
  Don't use when [anti-pattern].
argument-hint: "[options] <argument>"
license: MIT
---
```

The `description` field is what Claude uses to decide when to trigger the skill.
Make it specific, trigger-rich, and include "Don't use when" to prevent misuse.

Use `$ARGUMENTS` (not `{{ARGUMENTS}}`) for runtime argument injection.

## Public repo notice

This repository is public. Never commit secrets, credentials, API keys, or personal data.
Review all files before committing.
