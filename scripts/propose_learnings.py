#!/usr/bin/env python3
"""Extract [Unreleased] entries from a CHANGELOG.md and propose skill improvements.

Usage:
    python propose_learnings.py <changelog-path>

Reads the [Unreleased] section of a Keep a Changelog formatted file and prints
actionable improvement suggestions based on keyword routing. Deterministic,
stdlib-only — no LLM required.
"""

import re
import sys
from pathlib import Path


# Keyword → improvement category routing
ROUTES = {
    "trigger": "description",
    "autocomplete": "argument-hint",
    "argument": "argument-hint",
    "hint": "argument-hint",
    "eval": "evals",
    "test": "evals",
    "assert": "evals",
    "workflow": "workflow",
    "step": "workflow",
    "subagent": "workflow",
    "cd ": "workflow",
    "working directory": "workflow",
    "path": "workflow",
    "convention": "conventions",
    "format": "conventions",
    "output": "conventions",
    "install": "justfile",
    "symlink": "justfile",
    "just ": "justfile",
    "changelog": "reflection",
    "reflect": "reflection",
    "learning": "reflection",
    "description": "description",
    "when to": "description",
    "don't use": "description",
}

CATEGORY_LABELS = {
    "description": "SKILL.md description (trigger conditions)",
    "argument-hint": "argument-hint field (autocomplete display)",
    "evals": "evals/evals.json (test coverage)",
    "workflow": "Workflow steps (execution logic)",
    "conventions": "Output/format conventions",
    "justfile": "justfile targets",
    "reflection": "Reflection/changelog process",
}


def parse_unreleased(text: str) -> list[str]:
    """Extract bullet lines from the [Unreleased] section."""
    # Find [Unreleased] header
    unreleased_match = re.search(r"^## \[Unreleased\]", text, re.MULTILINE)
    if not unreleased_match:
        return []

    start = unreleased_match.end()

    # Find next ## header (next version section)
    next_section = re.search(r"^## \[", text[start:], re.MULTILINE)
    end = start + next_section.start() if next_section else len(text)

    section = text[start:end]

    # Extract all bullet lines (- or *)
    bullets = re.findall(r"^[-*]\s+(.+)", section, re.MULTILINE)
    return [b.strip() for b in bullets if b.strip()]


def route_bullet(bullet: str) -> str:
    """Route a bullet to the most relevant improvement category."""
    lower = bullet.lower()
    for keyword, category in ROUTES.items():
        if keyword in lower:
            return category
    return "workflow"  # default


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <changelog-path>", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(1)

    text = path.read_text()
    bullets = parse_unreleased(text)

    if not bullets:
        print("No [Unreleased] entries found. Nothing to propose.")
        return

    # Group bullets by category
    grouped: dict[str, list[str]] = {}
    for bullet in bullets:
        cat = route_bullet(bullet)
        grouped.setdefault(cat, []).append(bullet)

    skill_name = path.parent.name
    print(f"## Proposed improvements for: {skill_name}\n")
    print(f"Source: {path}\n")

    for cat, items in grouped.items():
        label = CATEGORY_LABELS.get(cat, cat)
        print(f"### {label}")
        for item in items:
            print(f"  - {item}")
        print()

    print(f"--- {len(bullets)} entries across {len(grouped)} categories ---")


if __name__ == "__main__":
    main()
