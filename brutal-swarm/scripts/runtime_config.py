#!/usr/bin/env python3
"""Resolve Brutal Swarm's worker runtime from BRUTAL.md frontmatter."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml


DEFAULT_RUNTIME = "tmux"
WORKER_RUNTIMES = frozenset({"tmux", "subagent"})


class RuntimeConfigError(ValueError):
    """Raised when BRUTAL.md contains an invalid execution configuration."""


def _frontmatter(text: str) -> Mapping[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as error:
        raise RuntimeConfigError("BRUTAL.md frontmatter is not terminated") from error

    try:
        parsed = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as error:
        raise RuntimeConfigError(f"invalid BRUTAL.md frontmatter: {error}") from error
    if parsed is None:
        return {}
    if not isinstance(parsed, Mapping):
        raise RuntimeConfigError("BRUTAL.md frontmatter must be a mapping")
    return parsed


def resolve_worker_runtime(path: str | Path) -> dict[str, Any]:
    """Return the normalized worker runtime and whether it was explicit."""

    brutal_path = Path(path).expanduser().resolve(strict=False)
    if not brutal_path.exists():
        return {
            "runtime": DEFAULT_RUNTIME,
            "explicit": False,
            "edit_sandbox_command": None,
            "path": str(brutal_path),
            "exists": False,
        }
    if not brutal_path.is_file():
        raise RuntimeConfigError(f"BRUTAL.md path is not a file: {brutal_path}")

    document = _frontmatter(brutal_path.read_text(encoding="utf-8"))
    execution = document.get("execution")
    if execution is None:
        runtime = DEFAULT_RUNTIME
        explicit = False
        edit_sandbox_command = None
    else:
        if not isinstance(execution, Mapping):
            raise RuntimeConfigError("execution must be a mapping")
        value = execution.get("worker_runtime")
        if value is None:
            runtime = DEFAULT_RUNTIME
            explicit = False
        else:
            if not isinstance(value, str) or value not in WORKER_RUNTIMES:
                expected = ", ".join(sorted(WORKER_RUNTIMES))
                raise RuntimeConfigError(
                    f"execution.worker_runtime must be one of: {expected}"
                )
            runtime = value
            explicit = True
        raw_command = execution.get("edit_sandbox_command")
        if raw_command is None:
            edit_sandbox_command = None
        elif (
            not isinstance(raw_command, list)
            or not raw_command
            or not all(isinstance(item, str) and item for item in raw_command)
        ):
            raise RuntimeConfigError(
                "execution.edit_sandbox_command must be a non-empty string array"
            )
        else:
            edit_sandbox_command = list(raw_command)

    return {
        "runtime": runtime,
        "explicit": explicit,
        "edit_sandbox_command": edit_sandbox_command,
        "path": str(brutal_path),
        "exists": True,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brutal-file", default="BRUTAL.md")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = resolve_worker_runtime(args.brutal_file)
    except (OSError, RuntimeConfigError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
