"""Package integrity only; model behavior evidence lives beside the skill evals."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LinearSkillPackagingTests(unittest.TestCase):
    def test_author_reference_survives_packaging(self) -> None:
        skill = ROOT / "skills" / "linear-author"
        text = (skill / "SKILL.md").read_text()
        references = re.findall(r"\]\((references/[^)]+)\)", text)
        self.assertTrue(references)
        for target in references:
            self.assertTrue((skill / target).is_file(), target)

    def test_author_evals_have_distinct_controlled_requests_and_oracles(self) -> None:
        path = ROOT / "skills" / "linear-author" / "evals" / "evals.json"
        data = json.loads(path.read_text())
        self.assertEqual(data["skill_name"], "linear-author")
        cases = data["evals"]
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        for case in cases:
            with self.subTest(case=case["id"]):
                for field in ("prompt", "snapshot", "expected_output", "expectations"):
                    self.assertTrue(case[field])


if __name__ == "__main__":
    unittest.main()
