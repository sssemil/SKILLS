#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("worktree_manager.py")
SPEC = importlib.util.spec_from_file_location("worktree_manager", SCRIPT)
assert SPEC and SPEC.loader
worktree_manager = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = worktree_manager
SPEC.loader.exec_module(worktree_manager)


class WorktreeManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "project"
        self.repo.mkdir()
        self.git("init")
        self.git("config", "user.name", "Brutal Test")
        self.git("config", "user.email", "brutal@example.invalid")
        (self.repo / "tracked.txt").write_text("one\n", encoding="utf-8")
        self.git("add", "tracked.txt")
        self.git("commit", "-m", "first")
        self.first = self.git("rev-parse", "HEAD").stdout.strip()
        (self.repo / "tracked.txt").write_text("two\n", encoding="utf-8")
        self.git("commit", "-am", "second")
        self.second = self.git("rev-parse", "HEAD").stdout.strip()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(cwd or self.repo), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def create(self, **overrides: str):
        values = {
            "repo_path": str(self.repo),
            "task_ref": "TASK-123",
            "title": "Exact base support!",
            "run_id": "run-7",
            "base": self.first,
        }
        values.update(overrides)
        return worktree_manager.create_worktree(**values)

    def test_branch_and_default_path_are_deterministic_and_safe(self) -> None:
        branch = worktree_manager.branch_name("TASK ../ 123", "Fix: unsafe / title")
        self.assertRegex(branch, r"^brutal/task-123-fix-unsafe-title-[0-9a-f]{8}$")
        repo = worktree_manager._repository(self.repo)
        path = worktree_manager.default_path(repo, "RUN 7", "TASK ../ 123")
        self.assertEqual(path.parent.name, "run-7")
        self.assertEqual(path.parent.parent.name, self.repo.name)
        self.assertEqual(path.parent.parent.parent.name, ".brutal-worktrees")
        self.assertFalse(path.is_relative_to(self.repo))

    def test_create_preserves_dirty_primary_and_uses_exact_base(self) -> None:
        (self.repo / "tracked.txt").write_text("dirty primary\n", encoding="utf-8")
        (self.repo / "untracked.txt").write_text("mine\n", encoding="utf-8")

        created = self.create()
        worktree = Path(created["path"])

        self.assertEqual(created["action"], "created")
        self.assertEqual(created["head"], self.first)
        self.assertEqual((worktree / "tracked.txt").read_text(encoding="utf-8"), "one\n")
        self.assertEqual((self.repo / "tracked.txt").read_text(encoding="utf-8"), "dirty primary\n")
        self.assertTrue((self.repo / "untracked.txt").exists())
        self.assertIn("tracked.txt", self.git("status", "--porcelain").stdout)

        inspected = worktree_manager.inspect_worktree(self.repo, worktree)
        self.assertTrue(inspected["registered"])
        self.assertTrue(inspected["clean"])
        self.assertEqual(inspected["task_ref"], "TASK-123")
        self.assertEqual(inspected["base_sha"], self.first)
        self.assertEqual(inspected["head"], self.first)

    def test_create_resumes_only_matching_registered_metadata(self) -> None:
        created = self.create()
        resumed = self.create()
        self.assertEqual(resumed["action"], "resumed")
        self.assertEqual(resumed["path"], created["path"])

        branch = created["branch"]
        self.git("config", f"branch.{branch}.brutalTaskRef", "OTHER-9")
        with self.assertRaisesRegex(worktree_manager.WorktreeError, "collision"):
            self.create()

    def test_create_resumes_matching_branch_after_cleanup_for_reconciliation(self) -> None:
        created = self.create()
        worktree = Path(created["path"])
        worktree_manager.cleanup_worktree(
            self.repo, worktree, "TASK-123", self.first, self.first
        )

        resumed = self.create(
            path=str(self.root / "reconcile"),
            base=self.second,
            branch=created["branch"],
        )

        self.assertEqual(resumed["action"], "resumed")
        self.assertEqual(resumed["head"], self.first)
        self.assertEqual(resumed["origin_base_sha"], self.first)
        self.assertEqual(resumed["base_sha"], self.second)
        self.assertTrue(resumed["base_changed"])

    def test_create_rejects_inside_primary_filesystem_and_branch_collisions(self) -> None:
        inside = self.repo / "nested-worktree"
        with self.assertRaisesRegex(worktree_manager.WorktreeError, "outside the primary"):
            self.create(path=str(inside))

        occupied = self.root / "occupied"
        occupied.mkdir()
        with self.assertRaisesRegex(worktree_manager.WorktreeError, "filesystem path collision"):
            self.create(path=str(occupied))

        created = self.create()
        other_path = self.root / "other-run" / "task"
        with self.assertRaisesRegex(worktree_manager.WorktreeError, "already checked out"):
            self.create(path=str(other_path), run_id="different-run")
        self.assertTrue(Path(created["path"]).exists())

    def test_registered_path_collision_is_rejected(self) -> None:
        collision = self.root / "collision"
        self.git("worktree", "add", "-b", "unrelated", str(collision), self.second)
        with self.assertRaisesRegex(worktree_manager.WorktreeError, "registered worktree collision"):
            self.create(path=str(collision))

    def test_cleanup_requires_clean_worktree_and_matching_external_heads(self) -> None:
        created = self.create()
        worktree = Path(created["path"])
        branch = created["branch"]
        (worktree / "dirty.txt").write_text("dirty\n", encoding="utf-8")

        with self.assertRaisesRegex(worktree_manager.WorktreeError, "not clean"):
            worktree_manager.cleanup_worktree(
                self.repo, worktree, "TASK-123", self.first, self.first
            )
        (worktree / "dirty.txt").unlink()

        with self.assertRaisesRegex(worktree_manager.WorktreeError, "head mismatch"):
            worktree_manager.cleanup_worktree(
                self.repo, worktree, "TASK-123", self.second, self.first
            )

        removed = worktree_manager.cleanup_worktree(
            self.repo, worktree, "TASK-123", self.first, self.first
        )
        self.assertEqual(removed["action"], "removed")
        self.assertFalse(worktree.exists())
        self.assertEqual(
            self.git("show-ref", "--verify", f"refs/heads/{branch}").returncode,
            0,
        )
        inspected = worktree_manager.inspect_worktree(self.repo, worktree)
        self.assertFalse(inspected["registered"])

    def test_cleanup_rejects_unregistered_and_primary_worktrees(self) -> None:
        with self.assertRaisesRegex(worktree_manager.WorktreeError, "not registered"):
            worktree_manager.cleanup_worktree(
                self.repo,
                self.root / "missing",
                "TASK-123",
                self.second,
                self.second,
            )
        with self.assertRaisesRegex(worktree_manager.WorktreeError, "primary"):
            worktree_manager.cleanup_worktree(
                self.repo, self.repo, "TASK-123", self.second, self.second
            )

    def test_cleanup_rejects_unrelated_or_mismatched_worktrees(self) -> None:
        unrelated = self.root / "unrelated"
        self.git("worktree", "add", "-b", "unrelated", str(unrelated), self.second)
        with self.assertRaisesRegex(worktree_manager.WorktreeError, "Brutal task metadata"):
            worktree_manager.cleanup_worktree(
                self.repo, unrelated, "TASK-123", self.second, self.second
            )

        created = self.create()
        with self.assertRaisesRegex(worktree_manager.WorktreeError, "Brutal task metadata"):
            worktree_manager.cleanup_worktree(
                self.repo,
                created["path"],
                "OTHER-9",
                self.first,
                self.first,
            )

    def test_cli_emits_json_for_success_and_failure(self) -> None:
        command = [
            sys.executable,
            str(SCRIPT),
            "create",
            "--repo",
            str(self.repo),
            "--task-ref",
            "CLI-1",
            "--title",
            "CLI task",
            "--run-id",
            "cli-run",
            "--base",
            self.first,
        ]
        success = subprocess.run(command, check=True, text=True, capture_output=True)
        self.assertTrue(json.loads(success.stdout)["ok"])

        failure = subprocess.run(command[:-1] + ["not-a-revision"], text=True, capture_output=True)
        self.assertEqual(failure.returncode, 2)
        self.assertFalse(json.loads(failure.stderr)["ok"])

        argument_failure = subprocess.run(
            [sys.executable, str(SCRIPT), "inspect"], text=True, capture_output=True
        )
        self.assertEqual(argument_failure.returncode, 2)
        self.assertFalse(json.loads(argument_failure.stderr)["ok"])


if __name__ == "__main__":
    unittest.main()
