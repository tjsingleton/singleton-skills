"""Package integrity; executed behavior transcripts live with skill evaluations."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class LinearUpdatePackagingTests(unittest.TestCase):
    def test_shared_dependency_is_resolvable(self):
        skill = ROOT / "skills/linear-update"
        self.assertTrue((skill / "SKILL.md").is_file())
        self.assertTrue((skill / "../linear-author/references/linear-contract.md").resolve().is_file())

    def test_controlled_evaluations_have_inputs_and_independent_oracles(self):
        data = json.loads((ROOT / "skills/linear-update/evals/evals.json").read_text())
        self.assertEqual(data["skill_name"], "linear-update")
        cases = data["evals"]
        self.assertEqual(len(cases), len({case["id"] for case in cases}))
        for case in cases:
            for field in ("prompt", "snapshot", "expected_output", "expectations"):
                self.assertTrue(case[field], (case["id"], field))

if __name__ == "__main__":
    unittest.main()
