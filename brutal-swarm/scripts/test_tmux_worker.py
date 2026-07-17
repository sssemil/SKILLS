#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path


SCRIPT = Path(__file__).with_name("tmux_worker.py")
SPEC = importlib.util.spec_from_file_location("tmux_worker", SCRIPT)
assert SPEC and SPEC.loader
tmux_worker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tmux_worker
SPEC.loader.exec_module(tmux_worker)


FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path

args = sys.argv[1:]
prompt = sys.stdin.read()
output_index = args.index("--output-last-message") + 1
output = Path(args[output_index])
output.parent.mkdir(parents=True, exist_ok=True)
with (output.parent / "fake-codex-invocations.jsonl").open("a", encoding="utf-8") as stream:
    stream.write(json.dumps({"args": args, "prompt": prompt}) + "\n")
print(json.dumps({"type": "thread.started", "thread_id": "thread-exact-123"}), flush=True)
if "WAIT_FOR_TEST" in prompt:
    time.sleep(1.0)
status = "blocked" if "RETURN_BLOCKED" in prompt else "clean"
task_ref = "OTHER-9" if "WRONG_TASK_RESULT" in prompt else "TASK-123"
if "MALFORMED_RESULT" in prompt:
    output.write_text("not-json", encoding="utf-8")
else:
    output.write_text(json.dumps({
        "status": status,
        "task_ref": task_ref,
        "summary": "fake worker result",
    }), encoding="utf-8")
