from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "singleton_repo_resolver",
    ROOT / "skills" / "dev-skill" / "scripts" / "resolve_repo.py",
)
assert SPEC and SPEC.loader
resolver = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resolver)


class RepositoryResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def checkout(self, name: str) -> Path:
        checkout = self.root / name
        (checkout / ".git").mkdir(parents=True)
        (checkout / "justfile").write_text("check:\n", encoding="utf-8")
        skill = checkout / "skills" / "dev-skill" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: dev-skill\n---\n", encoding="utf-8")
        return checkout

    def test_explicit_configuration_has_precedence(self) -> None:
        explicit = self.checkout("explicit")
        current = self.checkout("current")

        resolved = resolver.resolve_repo(
            explicit=str(explicit),
            cwd=current,
            active_skill_file=current / "skills" / "dev-skill" / "SKILL.md",
            environ={},
        )

        self.assertEqual(resolved, explicit.resolve())

    def test_environment_configuration_is_supported(self) -> None:
        configured = self.checkout("configured")

        resolved = resolver.resolve_repo(
            cwd=self.root,
            active_skill_file=self.root / "cache" / "SKILL.md",
            environ={"SINGLETON_SKILLS_PATH": str(configured)},
        )

        self.assertEqual(resolved, configured.resolve())

    def test_current_editable_checkout_is_discovered(self) -> None:
        checkout = self.checkout("checkout")
        nested = checkout / "skills" / "new-skill"
        nested.mkdir(parents=True)

        resolved = resolver.resolve_repo(
            cwd=nested,
            active_skill_file=checkout / "skills" / "dev-skill" / "SKILL.md",
            environ={},
        )

        self.assertEqual(resolved, checkout.resolve())

    def test_conflicting_checkouts_fail_closed(self) -> None:
        current = self.checkout("current")
        active = self.checkout("active")

        with self.assertRaisesRegex(resolver.ResolutionError, "multiple"):
            resolver.resolve_repo(
                cwd=current,
                active_skill_file=active / "skills" / "dev-skill" / "SKILL.md",
                environ={},
            )

    def test_non_git_plugin_cache_is_rejected(self) -> None:
        cache = self.root / "plugin-cache"
        (cache / "skills" / "dev-skill").mkdir(parents=True)
        (cache / "skills" / "dev-skill" / "SKILL.md").write_text(
            "---\nname: dev-skill\n---\n", encoding="utf-8"
        )
        (cache / "justfile").write_text("check:\n", encoding="utf-8")

        with self.assertRaisesRegex(resolver.ResolutionError, "could not find"):
            resolver.resolve_repo(
                cwd=cache,
                active_skill_file=cache / "skills" / "dev-skill" / "SKILL.md",
                environ={},
            )

    def test_invalid_explicit_path_does_not_fall_back(self) -> None:
        checkout = self.checkout("checkout")

        with self.assertRaisesRegex(resolver.ResolutionError, "does not identify"):
            resolver.resolve_repo(
                explicit=str(self.root / "missing"),
                cwd=checkout,
                active_skill_file=checkout / "skills" / "dev-skill" / "SKILL.md",
                environ={},
            )


if __name__ == "__main__":
    unittest.main()
