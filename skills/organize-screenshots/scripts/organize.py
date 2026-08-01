#!/usr/bin/env python3
"""Create and optionally apply a reviewed screenshot organization plan."""
from __future__ import annotations

import argparse
import csv
import re
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

STAMP = re.compile(
    r"(?:Screenshot|Screen Shot) (\d{4}-\d{2}-\d{2}) at (\d{1,2})\.(\d{2})\.(\d{2})[\u202f ]*(AM|PM)",
    re.IGNORECASE,
)


def read_ocr(path: Path) -> dict[str, str]:
    records, current, lines = {}, None, []
    for raw in path.read_text(errors="replace").splitlines():
        if raw.startswith("FILE:"):
            current, lines = raw[5:], []
        elif raw == "---":
            if current:
                records[current] = " ".join(lines)
            current = None
        elif current:
            lines.append(raw)
    return records


def classify(text: str) -> tuple[str, str]:
    t = text.lower()
    rules = [
        ("AI CRED", "AI CRED", ["ai cred", "al cred", "ai fluency", "fluency score", "aicred"]),
        ("EveryDollar", "Budget Reconciliation", ["everydollar", "budget month", "edit expense"]),
        ("Financial Accounts", "Financial Account Review", ["mortgage", "bank of america", "wells fargo", "credit card", "autopay"]),
        ("Church Technology", "Church Technology", ["new canaan", "ubiquiti", "unifi", "wordpress", "microsoft 365"]),
        ("Agent Workflow", "Agent Workflow", ["codex", "omx", "fable", "agent-shaped", "skills", "background tasks", "persistent memory", "sonnet"]),
        ("Media Services", "Media Service Review", ["xfinity", "peacock", "netflix", "roku", "plex", "youtube premium"]),
        ("Home Network", "Home Network", ["netgear", "tp-link", "wireless settings", "router", "wifiman"]),
        ("Home Maintenance", "Home Maintenance", ["breaker", "electrical panel", "water consumption", "floor plans"]),
        ("Home and Real Estate", "Home and Real Estate", ["homebot", "listing", "floor plans", "property"]),
        ("Shopping", "Shopping Review", ["amazon", "dell", "nissan", "carfax", "instacart", "order placed", "temporary email"]),
        ("Account Services", "Account Service Review", ["google one", "data options", "cellular telephone", "subscription"]),
        ("Documents", "Document Review", ["pdf", "personal info", "report", "memorizing scripture", "comparing elders", "untitled document", "ecredits", "workspace details"]),
        ("Bible Study", "Bible Reading Plan", ["new testament", "old testament", "matthew", "scripture"]),
        ("Browser Extensions", "Browser Extension Review", ["ublock"]),
        ("Career", "Career Review", ["performance review", "competitive context", "bio (optional", "characters"]),
        ("Mapping", "Map Review", ["radiusmapper", "location intelligence"]),
        ("Scheduling", "Schedule Review", ["calendar", "talk to emily", "meeting"]),
        ("Wellness", "Wellness Review", ["hunger", "wellness", "nutrition"]),
        ("Homelab", "Homelab Configuration", ["homelab", "iterm", "machine config"]),
    ]
    for episode, title, terms in rules:
        if any(term in t for term in terms):
            if episode == "AI CRED" and "score" in t:
                return episode, "AI Fluency Score"
            if episode == "Financial Accounts" and "mortgage" in t:
                return episode, "Mortgage Details"
            if episode == "Church Technology" and "wordpress" in t:
                return episode, "WordPress Configuration"
            if episode == "Agent Workflow" and "skills" in t:
                return episode, "Skills Configuration"
            return episode, title
    return "Unclassified", "Context Capture"


def timestamp(source: Path) -> datetime:
    match = STAMP.search(source.name)
    if not match:
        raise ValueError(f"No capture timestamp in {source.name}")
    date, hour, minute, second, meridiem = match.groups()
    hour_i = int(hour) % 12 + (12 if meridiem.upper() == "PM" else 0)
    return datetime.strptime(f"{date} {hour_i:02d}:{minute}:{second}", "%Y-%m-%d %H:%M:%S")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    text_by_path = read_ocr(args.ocr)
    planned: list[tuple[Path, Path, str, str]] = []
    seen: defaultdict[Path, int] = defaultdict(int)
    for source in sorted(args.source.glob("2026-*/*")):
        if not source.is_file() or source.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            continue
        captured = timestamp(source)
        episode, title = classify(text_by_path.get(str(source), ""))
        target_dir = args.destination / captured.strftime("%m/%d") / episode
        target = target_dir / f"{captured.strftime('%H-%M-%S')} - {title}{source.suffix.lower()}"
        seen[target] += 1
        if seen[target] > 1:
            target = target.with_stem(f"{target.stem} - {seen[target]}")
        planned.append((source, target, episode, title))

    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(["source", "destination", "episode", "title"])
        writer.writerows((source, target, episode, title) for source, target, episode, title in planned)

    if args.apply:
        for source, target, _, _ in planned:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))


if __name__ == "__main__":
    main()
