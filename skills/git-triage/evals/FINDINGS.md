# git-triage evaluation findings

## Scope boundary

The trigger evaluation established a useful boundary that remains part of the
skill's design:

| Query type | Expected behavior |
|---|---|
| Comprehensive whole-picture triage, pre-machine-switch checks, or session wrap-up | Trigger `git-triage` |
| A single fact such as status, one diff, one stash list, or one worktree list | Answer with the direct Git command; do not trigger the skill |
| A requested Git mutation such as push, commit, rebase, or branch creation | Use the host's normal Git workflow and approval rules; do not trigger triage solely for the mutation |

The skill should trigger when its cross-cutting classification adds value: local
changes, branch synchronization, stashes, worktrees, cached remote-only work, and
optional PR attention in one report.

## Historical trigger evidence

Manual CLI checks with three distinct comprehensive prompts triggered the skill
in all three cases. Single-domain prompts were handled directly, which is the
desired behavior. The queries in `trigger-eval.json` preserve this boundary.

An earlier automated description loop was not treated as reliable evidence in
this checkout because its evaluation runs timed out and returned uniformly null
trigger results. That limitation applies to the old measurement, not to the
current skill behavior. Re-run trigger evaluation with the active host's normal
skill-evaluation tooling and a timeout appropriate to that environment before
making quantitative cross-host claims.

## Accepted portable design

The portable implementation is a self-contained observer:

- The parent agent runs deterministic Git commands directly.
- The default local snapshot performs no network access and changes no refs.
- Remote refresh is separate, labeled, and gated by explicit request or
  approval; its target comes from the branch's tracking configuration or an
  explicit user choice.
- GitHub CLI enrichment is optional and failure-tolerant.
- Mutations remain recommendations until explicitly approved, followed by a
  narrow state read-back.
- Missing remotes, upstreams, authentication, branches, and comparison objects
  produce unavailable or blocked states rather than false clean results.

This design preserves the classification value measured by the trigger eval
without requiring a provider-specific agent, plugin, installation directory, or
machine-specific checkout path.

## Re-evaluation checklist

1. Run the trigger cases in `trigger-eval.json` on each claimed host.
2. Confirm all comprehensive prompts trigger and all single-fact/mutation prompts
   remain outside the skill.
3. Exercise clean, ahead, behind, diverged, no-upstream, dirty, stash, additional
   worktree, detached, no-remote, multiple-remote, remote-only, and unavailable
   GitHub cases in disposable repositories.
4. Confirm local mode runs no network-capable command and refreshed mode announces
   fetch side effects before execution.
5. Confirm every report includes all six categories, including explicit empty or
   unavailable states.
