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
attempt_path = output.parent / "attempt.json"
attempt = json.loads(attempt_path.read_text()) if attempt_path.exists() else None
control = prompt
if attempt:
    control += (output.parent / "phase-snapshot.json").read_text()
thread_id = f"thread-{attempt['attempt_id']}" if attempt else "thread-exact-123"
print(json.dumps({"type": "thread.started", "thread_id": thread_id}), flush=True)
if "WAIT_FOR_TEST" in control:
    time.sleep(1.0)
status = "blocked" if "RETURN_BLOCKED" in control else "clean"
task_ref = "OTHER-9" if "WRONG_TASK_RESULT" in control else "TASK-123"
if "MALFORMED_RESULT" in control:
    output.write_text("not-json", encoding="utf-8")
elif attempt:
    snapshot = json.loads((output.parent / "phase-snapshot.json").read_text())
    live = snapshot["live"]
    material = attempt["phase"] == "review" and live.get("test_scenario") == "material"
    checkpoint = {
        "branch": snapshot["identity"]["branch"],
        "head_sha": live.get("branch_head") or "head-unknown",
        "base_branch": live.get("base_branch") or "main",
        "base_sha": live.get("base_sha") or "base-unknown",
        "pull_request": "PR-123",
        "verification_head": live.get("branch_head"),
        "verification_summary": "fake verification",
        "review_id": "review-1" if attempt["phase"] == "review" else None,
        "findings_by_severity": {
            "CRITICAL": 0,
            "MAJOR": 1 if material else 0,
            "MINOR": 0 if material else 1,
            "NIT": 0,
        },
        "queued_finding_count": 1 if material else 0,
        "unhandled_finding_count": 0,
        "summary_posted": attempt["phase"] == "review",
        "residual_findings": [] if material else [{
            "fingerprint": "minor-1",
            "severity": "MINOR",
            "summary": "fake minor",
            "location": None,
        }],
    }
    common = {
        "schema_version": 3 if attempt.get("context_digest") else 2,
        "task_ref": task_ref,
        "summary": "fake worker result",
        "phase": attempt["phase"],
        "attempt_id": attempt["attempt_id"],
    }
    if attempt.get("context_digest"):
        common["context_digest"] = attempt["context_digest"]
    if "RETURN_CONFLICT" in control and attempt["phase"] in ("work", "fix"):
        result = {
            **common,
            "status": "conflict",
            "conflict": {
                "origin_phase": attempt["phase"],
                "operation": "merge",
                "base_sha": live.get("base_sha") or "base",
                "head_sha": live.get("branch_head") or "head",
                "conflicted_paths": ["src/api.rs"],
                "conflict_artifact_digest": "a" * 64,
            },
        }
    elif status == "blocked":
        result = {
            **common,
            "status": "blocked",
            "blocker": "fake blocker",
        }
    elif attempt["phase"] in ("handoff", "complete"):
        result = {
            **common,
            "status": "clean",
            "completion_kind": "merged" if attempt["phase"] == "complete" else "materially_clean",
            "cleanup_eligible": attempt["phase"] == "complete",
            "result": checkpoint,
        }
    else:
        result = {
            **common,
            "status": "checkpoint",
            "checkpoint": checkpoint,
        }
    output.write_text(json.dumps(result), encoding="utf-8")
else:
    output.write_text(json.dumps({
        "status": status,
        "task_ref": task_ref,
        "summary": "fake worker result",
    }), encoding="utf-8")
