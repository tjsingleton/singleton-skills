from __future__ import annotations

import importlib.util
import os
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = ("git-triage", "imessage-search")
SPEC = importlib.util.spec_from_file_location(
    "portable_conformance_installer", ROOT / "scripts" / "skill_installer.py"
)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


def read_frontmatter(skill_file: Path) -> dict[str, str]:
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{skill_file} does not start with YAML frontmatter")
    try:
        frontmatter = text.split("---\n", 2)[1]
    except IndexError as exc:
        raise AssertionError(f"{skill_file} has unterminated YAML frontmatter") from exc

    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        match = re.match(r"^([a-z][a-z0-9-]*):(?:\s*(.*))?$", line)
        if match:
            metadata[match.group(1)] = (match.group(2) or "").strip()
    return metadata


def public_files(skill_dir: Path):
    for path in skill_dir.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            yield path


class PortableCoreConformanceTests(unittest.TestCase):
    def test_supported_manifest_is_the_exact_contract_tested_candidate_set(self) -> None:
        names = tuple(
            line.strip()
            for line in (ROOT / "supported-skills.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        self.assertEqual(names, SUPPORTED)
        for name in names:
            self.assertTrue((ROOT / "skills" / name).is_dir())

    def test_supported_skills_have_portable_discovery_metadata(self) -> None:
        for name in SUPPORTED:
            with self.subTest(skill=name):
                skill_file = ROOT / "skills" / name / "SKILL.md"
                self.assertTrue(skill_file.is_file())
                metadata = read_frontmatter(skill_file)
                self.assertEqual(metadata.get("name"), name)
                self.assertIn("description", metadata)

    def test_supported_trees_have_no_forbidden_dependencies_or_personal_paths(self) -> None:
        forbidden = (
            "oh-my-" + "claudecode",
            "git" + "-master",
            "general" + "-purpose",
            "~/" + ".claude/skills",
            "O" + "MX",
            "O" + "MC",
        )
        personal_paths = (
            re.compile(r"/(?:Users|home)/[^/<\s]+/"),
            re.compile(r"/Volumes/[^/<\s]+/(?:Users/)?[^/<\s]+/"),
        )
        for name in SUPPORTED:
            for path in public_files(ROOT / "skills" / name):
                text = path.read_text(encoding="utf-8", errors="replace")
                relative = path.relative_to(ROOT)
                for token in forbidden:
                    with self.subTest(path=relative, token=token):
                        self.assertNotIn(token, text)
                for pattern in personal_paths:
                    with self.subTest(path=relative, pattern=pattern.pattern):
                        self.assertIsNone(pattern.search(text))

    def test_readme_keeps_the_support_claim_narrow(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in SUPPORTED:
            self.assertRegex(
                readme,
                rf"\| `{re.escape(name)}` \| Candidate; contract-tested \| "
                rf"Intended: Claude Code, Codex, Cursor \|",
            )
        self.assertIn("All other repository skills | Available, not certified", readme)
        self.assertIn(
            "Live Claude Code, Codex, and Cursor\n"
            "discovery and behavior smokes remain pending",
            readme,
        )
        self.assertIn(
            "intended portable support, not certified live cross-host support",
            readme,
        )
        self.assertNotRegex(
            readme, r"\| `(?:git-triage|imessage-search)` \| Supported \|"
        )
        self.assertIn("direct execution is the guaranteed fallback", readme)

    def test_shared_and_claude_routes_each_discover_supported_skills_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            checkout = temp / "checkout"
            (checkout / "skills").mkdir(parents=True)
            shutil.copy2(ROOT / "supported-skills.txt", checkout / "supported-skills.txt")
            for name in SUPPORTED:
                shutil.copytree(ROOT / "skills" / name, checkout / "skills" / name)

            roots = {"shared": temp / "shared", "claude": temp / "claude"}
            installer.install(checkout, "default", "all", roots)

            for route, root in roots.items():
                with self.subTest(route=route):
                    discovered = [
                        read_frontmatter(path / "SKILL.md")["name"]
                        for path in sorted(root.iterdir())
                        if path.is_symlink() and (path / "SKILL.md").is_file()
                    ]
                    self.assertEqual(discovered, list(SUPPORTED))
                    self.assertEqual(len(discovered), len(set(discovered)))
                    for name in SUPPORTED:
                        self.assertEqual(
                            os.readlink(root / name),
                            str((checkout / "skills" / name).resolve()),
                        )


if __name__ == "__main__":
    unittest.main()