sys.exit(7 if "PROCESS_FAILURE" in prompt else 0)
'''


class TmuxWorkerTest(unittest.TestCase):
    def setUp(self) -> None:
        if not shutil_which("tmux"):
            self.skipTest("tmux is not installed")
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
        self.head = self.git("rev-parse", "HEAD").stdout.strip()
        self.branch = "brutal/task-123-test-12345678"
        self.worktree = self.root / ".brutal-worktrees" / "project" / "run" / "task"
        self.worktree.parent.mkdir(parents=True)
        self.git("worktree", "add", "-b", self.branch, str(self.worktree), self.head)
        self.git("config", f"branch.{self.branch}.brutalTaskRef", "TASK-123")
        self.git("config", f"branch.{self.branch}.brutalBaseSha", self.head)
        self.fake_codex = self.root / "fake-codex"
        self.fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
        self.fake_codex.chmod(self.fake_codex.stat().st_mode | stat.S_IXUSR)
        self.socket = f"brutal-test-{uuid.uuid4().hex}"
        self.repository_identity = "github:example/project"

    def tearDown(self) -> None:
        if hasattr(self, "socket"):
            subprocess.run(
                ["tmux", "-L", self.socket, "kill-server"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        if hasattr(self, "temporary"):
            self.temporary.cleanup()

    def git(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(cwd or self.repo), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def common(self) -> dict[str, object]:
        return {
            "repo_path": self.repo,
            "worktree_path": self.worktree,
            "task_ref": "TASK-123",
            "branch": self.branch,
            "repository_identity": self.repository_identity,
            "tmux_socket": self.socket,
        }

    def launch(self, prompt: str = "do the exact task") -> dict[str, object]:
        return tmux_worker.launch_worker(
            **self.common(), prompt=prompt, codex_bin=str(self.fake_codex)
        )

    def inspect(self) -> dict[str, object]:
        return tmux_worker.inspect_worker(**self.common())

    def wait_dead(self, timeout: float = 5.0) -> dict[str, object]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            inspected = self.inspect()
            if inspected["pane_dead"]:
                return inspected
            time.sleep(0.05)
        self.fail("tmux worker did not exit")

    def test_stable_name_and_runtime_directory_are_deterministic_and_external(self) -> None:
        first = tmux_worker.stable_session_name(self.repository_identity, "TASK-123")
        second = tmux_worker.stable_session_name(self.repository_identity, "TASK-123")
        different = tmux_worker.stable_session_name(self.repository_identity, "TASK-124")
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertRegex(first, r"^brutal-[a-z0-9-]+-[0-9a-f]{16}$")

        launched = self.launch()
        state_dir = Path(str(launched["state_dir"]))
        self.assertEqual(state_dir.parents[1].name, ".brutal-runs")
        self.assertFalse(state_dir.is_relative_to(self.worktree))
        self.wait_dead()

    def test_launch_retains_dead_session_and_records_non_ephemeral_codex_result(self) -> None:
        launched = self.launch()
        state_dir = Path(str(launched["state_dir"]))
        inspected = self.wait_dead()

        self.assertTrue(inspected["session_exists"])
        self.assertFalse(inspected["running"])
        self.assertTrue(inspected["pane_dead"])
        self.assertEqual(inspected["thread_id"], "thread-exact-123")
        self.assertEqual(inspected["result"]["status"], "clean")
        self.assertEqual(inspected["exit"]["exit_code"], 0)
        captured = subprocess.run(
            launched["capture_argv"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertIn('"type": "thread.started"', captured.stdout)
        invocation = json.loads(
            (state_dir / "fake-codex-invocations.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        args = invocation["args"]
        self.assertEqual(args[0], "exec")
        self.assertIn("--json", args)
        self.assertIn("--output-schema", args)
        self.assertIn("--output-last-message", args)
        self.assertNotIn("--ephemeral", args)
        self.assertNotIn("--sandbox", args)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", args)
        self.assertEqual(stat.S_IMODE((state_dir / "prompt.txt").stat().st_mode), 0o600)

    def test_live_and_dead_panes_report_running_for_concurrency(self) -> None:
        self.launch("WAIT_FOR_TEST")
        live = self.inspect()
        self.assertTrue(live["running"])
        self.assertFalse(live["pane_dead"])

        dead = self.wait_dead()
        self.assertFalse(dead["running"])
        self.assertTrue(dead["pane_dead"])
        self.assertTrue(dead["session_exists"], "dead retained session still exists")

    def test_two_task_sessions_run_concurrently_and_remain_distinct(self) -> None:
        second_branch = "brutal/task-124-test-87654321"
        second_worktree = self.root / ".brutal-worktrees" / "project" / "run" / "task-2"
        self.git("worktree", "add", "-b", second_branch, str(second_worktree), self.head)
        self.git("config", f"branch.{second_branch}.brutalTaskRef", "TASK-124")
        self.git("config", f"branch.{second_branch}.brutalBaseSha", self.head)

        first = self.launch("WAIT_FOR_TEST")
        second_common = {
            **self.common(),
            "worktree_path": second_worktree,
            "task_ref": "TASK-124",
            "branch": second_branch,
        }
        second = tmux_worker.launch_worker(
            **second_common,
            prompt="WAIT_FOR_TEST",
            codex_bin=str(self.fake_codex),
        )
        self.assertNotEqual(first["session_name"], second["session_name"])
        self.assertTrue(self.inspect()["running"])
        self.assertTrue(tmux_worker.inspect_worker(**second_common)["running"])

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            first_state = self.inspect()
            second_state = tmux_worker.inspect_worker(**second_common)
            if first_state["pane_dead"] and second_state["pane_dead"]:
                break
            time.sleep(0.05)
        else:
            self.fail("concurrent tmux workers did not both exit")
        self.assertTrue(first_state["session_exists"])
        self.assertTrue(second_state["session_exists"])

    def test_handoff_is_resolved_copied_and_sent_through_private_prompt(self) -> None:
        handoff = {
            "mode": "managed",
            "run_id": "run-7",
            "task_ref": "TASK-123",
            "task_kind": "task",
            "worker_runtime": "tmux",
            "runtime": {"session_name": None, "state_dir": None},
            "work_store": {"adapter": "local", "identity": "test"},
            "code_host": {"adapter": "github", "repository": self.repository_identity},
            "worktree_path": str(self.worktree),
            "branch": self.branch,
            "branch_head": self.head,
            "base_branch": "main",
            "base_sha": self.head,
            "stacked_on": {"task_ref": None, "pr": None},
        }
        original = json.loads(json.dumps(handoff))
        launched = tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=handoff,
            codex_bin=str(self.fake_codex),
        )
        inspected = self.wait_dead()
        self.assertEqual(handoff, original, "caller handoff remains immutable")
        state_dir = Path(str(launched["state_dir"]))
        manifest = json.loads((state_dir / "manifest.json").read_text(encoding="utf-8"))
        resolved = manifest["handoff"]
        self.assertEqual(resolved["runtime"]["session_name"], launched["session_name"])
        self.assertEqual(resolved["runtime"]["state_dir"], launched["state_dir"])
        self.assertIn('"task_ref": "TASK-123"', (state_dir / "prompt.txt").read_text())
        self.assertEqual(inspected["result"]["status"], "clean")

    def test_resume_uses_exact_recorded_thread_and_fresh_requires_revalidation(self) -> None:
        launched = self.launch()
        self.wait_dead()
        resumed = tmux_worker.resume_worker(
            **self.common(), prompt="continue exact task", codex_bin=str(self.fake_codex)
        )
        self.assertEqual(resumed["action"], "resumed")
        self.assertEqual(resumed["thread_id"], "thread-exact-123")
        self.wait_dead()
        state_dir = Path(str(launched["state_dir"]))
        invocations = [
            json.loads(line)
            for line in (state_dir / "fake-codex-invocations.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(invocations[-1]["args"][0:2], ["exec", "resume"])
        self.assertIn("thread-exact-123", invocations[-1]["args"])

        (state_dir / "events.jsonl").unlink()
        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "no exact Codex thread"):
            tmux_worker.resume_worker(
                **self.common(), prompt="new", codex_bin=str(self.fake_codex)
            )
        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "caller revalidation"):
            tmux_worker.resume_worker(
                **self.common(),
                prompt="new",
                fresh=True,
                codex_bin=str(self.fake_codex),
            )
        restarted = tmux_worker.resume_worker(
            **self.common(),
            prompt="new",
            fresh=True,
            revalidated=True,
            codex_bin=str(self.fake_codex),
        )
        self.assertEqual(restarted["action"], "restarted_fresh")
        self.wait_dead()

    def test_resume_rejects_running_pane(self) -> None:
        self.launch("WAIT_FOR_TEST")
        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "running worker pane"):
            tmux_worker.resume_worker(
                **self.common(), prompt="do not duplicate", codex_bin=str(self.fake_codex)
            )
        self.wait_dead()

    def test_fresh_revalidated_resume_recreates_lost_tmux_server(self) -> None:
        self.launch()
        self.wait_dead()
        subprocess.run(
            ["tmux", "-L", self.socket, "kill-server"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        restarted = tmux_worker.resume_worker(
            **self.common(),
            prompt="revalidated exact task",
            fresh=True,
            revalidated=True,
            codex_bin=str(self.fake_codex),
        )
        self.assertEqual(restarted["action"], "restarted_fresh")
        self.wait_dead()

    def test_cleanup_is_exact_dead_only_and_preserves_all_runtime_files(self) -> None:
        launched = self.launch()
        self.wait_dead()
        state_dir = Path(str(launched["state_dir"]))
        files_before = {path.name for path in state_dir.iterdir()}
        self.assertIn("events.jsonl", files_before)
        self.assertIn("result.json", files_before)

        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "manifest"):
            tmux_worker.cleanup_worker(
                **{**self.common(), "task_ref": "OTHER-9"}
            )
        self.git("worktree", "remove", str(self.worktree))
        after_removal = self.inspect()
        self.assertFalse(after_removal["running"])
        discovered = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "inspect",
                "--repo",
                str(self.repo),
                "--task-ref",
                "TASK-123",
                "--repository-identity",
                self.repository_identity,
                "--tmux-socket",
                self.socket,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        discovered_result = json.loads(discovered.stdout)
        self.assertEqual(discovered_result["worktree"], str(self.worktree))
        self.assertEqual(discovered_result["branch"], self.branch)
        cleaned = tmux_worker.cleanup_worker(**self.common())
        self.assertTrue(cleaned["logs_preserved"])
        self.assertTrue(cleaned["worktree_preserved"])
        self.assertTrue(state_dir.is_dir())
        self.assertEqual(files_before, {path.name for path in state_dir.iterdir()})
        self.assertFalse(self.worktree.exists())
        self.assertFalse(self.inspect_after_cleanup_session_exists(state_dir))

    def inspect_after_cleanup_session_exists(self, state_dir: Path) -> bool:
        manifest = json.loads((state_dir / "manifest.json").read_text(encoding="utf-8"))
        return subprocess.run(
            ["tmux", "-L", self.socket, "has-session", "-t", f"={manifest['session_name']}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode == 0

    def test_identity_and_tmux_metadata_mismatches_are_rejected(self) -> None:
        launched = self.launch()
        self.wait_dead()
        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "manifest"):
            tmux_worker.inspect_worker(**{**self.common(), "task_ref": "OTHER-9"})
        subprocess.run(
            [
                "tmux",
                "-L",
                self.socket,
                "set-option",
                "-t",
                str(launched["session_name"]),
                "@brutal_branch",
                "brutal/other",
            ],
            check=True,
        )
        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "metadata mismatch"):
            self.inspect()

    def test_mismatched_structured_result_is_reported_failed(self) -> None:
        self.launch("WRONG_TASK_RESULT")
        inspected = self.wait_dead()
        self.assertEqual(inspected["result"]["status"], "failed")
        self.assertFalse(inspected["exit"]["structured_result_valid"])

    def test_nonzero_exit_is_failed_even_with_a_structured_clean_result(self) -> None:
        self.launch("PROCESS_FAILURE")
        inspected = self.wait_dead()
        self.assertEqual(inspected["exit"]["exit_code"], 7)
        self.assertTrue(inspected["exit"]["structured_result_valid"])
        self.assertEqual(inspected["reported_result"]["status"], "clean")
        self.assertEqual(inspected["result"]["status"], "failed")

    def test_malformed_result_is_reported_failed(self) -> None:
        self.launch("MALFORMED_RESULT")
        inspected = self.wait_dead()
        self.assertEqual(inspected["exit"]["exit_code"], 0)
        self.assertFalse(inspected["exit"]["structured_result_valid"])
        self.assertEqual(inspected["result"]["status"], "failed")

    def test_cli_accepts_yaml_handoff_and_always_emits_json(self) -> None:
        handoff = self.root / "handoff.yaml"
        handoff.write_text(
            "\n".join(
                [
                    "mode: managed",
                    "run_id: run-7",
                    "task_ref: TASK-123",
                    "task_kind: task",
                    "worker_runtime: tmux",
                    "code_host:",
                    "  adapter: github",
                    f"  repository: {self.repository_identity}",
                    f"worktree_path: {self.worktree}",
                    f"branch: {self.branch}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        command = [
            sys.executable,
            str(SCRIPT),
            "launch",
            "--repo",
            str(self.repo),
            "--handoff",
            str(handoff),
            "--tmux-socket",
            self.socket,
            "--codex-bin",
            str(self.fake_codex),
        ]
        success = subprocess.run(command, text=True, capture_output=True, check=True)
        self.assertTrue(json.loads(success.stdout)["ok"])
        self.wait_dead()

        failure = subprocess.run(
            [sys.executable, str(SCRIPT), "inspect", "--repo", str(self.repo)],
            text=True,
            capture_output=True,
        )
        self.assertEqual(failure.returncode, 2)
        self.assertFalse(json.loads(failure.stderr)["ok"])


def shutil_which(command: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / command
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


if __name__ == "__main__":
    unittest.main()
