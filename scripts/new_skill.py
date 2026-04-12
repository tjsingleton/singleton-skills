#!/usr/bin/env python3
"""Scaffold a new skill directory with SKILL.md and evals/evals.json stub.

Usage:
    python new_skill.py <skill-name> <skill-dir>
"""

import sys
import json
from pathlib import Path


def main() -> None:
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <skill-name> <skill-dir>", file=sys.stderr)
        sys.exit(1)

    name = sys.argv[1]
    skill_dir = Path(sys.argv[2])

    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "evals").mkdir(exist_ok=True)

    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        print(f"Error: {skill_md} already exists", file=sys.stderr)
        sys.exit(1)

    skill_md.write_text(
        f"""\
---
name: {name}
description: >
  TODO: Describe what this skill does and when to trigger it.
  Use this skill whenever the user wants to [action].
  Trigger on: [keyword, keyword].
  Don't use when [anti-pattern].
argument-hint: "[options] <argument>"
license: MIT
---

# {name}

> **Quick usage:**
> ```
> /singleton-skills:{name} <argument>
> ```
>
> If invoked with no arguments, show this hint and wait for input.

## Overview

TODO: What does this skill do and why does it exist?

## Workflow

### Step 1 — Parse arguments

Parse `$ARGUMENTS`:
- If empty or `--help`: show usage hint above and stop
- Otherwise: extract [describe expected args]

### Step 2 — TODO

TODO: describe the main steps.

## Output

TODO: describe the output format.

## Notes

- TODO: any important caveats or edge cases.
"""
    )

    evals_path = skill_dir / "evals" / "evals.json"
    evals_path.write_text(
        json.dumps({"skill_name": name, "evals": []}, indent=2) + "\n"
    )

    print(f"Created: {skill_md}")
    print(f"Created: {evals_path}")


if __name__ == "__main__":
    main()
