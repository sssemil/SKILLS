#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("scoped_edit.py")
SPEC = importlib.util.spec_from_file_location("scoped_edit", SCRIPT)
assert SPEC and SPEC.loader
scoped_edit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scoped_edit)


FAKE = """#!/usr/bin/env python3
import sys
from pathlib import Path
prompt = sys.stdin.read()
target = Path('../../outside.txt') if 'OUTSIDE' in prompt else Path('inside.txt')
target.write_text('changed')
"""


class ScopedEditTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        (self.repo / "src" / "api").mkdir(parents=True)
        subprocess.run(["git", "-C", str(self.repo), "init"], check=True, capture_output=True)
        subprocess.run(
            [
                "git", "-C", str(self.repo), "-c", "user.name=Test",
                "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "init",
            ],
            check=True,
            capture_output=True,
        )
        self.command = self.root / "safe-codex-test"
        self.command.write_text(FAKE)
        self.command.chmod(self.command.stat().st_mode | stat.S_IXUSR)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_validates_writable_directory(self) -> None:
        for value in ("/tmp", "../src", "missing"):
            with self.subTest(value=value), self.assertRaises(scoped_edit.ScopedEditError):
                scoped_edit.resolve_directory(self.repo, value)

    def test_runs_child_inside_directory_without_git_authority(self) -> None:
        result = scoped_edit.run(
            self.repo, "src/api", [str(self.command)], "edit inside"
        )
        self.assertEqual(result["changed_paths"], ["src/api/inside.txt"])
        self.assertTrue((self.repo / "src/api/inside.txt").exists())

    def test_blocks_missing_command_and_outside_change(self) -> None:
        with self.assertRaisesRegex(scoped_edit.ScopedEditError, "not found"):
            scoped_edit.run(self.repo, "src/api", ["definitely-missing-safe-codex"], "x")
        with self.assertRaisesRegex(scoped_edit.ScopedEditError, "outside writable"):
            scoped_edit.run(self.repo, "src/api", [str(self.command)], "OUTSIDE")
        self.assertTrue((self.repo / "outside.txt").exists(), "worktree is preserved")

    def test_requires_clean_worktree(self) -> None:
        (self.repo / "dirty.txt").write_text("dirty")
        with self.assertRaisesRegex(scoped_edit.ScopedEditError, "clean worktree"):
            scoped_edit.run(self.repo, "src/api", [str(self.command)], "inside")


if __name__ == "__main__":
    unittest.main()
