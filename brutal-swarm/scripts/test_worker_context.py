#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("worker_context.py")
SPEC = importlib.util.spec_from_file_location("worker_context", SCRIPT)
assert SPEC and SPEC.loader
worker_context = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker_context)


class WorkerContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_reference_has_only_path_and_checksum(self) -> None:
        reference = worker_context.store(self.root, {"large": [1, 2, 3]})
        self.assertEqual(set(reference), {"path", "sha256"})
        self.assertEqual(worker_context.load(self.root, reference), {"large": [1, 2, 3]})

    def test_rejects_escape_missing_and_checksum_mismatch(self) -> None:
        for reference, message in (
            ({"path": "../outside", "sha256": "0" * 64}, "escapes"),
            ({"path": "missing.json", "sha256": "0" * 64}, "cannot read"),
        ):
            with self.subTest(message=message), self.assertRaisesRegex(
                worker_context.ContextError, message
            ):
                worker_context.load(self.root, reference)
        reference = worker_context.store(self.root, {"value": 1})
        reference["sha256"] = "f" * 64
        with self.assertRaisesRegex(worker_context.ContextError, "checksum mismatch"):
            worker_context.load(self.root, reference)

    def test_phase_inputs_are_small_and_specific(self) -> None:
        handoff = {
            "task": {"title": "work"},
            "repository_rules": ["test"],
            "branch_state": {"head": "a"},
            "acceptance_criteria": ["works"],
            "review_context": {"diff": "large" * 1000},
            "checks": {"state": "success"},
            "finding_queue": [{"severity": "MAJOR"}],
            "checkpoint_summary": {"head": "b"},
            "provider_summary": {"pr": 1},
        }
        expected = {
            "work": {"phase_snapshot", "task", "repository_rules", "branch_state"},
            "review": {"phase_snapshot", "acceptance_criteria", "review_context", "checks"},
            "fix": {"phase_snapshot", "finding_queue"},
            "handoff": {"phase_snapshot", "checkpoint_summary", "provider_summary", "checks"},
        }
        for phase, keys in expected.items():
            with self.subTest(phase=phase):
                root = self.root / phase
                path, checksum = worker_context.build(
                    root,
                    phase=phase,
                    handoff=handoff,
                    phase_snapshot={"live": phase},
                    result_path=root / "result.json",
                )
                context = json.loads(path.read_text())
                self.assertEqual(set(context["inputs"]), keys)
                self.assertEqual(worker_context.sha256(context), checksum)
                rendered = worker_context.prompt(phase, path, checksum, root / "result.json")
                self.assertLessEqual(len(rendered.encode()), 2048)
                self.assertNotIn("large" * 10, rendered)


if __name__ == "__main__":
    unittest.main()
