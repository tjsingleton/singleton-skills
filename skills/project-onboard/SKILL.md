---
name: project-onboard
description: >
  Onboards a project for use with Claude + OMC by producing a comprehensive
  CLAUDE.md through codebase exploration, Socratic requirement gathering, and
  autonomous execution.
  Trigger on: "onboard this project", "set up Claude for this repo",
  "create a CLAUDE.md", "help Claude understand this codebase",
  "onboard for claude", "onboard for oh-my-claudecode".
  Don't use when a CLAUDE.md already exists and the user wants to update it —
  use direct editing instead.
argument-hint: "[--quick] [focus area]"
license: MIT
---

# project-onboard

> **Quick usage:**
> ```
> /singleton-skills:project-onboard
> ```
>
> If invoked with no arguments, run the full pipeline (explore → clarify → execute).
> Pass `--quick` to skip deep-interview and write a best-effort CLAUDE.md from exploration alone.

## Overview

Turns a vague "onboard this project" request into a validated `CLAUDE.md` via a
three-stage pipeline: codebase exploration → Socratic clarification → autonomous execution.

**Why it exists:** Starting Claude on an unfamiliar project without a `CLAUDE.md` produces
shallow, generic responses. Writing one manually is tedious and easy to get wrong. This skill
automates the full process — from understanding what the user actually wants to writing and
verifying the final file.

## Workflow

### Step 1 — Explore (always first, before asking the user anything)

Spawn an `explore` agent (haiku) to map the codebase:
- Language, framework, and tech stack
- Directory structure and entry points
- Existing AI config files (`.claude/`, `.omc/`, `AGENTS.md`, existing `CLAUDE.md`)
- Build system and task runner (Makefile, justfile, package.json scripts, etc.)
- Test setup and coverage configuration
- Key config or domain-specific files

Store findings as `codebase_context`. Never ask the user about facts the codebase already reveals.

### Step 2 — Clarify (skip if `--quick`)

Run `/deep-interview` to resolve ambiguity before writing anything. Target four dimensions:

1. **Artifact** — What should exist when onboarding is done?
   (CLAUDE.md only / CLAUDE.md + AGENTS.md / full OMC config)

2. **Primary use case** — What will Claude mainly help with?
   (general dev / debugging / adding data sources / extending the model / etc.)

3. **Workflow guardrails** — What rules must Claude always follow?
   (lint gates, protected files, mandatory test runs, off-limits commands, etc.)

4. **Depth** — How detailed should the output be?
   (minimal orientation / comprehensive reference / task-focused recipes / hybrid)

Continue until ambiguity ≤ 20% before proceeding. If the user says "just do it" or
"skip the questions", jump to Step 3 with a best-effort spec derived from exploration.

### Step 3 — Execute

Run `/autopilot` with the deep-interview spec (or exploration context if `--quick`) as
Phase 0 output. Autopilot reads the codebase, writes the `CLAUDE.md`, and verifies all
acceptance criteria before reporting completion.

**Minimum acceptance criteria for the output `CLAUDE.md`:**
- [ ] Project overview (what it does, tech stack) in 2–3 sentences
- [ ] Architecture / directory map with purpose of each top-level dir
- [ ] Build/task runner targets documented (all significant commands)
- [ ] Configuration schema if the project has domain-specific config files
- [ ] Test structure: how to run tests, any special markers or flags
- [ ] Workflow guardrails section (project-specific rules Claude must follow)
- [ ] Common task recipes (at least: run the project, run tests, lint/format)
- [ ] References to existing docs — no duplication of content already in `/docs/`

## Output

A `CLAUDE.md` at the project root that gives Claude full orientation for the
primary use case, verified against the acceptance criteria from the clarification step.

```
✓ CLAUDE.md created: <path>
  Sections: <list>
  Guardrails: <count> captured
  Ambiguity at execution: <score>%
  Acceptance criteria: all passed
```

## Notes

- Brownfield projects (existing source code) get an extra "Context Clarity" dimension
  in the deep-interview scoring (weight 0.15) to ensure the existing system is well understood.
- Does not create `AGENTS.md` or hooks unless explicitly requested during clarification.
- The explore step uses haiku for speed; the deep-interview scoring uses opus for consistency.
- If the project already has a `.omc/specs/` directory, check for an existing deep-interview
  spec before starting a new interview — it may be resumable.
- `--quick` mode skips clarification entirely and produces a best-effort file; useful when
  the project is small or the user is in a hurry. Quality will be lower.
