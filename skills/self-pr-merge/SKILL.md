---
name: self-pr-merge
description: >
  Review and merge a pull request authored by the current GitHub user when asked to
  merge their own PR or review-and-merge work they wrote. Do not use for someone
  else's PR, ordinary code review, or PR creation.
argument-hint: "[PR number or URL]"
license: MIT
---

# self-pr-merge

> **Quick usage:**
> ```
> self-pr-merge 123
> self-pr-merge https://github.com/OWNER/REPO/pull/123
> self-pr-merge                 # use the PR for the current branch
> ```

> **Defaults captured for this user:** squash merge; delete the remote head branch.

## Resolve the target

Use the supplied PR number or URL. With no argument, resolve the pull request for
the current branch. Confirm `gh auth status` succeeds before querying or changing
GitHub. Obtain the authenticated login and PR metadata, including author, draft
state, head branch, mergeability, conflict state, and checks.

Proceed only when the PR author is the authenticated user. If it is not, say that
this skill is restricted to the user's own PR and hand the request back for a normal
review/merge path. Stop for a draft, a missing PR, unavailable metadata, or failed
authentication.

## Fresh review gate

Review before considering a merge. Read the complete PR diff with fresh eyes using
`gh pr diff <PR> --patch`; also read the PR description and changed-file list when
available. Assess every changed area for:

- behavior defects, regressions, and unsafe error handling;
- debug artifacts, credentials, generated noise, and accidental files;
- missing or inadequate tests for changed behavior;
- scope creep or a mismatch with the PR's stated purpose.

Report a concise review record to the user before any merge attempt:

```text
Self-review — PR #<number>: <title>
Reviewed: full diff (<n> files), description, and checks
Findings: <numbered findings, each with file/line and impact; or "No actionable findings found after the full-diff review.">
Decision: blocked | ready for pre-merge checks
```

“No actionable findings” is a review conclusion only after completing that pass; it
is never a default. Any unresolved finding stops here and returns the findings to
the user. Do not fix, dismiss, or merge it unilaterally.

## Pre-merge gate

For a clear review, inspect the current state immediately before the merge:

1. Run `gh pr checks <PR> --required` and inspect every required check. Failed,
   pending, cancelled, skipped-without-policy-basis, or unavailable required checks
   block the merge.
2. Re-read PR mergeability and conflict state. A non-mergeable PR or any conflict
   blocks the merge.
3. State the GitHub limitation plainly: authors cannot provide an independent
   self-approval. Do not manufacture, bypass, or imply an approval; this is a
   documented self-review and the repository's own protection rules still apply.

Report the gate result and wait for an explicit user instruction to merge. The
review-and-merge request authorizes the review; the fresh review report gives the
user the decision point immediately before the irreversible operation. Re-run this
gate if the PR changes while waiting.

## Merge and verify

After explicit approval, run the selected strategy:

```bash
gh pr merge <PR> --squash --delete-branch
```

The configured choice is **squash**, and `--delete-branch` requests deletion of the
remote head branch. If repository rules prevent the merge or deletion, report the
exact result and stop; do not substitute a different merge strategy or force a
merge. Verify that the PR is merged and that remote-branch deletion succeeded.

## Worktree-safe cleanup

Inspect `git worktree list --porcelain` before local cleanup. When the PR head is
checked out in a linked worktree, preserve the branch while it is attached and use
the worktree path for cleanup: inspect it for changes, get any needed confirmation,
then run `git worktree remove <path>` and `git worktree prune`. A plain local branch
deletion is not a cleanup mechanism for a branch attached to a worktree.

If no worktree owns the branch, the remote deletion is the requested cleanup; only
remove a local branch when the user explicitly asks. Finish by reporting merge SHA,
remote-branch deletion status, and any retained or removed worktree.

## Stop rule

Return to the user without merging whenever a review finding remains unresolved, a
required check is not passing, mergeability/conflict status is not clear, or GitHub
rejects the merge. Include the evidence needed for the user to decide what happens
next.
