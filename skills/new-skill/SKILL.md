---
name: new-skill
description: >
  Scaffold a new skill in the singleton-skills plugin following all conventions.
  Use when creating a new skill from scratch — generates SKILL.md with correct
  frontmatter (name, description, argument-hint, license), a usage hint block,
  $ARGUMENTS placeholders, scripts/ directory, and evals/evals.json stub.
  Trigger on: "scaffold a skill", "create a new skill", "new skill template",
  "skill boilerplate". Don't use when iterating on an existing skill — use dev-skill instead.
argument-hint: "<skill-name>"
license: MIT
---

# new-skill

> **Quick usage:**
> ```
> /singleton-skills:new-skill <skill-name>
> ```
>
> If invoked with no arguments, ask for the skill name.

## Workflow

### Step 1 — Parse arguments

Parse `$ARGUMENTS` as the skill name. If empty, ask: "What should the new skill be called?"

Validate: kebab-case, no spaces. If the name has spaces, convert to kebab-case and confirm.

### Step 2 — Scaffold

Determine `SINGLETON_SKILLS_PATH`:
1. Check `$SINGLETON_SKILLS_PATH` env var
2. Fall back to known default: `/Volumes/DataDock/Users/tjsingleton/src/github.com/tjsingleton/singleton-skills`

Run:
```bash
cd $SINGLETON_SKILLS_PATH && just new name=$ARGUMENTS
```

### Step 3 — Fill in the SKILL.md

Open `skills/$ARGUMENTS/SKILL.md` and help the user fill in:

1. **`description`** — the most important field. Ask:
   - "When should Claude trigger this skill? What words or phrases would the user say?"
   - "What's a concrete example of a user request that should trigger it?"
   - "When should Claude NOT use it?"
   - Write a description that's trigger-rich and includes an explicit "Don't use when" contrast.

2. **`argument-hint`** — what arguments does the skill accept? Document them.

3. **Usage hint block** — a fenced block at the top of the body showing syntax and 2-3 examples.

4. **Steps** — the actual workflow. Replace the TODO placeholders.

### Step 4 — Offer dev cycle

Ask: "Would you like to enter the skill-creator loop to write evals and iterate?"
- Yes → invoke `/singleton-skills:dev-skill iterate $ARGUMENTS`
- No → remind the user to run `just install` to symlink the new skill

---

## SKILL.md conventions reference

### Frontmatter fields

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | kebab-case, matches directory name |
| `description` | Yes | Trigger-aware; "Use when / Don't use when"; ~150-300 chars |
| `argument-hint` | Yes | Shown in autocomplete; no runtime effect |
| `license` | Yes | MIT |

### Description quality checklist

- [ ] States explicitly WHEN to trigger (not just what it does)
- [ ] Includes at least one concrete example trigger phrase
- [ ] Has a "Don't use when" contrast
- [ ] Avoids vague verbs — prefers "Use when the user says X" over "Use for X"
- [ ] Long enough to be specific; short enough to fit in ~300 chars

### Argument injection

Use `$ARGUMENTS` in the skill body — the runtime substitutes it with the full
string typed after the skill name before Claude reads the prompt.

`$ARGUMENTS[0]` / `$0` — first positional arg (shell quoting applies).

If the skill body contains no `$ARGUMENTS`, the runtime appends
`ARGUMENTS: <input>` to the end automatically.

### Body structure

1. Quick usage hint (fenced block — shows syntax + examples)
2. If invoked with no args / `--help`: show hint and stop
3. Workflow steps
4. Output format (if structured)
5. Notes / edge cases
