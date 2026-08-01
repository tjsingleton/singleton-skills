from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_TEXT = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
FINDINGS_TEXT = (SKILL_DIR / "evals" / "FINDINGS.md").read_text(encoding="utf-8")
HELPER_TEXT = (SKILL_DIR / "scripts" / "git_triage.py").read_text(encoding="utf-8")


class GitTriageStaticContractTests(unittest.TestCase):
    def test_skill_has_no_provider_specific_execution_dependency(self) -> None:
        forbidden = (
            "oh-my-" + "claudecode",
            "git" + "-master",
            "O" + "MC",
            "~/" + ".claude/skills",
        )
        for token in forbidden:
            with self.subTest(token=token):
                self.assertNotIn(token, SKILL_TEXT)

    def test_local_snapshot_excludes_network_capable_commands(self) -> None:
        local = SKILL_TEXT.split("## Phase 1 — Local snapshot", 1)[1].split(
            "## Phase 2 — Optional refreshed snapshot", 1
        )[0]
        command_blocks = "\n".join(re.findall(r"```bash\n(.*?)```", local, re.DOTALL))
        for command in ("git fetch", "git pull", "git push", "git ls-remote", "gh "):
            with self.subTest(command=command):
                self.assertNotIn(command, command_blocks)

    def test_refreshed_mode_is_explicit_and_discovers_remote(self) -> None:
        refreshed = SKILL_TEXT.split("## Phase 2 — Optional refreshed snapshot", 1)[1]
        self.assertIn("explicit request or approval", refreshed)
        self.assertIn('git fetch --prune "<remote>"', refreshed)
        self.assertNotIn("git fetch --prune origin", refreshed)

    def test_bundled_helper_keeps_refresh_behind_an_explicit_gate(self) -> None:
        self.assertIn("scripts/git_triage.py", SKILL_TEXT)
        self.assertIn("approve_refresh", HELPER_TEXT)
        self.assertIn("refresh requires explicit approval", HELPER_TEXT)

    def test_all_report_categories_are_required(self) -> None:
        required = (
            "NEEDS PUSH",
            "IN PROGRESS",
            "STASHED",
            "ELSEWHERE",
            "PRs NEEDING ATTENTION",
            "CLEAN",
        )
        for category in required:
            with self.subTest(category=category):
                self.assertIn(category, SKILL_TEXT)
        self.assertIn("Every one of the six categories must appear", SKILL_TEXT)

    def test_mutations_require_approval_and_read_back(self) -> None:
        self.assertIn("explicitly approves the exact action", SKILL_TEXT)
        self.assertIn("## Phase 4 — Approved actions and read-back", SKILL_TEXT)
        self.assertIn("Required read-back", SKILL_TEXT)

    def test_public_findings_have_no_personal_absolute_paths(self) -> None:
        self.assertIsNone(re.search(r"/(?:Users|home)/[^/\s]+/", FINDINGS_TEXT))


if __name__ == "__main__":
    unittest.main()
