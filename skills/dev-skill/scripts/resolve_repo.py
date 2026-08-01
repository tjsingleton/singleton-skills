#!/usr/bin/env python3
"""Resolve an editable singleton-skills checkout without host-specific paths."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, Mapping


class ResolutionError(RuntimeError):
    """Raised when no single editable checkout can be resolved safely."""


def _resolved(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def is_editable_checkout(path: Path) -> bool:
    """Return whether *path* has the minimum shape of an editable checkout."""

    return (
        path.is_dir()
        and (path / ".git").exists()
        and (path / "justfile").is_file()
        and (path / "skills" / "dev-skill" / "SKILL.md").is_file()
    )


def _containing_checkout(start: Path) -> Path | None:
    current = _resolved(start)
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if is_editable_checkout(candidate):
            return candidate
    return None


def resolve_repo(
    *,
    explicit: str | None = None,
    cwd: Path | None = None,
    active_skill_file: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Resolve one checkout using explicit configuration, cwd, then skill source."""

    env = os.environ if environ is None else environ
    configured = explicit or env.get("SINGLETON_SKILLS_PATH")
    if configured:
        candidate = _resolved(configured)
        if not is_editable_checkout(candidate):
            raise ResolutionError(
                "SINGLETON_SKILLS_PATH does not identify an editable "
                "singleton-skills checkout"
            )
        return candidate

    starts: Iterable[Path] = (
        cwd or Path.cwd(),
        active_skill_file or Path(__file__),
    )
    candidates = {
        candidate
        for start in starts
        if (candidate := _containing_checkout(start)) is not None
    }
    if not candidates:
        raise ResolutionError(
            "could not find an editable singleton-skills checkout; set "
            "SINGLETON_SKILLS_PATH explicitly"
        )
    if len(candidates) > 1:
        rendered = ", ".join(str(path) for path in sorted(candidates))
        raise ResolutionError(
            f"multiple singleton-skills checkouts are in scope: {rendered}; "
            "set SINGLETON_SKILLS_PATH explicitly"
        )
    return candidates.pop()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve an editable singleton-skills checkout"
    )
    parser.add_argument("--explicit", help="Explicit checkout path")
    parser.add_argument("--cwd", type=Path, help="Working directory to inspect")
    args = parser.parse_args()
    try:
        print(resolve_repo(explicit=args.explicit, cwd=args.cwd))
    except ResolutionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
