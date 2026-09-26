---
name: session-to-skill-extractor
description: >
  Turn a substantial agent session into an evidence-backed skill draft for user review.
  Use when the user says "extract a skill from this session" or "turn this workflow into a skill".
  Don't use for general session notes or knowledge-base capture.
argument-hint: "[session transcript] [candidate skill name]"
license: MIT
---

# Session-to-skill extractor

> **Quick usage:**
> ```
> session-to-skill-extractor [session transcript] [candidate skill name]
> ```
>
> Examples:
> - `session-to-skill-extractor` reviews the current session.
> - `session-to-skill-extractor path/to/session.md database-migration-review` reviews a supplied transcript.

## Overview

Find a repeatable, agent-useful workflow in a substantial session and prepare a
skill draft the user can inspect and approve. The result should encode decisions
and checks that materially improved the work, not retell the session.

This skill creates skill candidates. It does not capture general learnings in a
PKB or OpenBrain. Keep it distinct from `learn-from-context`, whose purpose is
to store session insights for later retrieval.

## Workflow

### Step 1 — Identify the session source

Use the current conversation when no source is named. For another session, use
only a transcript or session artifact the user identifies or provides. If that
source is unavailable, ask for it. Do not search private session archives,
computer history, or unrelated projects on your own.

### Step 2 — Find a reusable workflow

Read enough of the session to establish what the user wanted, what the agent
did, which decisions mattered, and how the result was checked. Look for a
repeatable sequence with recognizable inputs, actions, and completion evidence.

Propose a skill only when the session demonstrates a workflow another agent
could reuse. Strong evidence includes a repeated process, explicit user
correction, or a consequential sequence with verified results. Do not turn a
one-off fact, preference, command, project detail, or generic good practice into
a skill. If the session does not support a useful candidate, explain why and
stop without inventing steps.

### Step 3 — Screen the candidate

Before drafting, check that the proposed skill:

- Has a distinct job and a clear trigger, with an explicit skip boundary.
- Carries forward observed decisions and verification criteria, not merely the
  session's final answer.
- Can work outside the original project after removing project-specific facts.
- Contains no credentials, personal details, private paths, confidential data,
  or copied session text that does not belong in a reusable skill.

If a reusable version cannot pass these checks, describe the gap and ask for
direction instead of silently generalizing or publishing sensitive material.

### Step 4 — Present the review draft

Return a short evidence summary and a complete proposed `SKILL.md` in the
conversation. Cite evidence by session section, step, or concise paraphrase. Do
not quote sensitive material. Separate observed behavior from any proposed
generalization, and mark unsupported details as open questions.

Include the candidate name, trigger and skip cases, workflow, decision rules,
completion checks, privacy considerations, and the reason it merits its own
skill. Ask the user to approve or revise the draft before creating files in a
repository. Do not install, commit, push, publish, or register it with a host.

### Step 5 — Create files after approval

After explicit approval, use the target repository's skill scaffold and
conventions. Create the approved `SKILL.md` and focused `evals/evals.json`.
Update only the repository's required skill inventory or manifest registration.
Keep existing files intact, then validate the frontmatter, directory name,
manifest registration, and eval JSON. Report the exact files changed and any
checks that remain unrun.

## Output

Before approval, provide:

1. **Evidence:** the session behaviors that support the candidate, with concise
   source locations or paraphrases.
2. **Candidate:** name, purpose, trigger, and skip boundary.
3. **Draft:** complete skill instructions, ready for review.
4. **Open questions:** only details that the source cannot establish and that
   would change the skill's behavior.

After approval and file creation, provide the changed paths and validation
results. If no candidate qualifies, state that plainly and do not create files.

## Notes

- Treat session content as evidence, not permission to copy it into a public
  repository. Keep the resulting skill generic and remove identifying details.
- Approval to draft is not approval to install, commit, push, publish, or alter
  another skill.
- Prefer a small skill with one clear job. Do not duplicate a capability that
  an existing skill already covers; explain the overlap when it matters.
