from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "skill_installer", REPOSITORY_ROOT / "scripts" / "skill_installer.py"
)
assert SPEC and SPEC.loader
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


class SkillInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "checkout"
        skills = self.repo / "skills"
        skills.mkdir(parents=True)
        self.skill_names = ["git-triage", "imessage-search", "other-skill"]
        for name in self.skill_names:
            (skills / name).mkdir()
        (self.repo / "supported-skills.txt").write_text(
            "git-triage\nimessage-search\n", encoding="utf-8"
        )
        self.shared = self.root / "shared"
        self.claude = self.root / "claude"
        self.roots = {"shared": self.shared, "claude": self.claude}

    def test_default_set_installs_only_supported_skills_with_versioned_provenance(self) -> None:
        changed = installer.install(self.repo, "default", "shared", self.roots)

        self.assertEqual([item.skill_name for item in changed], ["git-triage", "imessage-search"])
        self.assertTrue((self.shared / "git-triage").is_symlink())
        self.assertTrue((self.shared / "imessage-search").is_symlink())
        self.assertFalse(os.path.lexists(self.shared / "other-skill"))
        provenance = json.loads((self.repo / installer.PROVENANCE_NAME).read_bytes())
        self.assertEqual(provenance["schema_version"], 1)
        self.assertEqual(provenance["checkout_realpath"], str(self.repo.resolve()))
        self.assertEqual(len(provenance["records"]), 2)
        for record in provenance["records"]:
            self.assertEqual(record["checkout_realpath"], str(self.repo.resolve()))
            self.assertEqual(record["target_root"], str(self.shared.resolve()))
            self.assertEqual(record["target_kind"], "shared")
            self.assertEqual(record["installed_link_value"], record["source_path"])

    def test_all_set_and_all_targets_install_every_skill(self) -> None:
        changed = installer.install(self.repo, "all", "all", self.roots)

        self.assertEqual(len(changed), len(self.skill_names) * 2)
        for root in (self.shared, self.claude):
            self.assertEqual(
                sorted(path.name for path in root.iterdir()), sorted(self.skill_names)
            )

    def test_override_precedence_is_explicit_then_environment_then_default(self) -> None:
        env = {
            "HOME": str(self.root / "home"),
            "SINGLETON_SHARED_SKILLS_DIR": str(self.root / "env-shared"),
            "SINGLETON_CLAUDE_SKILLS_DIR": str(self.root / "env-claude"),
        }
        roots = installer.resolve_roots(str(self.root / "explicit"), None, env)
        self.assertEqual(roots["shared"], (self.root / "explicit").resolve())
        self.assertEqual(roots["claude"], (self.root / "env-claude").resolve())

        defaults = installer.resolve_roots(None, None, {"HOME": str(self.root / "home")})
        self.assertEqual(
            defaults["shared"], (self.root / "home" / ".agents" / "skills").resolve()
        )
        self.assertEqual(
            defaults["claude"], (self.root / "home" / ".claude" / "skills").resolve()
        )

    def test_refuses_foreign_file_and_foreign_symlink_without_changing_them(self) -> None:
        self.shared.mkdir()
        foreign_file = self.shared / "git-triage"
        foreign_file.write_text("foreign", encoding="utf-8")
        with self.assertRaisesRegex(installer.InstallerError, "foreign install target"):
            installer.install(self.repo, "default", "shared", self.roots)
        self.assertEqual(foreign_file.read_text(encoding="utf-8"), "foreign")
        self.assertFalse((self.repo / installer.PROVENANCE_NAME).exists())

        foreign_file.unlink()
        foreign_source = self.root / "foreign-source"
        foreign_source.mkdir()
        os.symlink(foreign_source, foreign_file)
        with self.assertRaisesRegex(installer.InstallerError, "foreign install target"):
            installer.install(self.repo, "default", "shared", self.roots)
        self.assertEqual(os.readlink(foreign_file), str(foreign_source))

    def test_refuses_malformed_or_symlinked_provenance(self) -> None:
        provenance_path = self.repo / installer.PROVENANCE_NAME
        provenance_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "checkout_realpath": str(self.repo.resolve()),
                    "records": [{"target_path": str(self.shared / "git-triage")}],
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(installer.InstallerError, "invalid ownership record"):
            installer.install(self.repo, "default", "shared", self.roots)

        provenance_path.unlink()
        foreign_provenance = self.root / "foreign-provenance"
        foreign_provenance.write_text("{}", encoding="utf-8")
        os.symlink(foreign_provenance, provenance_path)
        with self.assertRaisesRegex(installer.InstallerError, "must not be a symlink"):
            installer.install(self.repo, "default", "shared", self.roots)

    def test_manifest_rejects_path_traversal_and_non_basename_entries(self) -> None:
        manifest = self.repo / "supported-skills.txt"
        unsafe_names = (
            "../outside",
            "skills/git-triage",
            "skills\\git-triage",
            "/absolute",
            ".",
            "..",
        )
        for name in unsafe_names:
            with self.subTest(name=name):
                manifest.write_text(f"{name}\n", encoding="utf-8")
                with self.assertRaisesRegex(installer.InstallerError, "unsafe skill name"):
                    installer.install(self.repo, "default", "shared", self.roots)
                self.assertFalse(self.shared.exists())
                self.assertFalse((self.repo / installer.PROVENANCE_NAME).exists())

    def test_manifest_rejects_a_skill_symlink_that_escapes_the_skills_root(self) -> None:
        escaping = self.repo / "skills" / "escaping"
        outside = self.root / "outside"
        outside.mkdir()
        os.symlink(outside, escaping)
        (self.repo / "supported-skills.txt").write_text("escaping\n", encoding="utf-8")

        with self.assertRaisesRegex(installer.InstallerError, "escapes its required root"):
            installer.install(self.repo, "default", "shared", self.roots)

        self.assertFalse(self.shared.exists())
        self.assertFalse((self.repo / installer.PROVENANCE_NAME).exists())

    def test_uninstall_removes_only_owned_selected_links(self) -> None:
        installer.install(self.repo, "all", "shared", self.roots)

        removed = installer.uninstall(self.repo, "default", "shared", self.roots)

        self.assertEqual([item.skill_name for item in removed], ["git-triage", "imessage-search"])
        self.assertFalse(os.path.lexists(self.shared / "git-triage"))
        self.assertFalse(os.path.lexists(self.shared / "imessage-search"))
        self.assertTrue((self.shared / "other-skill").is_symlink())
        provenance = json.loads((self.repo / installer.PROVENANCE_NAME).read_bytes())
        self.assertEqual(
            [record["skill_name"] for record in provenance["records"]],
            ["other-skill"],
        )

    def test_uninstall_refuses_an_owned_link_that_was_retargeted(self) -> None:
        installer.install(self.repo, "default", "shared", self.roots)
        target = self.shared / "git-triage"
        target.unlink()
        foreign = self.root / "foreign"
        foreign.mkdir()
        os.symlink(foreign, target)

        with self.assertRaisesRegex(installer.InstallerError, "changed or foreign"):
            installer.uninstall(self.repo, "default", "shared", self.roots)
        self.assertEqual(os.readlink(target), str(foreign))
        self.assertTrue((self.shared / "imessage-search").is_symlink())

    def test_install_failure_restores_links_and_provenance_byte_for_byte(self) -> None:
        git_source = (self.repo / "skills" / "git-triage").resolve()
        canonical_shared = self.shared.resolve()
        canonical_shared.mkdir()
        git_target = canonical_shared / "git-triage"
        os.symlink(git_source, git_target)
        desired = installer.DesiredLink(
            "git-triage", "shared", canonical_shared, git_source, git_target
        )
        data = {
            "schema_version": 1,
            "checkout_realpath": str(self.repo.resolve()),
            "records": [desired.record(self.repo.resolve())],
        }
        original_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
        provenance_path = self.repo / installer.PROVENANCE_NAME
        provenance_path.write_bytes(original_bytes)
        real_write = installer._write_bytes_atomic
        calls = 0

        def fail_first_write(path: Path, content: bytes) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("injected later failure")
            real_write(path, content)

        with mock.patch.object(installer, "_write_bytes_atomic", side_effect=fail_first_write):
            with self.assertRaisesRegex(installer.InstallerError, "rolled back"):
                installer.install(self.repo, "default", "shared", self.roots)

        self.assertEqual(provenance_path.read_bytes(), original_bytes)
        self.assertEqual(os.readlink(git_target), str(git_source))
        self.assertFalse(os.path.lexists(self.shared / "imessage-search"))

    def test_install_refuses_target_created_between_preflight_and_atomic_symlink(self) -> None:
        real_symlink = os.symlink
        raced_target = self.shared.resolve() / "git-triage"

        def inject_foreign_target(
            source: str, target: str, *, dir_fd: int | None = None
        ) -> None:
            if target == "git-triage":
                raced_target.write_text("racer", encoding="utf-8")
                raise FileExistsError(str(raced_target))
            real_symlink(source, target, dir_fd=dir_fd)

        with mock.patch.object(installer.os, "symlink", side_effect=inject_foreign_target):
            with self.assertRaisesRegex(installer.InstallerError, "appeared after preflight"):
                installer.install(self.repo, "default", "shared", self.roots)

        self.assertEqual(raced_target.read_text(encoding="utf-8"), "racer")
        self.assertFalse(os.path.lexists(self.shared / "imessage-search"))
        self.assertFalse((self.repo / installer.PROVENANCE_NAME).exists())

    def test_install_revalidates_existing_owned_target_after_preflight(self) -> None:
        installer.install(self.repo, "default", "shared", self.roots)
        target = self.shared / "git-triage"
        foreign = self.root / "foreign"
        foreign.mkdir()
        real_preflight = installer._preflight_install

        def race_after_preflight(*args: object, **kwargs: object) -> None:
            real_preflight(*args, **kwargs)
            target.unlink()
            os.symlink(foreign, target)

        with mock.patch.object(installer, "_preflight_install", side_effect=race_after_preflight):
            with self.assertRaisesRegex(installer.InstallerError, "changed after preflight"):
                installer.install(self.repo, "default", "shared", self.roots)

        self.assertEqual(os.readlink(target), str(foreign))

    def test_concurrent_installs_serialize_before_reading_or_writing_provenance(self) -> None:
        real_write = installer._write_bytes_atomic
        first_in_write = threading.Event()
        release_first = threading.Event()
        second_started = threading.Event()
        errors: list[BaseException] = []

        def delayed_write(path: Path, content: bytes) -> None:
            if threading.current_thread().name == "first-installer":
                first_in_write.set()
                if not release_first.wait(timeout=5):
                    raise TimeoutError("test did not release first installer")
            real_write(path, content)

        def run(selection: str, started: threading.Event | None = None) -> None:
            if started is not None:
                started.set()
            try:
                installer.install(self.repo, selection, "shared", self.roots)
            except BaseException as exc:
                errors.append(exc)

        with mock.patch.object(
            installer, "_write_bytes_atomic", side_effect=delayed_write
        ):
            first = threading.Thread(
                target=run, args=("default",), name="first-installer"
            )
            second = threading.Thread(
                target=run,
                args=("all", second_started),
                name="second-installer",
            )
            first.start()
            self.assertTrue(first_in_write.wait(timeout=5))
            second.start()
            self.assertTrue(second_started.wait(timeout=5))
            second.join(timeout=0.1)
            self.assertTrue(second.is_alive(), "second install bypassed transaction lock")
            release_first.set()
            first.join(timeout=5)
            second.join(timeout=5)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertEqual(errors, [])
        provenance = json.loads((self.repo / installer.PROVENANCE_NAME).read_bytes())
        self.assertEqual(
            [record["skill_name"] for record in provenance["records"]],
            sorted(self.skill_names),
        )
        self.assertEqual(
            len({record["target_path"] for record in provenance["records"]}),
            len(self.skill_names),
        )

    def test_install_fails_closed_if_target_root_is_replaced_after_open(self) -> None:
        self.shared.mkdir()
        displaced = self.root / "displaced-shared"
        real_symlink = installer.RootHandle.symlink
        replaced = False

        def replace_root_after_first_link(
            handle: installer.RootHandle, source: str, name: str
        ) -> None:
            nonlocal replaced
            real_symlink(handle, source, name)
            if not replaced:
                replaced = True
                self.shared.rename(displaced)
                self.shared.mkdir()

        with mock.patch.object(
            installer.RootHandle,
            "symlink",
            autospec=True,
            side_effect=replace_root_after_first_link,
        ):
            with self.assertRaisesRegex(
                installer.InstallerError, "installation root identity changed"
            ):
                installer.install(self.repo, "default", "shared", self.roots)

        self.assertEqual(list(self.shared.iterdir()), [])
        self.assertEqual(list(displaced.iterdir()), [])
        self.assertFalse((self.repo / installer.PROVENANCE_NAME).exists())

    def test_list_reports_support_installation_and_ownership_independently(self) -> None:
        installer.install(self.repo, "default", "shared", self.roots)
        lines = installer.list_status(self.repo, "shared", self.roots)

        git_line = next(line for line in lines if "git-triage" in line)
        other_line = next(line for line in lines if "other-skill" in line)
        self.assertIn("supported=yes", git_line)
        self.assertIn("installed=yes", git_line)
        self.assertIn("owned=yes", git_line)
        self.assertIn("supported=no", other_line)
        self.assertIn("installed=no", other_line)
        self.assertIn("owned=no", other_line)


if __name__ == "__main__":
    unittest.main()
