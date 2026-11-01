"""Verify immutable pilot artifacts, not human or model performance."""
import hashlib
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LinearPilotPinsTests(unittest.TestCase):
    def test_revision2_pins_match_packet_and_committed_instructions(self):
        packet = ROOT / 'docs/evaluations/linear-skills/revision2'
        pins = json.loads((packet / 'pins.json').read_text())
        for name, expected in pins['sha256'].items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected)
        for name in pins['instruction_paths']:
            committed = subprocess.check_output(['git', 'show', f"{pins['skill_revision']}:{name}"], cwd=ROOT)
            self.assertEqual(hashlib.sha256(committed).hexdigest(), pins['sha256'][name])
        run = json.loads((packet / 'execution.json').read_text())
        self.assertEqual(run['skill_revision'], pins['skill_revision'])
        for pair, case in [('a', 'A'), ('b', 'B')]:
            recorded = next(item for item in run['cases'] if item['id'] == case)
            self.assertIn(recorded['display'], (packet / f'pair-{pair}.md').read_text())
            self.assertEqual(recorded['requested_operations'], [])


if __name__ == '__main__':
    unittest.main()
