---
name: goal-prompt-generator
description: >
  Package an implementation plan or task into a bounded, self-contained goal prompt
  for another autonomous agent session. Use when the user says "package this for another
  session," "write a goal prompt," "prepare a task for autonomous execution," or asks
  to hand work to a fresh agent. Don't use when the user wants the current session to
  implement, review, or merely summarize the work.
argument-hint: "<implementation plan or task description>"
license: MIT
---

# goal-prompt-generator

> **Quick usage:**
> ```
> goal-prompt-generator <implementation plan or task description>
> goal-prompt-generator package the approved plan from this conversation for a fresh agent
> goal-prompt-generator prepare this task for autonomous execution: <task>
> ```
>
> If invoked with no task, no referenced plan, and no usable conversation context, ask for
> the task or plan to package and stop.

## Purpose

Turn a plan into an executable contract for a receiving agent session that has no access to
the current conversation. The output is a **goal prompt**, not an implementation, a vague
handoff, or a restatement of a ticket. It must set a bounded scope, provide observable
completion criteria, and make the result independently checkable.

## Workflow

### 1. Collect only established facts

Read the task or approved plan and extract:

- the requested outcome and relevant background;
- repository root, exact paths, relevant existing behavior, and decisions already made;
- files or areas that are allowed to change and those that are protected;
- the acceptance criteria and exact available verification commands;
- external systems, credentials, approvals, migrations, deployments, or destructive actions
  that the receiving agent is not authorized to assume.

Inspect the repository when needed to replace a guessed path or command with a real one. Do
not invent product requirements, success criteria, repository paths, test commands, or an
authorization boundary. If a material detail cannot be established, use the stop conditions
below instead of filling the gap with a plausible assumption.

### 2. Bound the work

Convert the plan into small, outcome-oriented, verifiable statements. Scope is bounded only
when the prompt explicitly says both what may change and what must not change. Name exact
paths whenever known; do not use phrases such as "make any necessary changes" or "avoid
unrelated files."

If the work needs a choice that would materially alter behavior, architecture, data, or
authority, do not select one for the receiving agent. State it as a stop condition and ask
the current user for the choice before producing a supposedly executable prompt.

### 3. Write the goal prompt using the required structure

Every goal prompt must contain every section in the template below, in this order. Replace
all bracketed text with concrete information. Do not leave `TBD`, "as appropriate," or
unstated assumptions in a final prompt.

````markdown
# Goal: [short outcome]

## Objective

[One paragraph. State the desired end state, why it matters, the exact repository root, and
the essential background or prior decisions a fresh session needs. Include exact paths,
interfaces, data assumptions, and any in-progress-work context that affects this task.]

## Definition of Done

- [ ] [A verifiable statement describing the required delivered behavior or artifact.]
- [ ] [A verifiable statement covering each required edge case, compatibility constraint, or
      user-visible outcome.]
- [ ] [Only the allowed files/areas changed, unless the user explicitly approved an exception.]
- [ ] [Every verification gate below has passed with the stated result.]

## Repository Constraints

**Repository root:** `[absolute repository path]`

**May modify:**
- `[exact file or directory path]` — [reason or responsibility]

**Must NOT modify:**
- `[exact file, directory, generated artifact, configuration, or external system]` — [reason]

**Existing-work constraints:**
- [Relevant current branch/worktree facts, compatibility requirements, conventions, or
  instruction files. State "None established" only when that was actually checked.]

## Verification Gates

Run every command from `[working directory]` after implementing the change. Do not claim
completion until each gate has its expected result.

| Gate | Exact command | Expected result |
| --- | --- | --- |
| [focused behavior/test] | `[exact command]` | [exit status and observable passing result] |
| [lint/type/build/format check] | `[exact command]` | [exit status and observable passing result] |
| [scope review] | `[exact read-only command]` | [only the allowed paths appear in the diff/status] |

## Stop Conditions — halt and ask; do not improvise

- A required decision, expected behavior, acceptance criterion, path, or verification command
  is missing, ambiguous, or conflicts with the evidence in the repository.
- Completing the work requires modifying an area outside **May modify** or touching anything in
  **Must NOT modify**.
- The work requires secrets, credentials, external access, a deployment, data migration,
  purchase, user communication, or another approval not explicitly granted here.
- Existing changes, instructions, or tests conflict with this goal in a way that cannot be
  resolved entirely within the stated constraints.
- A verification gate fails and fixing its cause would require an unapproved scope change or
  an unverified behavioral decision. (A failure is never evidence of completion.)
- The action would be destructive, irreversible, or affect production data without explicit
  authorization in this prompt.

## Completion Report

Report: (1) the files changed, (2) how each Definition of Done item was satisfied, (3) each
verification command and its observed result, and (4) any remaining limitation or stop
condition. Do not report success if any checkbox or gate is unmet.
````

The **Objective** is exactly one paragraph. The **Definition of Done** is a checklist of
statements another person can verify, not a list of implementation activities. Verification
gates must give commands that can actually be run in the named repository and an expected,
observable result; include no placeholder commands.

### 4. Apply the self-containment rule

Assume the receiving session has **none** of this conversation's context. Put all information
it needs into the prompt itself: the absolute repository root, exact relevant paths, current
state that matters, expected behavior, prior decisions, constraints, and precise commands.
Do not refer to "the plan above," "our earlier discussion," a ticket without its contents, or
an inaccessible chat, screenshot, URL, branch, or external system. If a referenced source is
necessary, include its exact accessible path and the relevant facts from it.

### 5. Run the delivery quality check

Before delivering, ask exactly:

> "Could a competent agent with zero context execute this and could I verify the result without re-deriving the plan?"

The answer must be yes. Confirm that:

- the one-paragraph objective supplies enough background and exact paths;
- every Definition of Done item is observable and every required outcome is represented;
- allowed and protected areas are both explicit;
- every verification command is exact, runnable, and paired with an expected result; and
- every unknown, missing authority, or scope-expanding choice is a stop condition rather than
  a hidden assumption.

If the answer is no, repair the prompt from established evidence. If it cannot be repaired
without a material user decision, ask that one question and do not present the draft as ready
for autonomous execution.

## Output

Deliver the completed goal prompt in a single Markdown code block, ready to paste into a new
agent session. Precede it only with a concise note if the user needs to answer a stop-condition
question before the prompt can be final. Do not carry out the packaged task in this skill.

## Notes

- A plan can be detailed yet still fail this skill if it lacks a testable Definition of Done,
  safe repository boundaries, or real verification gates.
- A generic command such as `run tests` is not a verification gate. Discover and name the
  actual command and its expected result.
- If no real task follows the request to create this skill, acknowledge that the packaging test
  is pending the user's next task; do not manufacture a task merely to demonstrate the format.
