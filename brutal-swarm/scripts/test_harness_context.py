#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import harness_context as context


def capsule() -> dict:
    return {
        "task": {
            "ref": "TASK-1",
            "kind": "task",
            "title": "Small task",
            "goal": "Make the behavior exact",
            "acceptance_criteria": ["tests pass"],
            "blockers": [],
        },
        "coordination": {
            "decisions_owned": [{"id": "api.shape", "statement": "Use JSON"}],
            "decisions_consumed": [],
            "touch_surfaces": [
                {"path": "src/api", "kind": "prefix", "parallel_safe": False}
            ],
        },
        "verification_commands": ["pytest -q"],
        "artifacts": {},
    }


class ArtifactTests(unittest.TestCase):
    def test_store_deduplicates_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first = context.store_artifact(root, {"b": 2, "a": 1})
            second = context.store_artifact(root, {"a": 1, "b": 2})
            self.assertEqual(first, second)
            self.assertTrue(context.validate_artifact_ref(root, first).is_file())

    def test_rejects_escape_and_stale_digest(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            ref = context.store_artifact(root, "hello", "text/plain")
            escaped = dict(ref, path="../outside")
            with self.assertRaises(context.ContextError):
                context.validate_artifact_ref(root, escaped)
            path = root / ref["path"]
            path.write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(context.ContextError, "mismatch"):
                context.validate_artifact_ref(root, ref)

    def test_atomic_json_replaces_complete_document(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw) / "state.json"
            context.atomic_json(destination, {"revision": 1})
            context.atomic_json(destination, {"revision": 2, "ok": True})
            self.assertEqual(
                json.loads(destination.read_text()), {"ok": True, "revision": 2}
            )


class EnvelopeTests(unittest.TestCase):
    def test_capsule_manifest_and_small_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            manifest, digest = context.build_phase_manifest(
                root,
                phase="work",
                task_capsule=capsule(),
                phase_snapshot={"head_sha": "abc"},
                projections={"field_guide": {"entries": []}},
                outputs={"result": "result.json"},
            )
            self.assertEqual(manifest["schema_version"], 3)
            for ref in (
                manifest["task_capsule"],
                manifest["phase_snapshot"],
                manifest["projections"]["field_guide"],
            ):
                context.validate_artifact_ref(root, ref)
            prompt = context.build_phase_prompt(
                "work", root / "attempts" / "000001" / "context.json", digest
            )
            self.assertLessEqual(len(prompt.encode()), context.MAX_PROMPT_BYTES)
            self.assertIn(digest, prompt)

    def test_capsule_rejects_invalid_coordination(self) -> None:
        value = capsule()
        value["coordination"]["touch_surfaces"][0]["path"] = "../secret"
        with self.assertRaises(context.ContextError):
            context.build_task_capsule(value)

    def test_decision_registry_is_normalized_and_rejects_duplicate_owners(self) -> None:
        normalized = context.normalize_decision_registry(
            [
                {"id": "z.choice", "statement": "Z"},
                {"id": "a.choice", "statement": "A"},
            ]
        )
        self.assertEqual([item["id"] for item in normalized], ["a.choice", "z.choice"])
        with self.assertRaisesRegex(context.ContextError, "duplicate owners"):
            context.normalize_decision_registry(
                [
                    {"id": "a.choice", "statement": "A"},
                    {"id": "a.choice", "statement": "B"},
                ]
            )

    def test_review_lenses_are_decorrelated(self) -> None:
        raw = {
            "acceptance": "a",
            "diff_summary": "d",
            "diff": "raw",
            "tests": "t",
            "checks": "c",
            "transcript": "must never leak",
        }
        self.assertEqual(
            set(context.review_lens_projection("product", raw)),
            {"acceptance", "diff_summary"},
        )
        self.assertEqual(
            set(context.review_lens_projection("reliability", raw)),
            {"tests", "checks"},
        )
        for lens in context.REVIEW_LENS_FIELDS:
            self.assertNotIn("transcript", context.review_lens_projection(lens, raw))


class FieldGuideTests(unittest.TestCase):
    def test_persists_deduplicates_and_rejects_stale_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "field-guide.json"
            proposal = {
                "id": "repo.api",
                "text": "API handlers live under src/api.",
                "tags": ["api", "api"],
                "evidence": [{"path": "src/api/mod.rs", "blob_sha": "blob-1"}],
            }
            guide = context.merge_field_guide(
                path, [proposal], current_blob_shas={"src/api/mod.rs": "blob-1"}
            )
            self.assertEqual(len(guide["entries"]), 1)
            guide = context.merge_field_guide(
                path, [proposal], current_blob_shas={"src/api/mod.rs": "blob-1"}
            )
            self.assertEqual(len(guide["entries"]), 1)
            with self.assertRaisesRegex(context.ContextError, "stale"):
                context.merge_field_guide(
                    path, [proposal], current_blob_shas={"src/api/mod.rs": "blob-2"}
                )

    def test_projection_and_deterministic_eviction_respect_budgets(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "field-guide.json"
            proposals = [
                {
                    "id": f"fact.{index}",
                    "text": "x" * 1000,
                    "tags": ["api" if index % 2 else "db"],
                    "evidence": [
                        {"path": f"src/{index}/mod.rs", "blob_sha": f"blob-{index}"}
                    ],
                }
                for index in range(5)
            ]
            blobs = {
                f"src/{index}/mod.rs": f"blob-{index}" for index in range(5)
            }
            guide = context.merge_field_guide(
                path, proposals, current_blob_shas=blobs
            )
            rendered = json.dumps(guide, indent=2, sort_keys=True) + "\n"
            self.assertLessEqual(len(rendered.encode()), context.MAX_GUIDE_BYTES)
            self.assertLessEqual(len(rendered.splitlines()), context.MAX_GUIDE_LINES)
            projection = context.project_field_guide(
                guide, touch_paths=["src/3"], tags=["api"]
            )
            self.assertLessEqual(
                len(context.canonical_json(projection)),
                context.MAX_GUIDE_PROJECTION_BYTES,
            )
            selected_ids = [item["id"] for item in projection["entries"]]
            touched = context.touch_field_guide(path, selected_ids)
            self.assertGreater(touched["revision"], guide["revision"])
            for entry in touched["entries"]:
                if entry["id"] in selected_ids:
                    self.assertEqual(
                        entry["last_used_revision"], touched["revision"]
                    )


if __name__ == "__main__":
    unittest.main()
