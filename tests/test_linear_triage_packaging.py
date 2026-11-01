"""Packaging checks only; executed model evaluations are recorded separately."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class LinearTriagePackagingTests(unittest.TestCase):
    def test_sibling_contract_is_present_in_supported_install(self):
        skill = ROOT / 'skills' / 'linear-triage'
        links = re.findall(r'\]\((\.\./linear-author/[^)]+)\)',
                           (skill / 'SKILL.md').read_text())
        self.assertTrue(links)
        for link in links:
            self.assertTrue((skill / link).is_file())
        self.assertIn('linear-author', (ROOT / 'supported-skills.txt').read_text().splitlines())

    def test_controlled_evaluations_have_independent_oracles(self):
        data = json.loads((ROOT / 'skills/linear-triage/evals/evals.json').read_text())
        self.assertEqual(data['skill_name'], 'linear-triage')
        self.assertEqual(len({case['id'] for case in data['evals']}), len(data['evals']))
        for case in data['evals']:
            for field in ('prompt', 'snapshot', 'expected_output', 'expectations'):
                self.assertTrue(case[field])
