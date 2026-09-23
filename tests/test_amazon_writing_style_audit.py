"""CLI behavior for the Amazon writing-style auditor."""

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "skills/amazon-writing-style/scripts/audit_text.py"


def audit(draft: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(AUDITOR)],
        input=draft,
        capture_output=True,
        check=True,
        text=True,
    )
    return json.loads(result.stdout)


class AmazonWritingStyleAuditTests(unittest.TestCase):
    def test_defined_acronym_is_accepted_on_first_and_later_use(self):
        report = audit(
            "Service Level Agreement (SLA) sets the target. The SLA guides teams."
        )

        self.assertEqual(report["total_violations"], 0)

    def test_unexplained_allowlisted_acronym_is_reported(self):
        report = audit("API is available.")

        self.assertIn("JARGON/ACRONYMS", report["violations_by_sentence"][0]["issues"][0])

    def test_linking_verb_with_ed_ending_adjective_is_not_passive(self):
        report = audit("The logo is red.")

        self.assertEqual(report["total_violations"], 0)

    def test_passive_participle_is_reported(self):
        report = audit("The report was written.")

        self.assertIn("SVO", report["violations_by_sentence"][0]["issues"][0])

    def test_violation_lines_match_source_with_multiple_sentences_and_blank_lines(self):
        report = audit("API is useful. The API works.\n\nAPI remains common.")

        self.assertEqual(
            [item["line_number"] for item in report["violations_by_sentence"]],
            [1, 1, 3],
        )


if __name__ == "__main__":
    unittest.main()
