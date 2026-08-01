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
2. Otherwise, resolve the active `dev-skill` directory and use its repository
   root (two directories above this `SKILL.md`), following symlinks first
3. Verify the resolved root contains both `justfile` and `skills/dev-skill/SKILL.md`
4. If resolution fails: tell the user to set `SINGLETON_SKILLS_PATH` or run
   `just register`, then stop

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

Step 1 — Set working directory:
  SS="<resolved-singleton-skills-path>"
  cd "$SS"

Step 2 — Invoke skill-creator:
Invoke the skill-creator:skill-creator skill with skills/<name>/ as the target.

Context:
- SKILL.md is at: $SS/skills/<name>/SKILL.md
- Evals: $SS/skills/<name>/evals/evals.json
- Eval workspace (gitignored): $SS/skills/<name>/evals-workspace/
- skill-creator base: ~/.claude/plugins/cache/claude-plugins-official/skill-creator/unknown/

Use the existing SKILL.md as the starting point. Run the scaffold → eval → improve loop.

Step 3 — Reflect (after skill-creator loop completes):
Append a changelog entry to $SS/skills/<name>/CHANGELOG.md under the [Unreleased] section.
Format: Keep a Changelog (https://keepachangelog.com). Use subsections: Added, Changed, Fixed, Removed.
Include: what changed in the skill, why (user feedback, eval results, design rationale).
Sanitize before writing: do not include paths like /Users/<name>/ or email addresses.
If the file doesn't exist, create it with standard Keep a Changelog header and [Unreleased] section.
```

---

#### `eval <name>`

```
Run evals for: skills/<name>/

  SS="<resolved-singleton-skills-path>"
  cd "$SS"

Use the skill-creator:skill-creator eval runner on skills/<name>/evals/evals.json.
Outputs go to skills/<name>/evals-workspace/iteration-N/.
Report pass rates and open the viewer.
```

---

#### `install`

```
  SS="<resolved-singleton-skills-path>"
  cd "$SS" && just install

Report which skills were linked and print the /plugin registration commands.
```

---

#### `list`

```
  SS="<resolved-singleton-skills-path>"
  cd "$SS" && just list

Report the output.
```
