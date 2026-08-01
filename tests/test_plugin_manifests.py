from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.3.0"
PLUGIN_ID = "singleton-skills"
EXPECTED_SKILLS = {
    "dev-skill",
    "git-triage",
    "imessage-search",
    "learn-from-context",
    "new-skill",
    "organize-screenshots",
    "project-onboard",
}


def read_json(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def read_json_from(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class PluginManifestTests(unittest.TestCase):
    def test_all_host_plugin_manifests_share_identity_version_and_skill_root(self) -> None:
        manifests = {
            "claude": read_json(".claude-plugin/plugin.json"),
            "cursor": read_json(".cursor-plugin/plugin.json"),
            "codex": read_json(".codex-plugin/plugin.json"),
        }
        for host, manifest in manifests.items():
            with self.subTest(host=host):
                self.assertEqual(manifest["name"], PLUGIN_ID)
                self.assertEqual(manifest["version"], VERSION)
                self.assertEqual(manifest.get("skills", "./skills/"), "./skills/")
                self.assertEqual(manifest["license"], "MIT")
                self.assertNotIn("logo", manifest)
                self.assertNotIn("apps", manifest)
                self.assertNotIn("mcpServers", manifest)

    def test_marketplaces_use_the_final_id_and_repository_root_source(self) -> None:
        claude = read_json(".claude-plugin/marketplace.json")
        cursor = read_json(".cursor-plugin/marketplace.json")
        codex = read_json(".agents/plugins/marketplace.json")

        self.assertEqual(claude["name"], PLUGIN_ID)
        self.assertEqual(claude["plugins"][0]["name"], PLUGIN_ID)
        self.assertEqual(claude["plugins"][0]["source"], "./")
        self.assertEqual(claude["plugins"][0]["version"], VERSION)

        self.assertEqual(cursor["name"], PLUGIN_ID)
        self.assertEqual(cursor["plugins"][0]["name"], PLUGIN_ID)
        self.assertEqual(cursor["plugins"][0]["source"], ".")

        self.assertEqual(codex["name"], PLUGIN_ID)
        self.assertEqual(codex["plugins"][0]["name"], PLUGIN_ID)
        self.assertEqual(
            codex["plugins"][0]["source"], {"source": "url", "url": "./"}
        )

    def test_cursor_manifests_match_the_official_strict_field_contract(self) -> None:
        plugin = read_json(".cursor-plugin/plugin.json")
        marketplace = read_json(".cursor-plugin/marketplace.json")
        allowed_plugin = {
            "name",
            "displayName",
            "description",
            "version",
            "minClientVersions",
            "author",
            "publisher",
            "homepage",
            "repository",
            "license",
            "logo",
            "keywords",
            "category",
            "tags",
            "commands",
            "agents",
            "skills",
            "rules",
            "hooks",
            "mcpServers",
        }
        self.assertEqual(set(plugin) - allowed_plugin, set())
        self.assertRegex(plugin["name"], r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")
        self.assertEqual(set(marketplace) - {"name", "owner", "metadata", "plugins"}, set())
        for entry in marketplace["plugins"]:
            self.assertEqual(
                set(entry) - {"name", "source", "description", "minClientVersions"},
                set(),
            )

    def test_plugin_packages_every_skill_exactly_once(self) -> None:
        actual = {
            path.name
            for path in (ROOT / "skills").iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        }
        self.assertEqual(actual, EXPECTED_SKILLS)
        self.assertFalse((ROOT / "organize-screenshots").exists())

    def test_packaged_skills_have_no_machine_or_host_private_paths(self) -> None:
        forbidden_literals = ("~/.claude/", "~/.codex/", "~/.cursor/")
        personal_path = re.compile(r"/(?:Users|Volumes)/")
        for path in (ROOT / "skills").rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            relative = path.relative_to(ROOT)
            for token in forbidden_literals:
                with self.subTest(path=relative, token=token):
                    self.assertNotIn(token, text)
            with self.subTest(path=relative, pattern="personal absolute path"):
                self.assertIsNone(personal_path.search(text))

    def test_register_is_read_only_and_prints_all_host_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            home = Path(temp_name)
            before = list(home.rglob("*"))
            env = dict(os.environ, HOME=str(home))
            completed = subprocess.run(
                ["just", "--justfile", str(ROOT / "justfile"), "register"],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertEqual(list(home.rglob("*")), before)

        output = completed.stdout
        self.assertIn("SINGLETON_SKILLS_PATH", output)
        self.assertIn("singleton-skills@singleton-skills", output)
        self.assertIn("codex plugin marketplace add", output)
        self.assertIn("cursor-agent plugin marketplace add", output)

    def test_new_skill_template_is_host_neutral(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            skill_dir = Path(temp_name) / "sample-skill"
            subprocess.run(
                [
                    "python3",
                    str(ROOT / "scripts" / "new_skill.py"),
                    "sample-skill",
                    str(skill_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=True,
            )
            generated = (skill_dir / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("sample-skill <argument>", generated)
        self.assertNotIn("/singleton-skills:", generated)
        self.assertNotIn("$ARGUMENTS", generated)

    def test_bump_updates_every_version_bearing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            checkout = Path(temp_name)
            shutil.copy2(ROOT / "justfile", checkout / "justfile")
            for directory in (".claude-plugin", ".cursor-plugin", ".codex-plugin"):
                shutil.copytree(ROOT / directory, checkout / directory)

            subprocess.run(
                [
                    "just",
                    "--justfile",
                    str(checkout / "justfile"),
                    "bump",
                    "ver=9.8.7",
                ],
                cwd=checkout,
                text=True,
                capture_output=True,
                check=True,
            )

            for relative in (
                ".claude-plugin/plugin.json",
                ".cursor-plugin/plugin.json",
                ".codex-plugin/plugin.json",
            ):
                self.assertEqual(read_json_from(checkout / relative)["version"], "9.8.7")
            marketplace = read_json_from(checkout / ".claude-plugin/marketplace.json")
            self.assertEqual(marketplace["plugins"][0]["version"], "9.8.7")


if __name__ == "__main__":
    unittest.main()
