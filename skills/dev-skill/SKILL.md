---
name: dev-skill
description: >
  Manage the full development lifecycle for skills in the singleton-skills plugin.
  Use whenever creating a new skill, iterating on an existing skill with evals,
  running skill-creator workflows, or installing/publishing skills.
  Uses a capable subagent when available, with a direct execution fallback.
  Trigger on: "create a skill", "new skill", "iterate skill", "run skill evals",
  "improve skill", "dev skill", "scaffold skill", "skill development".
  Don't use for non-skill tasks or when working in a different skills repo.
argument-hint: "[new|eval|iterate|install|list] <skill-name>"
license: MIT
---

# dev-skill

> **Quick usage:**
> ```
> dev-skill new <name>        # scaffold a new skill
> dev-skill iterate <name>    # full skill-creator loop
> dev-skill eval <name>       # run evals only
> dev-skill install           # symlink supported skills
> dev-skill list              # show install status
> ```
>
> If invoked with no arguments, show this hint and wait for input.

## Setup

Use the host's normal skill invocation syntax. `SINGLETON_SKILLS_PATH` is only
required when the editable checkout cannot be identified from the current
workspace:

```bash
just register   # print shell-neutral setup and marketplace commands
```

## Workflow

### Step 1 — Parse arguments

Parse the arguments supplied with the skill invocation:
- If empty or `--help`: show usage hint above and stop
- First word = command: `new`, `eval`, `iterate`, `install`, `list`
- Remaining = skill name (required for `new`, `eval`, `iterate`)

### Step 2 — Resolve singleton-skills path

1. Resolve and run the bundled `scripts/resolve_repo.py` adjacent to this skill.
2. The resolver checks explicit `SINGLETON_SKILLS_PATH`, the current Git
   checkout, and then the active skill's source checkout.
3. A valid result must be an editable Git checkout containing `justfile` and
   `skills/dev-skill/SKILL.md`; installed plugin caches are not editable sources.
4. If resolution fails or finds conflicting checkouts, stop and ask the user to
   set `SINGLETON_SKILLS_PATH` explicitly.

### Step 3 — Execute with the available host capability

When the host supports subagents, delegate the bounded implementation or eval
step to a capable coding agent scoped to the resolved checkout. Do not require a
provider-specific role name. If delegation is unavailable, execute the same
commands directly and preserve the same verification requirements.

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
Invoke an installed `skill-creator` capability from the active host's skill
catalog with `skills/<name>/` as the target. If none is available, stop with a
clear dependency message rather than searching a host's plugin cache.

Context:
- SKILL.md is at: $SS/skills/<name>/SKILL.md
- Evals: $SS/skills/<name>/evals/evals.json
- Eval workspace (gitignored): $SS/skills/<name>/evals-workspace/

Use the existing SKILL.md as the starting point. Run the scaffold → eval → improve loop.

Step 3 — Reflect (after skill-creator loop completes):
Append a changelog entry to $SS/skills/<name>/CHANGELOG.md under the [Unreleased] section.
Format: Keep a Changelog (https://keepachangelog.com). Use subsections: Added, Changed, Fixed, Removed.
Include: what changed in the skill, why (user feedback, eval results, design rationale).
Sanitize before writing: do not include personal absolute paths or email addresses.
If the file doesn't exist, create it with standard Keep a Changelog header and [Unreleased] section.
```

---

#### `eval <name>`

```
Run evals for: skills/<name>/

  SS="<resolved-singleton-skills-path>"
  cd "$SS"

Use the active host's installed `skill-creator` eval runner on
skills/<name>/evals/evals.json.
Outputs go to skills/<name>/evals-workspace/iteration-N/.
Report pass rates and open the viewer.
```

---

#### `install`

```
  SS="<resolved-singleton-skills-path>"
  cd "$SS" && just install

Report which skills were linked and print the host marketplace registration commands.
```

---

#### `list`

```
  SS="<resolved-singleton-skills-path>"
  cd "$SS" && just list

Report the output.
```
