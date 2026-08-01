from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "git_triage_helper", SKILL_DIR / "scripts" / "git_triage.py"
)
assert SPEC and SPEC.loader
triage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = triage
SPEC.loader.exec_module(triage)


class GitTriageBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sequence = 0

    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode:
            self.fail(f"git {' '.join(args)} failed:\n{result.stderr}")
        return result.stdout.strip()

    def configure(self, repo: Path) -> None:
        self.git(repo, "config", "user.name", "Fixture User")
        self.git(repo, "config", "user.email", "fixture@example.invalid")

    def commit(self, repo: Path, label: str) -> None:
        self.sequence += 1
        path = repo / f"fixture-{self.sequence}.txt"
        path.write_text(f"{label}\n", encoding="utf-8")
        self.git(repo, "add", "--", path.name)
        self.git(repo, "commit", "-m", label)

    def make_remote_fixture(self, name: str) -> tuple[Path, Path, Path]:
        remote = self.root / f"{name}.git"
        seed = self.root / f"{name}-seed"
        repo = self.root / f"{name}-repo"
        peer = self.root / f"{name}-peer"
        self.git(self.root, "init", "--bare", str(remote))
        self.git(self.root, "init", "-b", "main", str(seed))
        self.configure(seed)
        self.commit(seed, "seed")
        self.git(seed, "remote", "add", "origin", str(remote))
        self.git(seed, "push", "-u", "origin", "main")
        self.git(remote, "symbolic-ref", "HEAD", "refs/heads/main")
        self.git(self.root, "clone", str(remote), str(repo))
        self.git(self.root, "clone", str(remote), str(peer))
        self.configure(repo)
        self.configure(peer)
        return remote, repo, peer

    @staticmethod
    def branch(snapshot: dict[str, object], name: str) -> dict[str, object]:
        branches = snapshot["branches"]
        assert isinstance(branches, list)
        return next(item for item in branches if item["name"] == name)

    def test_clean_ahead_behind_and_diverged_classification(self) -> None:
        _, repo, peer = self.make_remote_fixture("relationships")

        clean = triage.collect(repo)
        self.assertIn(self.branch(clean, "main"), clean["categories"]["clean"])

        self.commit(repo, "local ahead")
        ahead = triage.collect(repo)
        self.assertEqual(
            (
                self.branch(ahead, "main")["ahead"],
                self.branch(ahead, "main")["behind"],
            ),
            (1, 0),
        )
        self.assertIn(self.branch(ahead, "main"), ahead["categories"]["needs_push"])

        self.git(repo, "reset", "--hard", "origin/main")
        self.commit(peer, "remote ahead")
        self.git(peer, "push", "origin", "main")
        self.git(repo, "fetch", "origin")
        behind = triage.collect(repo)
        self.assertEqual(
            (
                self.branch(behind, "main")["ahead"],
                self.branch(behind, "main")["behind"],
            ),
            (0, 1),
        )
        self.assertTrue(
            any(
                item["kind"] == "behind-or-diverged"
                for item in behind["categories"]["in_progress"]
            )
        )

        self.commit(repo, "local divergence")
        diverged = triage.collect(repo)
        self.assertEqual(
            (
                self.branch(diverged, "main")["ahead"],
                self.branch(diverged, "main")["behind"],
            ),
            (1, 1),
        )
        self.assertIn(self.branch(diverged, "main"), diverged["categories"]["needs_push"])
        self.assertTrue(
            any(
                item["kind"] == "behind-or-diverged"
                for item in diverged["categories"]["in_progress"]
            )
        )

    def test_detached_stash_and_additional_worktree_are_reported(self) -> None:
        _, repo, _ = self.make_remote_fixture("parked")
        (repo / "fixture-1.txt").write_text("dirty\n", encoding="utf-8")
        self.git(repo, "stash", "push", "-m", "parked fixture")
        worktree = self.root / "linked-worktree"
        self.git(repo, "worktree", "add", "-b", "feature", str(worktree))
        self.git(repo, "checkout", "--detach", "HEAD")

        snapshot = triage.collect(repo)
        kinds = {item["kind"] for item in snapshot["categories"]["in_progress"]}
        self.assertTrue(snapshot["head"]["detached"])
        self.assertIn("detached-head", kinds)
        self.assertIn("additional-worktree", kinds)
        self.assertEqual(len(snapshot["categories"]["stashed"]), 1)
        self.assertIn("parked fixture", snapshot["categories"]["stashed"][0])

    def test_multiple_remote_and_no_remote_rules(self) -> None:
        repo = self.root / "local"
        self.git(self.root, "init", "-b", "main", str(repo))
        self.configure(repo)
        self.commit(repo, "local only")

        no_remote = triage.collect(repo)
        self.assertEqual(no_remote["remotes"], [])
        self.assertEqual(no_remote["categories"]["elsewhere"], [])
        self.assertEqual(
            [item["name"] for item in no_remote["categories"]["needs_push"]],
            ["main"],
        )
        with self.assertRaisesRegex(triage.TriageError, "no remote"):
            triage.collect(repo, refresh=True, approve_refresh=True)

        for name in ("alpha", "beta"):
            remote = self.root / f"{name}.git"
            self.git(self.root, "init", "--bare", str(remote))
            self.git(repo, "remote", "add", name, str(remote))
        multiple = triage.collect(repo)
        self.assertEqual(multiple["remotes"], ["alpha", "beta"])
        with self.assertRaisesRegex(triage.TriageError, "ambiguous"):
            triage.collect(repo, refresh=True, approve_refresh=True)

    def test_unborn_branch_is_explicitly_in_progress(self) -> None:
        repo = self.root / "unborn"
        self.git(self.root, "init", "-b", "main", str(repo))

        snapshot = triage.collect(repo)

        self.assertEqual(snapshot["head"]["branch"], "main")
        self.assertIsNone(snapshot["head"]["commit"])
        self.assertTrue(snapshot["head"]["unborn"])
        self.assertIn(
            {"kind": "unborn-head", "branch": "main"},
            snapshot["categories"]["in_progress"],
        )

    def test_refresh_is_gated_and_reclassifies_from_fresh_local_remote_refs(self) -> None:
        remote, repo, peer = self.make_remote_fixture("refresh")
        self.commit(peer, "new remote commit")
        self.git(peer, "push", "origin", "main")

        stale = triage.collect(repo)
        self.assertEqual(stale["snapshot"], "local-only")
        self.assertEqual(self.branch(stale, "main")["behind"], 0)
        with self.assertRaisesRegex(triage.TriageError, "explicit approval"):
            triage.collect(repo, refresh=True)
        self.assertEqual(
            self.git(repo, "rev-parse", "origin/main"),
            self.git(repo, "rev-parse", "HEAD"),
        )

        refreshed = triage.collect(repo, refresh=True, approve_refresh=True)
        self.assertEqual(refreshed["snapshot"], "refreshed")
        self.assertEqual(refreshed["refreshed_from"], "origin")
        self.assertEqual(self.branch(refreshed, "main")["behind"], 1)
        self.assertEqual(self.git(repo, "remote", "get-url", "origin"), str(remote))


if __name__ == "__main__":
    unittest.main()
