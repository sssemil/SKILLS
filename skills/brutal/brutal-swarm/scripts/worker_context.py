#!/usr/bin/env python3
"""Write the phase-specific context consumed by one worker attempt."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Mapping


PHASE_KEYS = {
    "work": ("task", "repository_rules", "branch_state"),
    "review": ("acceptance_criteria", "review_context", "checks"),
    "fix": ("finding_queue",),
    "handoff": ("checkpoint_summary", "provider_summary", "checks"),
    "complete": ("provider_summary", "checks"),
}


def _write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build(
    attempt: Path,
    *,
    phase: str,
    handoff: Mapping[str, Any],
    phase_snapshot: Mapping[str, Any],
    result_path: Path,
    resume_instruction: str | None = None,
) -> Path:
    if phase not in PHASE_KEYS:
        raise ValueError(f"unknown worker phase: {phase}")
    context = {
        "phase": phase,
        "phase_snapshot": dict(phase_snapshot),
        "inputs": {key: handoff[key] for key in PHASE_KEYS[phase] if key in handoff},
        "result_path": str(result_path),
    }
    if "dot_spec" in handoff:
        context["inputs"]["dot_spec"] = handoff["dot_spec"]
    if resume_instruction:
        context["resume_instruction"] = resume_instruction.strip()
    path = attempt / "context.json"
    _write_json(path, context)
    return path


def prompt(phase: str, context_path: Path, result_path: Path) -> str:
    return (
        "Use $brutal-worker for only this managed phase.\n"
        f"phase: {phase}\n"
        f"context_file: {context_path}\n"
        f"result_file: {result_path}\n"
    )
