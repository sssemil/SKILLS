#!/usr/bin/env python3

from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("swarm_wave.py")
SPEC = importlib.util.spec_from_file_location("swarm_wave", SCRIPT)
assert SPEC and SPEC.loader
swarm_wave = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = swarm_wave
SPEC.loader.exec_module(swarm_wave)


ROOT = {"branch": "main", "sha": "a" * 40}


def graph(tasks, *, limit=10):
    return {
        "root_base": ROOT,
        "limit": limit,
        "tasks": tasks,
    }


def task(ref, *, kind="task", state="todo", blockers=None, order_key=None, **extra):
    return {
        "ref": ref,
        "kind": kind,
        "state": state,
        "order_key": order_key or ref,
        "blockers": blockers or [],
        "claimable": True,
        "decision_complete": True,
        "owned": False,
        **extra,
    }


def opened(branch, *, clean=True):
    return {
        "state": "open",
        "clean": clean,
        "branch": branch,
        "base_branch": "main",
        "head_sha": branch + "-sha",
    }


def materially_clean(branch):
    return {
        **opened(branch, clean=False),
        "review_gate": "materially_clean",
    }


class NormalizeGraphTests(unittest.TestCase):
    def test_normalizes_order_alias_head_and_owned_user(self):
        payload = graph(
            [
                task(
                    "B",
                    state="in_progress",
                    owned=True,
                    pr={
                        "state": "open",
                        "clean": True,
                        "branch": "feature-b",
                        "head_sha": "b-sha",
                    },
                ),
                task("A", kind="review_finding"),
            ]
        )
        normalized = swarm_wave.normalize_graph(payload)
        self.assertEqual([item["ref"] for item in normalized["tasks"]], ["A", "B"])
        self.assertTrue(normalized["tasks"][1]["owned"])
        self.assertEqual(normalized["tasks"][1]["pr"]["branch"], "feature-b")

    def test_rejects_duplicate_task_refs(self):
        with self.assertRaisesRegex(swarm_wave.InputError, "duplicate task refs: A"):
            swarm_wave.normalize_graph(graph([task("A"), task("A")]))

    def test_rejects_bad_root_task_fields_and_duplicate_blockers(self):
        invalid = [
            ({"root_base": {"branch": "main"}, "tasks": [], "limit": 1}, "root_base.sha"),
            (graph([task("A", kind="plan")]), r"tasks\[0\].kind"),
            (graph([task("A", state="staged")]), r"tasks\[0\].state"),
            (graph([task("A", blockers="B")]), r"tasks\[0\].blockers"),
            (graph([task("A", blockers=["B", "B"])]), "duplicate refs"),
            (graph([task("A", blockers=["A"])]), "own ref"),
            (graph([task("A", pr={"state": "open", "needs_reconcile": "yes"})]), "needs_reconcile"),
            (graph([task("A", pr={"state": "unknown"})]), "pr.state"),
            (graph([task("A", pr={"state": "open", "review_gate": "maybe"})]), "review_gate"),
        ]
        for payload, message in invalid:
            with self.subTest(message=message):
                with self.assertRaisesRegex(swarm_wave.InputError, message):
                    swarm_wave.normalize_graph(payload)

    def test_rejects_bad_limits(self):
        for value in (0, -1, True, "2"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(swarm_wave.InputError, "positive integer"):
                    swarm_wave.select_wave(graph([], limit=value))

    def test_requires_limit_from_input_or_override(self):
        payload = graph([])
        del payload["limit"]
        with self.assertRaisesRegex(swarm_wave.InputError, "limit is required"):
            swarm_wave.select_wave(payload)

    def test_accepts_numeric_order_keys(self):
        normalized = swarm_wave.normalize_graph(
            graph([task("B", order_key=20), task("A", order_key=3)])
        )
        self.assertEqual([item["ref"] for item in normalized["tasks"]], ["A", "B"])

    def test_identifies_dependency_cycles(self):
        normalized = swarm_wave.normalize_graph(
            graph([task("A", blockers=["B"]), task("B", blockers=["A"]), task("C")])
        )
        self.assertEqual(normalized["cycle_refs"], ["A", "B"])


class SelectWaveTests(unittest.TestCase):
    def test_independent_roots_are_deterministic_and_limited(self):
        result = swarm_wave.select_wave(graph([task("C"), task("A"), task("B")], limit=2))
        self.assertEqual([item["ref"] for item in result["selected"]], ["A", "B"])
        self.assertEqual(
            (result["selected"][0]["base_branch"], result["selected"][0]["base_sha"], result["selected"][0]["stacked_on"]),
            (ROOT["branch"], ROOT["sha"], None),
        )
        self.assertEqual(result["held"], [
            {"ref": "C", "kind": "task", "state": "todo", "reason": "concurrency_limit"}
        ])

    def test_single_open_clean_blocker_stacks_on_its_head(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task("A", state="in_review", pr=opened("brutal/a")),
                    task("B", blockers=["A"]),
                ]
            )
        )
        selected = result["selected"]
        self.assertEqual([item["ref"] for item in selected], ["B"])
        self.assertEqual(selected[0]["mode"], "implement")
        self.assertEqual(
            (selected[0]["base_branch"], selected[0]["base_sha"], selected[0]["stacked_on"]),
            ("brutal/a", "brutal/a-sha", "A"),
        )
        self.assertEqual(result["held"][0]["reason"], "awaiting_review")

    def test_materially_clean_blocker_is_stack_ready(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task("A", state="in_review", pr=materially_clean("brutal/a")),
                    task("B", blockers=["A"]),
                ]
            )
        )
        selected = next(item for item in result["selected"] if item["ref"] == "B")
        self.assertEqual(selected["stacked_on"], "A")

    def test_explicit_not_ready_gate_overrides_legacy_clean_flag(self):
        parent = opened("brutal/a", clean=True)
        parent["review_gate"] = "not_ready"
        result = swarm_wave.select_wave(
            graph([task("A", state="in_review", pr=parent), task("B", blockers=["A"])])
        )
        held = next(item for item in result["held"] if item["ref"] == "B")
        self.assertEqual(held["reason"], "blocker_pr_not_clean")

    def test_done_and_merged_blockers_are_satisfied(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task("A", state="done"),
                    task("B", state="in_review", pr={"state": "merged"}),
                    task("C", blockers=["A", "B"]),
                ]
            )
        )
        self.assertEqual(
            [(item["ref"], item["mode"]) for item in result["selected"]],
            [("B", "finalize"), ("C", "implement")],
        )
        self.assertIsNone(result["selected"][1]["stacked_on"])

    def test_multiple_direct_blockers_wait_until_every_pr_merges(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task("A", state="in_review", pr=opened("a")),
                    task("B", state="in_review", pr=opened("b")),
                    task("C", blockers=["B", "A"]),
                ]
            )
        )
        hold = next(item for item in result["held"] if item["ref"] == "C")
        self.assertEqual(hold["reason"], "multi_blocker_waiting_for_merges")
        self.assertEqual(hold["blockers"], ["A", "B"])

        one_merged = swarm_wave.select_wave(
            graph(
                [
                    task("A", state="done"),
                    task("B", state="in_review", pr=opened("b")),
                    task("C", blockers=["A", "B"]),
                ]
            )
        )
        hold = next(item for item in one_merged["held"] if item["ref"] == "C")
        self.assertEqual(hold["reason"], "multi_blocker_waiting_for_merges")
        self.assertEqual(hold["blockers"], ["B"])

    def test_unknown_dirty_closed_and_missing_blockers_are_held(self):
        cases = [
            (["MISSING"], [], "unknown_blocker"),
            (["A"], [task("A", state="in_review", pr=opened("a", clean=False))], "blocker_pr_not_clean"),
            (["A"], [task("A", state="in_review", pr={"state": "closed"})], "blocker_pr_closed"),
            (["A"], [task("A", state="in_progress", owned=True)], "blocker_pr_missing"),
        ]
        for blockers, parents, reason in cases:
            with self.subTest(reason=reason):
                result = swarm_wave.select_wave(graph(parents + [task("Z", blockers=blockers)]))
                hold = next(item for item in result["held"] if item["ref"] == "Z")
                self.assertEqual(hold["reason"], reason)

    def test_owned_in_progress_resumes_before_todo_and_foreign_work_holds(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task("A", state="todo"),
                    task("B", state="in_progress", owned=True),
                    task("C", state="in_progress", owned=False),
                ],
                limit=1,
            )
        )
        self.assertEqual((result["selected"][0]["ref"], result["selected"][0]["mode"]), ("B", "resume"))
        reasons = {item["ref"]: item["reason"] for item in result["held"]}
        self.assertEqual(reasons, {"A": "concurrency_limit", "C": "in_progress_not_owned"})

    def test_priority_then_order_key_break_ties_within_one_mode(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task("A", priority=2, order_key="01"),
                    task("B", priority=1, order_key="99"),
                    task("C", priority=1, order_key="02"),
                ],
                limit=3,
            )
        )
        self.assertEqual([item["ref"] for item in result["selected"]], ["C", "B", "A"])

    def test_unclaimable_and_incomplete_tasks_are_held(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task("A", claimable=False),
                    task("B", decision_complete=False),
                ]
            )
        )
        self.assertEqual(
            {item["ref"]: item["reason"] for item in result["held"]},
            {"A": "not_claimable", "B": "decision_incomplete"},
        )

    def test_review_lifecycle_actions_precede_implementation(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task("A"),
                    task("B", state="in_review", pr={"state": "merged"}),
                    task("C", state="in_review", pr={**opened("c", clean=False), "needs_reconcile": True}),
                    task("D", state="in_review", pr=opened("d")),
                ],
                limit=2,
            )
        )
        self.assertEqual(
            [(item["ref"], item["mode"]) for item in result["selected"]],
            [("B", "finalize"), ("C", "reconcile")],
        )
        reasons = {item["ref"]: item["reason"] for item in result["held"]}
        self.assertEqual(reasons, {"A": "concurrency_limit", "D": "awaiting_review"})

    def test_reconcile_after_merged_blocker_uses_root_base(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task("A", state="done"),
                    task(
                        "B",
                        state="in_review",
                        blockers=["A"],
                        pr={**opened("b"), "needs_reconcile": True},
                    ),
                ]
            )
        )
        assignment = result["selected"][0]
        self.assertEqual(assignment["mode"], "reconcile")
        self.assertEqual(
            (assignment["base_branch"], assignment["base_sha"], assignment["stacked_on"]),
            (ROOT["branch"], ROOT["sha"], None),
        )

    def test_incomplete_blocker_holds_descendant(self):
        result = swarm_wave.select_wave(
            graph(
                [
                    task(
                        "A",
                        state="in_review",
                        decision_complete=False,
                        pr=opened("a"),
                    ),
                    task("B", blockers=["A"]),
                ]
            )
        )
        hold = next(item for item in result["held"] if item["ref"] == "B")
        self.assertEqual(hold["reason"], "blocker_decision_incomplete")

    def test_terminal_states_are_reported_as_held(self):
        result = swarm_wave.select_wave(graph([task("A", state="done"), task("B", state="canceled")]))
        self.assertEqual(result["selected"], [])
        self.assertEqual(
            {item["ref"]: item["reason"] for item in result["held"]},
            {"A": "done", "B": "canceled"},
        )

    def test_dependency_cycles_are_held_explicitly(self):
        result = swarm_wave.select_wave(
            graph([task("A", blockers=["B"]), task("B", blockers=["A"]), task("C")])
        )
        self.assertEqual([item["ref"] for item in result["selected"]], ["C"])
        self.assertEqual(
            {item["ref"]: item["reason"] for item in result["held"]},
            {"A": "dependency_cycle", "B": "dependency_cycle"},
        )

    def test_cli_limit_override_and_file_output(self):
        script = Path(swarm_wave.__file__)
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.json"
            input_path.write_text(json.dumps(graph([task("B"), task("A")], limit=2)))
            completed = subprocess.run(
                [sys.executable, str(script), "-i", str(input_path), "-o", str(output_path), "-n", "1"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            output = json.loads(output_path.read_text())
            self.assertEqual([item["ref"] for item in output["selected"]], ["A"])

    def test_cli_rejects_invalid_json(self):
        completed = subprocess.run(
            [sys.executable, str(Path(swarm_wave.__file__))],
            input="{",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("invalid JSON", completed.stderr)


if __name__ == "__main__":
    unittest.main()
