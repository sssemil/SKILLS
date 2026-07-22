from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("dotspec.py")
SPEC = importlib.util.spec_from_file_location("dotspec", SCRIPT)
assert SPEC and SPEC.loader
dotspec = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dotspec)


class DotSpecTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.git("init")
        self.git("config", "user.name", "Dot Spec Test")
        self.git("config", "user.email", "dotspec@example.invalid")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, name: str, value: object) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout.strip()

    def commit_graph(self) -> str:
        self.git("add", ".")
        self.git("commit", "-m", "graph")
        return self.git("rev-parse", "HEAD")

    def module(self, *, requirement: str = "The operation is idempotent.", imports: list[dict[str, str]] | None = None) -> dict[str, object]:
        return {
            "schema_version": 1,
            "module": "billing",
            "imports": imports or [],
            "seams": ["public-api"],
            "requirements": [{
                "id": "billing.idempotency",
                "concern": "behavior",
                "statement": requirement,
                "provenance": {"kind": "declared", "refs": ["ADR-1"]},
                "verification": ["contract::idempotency"],
            }],
        }

    def manifest(self, spec: str = "billing.json", maturity: str = "guarded") -> dict[str, object]:
        return {
            "schema_version": 1,
            "modules": [{
                "id": "billing",
                "spec": spec,
                "maturity": maturity,
                "authority": {"behavior": "spec", "implementation": "code"},
            }],
        }

    def valid_graph(self) -> Path:
        self.write("billing.json", self.module())
        return self.write("modules.json", self.manifest())

    def test_valid_graph_and_trace(self) -> None:
        manifest = self.valid_graph()
        modules, errors = dotspec.validate_graph(manifest)
        self.assertEqual(errors, [])
        trace = dotspec.trace_graph(modules)["trace"]
        self.assertEqual(trace[0]["requirement_id"], "billing.idempotency")
        self.assertEqual(trace[0]["authority"], "spec")

    def test_rejects_unknown_provenance_and_missing_guard(self) -> None:
        spec = self.module()
        req = spec["requirements"][0]
        req["provenance"] = {"kind": "unknown"}
        req["verification"] = []
        self.write("billing.json", spec)
        manifest = self.write("modules.json", self.manifest())
        _, errors = dotspec.validate_graph(manifest)
        self.assertTrue(any("invalid active provenance" in error for error in errors))
        self.assertTrue(any("need verification evidence" in error for error in errors))

    def test_rejects_import_cycle(self) -> None:
        billing = self.module(imports=[{"module": "identity"}])
        identity = {
            "schema_version": 1,
            "module": "identity",
            "imports": [{"module": "billing"}],
            "requirements": [{
                "id": "identity.subject",
                "concern": "behavior",
                "statement": "Each subject has a stable identifier.",
                "provenance": "declared",
                "verification": ["contract::subject"],
            }],
        }
        self.write("billing.json", billing)
        self.write("identity.json", identity)
        manifest = self.manifest()
        manifest["modules"].append({
            "id": "identity",
            "spec": "identity.json",
            "maturity": "guarded",
            "authority": {"behavior": "spec"},
        })
        path = self.write("modules.json", manifest)
        _, errors = dotspec.validate_graph(path)
        self.assertTrue(any("import cycle" in error for error in errors))

    def test_rejects_spec_path_escape(self) -> None:
        manifest = self.write("nested/modules.json", self.manifest(spec="../billing.json"))
        self.write("billing.json", self.module())
        _, errors = dotspec.validate_graph(manifest)
        self.assertTrue(any("escapes the manifest directory" in error for error in errors))

    def test_semantic_diff_is_requirement_based(self) -> None:
        old_manifest = self.valid_graph()
        old_modules, errors = dotspec.validate_graph(old_manifest)
        self.assertEqual(errors, [])
        changed = self.module(requirement="Retries have exactly one effect.")
        self.write("after/billing.json", changed)
        after_manifest = self.write("after/modules.json", self.manifest())
        new_modules, errors = dotspec.validate_graph(after_manifest)
        self.assertEqual(errors, [])
        delta = dotspec.semantic_diff(old_modules, new_modules)
        self.assertEqual(delta["operations"][0]["op"], "replace")
        self.assertEqual(delta["operations"][0]["requirement_id"], "billing.idempotency")

    def test_semantic_diff_includes_authority_and_maturity(self) -> None:
        old_manifest = self.valid_graph()
        old_modules, errors = dotspec.validate_graph(old_manifest)
        self.assertEqual(errors, [])
        self.write("after/billing.json", self.module())
        changed_manifest = self.manifest(maturity="spec-driven")
        changed_manifest["modules"][0]["authority"]["implementation"] = "spec"
        after_manifest = self.write("after/modules.json", changed_manifest)
        new_modules, errors = dotspec.validate_graph(after_manifest)
        self.assertEqual(errors, [])
        delta = dotspec.semantic_diff(old_modules, new_modules)
        self.assertEqual(delta["module_changes"][0]["module"], "billing")
        self.assertEqual(delta["module_changes"][0]["after"]["maturity"], "spec-driven")

    def test_semantic_diff_rejects_module_set_changes(self) -> None:
        manifest = self.valid_graph()
        before, errors = dotspec.validate_graph(manifest)
        self.assertEqual(errors, [])
        with self.assertRaisesRegex(dotspec.DotSpecError, "module set changes"):
            dotspec.semantic_diff(before, {})

    def test_normalized_delta_digest_ignores_operation_order(self) -> None:
        operations = [
            {"op": "add", "module": "billing", "requirement_id": "billing.a"},
            {"op": "add", "module": "billing", "requirement_id": "billing.b"},
        ]
        self.assertEqual(
            dotspec.digest({"operations": operations}),
            dotspec.digest({"operations": list(reversed(operations))}),
        )

    def test_delta_base_digest_and_assignment(self) -> None:
        manifest = self.valid_graph()
        modules, errors = dotspec.validate_graph(manifest)
        self.assertEqual(errors, [])
        base_sha = self.commit_graph()
        delta = {
            "schema_version": 1,
            "change_id": "dot-1",
            "base_sha": base_sha,
            "base_specs": {"billing": dotspec.digest(modules["billing"]["spec"])},
            "approval": {"status": "approved", "by": "user", "at": "2026-07-22T00:00:00Z"},
            "operations": [{
                "op": "replace",
                "module": "billing",
                "requirement_id": "billing.idempotency",
                "ticket": "ENG-1",
                "activates_with": "ENG-1",
                "before_digest": dotspec.digest(self.module()["requirements"][0]),
                "after": self.module()["requirements"][0],
            }],
            "module_changes": [],
        }
        path = self.write("delta.json", delta)
        self.assertEqual(dotspec.validate_delta(path, modules, True), [])
        delta["base_specs"]["billing"] = "stale"
        path = self.write("delta.json", delta)
        self.assertTrue(any("stale base digest" in error for error in dotspec.validate_delta(path, modules, True)))

    def test_delta_rejects_stale_requirement_digest(self) -> None:
        manifest = self.valid_graph()
        modules, errors = dotspec.validate_graph(manifest)
        self.assertEqual(errors, [])
        base_sha = self.commit_graph()
        delta = {
            "schema_version": 1,
            "change_id": "dot-2",
            "base_sha": base_sha,
            "base_specs": {"billing": dotspec.digest(modules["billing"]["spec"])},
            "approval": {"status": "approved", "by": "user", "at": "2026-07-22T00:00:00Z"},
            "operations": [{
                "op": "replace",
                "module": "billing",
                "requirement_id": "billing.idempotency",
                "ticket": "ENG-2",
                "activates_with": "ENG-2",
                "before_digest": "stale",
                "after": self.module()["requirements"][0],
            }],
        }
        path = self.write("delta.json", delta)
        self.assertTrue(any("stale requirement digest" in error for error in dotspec.validate_delta(path, modules, True)))

    def test_delta_rejects_stale_git_base_and_incomplete_after(self) -> None:
        manifest = self.valid_graph()
        modules, errors = dotspec.validate_graph(manifest)
        self.assertEqual(errors, [])
        base_sha = self.commit_graph()
        requirement = self.module()["requirements"][0]
        delta = {
            "schema_version": 1,
            "change_id": "dot-invalid",
            "base_sha": "0" * 40,
            "base_specs": {"billing": dotspec.digest(modules["billing"]["spec"])},
            "approval": {"status": "approved", "by": "user", "at": "2026-07-22T00:00:00Z"},
            "operations": [{
                "op": "replace",
                "module": "billing",
                "requirement_id": "billing.idempotency",
                "ticket": "ENG-3",
                "activates_with": "ENG-3",
                "before_digest": dotspec.digest(requirement),
                "after": {"id": "billing.idempotency"},
            }],
        }
        path = self.write("delta.json", delta)
        errors = dotspec.validate_delta(path, modules, True)
        self.assertTrue(any("stale base SHA" in error for error in errors))
        delta["base_sha"] = base_sha
        path = self.write("delta.json", delta)
        errors = dotspec.validate_delta(path, modules, True)
        self.assertTrue(any("statement is required" in error for error in errors))

    def test_invalid_graph_stops_before_delta_processing(self) -> None:
        self.write("billing.json", {
            "schema_version": 1,
            "module": "billing",
            "requirements": ["bad"],
        })
        manifest = self.write("modules.json", self.manifest())
        delta = self.write("delta.json", {
            "schema_version": 1,
            "change_id": "dot-bad",
            "base_sha": "bad",
            "base_specs": {},
            "approval": {"status": "draft"},
            "operations": [],
        })
        self.assertEqual(dotspec.main(["validate", str(manifest), "--delta", str(delta)]), 1)

    def test_verify_records_head_and_spec_digests(self) -> None:
        manifest = self.valid_graph()
        head_sha = self.commit_graph()
        output = self.root / "evidence.json"
        status = dotspec.main([
            "verify",
            str(manifest),
            "--head-sha",
            head_sha,
            "--output",
            str(output),
            "--",
            sys.executable,
            "-c",
            "pass",
        ])
        self.assertEqual(status, 0)
        evidence = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(evidence["head_sha"], head_sha)
        self.assertTrue(evidence["passed"])
        self.assertIn("billing", evidence["module_spec_digests"])

    def test_verify_rejects_mismatched_and_dirty_snapshots(self) -> None:
        manifest = self.valid_graph()
        head_sha = self.commit_graph()
        output = self.root.parent / "evidence.json"
        mismatch = dotspec.main([
            "verify", str(manifest), "--head-sha", "0" * 40,
            "--output", str(output), "--", sys.executable, "-c", "pass",
        ])
        self.assertEqual(mismatch, 2)
        (self.root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        dirty = dotspec.main([
            "verify", str(manifest), "--head-sha", head_sha,
            "--output", str(output), "--", sys.executable, "-c", "pass",
        ])
        self.assertEqual(dirty, 2)

    def test_verify_runs_from_repository_root(self) -> None:
        self.write(".dotspec/billing.json", self.module())
        manifest = self.write(".dotspec/modules.json", self.manifest())
        head_sha = self.commit_graph()
        output = self.root.parent / "cwd-evidence.json"
        status = dotspec.main([
            "verify", str(manifest), "--head-sha", head_sha,
            "--output", str(output), "--", sys.executable, "-c",
            f"import pathlib; assert pathlib.Path.cwd() == pathlib.Path({str(self.root)!r})",
        ])
        self.assertEqual(status, 0)


if __name__ == "__main__":
    unittest.main()
