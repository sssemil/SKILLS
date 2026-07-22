#!/usr/bin/env python3
"""Create and validate small, checksum-bound worker context files."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Mapping


class ContextError(ValueError):
    """Raised when a context file or reference is unsafe or stale."""


def _bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        temporary.write_bytes(_bytes(value) + b"\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def store(root: Path, value: Any) -> dict[str, str]:
    root = root.resolve()
    digest = sha256(value)
    path = root / "content" / f"{digest}.json"
    if not path.exists():
        atomic_json(path, value)
    return {"path": path.relative_to(root).as_posix(), "sha256": digest}


def load(root: Path, reference: Mapping[str, Any]) -> Any:
    if set(reference) != {"path", "sha256"}:
        raise ContextError("context reference requires exactly path and sha256")
    raw_path = reference.get("path")
    digest = reference.get("sha256")
    if not isinstance(raw_path, str) or not isinstance(digest, str):
        raise ContextError("context reference path and sha256 must be strings")
    root = root.resolve()
    path = (root / raw_path).resolve()
    if path != root and root not in path.parents:
        raise ContextError("context reference escapes its root")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextError(f"cannot read context reference: {exc}") from exc
    if sha256(value) != digest:
        raise ContextError("context reference checksum mismatch")
    return value


_PHASE_KEYS = {
    "work": ("task", "repository_rules", "branch_state"),
    "review": ("acceptance_criteria", "review_context", "checks"),
    "fix": ("finding_queue",),
    "handoff": ("checkpoint_summary", "provider_summary", "checks"),
    "complete": ("provider_summary", "checks"),
}


def build(
    root: Path,
    *,
    phase: str,
    handoff: Mapping[str, Any],
    phase_snapshot: Mapping[str, Any],
    result_path: Path,
    resume_instruction: str | None = None,
) -> tuple[Path, str]:
    if phase not in _PHASE_KEYS:
        raise ContextError(f"unknown worker phase: {phase}")
    root.mkdir(parents=True, exist_ok=True)
    inputs = {"phase_snapshot": store(root, phase_snapshot)}
    for key in _PHASE_KEYS[phase]:
        if key in handoff:
            inputs[key] = store(root, handoff[key])
    if resume_instruction:
        inputs["resume_instruction"] = store(root, resume_instruction.strip())
    context = {
        "version": 1,
        "phase": phase,
        "inputs": inputs,
        "result_path": str(result_path),
    }
    context_path = root / "context.json"
    atomic_json(context_path, context)
    return context_path, sha256(context)


def prompt(phase: str, context_path: Path, context_sha256: str, result_path: Path) -> str:
    value = (
        "Use $brutal-worker for only this managed phase. Validate every context "
        "reference before use. Return the exact result schema and echo "
        "context_sha256.\n"
        f"phase: {phase}\n"
        f"context_file: {context_path}\n"
        f"context_sha256: {context_sha256}\n"
        f"result_file: {result_path}\n"
    )
    if len(value.encode("utf-8")) > 2048:
        raise ContextError("worker prompt exceeds 2 KiB")
    return value