sys.exit(7 if "PROCESS_FAILURE" in control else 0)
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

    def managed_handoff(self, phase: str = "work") -> dict[str, object]:
        return {
            "mode": "managed",
            "run_id": "run-7",
            "task_ref": "TASK-123",
            "task_kind": "task",
            "worker_runtime": "tmux",
            "phase": phase,
            "runtime": {"session_name": None, "state_dir": None},
            "work_store": {"adapter": "local", "identity": "test"},
            "code_host": {
                "adapter": "github",
                "repository": self.repository_identity,
            },
            "worktree_path": str(self.worktree),
            "branch": self.branch,
            "branch_head": self.head,
            "base_branch": "main",
            "base_sha": self.head,
            "task_state": "in_progress",
            "task_owner": "worker-1",
            "pull_request": None,
            "checks": None,
            "stacked_on": {"task_ref": None, "pr": None},
        }

    def phase_snapshot(self, **live_updates: object) -> dict[str, object]:
        return {
            "schema_version": 1,
            "identity": {
                "task_ref": "TASK-123",
                "branch": self.branch,
                "worktree_path": str(self.worktree),
                "code_host_repository": self.repository_identity,
            },
            "live": {
                "task_state": "in_progress",
                "task_owner": "worker-1",
                "branch_head": self.head,
                "base_branch": "main",
                "base_sha": self.head,
                "pull_request": "PR-123",
                "checks": {"state": "success"},
                **live_updates,
            },
        }

    def inspect(self) -> dict[str, object]:
        return tmux_worker.inspect_worker(**self.common())

    def wait_dead(self, timeout: float = 5.0) -> dict[str, object]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            inspected = self.inspect()
            if inspected["pane_dead"] and inspected["exit"] is not None:
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
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", args)
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

    def test_handoff_is_resolved_into_artifacts_and_small_private_prompt(self) -> None:
        handoff = self.managed_handoff()
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
        attempt_dir = state_dir / "attempts" / "000001"
        prompt = (attempt_dir / "prompt.txt").read_text()
        self.assertNotIn('"task_ref": "TASK-123"', prompt)
        self.assertNotIn('"immutable_assignment"', prompt)
        self.assertLessEqual(len(prompt.encode()), 2 * 1024)
        self.assertIn("context_digest=", prompt)
        context_manifest = json.loads(
            (attempt_dir / "context-manifest.json").read_text()
        )
        self.assertEqual(context_manifest["schema_version"], 3)
        self.assertEqual(
            set(context_manifest["task_capsule"]),
            {"path", "sha256", "bytes", "media_type"},
        )
        schema = json.loads(
            (attempt_dir / "result-schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(schema["oneOf"]), 3)
        self.assertEqual(
            schema["oneOf"][0]["properties"]["status"], {"const": "checkpoint"}
        )
        self.assertNotIn("completion_kind", schema["oneOf"][0]["properties"])
        self.assertEqual(inspected["result"]["status"], "checkpoint")
        self.assertEqual(inspected["phase"], "work")

    def test_managed_phases_use_append_only_attempts_and_fresh_threads(self) -> None:
        launched = tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=self.managed_handoff(),
            codex_bin=str(self.fake_codex),
        )
        work = self.wait_dead()
        self.assertEqual(work["attempt_id"], "000001")
        self.assertEqual(work["phase"], "work")
        self.assertEqual(work["result"]["status"], "checkpoint")

        advanced_base = "b" * 40
        review_started = tmux_worker.advance_worker(
            **self.common(),
            phase_snapshot=self.phase_snapshot(base_sha=advanced_base),
            expected_attempt_id="000001",
            expected_checkpoint_digest=work["checkpoint_digest"],
            revalidated=True,
            codex_bin=str(self.fake_codex),
        )
        self.assertEqual(review_started["attempt_id"], "000002")
        self.assertEqual(review_started["phase"], "review")
        state_dir = Path(str(launched["state_dir"]))
        review_snapshot = json.loads(
            (state_dir / "attempts" / "000002" / "phase-snapshot.json").read_text()
        )
        self.assertEqual(review_snapshot["live"]["base_sha"], advanced_base)
        review = self.wait_dead()
        self.assertEqual(review["thread_id"], "thread-000002")

        handoff_started = tmux_worker.advance_worker(
            **self.common(),
            phase_snapshot=self.phase_snapshot(),
            expected_attempt_id="000002",
            expected_checkpoint_digest=review["checkpoint_digest"],
            revalidated=True,
            codex_bin=str(self.fake_codex),
        )
        self.assertEqual(handoff_started["phase"], "handoff")
        terminal = self.wait_dead()
        self.assertEqual(terminal["result"]["status"], "clean")
        self.assertEqual(terminal["result"]["completion_kind"], "materially_clean")
        self.assertEqual(
            sorted(path.name for path in (state_dir / "attempts").iterdir()),
            ["000001", "000002", "000003"],
        )
        for attempt_id in ("000001", "000002", "000003"):
            self.assertTrue((state_dir / "attempts" / attempt_id / "exit.json").exists())

    def test_complete_phase_maps_post_merge_finalize_to_terminal_result(self) -> None:
        handoff = self.managed_handoff(phase="complete")
        handoff["task_state"] = "in_review"
        handoff["pull_request"] = {"state": "merged", "number": 123}
        launched = tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=handoff,
            codex_bin=str(self.fake_codex),
        )
        completed = self.wait_dead()
        self.assertEqual(completed["phase"], "complete")
        self.assertEqual(completed["result"]["completion_kind"], "merged")
        schema = json.loads(
            (
                Path(str(launched["state_dir"]))
                / "attempts"
                / "000001"
                / "result-schema.json"
            ).read_text()
        )
        self.assertEqual(
            schema["oneOf"][0]["properties"]["completion_kind"]["enum"],
            ["merged"],
        )

    def test_material_review_advances_to_fix_and_stale_replay_is_rejected(self) -> None:
        tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=self.managed_handoff(),
            codex_bin=str(self.fake_codex),
        )
        work = self.wait_dead()
        tmux_worker.advance_worker(
            **self.common(),
            phase_snapshot=self.phase_snapshot(test_scenario="material"),
            expected_attempt_id="000001",
            expected_checkpoint_digest=work["checkpoint_digest"],
            revalidated=True,
            codex_bin=str(self.fake_codex),
        )
        review = self.wait_dead()
        self.assertEqual(
            review["result"]["checkpoint"]["findings_by_severity"]["MAJOR"], 1
        )
        fixed = tmux_worker.advance_worker(
            **self.common(),
            phase_snapshot=self.phase_snapshot(),
            expected_attempt_id="000002",
            expected_checkpoint_digest=review["checkpoint_digest"],
            revalidated=True,
            codex_bin=str(self.fake_codex),
        )
        self.assertEqual(fixed["phase"], "fix")
        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "stale attempt replay"):
            tmux_worker.advance_worker(
                **self.common(),
                phase_snapshot=self.phase_snapshot(),
                expected_attempt_id="000002",
                expected_checkpoint_digest=review["checkpoint_digest"],
                revalidated=True,
                codex_bin=str(self.fake_codex),
            )

    def test_work_conflict_uses_fresh_reconciler_then_returns_to_work(self) -> None:
        handoff = self.managed_handoff()
        handoff["checks"] = "RETURN_CONFLICT"
        tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=handoff,
            codex_bin=str(self.fake_codex),
        )
        conflict = self.wait_dead()
        self.assertEqual(conflict["result"]["status"], "conflict")
        self.assertEqual(conflict["phase"], "work")
        reconciled = tmux_worker.advance_worker(
            **self.common(),
            phase_snapshot=self.phase_snapshot(),
            expected_attempt_id=conflict["attempt_id"],
            expected_checkpoint_digest=conflict["transition_digest"],
            revalidated=True,
            codex_bin=str(self.fake_codex),
        )
        self.assertEqual(reconciled["phase"], "reconcile")
        reconcile_result = self.wait_dead()
        self.assertEqual(reconcile_result["result"]["status"], "checkpoint")
        returned = tmux_worker.advance_worker(
            **self.common(),
            phase_snapshot=self.phase_snapshot(),
            expected_attempt_id=reconcile_result["attempt_id"],
            expected_checkpoint_digest=reconcile_result["transition_digest"],
            revalidated=True,
            codex_bin=str(self.fake_codex),
        )
        self.assertEqual(returned["phase"], "work")
        state_dir = Path(str(returned["state_dir"]))
        attempts = sorted(path.name for path in (state_dir / "attempts").iterdir())
        self.assertEqual(attempts, ["000001", "000002", "000003"])
        self.wait_dead()

    def test_managed_advance_requires_zero_exit_and_exact_checkpoint_digest(self) -> None:
        launched = tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=self.managed_handoff(),
            codex_bin=str(self.fake_codex),
        )
        work = self.wait_dead()
        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "stale checkpoint digest"):
            tmux_worker.advance_worker(
                **self.common(),
                phase_snapshot=self.phase_snapshot(),
                expected_attempt_id="000001",
                expected_checkpoint_digest="0" * 64,
                revalidated=True,
                codex_bin=str(self.fake_codex),
            )
        state_dir = Path(str(launched["state_dir"]))
        (state_dir / "attempts" / "000001" / "exit.json").unlink()
        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "completed zero exit"):
            tmux_worker.advance_worker(
                **self.common(),
                phase_snapshot=self.phase_snapshot(),
                expected_attempt_id="000001",
                expected_checkpoint_digest=work["checkpoint_digest"],
                revalidated=True,
                codex_bin=str(self.fake_codex),
            )

    def test_controller_merges_evidence_backed_field_guide_proposals_once(self) -> None:
        launched = tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=self.managed_handoff(),
            codex_bin=str(self.fake_codex),
        )
        completed = self.wait_dead()
        state_dir = Path(str(launched["state_dir"]))
        blob_sha = self.git(
            "rev-parse", "HEAD:tracked.txt", cwd=self.worktree
        ).stdout.strip()
        proposal_path = state_dir / "attempts" / "000001" / "guide-proposals.json"
        proposal_path.write_text(
            json.dumps(
                [
                    {
                        "id": "repo.tracked",
                        "text": "tracked.txt is repository evidence.",
                        "tags": ["test"],
                        "evidence": [{"path": "tracked.txt", "blob_sha": blob_sha}],
                    }
                ]
            ),
            encoding="utf-8",
        )
        tmux_worker.advance_worker(
            **self.common(),
            phase_snapshot=self.phase_snapshot(),
            expected_attempt_id=completed["attempt_id"],
            expected_checkpoint_digest=completed["transition_digest"],
            revalidated=True,
            codex_bin=str(self.fake_codex),
        )
        manifest = json.loads((state_dir / "manifest.json").read_text())
        guide = json.loads(Path(manifest["coordination"]["field_guide"]).read_text())
        self.assertEqual([item["id"] for item in guide["entries"]], ["repo.tracked"])
        marker = state_dir / "attempts" / "000001" / "guide-merged.json"
        self.assertTrue(marker.exists())

    def test_managed_checkpoint_rejects_partial_and_extra_fields(self) -> None:
        launched = tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=self.managed_handoff(),
            codex_bin=str(self.fake_codex),
        )
        completed = self.wait_dead()
        state_dir = Path(str(launched["state_dir"]))
        result_path = state_dir / "attempts" / "000001" / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["unexpected"] = True
        result_path.write_text(json.dumps(result), encoding="utf-8")
        inspected = self.inspect()
        self.assertEqual(inspected["result"]["status"], "failed")
        self.assertIsNone(inspected["checkpoint_digest"])
        with self.assertRaisesRegex(tmux_worker.TmuxWorkerError, "advanceable checkpoint"):
            tmux_worker.advance_worker(
                **self.common(),
                phase_snapshot=self.phase_snapshot(),
                expected_attempt_id="000001",
                expected_checkpoint_digest=completed["checkpoint_digest"],
                revalidated=True,
                codex_bin=str(self.fake_codex),
            )

    def test_retained_v2_results_remain_readable_and_v3_digest_is_bound(self) -> None:
        launched = tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=self.managed_handoff(),
            codex_bin=str(self.fake_codex),
        )
        completed = self.wait_dead()
        result = dict(completed["result"])
        context_digest = result.pop("context_digest")
        result["schema_version"] = 2
        path = Path(str(launched["state_dir"])) / "retained-v2-result.json"
        path.write_text(json.dumps(result), encoding="utf-8")
        self.assertIsNotNone(
            tmux_worker._read_result(
                path,
                "TASK-123",
                expected_phase="work",
                expected_attempt_id="000001",
                managed=True,
                managed_version=2,
            )
        )
        result["schema_version"] = 3
        result["context_digest"] = context_digest
        path.write_text(json.dumps(result), encoding="utf-8")
        self.assertIsNone(
            tmux_worker._read_result(
                path,
                "TASK-123",
                expected_phase="work",
                expected_attempt_id="000001",
                managed=True,
                managed_version=3,
                expected_context_digest="f" * 64,
            )
        )

    def test_managed_transition_lock_rejects_concurrent_restart(self) -> None:
        launched = tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=self.managed_handoff(),
            codex_bin=str(self.fake_codex),
        )
        completed = self.wait_dead()
        state_dir = Path(str(launched["state_dir"]))
        with tmux_worker._transition_lock(state_dir):
            with self.assertRaisesRegex(
                tmux_worker.TmuxWorkerError, "transition is already in progress"
            ):
                tmux_worker.advance_worker(
                    **self.common(),
                    phase_snapshot=self.phase_snapshot(),
                    expected_attempt_id="000001",
                    expected_checkpoint_digest=completed["checkpoint_digest"],
                    revalidated=True,
                    codex_bin=str(self.fake_codex),
                )

    def test_managed_resume_reuses_thread_only_within_same_phase(self) -> None:
        handoff = self.managed_handoff()
        handoff["checks"] = "MALFORMED_RESULT"
        launched = tmux_worker.launch_worker(
            **self.common(),
            prompt="ignored",
            handoff=handoff,
            codex_bin=str(self.fake_codex),
        )
        failed = self.wait_dead()
        self.assertEqual(failed["result"]["status"], "failed")
        resumed = tmux_worker.resume_worker(
            **self.common(),
            prompt="retry interrupted phase",
            codex_bin=str(self.fake_codex),
        )
        self.assertEqual(resumed["attempt_id"], "000002")
        self.assertEqual(resumed["phase"], "work")
        self.assertEqual(resumed["thread_id"], "thread-000001")
        self.wait_dead()
        state_dir = Path(str(launched["state_dir"]))
        invocation = json.loads(
            (state_dir / "attempts" / "000002" / "fake-codex-invocations.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()[0]
        )
        self.assertIn("resume", invocation["args"])
        self.assertIn("thread-000001", invocation["args"])
        attempt = state_dir / "attempts" / "000002"
        self.assertLessEqual(len((attempt / "prompt.txt").read_bytes()), 2 * 1024)
        context_manifest = json.loads(
            (attempt / "context-manifest.json").read_text()
        )
        self.assertIn("resume_instruction", context_manifest["projections"])

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
        self.assertEqual(invocations[-1]["args"][0], "exec")
        self.assertIn("resume", invocations[-1]["args"])
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
