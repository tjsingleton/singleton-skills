---
name: dev-skill
description: >
  Manage the full development lifecycle for skills in the singleton-skills plugin.
  Use whenever creating a new skill, iterating on an existing skill with evals,
  running skill-creator workflows, or installing/publishing skills.
  Spawns a subagent scoped to the singleton-skills repo — invoke from any project.
  Trigger on: "create a skill", "new skill", "iterate skill", "run skill evals",
  "improve skill", "dev skill", "scaffold skill", "skill development".
  Don't use for non-skill tasks or when working in a different skills repo.
argument-hint: "[new|eval|iterate|install|list] <skill-name>"
license: MIT
---

# dev-skill

> **Quick usage:**
> ```
> /singleton-skills:dev-skill new <name>        # scaffold a new skill
> /singleton-skills:dev-skill iterate <name>    # full skill-creator loop
> /singleton-skills:dev-skill eval <name>       # run evals only
> /singleton-skills:dev-skill install           # symlink all skills
> /singleton-skills:dev-skill list              # show install status
> ```
>
> If invoked with no arguments, show this hint and wait for input.

## Setup

This skill requires `SINGLETON_SKILLS_PATH` to be set:

```bash
just register   # run once in singleton-skills to write to ~/.zprofile
```

## Workflow

### Step 1 — Parse arguments

Parse `$ARGUMENTS`:
- If empty or `--help`: show usage hint above and stop
- First word = command: `new`, `eval`, `iterate`, `install`, `list`
- Remaining = skill name (required for `new`, `eval`, `iterate`)

### Step 2 — Resolve singleton-skills path

1. Check `$SINGLETON_SKILLS_PATH` env var
2. Fall back to: `/Volumes/DataDock/Users/tjsingleton/src/github.com/tjsingleton/singleton-skills`
3. If path doesn't exist: tell the user to run `just register` and stop

### Step 3 — Execute in subagent

Spawn a `general-purpose` subagent scoped to the singleton-skills path.
Always include the resolved path in the subagent prompt.

---

#### `new <name>`

```
Scaffold a new skill in the singleton-skills repo at: <SINGLETON_SKILLS_PATH>

Run:
  cd <SINGLETON_SKILLS_PATH> && just new name=<name>

Then open skills/<name>/SKILL.md and help fill in the description, argument-hint,
usage hint block, and workflow steps following the conventions in skills/new-skill/SKILL.md.
```

---

#### `iterate <name>`

```
Run the full skill-creator development loop for: skills/<name>/
Working directory: <SINGLETON_SKILLS_PATH>

Invoke the skill-creator:skill-creator skill with skills/<name>/ as the target.

Context:
- SKILL.md is at: <SINGLETON_SKILLS_PATH>/skills/<name>/SKILL.md
- Evals: <SINGLETON_SKILLS_PATH>/skills/<name>/evals/evals.json
- Eval workspace (gitignored): <SINGLETON_SKILLS_PATH>/skills/<name>/evals-workspace/
- skill-creator base: ~/.claude/plugins/cache/claude-plugins-official/skill-creator/unknown/

Use the existing SKILL.md as the starting point. Run the scaffold → eval → improve loop.
```

---

#### `eval <name>`

```
Run evals for: skills/<name>/
Working directory: <SINGLETON_SKILLS_PATH>

Use the skill-creator:skill-creator eval runner on skills/<name>/evals/evals.json.
Outputs go to skills/<name>/evals-workspace/iteration-N/.
Report pass rates and open the viewer.
```

---

#### `install`

```
Run in <SINGLETON_SKILLS_PATH>:
  just install

Report which skills were linked and print the /plugin registration commands.
```

---

#### `list`

```
Run in <SINGLETON_SKILLS_PATH>:
  just list

Report the output.
```
