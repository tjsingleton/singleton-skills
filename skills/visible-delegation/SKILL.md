---
name: visible-delegation
description: Delegate bounded work to a separate agent session when the user asks to delegate or run work in parallel and wants the work to remain visible and supervisable. Use a named tmux session, then verify and close it; use direct execution for a simple local task.
license: MIT
---

# Visible Delegation

Run a **watchable handoff**: another agent works in a named tmux session, while
the supervising agent keeps the session observable, verifies its result, and
closes it. A detached tmux session is watchable only when its name and attach
command are immediately given to the user.

## 1. Establish the control plane

1. Check that `tmux` is available. If it is missing, ask for authorization to
   install it with the platform package manager, then confirm `tmux -V`.
2. Discover the available delegate CLIs and tell the user which were found:

   ```bash
   for cli in claude codex cursor-agent gemini; do
     command -v "$cli" || true
   done
   ```

   Honor a named CLI; otherwise use the first available CLI in that order and
   state the choice. If none is available, stop with that blocker.
3. Confirm the workspace boundary. In a shared checkout, the delegate preserves
   existing work and changes only paths the goal explicitly permits.

**Complete when:** tmux works, the selected CLI is known, and the user has the
chosen CLI and workspace boundary.

## 2. Package the handoff

Use `goal-prompt-generator` to make a self-contained goal prompt. If it is not
available, produce its equivalent: an objective with the absolute repository
root, Definition of Done, exact allowed and protected paths, runnable
verification gates with expected results, stop conditions, and a completion
report.

The prompt must give a fresh agent all material context and state whether commits,
pushes, destructive commands, credential changes, or external actions are
authorized. Unknown authority or a required choice is a stop condition, not an
assumption.

**Complete when:** the goal is bounded and every acceptance item has a
supervisor-runnable verification gate.

## 3. Start the watchable handoff

Create a unique, descriptive name such as `delegate-parser-20260915-1430`; make
sure it is unused. Launch the selected agent interactively in the task directory
with the goal prompt as its initial prompt:

```bash
tmux new-session -d -s "$session" -c "$workspace" "$agent_cli" "$goal_prompt"
tmux has-session -t "$session"
```

Immediately give the user both the name and observation commands:

```bash
tmux attach -t "$session"
tmux capture-pane -p -t "$session" -S -200
```

Use tmux only as the visible control plane; launch the delegate CLI in its normal
interactive mode, not its own background, daemon, or cloud mode. If startup
fails, capture the pane and close that session.

**Complete when:** the pane is live and the user can attach by the supplied
command.

## 4. Supervise the handoff

Inspect the pane shortly after launch, then every 2–5 minutes while active, and
when the delegate plans, asks for approval, starts a mutation, or claims
completion. Let it continue while it shows relevant progress, including a known
slow test or build.

Redirect through `tmux send-keys` when it repeats the same failure three times,
needs an answer it has not surfaced, expands beyond the goal, or approaches an
unapproved destructive, credential, commit/push, or external action. Preserve
the relevant pane output before interrupting. Escalate a new authority or product
decision to the user.

**Complete when:** the delegate is progressing within the goal, or a concrete
blocker has been surfaced and handled.

## 5. Verify, then close

Treat the delegate's completion report as a claim. In the shared workspace, run
every verification gate from the goal prompt yourself. When files could have
changed, also inspect the relevant diff and working-tree status. Compare the
observed results with every Definition of Done item and the workspace boundary.

Send a failed or incomplete gate back to the same tmux session with the observed
evidence. Report success only after every gate passes; otherwise report the
blocked or partial state precisely.

After the verified report—or after a blocked handoff has been given to the
user—close exactly the created session and confirm it is gone:

```bash
tmux kill-session -t "$session"
tmux has-session -t "$session"  # expected to fail
```

**Complete when:** the user receives the delegate result, independent gate
results, remaining risk or decision, and the session's closed status.
