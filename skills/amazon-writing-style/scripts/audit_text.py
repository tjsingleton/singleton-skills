#!/usr/bin/env python3
"""Audit prose against the six Amazon writing rules this skill enforces."""

from __future__ import annotations

import json
import re
import sys

WEASEL = [
    r"\bmostly\b",
    r"\bsignificantly\b",
    r"\bsubstantially\b",
    r"\bapproximately\b",
    r"\bmany\b",
    r"\bsome\b",
    r"\bnearly\b",
    r"\bfairly\b",
    r"\bextremely\b",
    r"\bvast majority\b",
]
ADJECTIVES = [
    r"\bsuccessful\b",
    r"\bdisappointing\b",
    r"\bexciting\b",
    r"\bremarkable\b",
    r"\bgreatly\b",
    r"\bdrastically\b",
    r"\bterrible\b",
]
CLUTTER = [
    (r"\bdue to the fact that\b", "because"),
    (r"\bin order to\b", "to"),
    (r"\bfor the purpose of\b", "to"),
    (r"\bin the event that\b", "if"),
    (r"\bwith regard to\b", "about"),
    (r"\ba number of\b", "a count"),
]
SVO = [
    r"\b(am|is|are|was|were|be|been|being)\b\s+(\w+ed|\bseen\b|\bchosen\b|\bdriven\b|\bexpected\b|\bmade\b)"
]
# Common expansions that do not need a first-use lecture in every sentence.
KNOWN_ACRONYMS = {
    "AI",
    "API",
    "CEO",
    "FAQ",
    "PR",
    "US",
    "USA",
    "UK",
}


def _acronyms(sentence: str) -> list[str]:
    found = re.findall(r"\b[A-Z]{2,}\b", sentence)
    return [a for a in found if a not in KNOWN_ACRONYMS]


def audit_text(text: str) -> dict:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    report = {"total_violations": 0, "violations_by_sentence": []}

    for idx, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
        issues: list[str] = []
        word_count = len(sentence.split())

        if word_count >= 30:
            issues.append(
                f"SHORT SENTENCES: {word_count} words (maximum is 30)."
            )

        for pattern in WEASEL:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            if matches:
                issues.append(
                    f"DATA OVER ADJECTIVES: weasel {matches}. Use a number."
                )

        for pattern in ADJECTIVES:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            if matches:
                issues.append(
                    f"DATA OVER ADJECTIVES: {matches}. Replace with a fact."
                )

        for pattern, replacement in CLUTTER:
            if re.search(pattern, sentence, re.IGNORECASE):
                issues.append(
                    f"CLUTTER: matched {pattern}. Use '{replacement}'."
                )

        for pattern in SVO:
            matches = re.findall(pattern, sentence, re.IGNORECASE)
            if matches:
                match_text = " ".join(m for sub in matches for m in sub if m)
                issues.append(
                    f"SVO: '{match_text}' hides the doer. Name actor + verb."
                )

        unexplained = _acronyms(sentence)
        if unexplained:
            issues.append(
                f"JARGON/ACRONYMS: {unexplained}. Spell out on first use."
            )

        if issues:
            report["total_violations"] += len(issues)
            report["violations_by_sentence"].append(
                {
                    "line_number": idx + 1,
                    "sentence": sentence.strip(),
                    "issues": issues,
                }
            )

    return report


if __name__ == "__main__":
    input_text = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not input_text.strip():
        print(
            "Pass draft text on stdin: python3 scripts/audit_text.py < draft.txt",
            file=sys.stderr,
        )
        sys.exit(1)
    print(json.dumps(audit_text(input_text), indent=2))
