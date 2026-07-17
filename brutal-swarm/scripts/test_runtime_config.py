from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("runtime_config.py")
SPEC = importlib.util.spec_from_file_location("runtime_config", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
runtime_config = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_config)


class RuntimeConfigTests(unittest.TestCase):
    def test_missing_file_and_missing_field_default_to_tmux(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = runtime_config.resolve_worker_runtime(root / "BRUTAL.md")
            self.assertEqual(missing["runtime"], "tmux")
            self.assertFalse(missing["explicit"])
            self.assertFalse(missing["exists"])

            path = root / "BRUTAL.md"
            path.write_text("---\nversion: 2\n---\n", encoding="utf-8")
            implicit = runtime_config.resolve_worker_runtime(path)
            self.assertEqual(implicit["runtime"], "tmux")
            self.assertFalse(implicit["explicit"])

    def test_explicit_runtimes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "BRUTAL.md"
            for runtime in ("tmux", "subagent"):
                path.write_text(
                    f"---\nexecution:\n  worker_runtime: {runtime}\n---\n",
                    encoding="utf-8",
                )
                resolved = runtime_config.resolve_worker_runtime(path)
                self.assertEqual(resolved["runtime"], runtime)
                self.assertTrue(resolved["explicit"])

    def test_invalid_runtime_shape_value_and_frontmatter_fail(self) -> None:
        documents = (
            "---\nexecution: tmux\n---\n",
            "---\nexecution:\n  worker_runtime: process\n---\n",
            "---\nexecution:\n  worker_runtime: TMUX\n---\n",
            "---\nexecution:\n  worker_runtime: [tmux]\n---\n",
            "---\nexecution: [\n---\n",
            "---\nexecution:\n  worker_runtime: tmux\n",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "BRUTAL.md"
            for document in documents:
                with self.subTest(document=document):
                    path.write_text(document, encoding="utf-8")
                    with self.assertRaises(runtime_config.RuntimeConfigError):
                        runtime_config.resolve_worker_runtime(path)

    def test_cli_returns_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "BRUTAL.md"
            path.write_text(
                "---\nexecution:\n  worker_runtime: subagent\n---\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--brutal-file", str(path)],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["runtime"], "subagent")


if __name__ == "__main__":
    unittest.main()
