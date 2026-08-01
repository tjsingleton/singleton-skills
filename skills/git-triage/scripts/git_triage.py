#!/usr/bin/env python3
"""Collect a local Git triage snapshot, with an explicitly gated refresh."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


class TriageError(RuntimeError):
    """A deterministic collection or refresh refusal."""


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise TriageError(f"git {' '.join(args)} failed: {detail}")
    return result


def _lines(repo: Path, *args: str) -> list[str]:
    return [line for line in _git(repo, *args).stdout.splitlines() if line]


def _status(repo: Path) -> tuple[dict[str, int], str | None, tuple[int, int] | None]:
    counts = {"staged": 0, "modified": 0, "untracked": 0, "conflicted": 0}
    upstream = None
    ahead_behind = None
    for line in _git(repo, "status", "--porcelain=v2", "--branch").stdout.splitlines():
        if line.startswith("# branch.upstream "):
            upstream = line.removeprefix("# branch.upstream ")
        elif line.startswith("# branch.ab "):
            ahead, behind = line.removeprefix("# branch.ab ").split()
            ahead_behind = (int(ahead[1:]), int(behind[1:]))
        elif line.startswith("? "):
            counts["untracked"] += 1
        elif line.startswith("u "):
            counts["conflicted"] += 1
        elif line[:2] in {"1 ", "2 "}:
            xy = line.split(" ", 2)[1]
            if xy[0] != ".":
                counts["staged"] += 1
            if xy[1] != ".":
                counts["modified"] += 1
    return counts, upstream, ahead_behind


def _branches(repo: Path) -> list[dict[str, object]]:
    branches: list[dict[str, object]] = []
    for line in _lines(
        repo,
        "branch",
        "--format=%(refname:short)|%(objectname)|%(upstream:short)",
    ):
        name, commit, upstream = line.split("|", 2)
        ahead = behind = None
        if upstream:
            comparison = _git(
                repo, "rev-list", "--left-right", "--count", f"{name}...{upstream}", check=False
            )
            if comparison.returncode == 0:
                ahead, behind = (int(value) for value in comparison.stdout.split())
        branches.append(
            {
                "name": name,
                "commit": commit,
                "upstream": upstream or None,
                "ahead": ahead,
                "behind": behind,
            }
        )
    return branches


def _worktrees(repo: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    current: dict[str, object] = {}
    for line in _git(repo, "worktree", "list", "--porcelain").stdout.splitlines() + [""]:
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key == "HEAD":
            current["commit"] = value
        elif key in {"detached", "locked", "prunable"}:
            current[key] = value or True
    return entries


def _choose_refresh_remote(
    repo: Path,
    branch: str | None,
    remotes: list[str],
    requested: str | None,
) -> str:
    if requested:
        if requested not in remotes:
            raise TriageError(f"refresh remote is not configured: {requested}")
        return requested
    if branch:
        configured = _git(repo, "config", "--get", f"branch.{branch}.remote", check=False)
        candidate = configured.stdout.strip()
        if configured.returncode == 0 and candidate and candidate != ".":
            return candidate
    if len(remotes) == 1:
        return remotes[0]
    if not remotes:
        raise TriageError("refresh unavailable: no remote")
    raise TriageError("refresh remote is ambiguous: multiple remotes configured")


def collect(
    repo: Path,
    *,
    refresh: bool = False,
    approve_refresh: bool = False,
    remote: str | None = None,
) -> dict[str, object]:
    repo = repo.resolve(strict=True)
    if _git(repo, "rev-parse", "--is-inside-work-tree", check=False).stdout.strip() != "true":
        raise TriageError("not a Git worktree")

    branch_result = _git(repo, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    branch = branch_result.stdout.strip() or None
    remotes = _lines(repo, "remote")
    refreshed_from = None
    if refresh:
        if not approve_refresh:
            raise TriageError("refresh requires explicit approval")
        refreshed_from = _choose_refresh_remote(repo, branch, remotes, remote)
        _git(repo, "fetch", "--prune", refreshed_from)

    counts, upstream, ahead_behind = _status(repo)
    branches = _branches(repo)
    worktrees = _worktrees(repo)
    head = _git(repo, "rev-parse", "--short", "HEAD", check=False).stdout.strip() or None
    unborn = branch is not None and head is None
    current_path = str(repo)
    additional_worktrees = [item for item in worktrees if item.get("path") != current_path]
    dirty = any(counts.values())

    needs_push: list[dict[str, object]] = []
    in_progress: list[dict[str, object]] = []
    clean: list[dict[str, object]] = []
    for item in branches:
        if item["upstream"] is None or (item["ahead"] or 0) > 0:
            needs_push.append(item)
        if (item["behind"] or 0) > 0:
            in_progress.append({"kind": "behind-or-diverged", **item})
        if (
            item["upstream"] is not None
            and item["ahead"] == 0
            and item["behind"] == 0
            and (item["name"] != branch or not dirty)
        ):
            clean.append(item)
    if dirty:
        in_progress.append({"kind": "dirty-worktree", "counts": counts})
    if unborn:
        in_progress.append({"kind": "unborn-head", "branch": branch})
    elif branch is None:
        in_progress.append({"kind": "detached-head"})
    for item in additional_worktrees:
        in_progress.append({"kind": "additional-worktree", **item})

    local_names = {str(item["name"]) for item in branches}
    elsewhere: list[dict[str, str]] = []
    for line in _lines(
        repo,
        "for-each-ref",
        "--format=%(refname:short)|%(symref)",
        "refs/remotes",
    ):
        ref, symref = line.split("|", 1)
        if symref or ref.endswith("/__dolt_remote_info__"):
            continue
        remote_name, separator, branch_name = ref.partition("/")
        if separator and branch_name not in local_names:
            elsewhere.append({"remote": remote_name, "branch": branch_name, "ref": ref})

    return {
        "snapshot": "refreshed" if refreshed_from else "local-only",
        "refreshed_from": refreshed_from,
        "repository": str(repo),
        "head": {
            "branch": branch,
            "commit": head,
            "detached": branch is None,
            "unborn": unborn,
        },
        "current_upstream": upstream,
        "current_ahead_behind": ahead_behind,
        "worktree_counts": counts,
        "remotes": remotes,
        "branches": branches,
        "worktrees": worktrees,
        "categories": {
            "needs_push": needs_push,
            "in_progress": in_progress,
            "stashed": _lines(
                repo,
                "stash",
                "list",
                "--date=iso-strict",
                "--format=%gd|%ci|%s",
            ),
            "elsewhere": elsewhere,
            "prs_needing_attention": None,
            "clean": clean,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--approve-refresh", action="store_true")
    parser.add_argument("--remote")
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                collect(
                    Path(args.repo),
                    refresh=args.refresh,
                    approve_refresh=args.approve_refresh,
                    remote=args.remote,
                ),
                indent=2,
                sort_keys=True,
            )
        )
    except TriageError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
