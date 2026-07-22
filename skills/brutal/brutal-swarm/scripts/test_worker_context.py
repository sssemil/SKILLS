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
    def test_writes_one_phase_specific_context_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            attempt = Path(directory)
            path = worker_context.build(
                attempt,
                phase="fix",
                handoff={"finding_queue": [{"severity": "MAJOR"}], "task": "unused"},
                phase_snapshot={"live": {"head": "abc"}},
                result_path=attempt / "result.json",
            )
            context = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(path, attempt / "context.json")
            self.assertEqual(set(context["inputs"]), {"finding_queue"})
            prompt = worker_context.prompt("fix", path, attempt / "result.json")
            self.assertLessEqual(len(prompt.encode()), 2048)
            self.assertNotIn("MAJOR", prompt)

    def test_preserves_dot_spec_assignment_for_every_phase(self) -> None:
        dot_spec = {
            "change_id": "dot-7",
            "delta_digest": "abc",
            "base_specs": {"billing": "def"},
            "operations": [{"op": "replace"}],
            "activates": ["billing.idempotency"],
            "independent_verify": ["./scripts/verify-contracts"],
        }
        with tempfile.TemporaryDirectory() as directory:
            for phase in worker_context.PHASE_KEYS:
                attempt = Path(directory) / phase
                attempt.mkdir()
                path = worker_context.build(
                    attempt,
                    phase=phase,
                    handoff={"dot_spec": dot_spec},
                    phase_snapshot={},
                    result_path=attempt / "result.json",
                )
                context = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(context["inputs"]["dot_spec"], dot_spec)


if __name__ == "__main__":
    unittest.main()
