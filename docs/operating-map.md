# Operating map

Read this map before starting or joining work in this repository. It is the
coordination source for concurrent sessions: lanes, ownership, material state,
blockers, and decisions. It is not a work journal.

**Last materially updated:** 2026-09-15

## Active lanes

| Lane | Objective | Owning session | Current state | Blockers |
| --- | --- | --- | --- | --- |
| `agentic-harness-designer` | Define the `agentic-harness-designer` skill for designing and reviewing agent systems. | Unknown — pre-existing working-tree change | In progress: a substantive untracked skill draft exists. | Owning session is not identified in the shared worktree. |
| `goal-prompt-generator` | Define and complete the `goal-prompt-generator` skill. | Unknown — pre-existing working-tree change | In progress: a substantive untracked skill draft exists. | Owning session is not identified in the shared worktree. |
| `image-gateway` | Define the shared OpenRouter bitmap-generation gateway skill. | Unknown — pre-existing working-tree change | In progress: a substantive untracked skill draft exists. | Owning session is not identified in the shared worktree. |
| `visible-delegation` | Define and complete the `visible-delegation` skill. | Unknown — pre-existing working-tree change | Blocked: the scaffold is incomplete and currently has an incorrect `name=visible-delegation` frontmatter value. | Needs its owning session or the user to define the skill's purpose and correct the scaffold. |

## Current decisions

| Decision | Rationale | Affects |
| --- | --- | --- |
| Use this file as the single repo-local coordination map. | The requested coordination convention needs one durable, read-first source rather than per-session notes. | All concurrent lanes |

## Lane discipline

- Keep one lane per independently owned concern; split work that has separate
  objectives, owners, or blockers.
- Give lanes short, obvious names (usually the feature, module, or decision
  they own). Do not use vague names such as `misc` or `updates`.
- Update an entry only when its state materially changes: started, blocked,
  handed off, or done. Do not append progress notes or a play-by-play.
- Record decisions here only while they affect an active lane. Promote durable
  project knowledge to the appropriate documentation or skill.

## Done lanes

Move a finished lane here with a one-line outcome. Then promote any reusable
lesson to project documentation or the relevant skill rather than leaving it
only in this map.

| Lane | Outcome |
| --- | --- |
| `session-operating-map` | Added the reusable skill and initialized this repository's operating map. |
| `plain-english-docs` | Added the plain-language documentation skill, portable contract coverage, and a verified shared-skill link. |
| `self-pr-merge` | Added a fresh-review-first self-PR merge skill with squash/delete defaults, clean-check gates, and worktree-safe cleanup. |
