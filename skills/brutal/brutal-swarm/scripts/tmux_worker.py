#!/usr/bin/env python3
"""Launch and supervise exact Brutal workers in retained tmux sessions."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from worker_context import build as build_context, prompt as context_prompt

class TmuxWorkerError(RuntimeError):
    """A user-actionable worker identity, runtime, or process error."""


LEGACY_RESULT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "task_ref", "summary"],
    "properties": {
        "status": {
            "type": "string",
            "enum": ["clean", "blocked", "canceled", "claim_lost", "failed"],
        },
        "task_ref": {"type": "string", "minLength": 1},
        "summary": {"type": "string"},
    },
}

_PHASES = ("work", "review", "fix", "handoff", "complete")
_CHECKPOINT_PHASES = ("work", "review", "fix")
_TERMINAL_STATUSES = ("clean", "blocked", "canceled", "claim_lost", "failed")

_COMMON_MANAGED_PROPERTIES: dict[str, Any] = {
    "schema_version": {"const": 2},
    "task_ref": {"type": "string", "minLength": 1},
    "summary": {"type": "string"},
    "phase": {"type": "string", "enum": list(_PHASES)},
    "attempt_id": {"type": "string", "pattern": r"^[0-9]{6}$"},
}

_FINDING_COUNTS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["CRITICAL", "MAJOR", "MINOR", "NIT"],
    "properties": {
        severity: {"type": "integer", "minimum": 0}
        for severity in ("CRITICAL", "MAJOR", "MINOR", "NIT")
    },
}

_DOT_SPEC_RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "actual_delta_digest",
        "spec_digests",
        "trace",
        "evidence",
        "activations",
    ],
    "properties": {
        "actual_delta_digest": {"type": "string", "minLength": 1},
        "spec_digests": {
            "type": "object",
            "additionalProperties": {"type": "string", "minLength": 1},
        },
        "trace": {"type": "object"},
        "evidence": {"type": "object"},
        "activations": {
            "type": "object",
            "additionalProperties": {"type": "boolean"},
        },
    },
}

_CHECKPOINT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "branch",
        "head_sha",
        "base_branch",
        "base_sha",
        "pull_request",
        "verification_head",
        "verification_summary",
        "review_id",
        "findings_by_severity",
        "queued_finding_count",
        "unhandled_finding_count",
        "summary_posted",
        "residual_findings",
    ],
    "properties": {
        "branch": {"type": "string", "minLength": 1},
        "head_sha": {"type": "string", "minLength": 1},
        "base_branch": {"type": "string", "minLength": 1},
        "base_sha": {"type": "string", "minLength": 1},
        "pull_request": {"type": ["string", "null"]},
        "verification_head": {"type": ["string", "null"]},
        "verification_summary": {"type": "string"},
        "review_id": {"type": ["string", "null"]},
        "findings_by_severity": _FINDING_COUNTS_SCHEMA,
        "queued_finding_count": {"type": "integer", "minimum": 0},
        "unhandled_finding_count": {"type": "integer", "minimum": 0},
        "summary_posted": {"type": "boolean"},
        "residual_findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["fingerprint", "severity", "summary"],
                "properties": {
                    "fingerprint": {"type": "string", "minLength": 1},
                    "severity": {"enum": ["MINOR", "NIT"]},
                    "summary": {"type": "string", "minLength": 1},
                    "location": {"type": ["string", "null"]},
                },
            },
        },
        "dot_spec": _DOT_SPEC_RESULT_SCHEMA,
    },
}

def _managed_variant(status: str, extra: Mapping[str, Any]) -> dict[str, Any]:
    properties = {**_COMMON_MANAGED_PROPERTIES, "status": {"const": status}, **extra}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


MANAGED_RESULT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "oneOf": [
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["schema_version", "status", "task_ref", "summary"],
            "properties": {
                "schema_version": {"const": 2},
                "status": {"const": "progress"},
                "task_ref": {"type": "string", "minLength": 1},
                "summary": {"type": "string"},
            },
        },
        _managed_variant("checkpoint", {"checkpoint": _CHECKPOINT_SCHEMA}),
        _managed_variant(
            "clean",
            {
                "completion_kind": {
                    "enum": ["zero_findings", "materially_clean", "merged"]
                },
                "cleanup_eligible": {"type": "boolean"},
                "result": _CHECKPOINT_SCHEMA,
            },
        ),
        *[
            _managed_variant(status, {"blocker": {"type": ["string", "null"]}})
            for status in ("blocked", "canceled", "claim_lost", "failed")
        ],
    ],
}


def _managed_phase_variant(
    phase: str, status: str | Mapping[str, Any], extra: Mapping[str, Any]
) -> dict[str, Any]:
    properties = {
        **_COMMON_MANAGED_PROPERTIES,
        "phase": {"const": phase},
        "status": {"const": status} if isinstance(status, str) else dict(status),
        **extra,
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


def _managed_result_schema(phase: str, *, require_dot_spec: bool = False) -> dict[str, Any]:
    if phase not in _PHASES:
        raise TmuxWorkerError(f"unknown managed phase: {phase}")
    checkpoint_schema = copy.deepcopy(_CHECKPOINT_SCHEMA)
    if require_dot_spec:
        checkpoint_schema["required"].append("dot_spec")
    variants: list[dict[str, Any]] = []
    if phase in _CHECKPOINT_PHASES:
        variants.append(
            _managed_phase_variant(
                phase, "checkpoint", {"checkpoint": checkpoint_schema}
            )
        )
    else:
        completion_kinds = (
            ["merged"] if phase == "complete" else ["zero_findings", "materially_clean"]
        )
        variants.append(
            _managed_phase_variant(
                phase,
                "clean",
                {
                    "completion_kind": {"enum": completion_kinds},
                    "cleanup_eligible": {"type": "boolean"},
                    "result": checkpoint_schema,
                },
            )
        )
    variants.append(
        _managed_phase_variant(
            phase,
            {"enum": ["blocked", "canceled", "claim_lost", "failed"]},
            {"blocker": {"type": ["string", "null"]}},
        )
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "oneOf": variants,
    }


# Backward-compatible name for callers that import the original constant.
RESULT_SCHEMA = LEGACY_RESULT_SCHEMA

_TMUX_METADATA = {
    "repository": "@brutal_repository",
    "task_ref": "@brutal_task_ref",
    "branch": "@brutal_branch",
    "worktree": "@brutal_worktree",
    "state_dir": "@brutal_state_dir",
}


def _resolve(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _slug(value: str, fallback: str, limit: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or fallback)[:limit].rstrip("-")


def stable_session_name(repository: str, task_ref: str) -> str:
    """Return a tmux-safe stable name for one canonical repository/task pair."""
    if not repository.strip() or not task_ref.strip():
        raise TmuxWorkerError("repository identity and task ref must not be empty")
    digest = hashlib.sha256(
        f"{repository}\0{task_ref}".encode("utf-8")
    ).hexdigest()[:16]
    return (
        f"brutal-{_slug(repository.rsplit('/', 1)[-1], 'repo', 28)}-"
        f"{_slug(task_ref, 'task', 36)}-{digest}"
    )


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise TmuxWorkerError(detail)
    return result


def _parse_worktrees(raw: str) -> list[dict[str, str | bool]]:
    records: list[dict[str, str | bool]] = []
    current: dict[str, str | bool] = {}
    for field in raw.split("\0"):
        if not field:
            if current:
                records.append(current)
                current = {}
            continue
        key, separator, value = field.partition(" ")
        current[key] = value if separator else True
    if current:
        records.append(current)
    return records


def _repository(repo_path: str | Path) -> tuple[Path, Path]:
    candidate = _resolve(repo_path)
    probe = _git(candidate, "rev-parse", "--is-inside-work-tree", check=False)
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        raise TmuxWorkerError(f"not a non-bare Git worktree: {candidate}")
    records = _parse_worktrees(
        _git(candidate, "worktree", "list", "--porcelain", "-z").stdout
    )
    if not records or not isinstance(records[0].get("worktree"), str):
        raise TmuxWorkerError("Git did not report a primary worktree")
    primary = _resolve(str(records[0]["worktree"]))
    common_value = Path(_git(primary, "rev-parse", "--git-common-dir").stdout.strip())
    common = (
        common_value.resolve(strict=False)
        if common_value.is_absolute()
        else (primary / common_value).resolve(strict=False)
    )
    return primary, common


def _canonical_repository(primary: Path, common: Path) -> str:
    digest = hashlib.sha256(f"{primary}\0{common}".encode("utf-8")).hexdigest()
    return f"local:{_slug(primary.name, 'repo', 40)}:{digest}"


def _branch_metadata(primary: Path, branch: str) -> str | None:
    result = _git(
        primary,
        "config",
        "--local",
        "--get",
        f"branch.{branch}.brutalTaskRef",
        check=False,
    )
    return result.stdout.rstrip("\n") if result.returncode == 0 else None


def _validate_worktree(
    repo_path: str | Path,
    worktree_path: str | Path,
    branch: str,
    task_ref: str,
) -> tuple[Path, Path, Path]:
    if not task_ref.strip() or not branch.strip():
        raise TmuxWorkerError("task ref and branch must not be empty")
    primary, common = _repository(repo_path)
    worktree = _resolve(worktree_path)
    records = _parse_worktrees(
        _git(primary, "worktree", "list", "--porcelain", "-z").stdout
    )
    record = next(
        (
            item
            for item in records
            if isinstance(item.get("worktree"), str)
            and _resolve(str(item["worktree"])) == worktree
        ),
        None,
    )
    if record is None:
        raise TmuxWorkerError(f"worktree is not registered: {worktree}")
    if worktree == primary:
        raise TmuxWorkerError("refusing to run a task worker in the primary worktree")
    expected_ref = f"refs/heads/{branch}"
    if record.get("branch") != expected_ref:
        raise TmuxWorkerError(
            f"registered worktree branch mismatch: expected {branch}, "
            f"found {record.get('branch')}"
        )
    if not worktree.is_dir():
        raise TmuxWorkerError(f"registered worktree does not exist: {worktree}")
    actual_ref = _git(worktree, "symbolic-ref", "--quiet", "HEAD", check=False)
    if actual_ref.returncode != 0 or actual_ref.stdout.strip() != expected_ref:
        raise TmuxWorkerError(f"worktree is not checked out on exact branch: {branch}")
    metadata = _branch_metadata(primary, branch)
    if metadata != task_ref:
        raise TmuxWorkerError(
            "worktree does not have matching Brutal task metadata: "
            f"expected {task_ref!r}, found {metadata!r}"
        )
    return primary, common, worktree


def _executable(value: str, label: str) -> str:
    candidate = shutil.which(value)
    if candidate is None:
        raise TmuxWorkerError(f"required {label} executable was not found: {value}")
    return str(_resolve(candidate))


def _tmux_command(tmux_bin: str, socket_name: str | None, *args: str) -> list[str]:
    command = [tmux_bin]
    if socket_name:
        if "/" in socket_name or "\\" in socket_name:
            raise TmuxWorkerError("tmux socket name must not contain a path separator")
        command.extend(["-L", socket_name])
    command.extend(args)
    return command


def _tmux(
    tmux_bin: str,
    socket_name: str | None,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        _tmux_command(tmux_bin, socket_name, *args),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "tmux command failed"
        raise TmuxWorkerError(detail)
    return result


def _state_dir(primary: Path, repository: str, task_ref: str) -> Path:
    repo_digest = hashlib.sha256(repository.encode("utf-8")).hexdigest()[:12]
    task_digest = hashlib.sha256(task_ref.encode("utf-8")).hexdigest()[:16]
    return (
        primary.parent
        / ".brutal-runs"
        / f"{_slug(primary.name, 'repo', 40)}-{repo_digest}"
        / task_digest
    )


def _atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        temporary.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _json_digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _is_managed(manifest: Mapping[str, Any]) -> bool:
    return manifest.get("version") == 2 and isinstance(manifest.get("handoff"), Mapping)


def _attempt_id(number: int) -> str:
    return f"{number:06d}"


def _attempt_dir(state_dir: Path, attempt_id: str) -> Path:
    return state_dir / "attempts" / attempt_id


def _active_attempt(state_dir: Path) -> dict[str, Any]:
    active = _read_json(state_dir / "active.json")
    if active is None:
        raise TmuxWorkerError("managed worker has no active attempt")
    attempt_id = active.get("attempt_id")
    phase = active.get("phase")
    if (
        not isinstance(attempt_id, str)
        or not re.fullmatch(r"[0-9]{6}", attempt_id)
        or phase not in _PHASES
    ):
        raise TmuxWorkerError("managed worker active attempt is malformed")
    return active


@contextmanager
def _transition_lock(state_dir: Path) -> Iterator[None]:
    lock_path = state_dir / "transition.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise TmuxWorkerError("another worker transition is already in progress") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _initial_phase(handoff: Mapping[str, Any]) -> str:
    phase = handoff.get("phase", "work")
    if phase not in {"work", "review", "fix", "complete"}:
        raise TmuxWorkerError(
            "managed handoff phase must be work, review, fix, or complete"
        )
    return str(phase)


def _phase_snapshot(
    manifest: Mapping[str, Any],
    phase: str,
    attempt_id: str,
    *,
    live: Mapping[str, Any],
    parent_attempt_id: str | None,
) -> dict[str, Any]:
    handoff = manifest.get("handoff")
    assert isinstance(handoff, Mapping)
    return {
        "schema_version": 1,
        "phase": phase,
        "attempt_id": attempt_id,
        "parent_attempt_id": parent_attempt_id,
        "identity": {
            "task_ref": manifest["task_ref"],
            "branch": manifest["branch"],
            "worktree_path": manifest["worktree"],
            "code_host_repository": manifest["repository"],
        },
        "live": dict(live),
    }


def _initial_live_snapshot(handoff: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "task_state": handoff.get("task_state"),
        "task_owner": handoff.get("task_owner"),
        "branch_head": handoff.get("branch_head"),
        "base_branch": handoff.get("base_branch"),
        "base_sha": handoff.get("base_sha"),
        "pull_request": handoff.get("pull_request"),
        "checks": handoff.get("checks"),
    }


def _validate_live_snapshot(
    snapshot: Mapping[str, Any], manifest: Mapping[str, Any]
) -> dict[str, Any]:
    if snapshot.get("schema_version") != 1:
        raise TmuxWorkerError("phase snapshot schema_version must be 1")
    identity = snapshot.get("identity")
    live = snapshot.get("live")
    if not isinstance(identity, Mapping) or not isinstance(live, Mapping):
        raise TmuxWorkerError("phase snapshot requires identity and live objects")
    expected = {
        "task_ref": manifest["task_ref"],
        "branch": manifest["branch"],
        "worktree_path": manifest["worktree"],
        "code_host_repository": manifest["repository"],
    }
    mismatches = [key for key, value in expected.items() if identity.get(key) != value]
    if mismatches:
        raise TmuxWorkerError(
            "phase snapshot identity mismatch: " + ", ".join(sorted(mismatches))
        )
    required_live = ("task_state", "task_owner", "branch_head", "base_branch", "base_sha")
    missing = [key for key in required_live if key not in live]
    if missing:
        raise TmuxWorkerError(
            "phase snapshot live state is missing: " + ", ".join(sorted(missing))
        )
    return dict(live)


def _write_attempt(
    state_dir: Path,
    manifest: Mapping[str, Any],
    *,
    attempt_id: str,
    phase: str,
    live: Mapping[str, Any],
    parent_attempt_id: str | None,
    mode: str,
) -> tuple[Path, dict[str, Any]]:
    attempt = _attempt_dir(state_dir, attempt_id)
    if attempt.exists():
        raise TmuxWorkerError(f"managed attempt already exists: {attempt_id}")
    attempt.mkdir(parents=True)
    os.chmod(attempt, 0o700)
    snapshot = _phase_snapshot(
        manifest,
        phase,
        attempt_id,
        live=live,
        parent_attempt_id=parent_attempt_id,
    )
    prompt_path = attempt / "prompt.txt"
    handoff = manifest["handoff"]
    assert isinstance(handoff, Mapping)
    context_values = dict(handoff)
    context_values.setdefault("task", {"task_ref": manifest["task_ref"]})
    context_values["branch_state"] = dict(live)
    context_path = build_context(
        attempt,
        phase=phase,
        handoff=context_values,
        phase_snapshot=snapshot,
        result_path=attempt / "result.json",
    )
    prompt = context_prompt(phase, context_path, attempt / "result.json")
    prompt_path.write_text(prompt, encoding="utf-8")
    os.chmod(prompt_path, 0o600)
    _atomic_json(attempt / "phase-snapshot.json", snapshot)
    _atomic_json(
        attempt / "result-schema.json",
        _managed_result_schema(
            phase,
            require_dot_spec=isinstance(handoff.get("dot_spec"), Mapping),
        ),
    )
    _atomic_json(
        attempt / "attempt.json",
        {
            "attempt_id": attempt_id,
            "phase": phase,
            "mode": mode,
            "parent_attempt_id": parent_attempt_id,
            "created_at": time.time(),
        },
    )
    return attempt, snapshot


def _load_data(path: str | Path) -> dict[str, Any]:
    source = _resolve(path)
    try:
        raw = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise TmuxWorkerError(f"cannot read handoff file {source}: {exc}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise TmuxWorkerError("YAML handoffs require PyYAML") from exc
        try:
            value = yaml.safe_load(raw)
        except yaml.YAMLError as exc:
            raise TmuxWorkerError(f"invalid handoff JSON/YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise TmuxWorkerError("handoff must be a JSON/YAML object")
    return value


def _handoff_identity(handoff: Mapping[str, Any]) -> tuple[str, str, str, str]:
    if handoff.get("mode") != "managed":
        raise TmuxWorkerError("handoff mode must be managed")
    if handoff.get("worker_runtime") not in (None, "tmux"):
        raise TmuxWorkerError("handoff worker_runtime must be tmux")
    code_host = handoff.get("code_host")
    if not isinstance(code_host, Mapping):
        raise TmuxWorkerError("handoff code_host must be an object")
    values = (
        handoff.get("task_ref"),
        handoff.get("worktree_path"),
        handoff.get("branch"),
        code_host.get("repository"),
    )
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise TmuxWorkerError(
            "handoff requires task_ref, worktree_path, branch, and code_host.repository"
        )
    return values  # type: ignore[return-value]


def _read_manifest(state_dir: Path) -> dict[str, Any]:
    try:
        value = json.loads((state_dir / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TmuxWorkerError(f"cannot read worker manifest in {state_dir}: {exc}") from exc
    if not isinstance(value, dict):
        raise TmuxWorkerError("worker manifest is not an object")
    return value


def _parse_thread_id(events_path: Path) -> str | None:
    if not events_path.exists():
        return None
    found: str | None = None
    for line in events_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        for key in ("thread_id", "session_id"):
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                found = value
        thread = event.get("thread")
        if isinstance(thread, dict):
            value = thread.get("id")
            if isinstance(value, str) and value.strip():
                found = value
    return found


def _nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_checkpoint(value: Any, *, require_dot_spec: bool = False) -> bool:
    if not isinstance(value, dict):
        return False
    required = {
        "branch",
        "head_sha",
        "base_branch",
        "base_sha",
        "pull_request",
        "verification_head",
        "verification_summary",
        "review_id",
        "findings_by_severity",
        "queued_finding_count",
        "unhandled_finding_count",
        "summary_posted",
        "residual_findings",
    }
    if set(value) not in (required, required | {"dot_spec"}):
        return False
    if require_dot_spec and "dot_spec" not in value:
        return False
    if any(
        not isinstance(value[key], str) or not value[key]
        for key in ("branch", "head_sha", "base_branch", "base_sha")
    ):
        return False
    if not isinstance(value["verification_summary"], str):
        return False
    for key in ("pull_request", "verification_head", "review_id"):
        if value[key] is not None and not isinstance(value[key], str):
            return False
    if not isinstance(value["summary_posted"], bool):
        return False
    if not all(
        _nonnegative_integer(value[key])
        for key in ("queued_finding_count", "unhandled_finding_count")
    ):
        return False
    counts = value["findings_by_severity"]
    severities = {"CRITICAL", "MAJOR", "MINOR", "NIT"}
    if (
        not isinstance(counts, dict)
        or set(counts) != severities
        or not all(_nonnegative_integer(counts[key]) for key in severities)
    ):
        return False
    residuals = value["residual_findings"]
    if not isinstance(residuals, list):
        return False
    for residual in residuals:
        if not isinstance(residual, dict) or set(residual) not in (
            {"fingerprint", "severity", "summary"},
            {"fingerprint", "severity", "summary", "location"},
        ):
            return False
        if residual.get("severity") not in {"MINOR", "NIT"}:
            return False
        if any(
            not isinstance(residual.get(key), str) or not residual[key]
            for key in ("fingerprint", "summary")
        ):
            return False
        if (
            "location" in residual
            and residual["location"] is not None
            and not isinstance(residual["location"], str)
        ):
            return False
    if len(residuals) != counts["MINOR"] + counts["NIT"]:
        return False
    if "dot_spec" in value:
        dot_spec = value["dot_spec"]
        if not isinstance(dot_spec, dict) or set(dot_spec) != {
            "actual_delta_digest",
            "spec_digests",
            "trace",
            "evidence",
            "activations",
        }:
            return False
        if not isinstance(dot_spec["actual_delta_digest"], str) or not dot_spec["actual_delta_digest"]:
            return False
        if not isinstance(dot_spec["spec_digests"], dict) or not all(
            isinstance(key, str) and key and isinstance(item, str) and item
            for key, item in dot_spec["spec_digests"].items()
        ):
            return False
        if not isinstance(dot_spec["trace"], dict) or not isinstance(dot_spec["evidence"], dict):
            return False
        if not isinstance(dot_spec["activations"], dict) or not all(
            isinstance(key, str) and key and isinstance(item, bool)
            for key, item in dot_spec["activations"].items()
        ):
            return False
    return True


def _read_result(
    result_path: Path,
    expected_task_ref: str | None = None,
    *,
    expected_phase: str | None = None,
    expected_attempt_id: str | None = None,
    managed: bool = False,
    require_dot_spec: bool = False,
) -> dict[str, Any] | None:
    if not result_path.exists():
        return None
    try:
        value = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    if not isinstance(value.get("task_ref"), str) or not value["task_ref"]:
        return None
    if not isinstance(value.get("summary"), str):
        return None
    if expected_task_ref is not None and value.get("task_ref") != expected_task_ref:
        return None
    status = value.get("status")
    if not managed:
        if status not in _TERMINAL_STATUSES:
            return None
        return value
    if value.get("schema_version") != 2 or status == "progress":
        return None
    if status not in {"checkpoint", *_TERMINAL_STATUSES}:
        return None
    if value.get("phase") not in _PHASES or not isinstance(value.get("attempt_id"), str):
        return None
    if expected_phase is not None and value.get("phase") != expected_phase:
        return None
    if expected_attempt_id is not None and value.get("attempt_id") != expected_attempt_id:
        return None
    common = {"schema_version", "status", "task_ref", "summary", "phase", "attempt_id"}
    if status == "checkpoint":
        if (
            set(value) != common | {"checkpoint"}
            or value.get("phase") not in _CHECKPOINT_PHASES
            or not _valid_checkpoint(
                value.get("checkpoint"), require_dot_spec=require_dot_spec
            )
        ):
            return None
    elif status == "clean":
        if (
            set(value) != common | {"completion_kind", "cleanup_eligible", "result"}
            or value.get("phase") not in {"handoff", "complete"}
        ):
            return None
        if value.get("completion_kind") not in {
            "zero_findings",
            "materially_clean",
            "merged",
        }:
            return None
        if (
            value["phase"] == "handoff"
            and value["completion_kind"] not in {"zero_findings", "materially_clean"}
        ) or (
            value["phase"] == "complete" and value["completion_kind"] != "merged"
        ):
            return None
        if not isinstance(value.get("cleanup_eligible"), bool) or not _valid_checkpoint(
            value.get("result"), require_dot_spec=require_dot_spec
        ):
            return None
        counts = value["result"]["findings_by_severity"]
        if (
            value["result"]["queued_finding_count"] != 0
            or value["result"]["unhandled_finding_count"] != 0
        ):
            return None
        if value["completion_kind"] == "zero_findings" and any(counts.values()):
            return None
        if value["completion_kind"] == "materially_clean" and (
            counts["CRITICAL"] != 0 or counts["MAJOR"] != 0
        ):
            return None
    else:
        blocker = value.get("blocker")
        if set(value) != common | {"blocker"} or (
            blocker is not None and not isinstance(blocker, str)
        ):
            return None
    return value


def _session_exists(tmux_bin: str, socket_name: str | None, session: str) -> bool:
    return _tmux(tmux_bin, socket_name, "has-session", "-t", f"={session}", check=False).returncode == 0


def _metadata(
    tmux_bin: str, socket_name: str | None, session: str
) -> dict[str, str]:
    values: dict[str, str] = {}
    for name, option in _TMUX_METADATA.items():
        result = _tmux(
            tmux_bin,
            socket_name,
            "show-options",
            "-qv",
            "-t",
            session,
            option,
            check=False,
        )
        if result.returncode == 0:
            values[name] = result.stdout.rstrip("\n")
    return values


def _validate_manifest(
    manifest: Mapping[str, Any],
    *,
    repository: str,
    task_ref: str,
    branch: str,
    worktree: Path,
    state_dir: Path,
    session: str,
) -> None:
    expected = {
        "repository": repository,
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "state_dir": str(state_dir),
        "session_name": session,
    }
    mismatches = [
        name for name, value in expected.items() if manifest.get(name) != value
    ]
    if mismatches:
        raise TmuxWorkerError(
            "worker manifest identity mismatch: " + ", ".join(sorted(mismatches))
        )


def _validate_tmux_metadata(
    tmux_bin: str,
    socket_name: str | None,
    session: str,
    expected: Mapping[str, str],
) -> None:
    actual = _metadata(tmux_bin, socket_name, session)
    mismatches = [key for key, value in expected.items() if actual.get(key) != value]
    if mismatches:
        raise TmuxWorkerError(
            "tmux session metadata mismatch: " + ", ".join(sorted(mismatches))
        )


def _pane_state(tmux_bin: str, socket_name: str | None, session: str) -> dict[str, Any]:
    result = _tmux(
        tmux_bin,
        socket_name,
        "list-panes",
        "-t",
        f"={session}",
        "-F",
        "#{pane_dead}\t#{pane_pid}\t#{pane_current_command}\t#{pane_dead_status}",
    )
    lines = result.stdout.rstrip("\n").splitlines()
    if len(lines) != 1:
        raise TmuxWorkerError("worker session must contain exactly one pane")
    fields = lines[0].split("\t")
    if len(fields) != 4:
        raise TmuxWorkerError("tmux returned malformed pane state")
    return {
        "running": fields[0] != "1",
        "pane_dead": fields[0] == "1",
        "pane_pid": int(fields[1]) if fields[1].isdigit() else None,
        "pane_command": fields[2],
        "pane_dead_status": int(fields[3]) if fields[3].lstrip("-").isdigit() else None,
    }


def _write_runtime_files(
    state_dir: Path,
    prompt: str,
    manifest: Mapping[str, Any],
) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(state_dir, 0o700)
    prompt_path = state_dir / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    os.chmod(prompt_path, 0o600)
    _atomic_json(state_dir / "result-schema.json", LEGACY_RESULT_SCHEMA)
    _atomic_json(state_dir / "manifest.json", manifest)


def _worker_command(
    state_dir: Path,
    *,
    mode: str,
    codex_bin: str,
    thread_id: str | None = None,
    attempt_dir: Path | None = None,
) -> list[str]:
    command = [
        sys.executable,
        str(_resolve(__file__)),
        "_run",
        "--state-dir",
        str(state_dir),
        "--mode",
        mode,
        "--codex-bin",
        codex_bin,
    ]
    if attempt_dir is not None:
        command.extend(["--attempt-dir", str(attempt_dir)])
    if thread_id is not None:
        command.extend(["--thread-id", thread_id])
    return command


def _spawn_pane(
    tmux_bin: str,
    socket_name: str | None,
    session: str,
    worktree: Path,
    command: Sequence[str],
    metadata: Mapping[str, str],
) -> None:
    # The retained shell is deliberately created first: remain-on-exit is a pane
    # option and must be installed before the pane is replaced by Codex.
    _tmux(
        tmux_bin,
        socket_name,
        "new-session",
        "-d",
        "-s",
        session,
        "-c",
        str(worktree),
        "while :; do sleep 3600; done",
    )
    try:
        _tmux(
            tmux_bin,
            socket_name,
            "set-option",
            "-p",
            "-t",
            f"={session}:0.0",
            "remain-on-exit",
            "on",
        )
        _install_metadata(tmux_bin, socket_name, session, metadata)
        _tmux(
            tmux_bin,
            socket_name,
            "respawn-pane",
            "-k",
            "-t",
            f"={session}:0.0",
            "-c",
            str(worktree),
            shlex.join(command),
        )
    except Exception:
        _tmux(tmux_bin, socket_name, "kill-session", "-t", f"={session}", check=False)
        raise


def _install_metadata(
    tmux_bin: str,
    socket_name: str | None,
    session: str,
    values: Mapping[str, str],
) -> None:
    for name, option in _TMUX_METADATA.items():
        _tmux(
            tmux_bin,
            socket_name,
            "set-option",
            "-t",
            session,
            option,
            values[name],
        )


def _observer_commands(
    tmux_bin: str, socket_name: str | None, session: str
) -> dict[str, list[str]]:
    return {
        "attach_argv": _tmux_command(
            tmux_bin, socket_name, "attach-session", "-t", f"={session}"
        ),
        "capture_argv": _tmux_command(
            tmux_bin,
            socket_name,
            "capture-pane",
            "-p",
            "-t",
            f"={session}:0.0",
            "-S",
            "-",
        ),
    }


def launch_worker(
    *,
    repo_path: str | Path,
    worktree_path: str | Path,
    task_ref: str,
    branch: str,
    prompt: str,
    repository_identity: str | None = None,
    handoff: Mapping[str, Any] | None = None,
    tmux_socket: str | None = None,
    tmux_bin: str = "tmux",
    codex_bin: str = "codex",
) -> dict[str, Any]:
    primary, common, worktree = _validate_worktree(
        repo_path, worktree_path, branch, task_ref
    )
    tmux_executable = _executable(tmux_bin, "tmux")
    codex_executable = _executable(codex_bin, "Codex")
    repository = repository_identity or _canonical_repository(primary, common)
    session = stable_session_name(repository, task_ref)
    state_dir = _state_dir(primary, repository, task_ref)
    if state_dir.exists():
        existing = _read_manifest(state_dir)
        _validate_manifest(
            existing,
            repository=repository,
            task_ref=task_ref,
            branch=branch,
            worktree=worktree,
            state_dir=state_dir,
            session=session,
        )
        raise TmuxWorkerError(
            f"worker runtime already exists; inspect or resume it: {state_dir}"
        )
    if _session_exists(tmux_executable, tmux_socket, session):
        raise TmuxWorkerError(f"tmux session collision: {session}")

    manifest: dict[str, Any] = {
        "version": 2 if handoff is not None else 1,
        "repository": repository,
        "canonical_repository": _canonical_repository(primary, common),
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "state_dir": str(state_dir),
        "session_name": session,
        "tmux_socket": tmux_socket,
        "codex_bin": codex_executable,
        "created_at": time.time(),
    }
    if handoff is not None:
        resolved_handoff = dict(handoff)
        resolved_handoff["worker_runtime"] = "tmux"
        resolved_handoff["runtime"] = {
            "session_name": session,
            "state_dir": str(state_dir),
        }
        manifest["handoff"] = resolved_handoff
    state_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(state_dir, 0o700)
    _atomic_json(state_dir / "manifest.json", manifest)
    attempt: Path | None = None
    phase: str | None = None
    if handoff is None:
        _write_runtime_files(state_dir, prompt, manifest)
    else:
        phase = _initial_phase(resolved_handoff)
        attempt_id = _attempt_id(1)
        attempt, _ = _write_attempt(
            state_dir,
            manifest,
            attempt_id=attempt_id,
            phase=phase,
            live=_initial_live_snapshot(resolved_handoff),
            parent_attempt_id=None,
            mode="fresh",
        )
        _atomic_json(
            state_dir / "active.json",
            {"attempt_id": attempt_id, "phase": phase, "started": False},
        )
    metadata = {
        "repository": repository,
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "state_dir": str(state_dir),
    }
    try:
        _spawn_pane(
            tmux_executable,
            tmux_socket,
            session,
            worktree,
            _worker_command(
                state_dir,
                mode="fresh",
                codex_bin=codex_executable,
                attempt_dir=attempt,
            ),
            metadata,
        )
        if attempt is not None:
            _atomic_json(
                state_dir / "active.json",
                {
                    "attempt_id": attempt.name,
                    "phase": phase,
                    "started": True,
                },
            )
    except Exception:
        # Provisioning failed before Codex could be trusted as a worker. Runtime
        # evidence is intentionally retained for diagnosis.
        raise
    return {
        "action": "launched",
        "session_name": session,
        "state_dir": str(state_dir),
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "running": True,
        "attempt_id": attempt.name if attempt is not None else None,
        "phase": phase,
        **_observer_commands(tmux_executable, tmux_socket, session),
    }


def _identity(
    repo_path: str | Path,
    worktree_path: str | Path,
    task_ref: str,
    branch: str,
    repository_identity: str | None,
    tmux_socket: str | None,
    *,
    require_registered_worktree: bool,
) -> tuple[str, Path, Path, str]:
    primary, common = _repository(repo_path)
    worktree = _resolve(worktree_path)
    repository = repository_identity or _canonical_repository(primary, common)
    state_dir = _state_dir(primary, repository, task_ref)
    session = stable_session_name(repository, task_ref)
    manifest = _read_manifest(state_dir)
    canonical_repository = _canonical_repository(primary, common)
    if manifest.get("canonical_repository") != canonical_repository:
        raise TmuxWorkerError("worker manifest canonical repository no longer matches Git")
    if manifest.get("tmux_socket") != tmux_socket:
        raise TmuxWorkerError(
            "worker manifest tmux socket mismatch; refusing cross-server recovery"
        )
    _validate_manifest(
        manifest,
        repository=repository,
        task_ref=task_ref,
        branch=branch,
        worktree=worktree,
        state_dir=state_dir,
        session=session,
    )
    if require_registered_worktree:
        validated_primary, validated_common, validated_worktree = _validate_worktree(
            repo_path, worktree_path, branch, task_ref
        )
        if (
            validated_primary != primary
            or validated_common != common
            or validated_worktree != worktree
        ):
            raise TmuxWorkerError("registered worktree repository identity changed")
    return repository, worktree, state_dir, session


def inspect_worker(
    *,
    repo_path: str | Path,
    worktree_path: str | Path,
    task_ref: str,
    branch: str,
    repository_identity: str | None = None,
    tmux_socket: str | None = None,
    tmux_bin: str = "tmux",
) -> dict[str, Any]:
    tmux_executable = _executable(tmux_bin, "tmux")
    repository, worktree, state_dir, session = _identity(
        repo_path,
        worktree_path,
        task_ref,
        branch,
        repository_identity,
        tmux_socket,
        require_registered_worktree=False,
    )
    manifest = _read_manifest(state_dir)
    managed = _is_managed(manifest)
    active: dict[str, Any] | None = _active_attempt(state_dir) if managed else None
    runtime_dir = (
        _attempt_dir(state_dir, str(active["attempt_id"])) if active else state_dir
    )
    exists = _session_exists(tmux_executable, tmux_socket, session)
    thread_id = _parse_thread_id(runtime_dir / "events.jsonl")
    if thread_id:
        _atomic_json(
            state_dir / "session.json",
            {
                "thread_id": thread_id,
                "attempt_id": active["attempt_id"] if active else None,
            },
        )
    result = _read_result(
        runtime_dir / "result.json",
        task_ref,
        expected_phase=str(active["phase"]) if active else None,
        expected_attempt_id=str(active["attempt_id"]) if active else None,
        managed=managed,
        require_dot_spec=managed
        and isinstance(manifest.get("handoff"), Mapping)
        and isinstance(manifest["handoff"].get("dot_spec"), Mapping),
    )
    exit_data: dict[str, Any] | None = None
    try:
        raw_exit = json.loads((runtime_dir / "exit.json").read_text(encoding="utf-8"))
        if isinstance(raw_exit, dict):
            exit_data = raw_exit
    except (OSError, json.JSONDecodeError):
        pass
    response: dict[str, Any] = {
        "action": "inspected",
        "session_name": session,
        "state_dir": str(state_dir),
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "session_exists": exists,
        "thread_id": thread_id,
        "result": result,
        "exit": exit_data,
        "managed": managed,
        "attempt_id": active["attempt_id"] if active else None,
        "phase": active["phase"] if active else None,
        **_observer_commands(tmux_executable, tmux_socket, session),
    }
    if not exists:
        response.update({"running": False, "pane_dead": None, "tmux_lost": True})
        return response
    expected = {
        "repository": repository,
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "state_dir": str(state_dir),
    }
    _validate_tmux_metadata(tmux_executable, tmux_socket, session, expected)
    response.update(_pane_state(tmux_executable, tmux_socket, session))
    response["tmux_lost"] = False
    process_failed = (
        not response["running"]
        and exit_data is not None
        and exit_data.get("exit_code") not in (None, 0)
    )
    if process_failed:
        response["reported_result"] = result
        response["result"] = {
            "status": "failed",
            "task_ref": task_ref,
            "summary": f"worker process exited with status {exit_data.get('exit_code')}",
        }
    elif not response["running"] and result is None:
        response["result"] = {
            "status": "failed",
            "task_ref": task_ref,
            "summary": "worker process exited without a valid structured result",
        }
    elif (
        not response["running"]
        and managed
        and result is not None
        and result.get("status") == "checkpoint"
        and (exit_data is None or exit_data.get("exit_code") != 0)
    ):
        response["reported_result"] = result
        response["result"] = {
            "status": "failed",
            "task_ref": task_ref,
            "summary": "transition is not backed by a completed zero-exit attempt",
        }
    return response


def _next_attempt_id(state_dir: Path) -> str:
    attempts = state_dir / "attempts"
    numbers = [
        int(path.name)
        for path in attempts.iterdir()
        if path.is_dir() and re.fullmatch(r"[0-9]{6}", path.name)
    ]
    return _attempt_id((max(numbers) if numbers else 0) + 1)


def _derived_successor(result: Mapping[str, Any]) -> str:
    phase = result.get("phase")
    if phase == "work":
        return "review"
    if phase == "fix":
        checkpoint = result.get("checkpoint")
        if not isinstance(checkpoint, Mapping) or checkpoint.get(
            "unhandled_finding_count"
        ) != 0:
            raise TmuxWorkerError("fix checkpoint has an undrained finding queue")
        return "review"
    if phase == "review":
        checkpoint = result.get("checkpoint")
        if not isinstance(checkpoint, Mapping):
            raise TmuxWorkerError("review checkpoint is missing evidence")
        counts = checkpoint.get("findings_by_severity")
        if not isinstance(counts, Mapping):
            raise TmuxWorkerError("review checkpoint is missing finding counts")
        material_counts = (counts.get("CRITICAL"), counts.get("MAJOR"))
        if any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in material_counts
        ):
            raise TmuxWorkerError("review checkpoint has invalid material finding counts")
        material = sum(material_counts)
        if material == 0 and (
            checkpoint.get("queued_finding_count") != 0
            or checkpoint.get("unhandled_finding_count") != 0
        ):
            raise TmuxWorkerError(
                "materially clean review checkpoint still has an actionable queue"
            )
        return "fix" if material > 0 else "handoff"
    raise TmuxWorkerError(f"phase {phase!r} cannot advance")


def _attempt_result(
    state_dir: Path,
    manifest: Mapping[str, Any],
    active: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    attempt = _attempt_dir(state_dir, str(active["attempt_id"]))
    exit_data = _read_json(attempt / "exit.json")
    if exit_data is None or exit_data.get("exit_code") != 0:
        raise TmuxWorkerError("active attempt does not have a completed zero exit")
    result = _read_result(
        attempt / "result.json",
        str(manifest["task_ref"]),
        expected_phase=str(active["phase"]),
        expected_attempt_id=str(active["attempt_id"]),
        managed=True,
        require_dot_spec=isinstance(manifest.get("handoff"), Mapping)
        and isinstance(manifest["handoff"].get("dot_spec"), Mapping),
    )
    if result is None or result.get("status") != "checkpoint":
        raise TmuxWorkerError(
            "active attempt does not have an advanceable checkpoint"
        )
    return result, exit_data


def _start_managed_attempt(
    *,
    state_dir: Path,
    manifest: Mapping[str, Any],
    worktree: Path,
    session: str,
    tmux_executable: str,
    tmux_socket: str | None,
    codex_executable: str,
    phase: str,
    live: Mapping[str, Any],
    parent_attempt_id: str,
    mode: str,
    thread_id: str | None,
    expected_metadata: Mapping[str, str],
    session_exists: bool,
    resume_instruction: str | None = None,
) -> tuple[str, dict[str, Any]]:
    attempt_id = _next_attempt_id(state_dir)
    attempt, snapshot = _write_attempt(
        state_dir,
        manifest,
        attempt_id=attempt_id,
        phase=phase,
        live=live,
        parent_attempt_id=parent_attempt_id,
        mode=mode,
    )
    if resume_instruction:
        prompt_path = attempt / "prompt.txt"
        handoff = manifest["handoff"]
        assert isinstance(handoff, Mapping)
        context_values = dict(handoff)
        context_values.setdefault("task", {"task_ref": manifest["task_ref"]})
        context_values["branch_state"] = dict(live)
        context_path = build_context(
            attempt,
            phase=phase,
            handoff=context_values,
            phase_snapshot=snapshot,
            result_path=attempt / "result.json",
            resume_instruction=resume_instruction,
        )
        prompt_path.write_text(
            context_prompt(phase, context_path, attempt / "result.json"),
            encoding="utf-8",
        )
    previous = _active_attempt(state_dir)
    _atomic_json(
        state_dir / "active.json",
        {
            "attempt_id": attempt_id,
            "phase": phase,
            "started": False,
            "parent_attempt_id": parent_attempt_id,
        },
    )
    command = _worker_command(
        state_dir,
        mode=mode,
        codex_bin=codex_executable,
        thread_id=thread_id,
        attempt_dir=attempt,
    )
    try:
        if session_exists:
            _tmux(
                tmux_executable,
                tmux_socket,
                "respawn-pane",
                "-k",
                "-t",
                f"={session}:0.0",
                "-c",
                str(worktree),
                shlex.join(command),
            )
        else:
            _spawn_pane(
                tmux_executable,
                tmux_socket,
                session,
                worktree,
                command,
                expected_metadata,
            )
    except Exception:
        _atomic_json(state_dir / "active.json", previous)
        raise
    _atomic_json(
        state_dir / "active.json",
        {
            "attempt_id": attempt_id,
            "phase": phase,
            "started": True,
            "parent_attempt_id": parent_attempt_id,
        },
    )
    return attempt_id, snapshot


def advance_worker(
    *,
    repo_path: str | Path,
    worktree_path: str | Path,
    task_ref: str,
    branch: str,
    phase_snapshot: Mapping[str, Any],
    expected_attempt_id: str,
    revalidated: bool,
    repository_identity: str | None = None,
    tmux_socket: str | None = None,
    tmux_bin: str = "tmux",
    codex_bin: str = "codex",
) -> dict[str, Any]:
    if not revalidated:
        raise TmuxWorkerError("managed advance requires caller revalidation")
    tmux_executable = _executable(tmux_bin, "tmux")
    codex_executable = _executable(codex_bin, "Codex")
    repository, worktree, state_dir, session = _identity(
        repo_path,
        worktree_path,
        task_ref,
        branch,
        repository_identity,
        tmux_socket,
        require_registered_worktree=True,
    )
    manifest = _read_manifest(state_dir)
    if not _is_managed(manifest):
        raise TmuxWorkerError("advance requires a managed worker")
    expected_metadata = {
        "repository": repository,
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "state_dir": str(state_dir),
    }
    with _transition_lock(state_dir):
        active = _active_attempt(state_dir)
        if active["attempt_id"] != expected_attempt_id:
            raise TmuxWorkerError(
                f"stale attempt replay: expected {expected_attempt_id}, "
                f"active is {active['attempt_id']}"
            )
        session_exists = _session_exists(tmux_executable, tmux_socket, session)
        if session_exists:
            _validate_tmux_metadata(
                tmux_executable, tmux_socket, session, expected_metadata
            )
            if _pane_state(tmux_executable, tmux_socket, session)["running"]:
                raise TmuxWorkerError("refusing to advance a running worker pane")
        result, _ = _attempt_result(state_dir, manifest, active)
        live = _validate_live_snapshot(phase_snapshot, manifest)
        phase = _derived_successor(result)
        attempt_id, snapshot = _start_managed_attempt(
            state_dir=state_dir,
            manifest=manifest,
            worktree=worktree,
            session=session,
            tmux_executable=tmux_executable,
            tmux_socket=tmux_socket,
            codex_executable=codex_executable,
            phase=phase,
            live=live,
            parent_attempt_id=expected_attempt_id,
            mode="fresh",
            thread_id=None,
            expected_metadata=expected_metadata,
            session_exists=session_exists,
        )
    return {
        "action": "advanced",
        "session_name": session,
        "state_dir": str(state_dir),
        "task_ref": task_ref,
        "attempt_id": attempt_id,
        "phase": phase,
        "snapshot_digest": _json_digest(snapshot),
        "running": True,
        **_observer_commands(tmux_executable, tmux_socket, session),
    }


def _resume_managed_worker(
    *,
    repository: str,
    worktree: Path,
    state_dir: Path,
    session: str,
    task_ref: str,
    branch: str,
    prompt: str,
    revalidated: bool,
    tmux_socket: str | None,
    tmux_executable: str,
    codex_executable: str,
) -> dict[str, Any]:
    manifest = _read_manifest(state_dir)
    expected_metadata = {
        "repository": repository,
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "state_dir": str(state_dir),
    }
    with _transition_lock(state_dir):
        active = _active_attempt(state_dir)
        attempt = _attempt_dir(state_dir, str(active["attempt_id"]))
        session_exists = _session_exists(tmux_executable, tmux_socket, session)
        if session_exists:
            _validate_tmux_metadata(
                tmux_executable, tmux_socket, session, expected_metadata
            )
            if _pane_state(tmux_executable, tmux_socket, session)["running"]:
                raise TmuxWorkerError("refusing to resume a running worker pane")
        elif not revalidated:
            raise TmuxWorkerError(
                "recreating a lost managed tmux session requires caller revalidation"
            )
        completed = _read_json(attempt / "exit.json")
        result = _read_result(
            attempt / "result.json",
            task_ref,
            expected_phase=str(active["phase"]),
            expected_attempt_id=str(active["attempt_id"]),
            managed=True,
            require_dot_spec=isinstance(manifest.get("handoff"), Mapping)
            and isinstance(manifest["handoff"].get("dot_spec"), Mapping),
        )
        if (
            completed is not None
            and completed.get("exit_code") == 0
            and result is not None
            and result.get("status") == "checkpoint"
        ):
            raise TmuxWorkerError("completed transition must advance to a fresh phase")
        thread_id = _parse_thread_id(attempt / "events.jsonl")
        if thread_id is None:
            raise TmuxWorkerError("managed attempt has no exact Codex thread to resume")
        phase_data = _read_json(attempt / "phase-snapshot.json")
        if phase_data is None or not isinstance(phase_data.get("live"), Mapping):
            raise TmuxWorkerError("managed attempt has no reusable live snapshot")
        attempt_id, snapshot = _start_managed_attempt(
            state_dir=state_dir,
            manifest=manifest,
            worktree=worktree,
            session=session,
            tmux_executable=tmux_executable,
            tmux_socket=tmux_socket,
            codex_executable=codex_executable,
            phase=str(active["phase"]),
            live=dict(phase_data["live"]),
            parent_attempt_id=str(active["attempt_id"]),
            mode="resume",
            thread_id=thread_id,
            expected_metadata=expected_metadata,
            session_exists=session_exists,
            resume_instruction=prompt,
        )
    return {
        "action": "resumed",
        "session_name": session,
        "state_dir": str(state_dir),
        "task_ref": task_ref,
        "thread_id": thread_id,
        "attempt_id": attempt_id,
        "phase": active["phase"],
        "snapshot_digest": _json_digest(snapshot),
        "running": True,
        **_observer_commands(tmux_executable, tmux_socket, session),
    }


def resume_worker(
    *,
    repo_path: str | Path,
    worktree_path: str | Path,
    task_ref: str,
    branch: str,
    prompt: str,
    repository_identity: str | None = None,
    fresh: bool = False,
    revalidated: bool = False,
    tmux_socket: str | None = None,
    tmux_bin: str = "tmux",
    codex_bin: str = "codex",
) -> dict[str, Any]:
    tmux_executable = _executable(tmux_bin, "tmux")
    codex_executable = _executable(codex_bin, "Codex")
    repository, worktree, state_dir, session = _identity(
        repo_path,
        worktree_path,
        task_ref,
        branch,
        repository_identity,
        tmux_socket,
        require_registered_worktree=True,
    )
    manifest = _read_manifest(state_dir)
    if _is_managed(manifest):
        if fresh:
            raise TmuxWorkerError(
                "managed phase changes use advance; resume only continues one phase"
            )
        return _resume_managed_worker(
            repository=repository,
            worktree=worktree,
            state_dir=state_dir,
            session=session,
            task_ref=task_ref,
            branch=branch,
            prompt=prompt,
            revalidated=revalidated,
            tmux_socket=tmux_socket,
            tmux_executable=tmux_executable,
            codex_executable=codex_executable,
        )
    expected = {
        "repository": repository,
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "state_dir": str(state_dir),
    }
    session_exists = _session_exists(tmux_executable, tmux_socket, session)
    if session_exists:
        _validate_tmux_metadata(tmux_executable, tmux_socket, session, expected)
        pane = _pane_state(tmux_executable, tmux_socket, session)
        if pane["running"]:
            raise TmuxWorkerError("refusing to resume a running worker pane")
    elif not (fresh and revalidated):
        raise TmuxWorkerError(
            "retained tmux session is missing; recreate it only with fresh mode "
            "after explicit caller revalidation"
        )
    thread_id = _parse_thread_id(state_dir / "events.jsonl")
    if fresh:
        if not revalidated:
            raise TmuxWorkerError("fresh resume requires explicit caller revalidation")
        mode = "fresh"
        thread_id = None
    else:
        if thread_id is None:
            raise TmuxWorkerError(
                "no exact Codex thread ID was recorded; use fresh mode only after revalidation"
            )
        mode = "resume"
    prompt_path = state_dir / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    os.chmod(prompt_path, 0o600)
    for name in ("events.jsonl", "result.json", "exit.json"):
        path = state_dir / name
        if path.exists():
            archived = state_dir / f"{name}.{int(time.time() * 1000)}.previous"
            path.replace(archived)
    command = _worker_command(
        state_dir,
        mode=mode,
        codex_bin=codex_executable,
        thread_id=thread_id,
    )
    if session_exists:
        _tmux(
            tmux_executable,
            tmux_socket,
            "respawn-pane",
            "-k",
            "-t",
            f"={session}:0.0",
            "-c",
            str(worktree),
            shlex.join(command),
        )
    else:
        _spawn_pane(
            tmux_executable,
            tmux_socket,
            session,
            worktree,
            command,
            expected,
        )
    return {
        "action": "resumed" if mode == "resume" else "restarted_fresh",
        "session_name": session,
        "state_dir": str(state_dir),
        "task_ref": task_ref,
        "thread_id": thread_id,
        "running": True,
        **_observer_commands(tmux_executable, tmux_socket, session),
    }


def cleanup_worker(
    *,
    repo_path: str | Path,
    worktree_path: str | Path,
    task_ref: str,
    branch: str,
    repository_identity: str | None = None,
    tmux_socket: str | None = None,
    tmux_bin: str = "tmux",
) -> dict[str, Any]:
    tmux_executable = _executable(tmux_bin, "tmux")
    repository, worktree, state_dir, session = _identity(
        repo_path,
        worktree_path,
        task_ref,
        branch,
        repository_identity,
        tmux_socket,
        require_registered_worktree=False,
    )
    if not _session_exists(tmux_executable, tmux_socket, session):
        raise TmuxWorkerError("exact retained tmux session does not exist")
    expected = {
        "repository": repository,
        "task_ref": task_ref,
        "branch": branch,
        "worktree": str(worktree),
        "state_dir": str(state_dir),
    }
    _validate_tmux_metadata(tmux_executable, tmux_socket, session, expected)
    pane = _pane_state(tmux_executable, tmux_socket, session)
    if pane["running"]:
        raise TmuxWorkerError("refusing to clean up a running worker session")
    _tmux(tmux_executable, tmux_socket, "kill-session", "-t", f"={session}")
    return {
        "action": "session_removed",
        "session_name": session,
        "state_dir": str(state_dir),
        "logs_preserved": True,
        "worktree_preserved": True,
        "branch_preserved": True,
    }


def _run_worker(
    state_dir: Path,
    mode: str,
    codex_bin: str,
    thread_id: str | None,
    attempt_dir: Path | None,
) -> int:
    manifest = _read_manifest(state_dir)
    worktree = _resolve(str(manifest["worktree"]))
    managed = attempt_dir is not None
    runtime_dir = state_dir
    expected_phase: str | None = None
    expected_attempt_id: str | None = None
    if managed:
        runtime_dir = _resolve(attempt_dir)
        if runtime_dir.parent != _resolve(state_dir / "attempts"):
            raise TmuxWorkerError("attempt directory is outside managed runtime")
        attempt = _read_json(runtime_dir / "attempt.json")
        if attempt is None:
            raise TmuxWorkerError("managed attempt metadata is missing")
        expected_attempt_id = attempt.get("attempt_id")
        expected_phase = attempt.get("phase")
        if (
            not isinstance(expected_attempt_id, str)
            or expected_phase not in _PHASES
            or runtime_dir.name != expected_attempt_id
        ):
            raise TmuxWorkerError("managed attempt metadata is malformed")
        active = _active_attempt(state_dir)
        if active.get("attempt_id") != expected_attempt_id:
            raise TmuxWorkerError("refusing to run a stale managed attempt")
    elif _is_managed(manifest):
        raise TmuxWorkerError("managed worker runner requires --attempt-dir")
    prompt_path = runtime_dir / "prompt.txt"
    events_path = runtime_dir / "events.jsonl"
    result_path = runtime_dir / "result.json"
    schema_path = runtime_dir / "result-schema.json"
    command = [codex_bin, "exec", "--dangerously-bypass-approvals-and-sandbox"]
    if mode == "resume":
        if thread_id is None:
            raise TmuxWorkerError("resume runner requires an exact thread ID")
        command.extend(["resume", "--json", "--output-schema", str(schema_path)])
        command.extend(["--output-last-message", str(result_path), thread_id, "-"])
    else:
        command.extend(
            [
                "--json",
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(result_path),
                "-C",
                str(worktree),
                "-",
            ]
        )
    started = time.time()
    with prompt_path.open("rb") as prompt_handle, events_path.open("wb") as events_handle:
        process = subprocess.Popen(
            command,
            cwd=worktree,
            stdin=prompt_handle,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert process.stdout is not None
        for line in process.stdout:
            events_handle.write(line)
            events_handle.flush()
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        return_code = process.wait()
    thread = _parse_thread_id(events_path)
    if thread:
        _atomic_json(
            state_dir / "session.json",
            {"thread_id": thread, "attempt_id": expected_attempt_id},
        )
    _atomic_json(
        runtime_dir / "exit.json",
        {
            "exit_code": return_code,
            "started_at": started,
            "finished_at": time.time(),
            "mode": mode,
            "thread_id": thread,
            "structured_result_valid": _read_result(
                result_path,
                str(manifest["task_ref"]),
                expected_phase=expected_phase,
                expected_attempt_id=expected_attempt_id,
                managed=managed,
                require_dot_spec=managed
                and isinstance(manifest.get("handoff"), Mapping)
                and isinstance(manifest["handoff"].get("dot_spec"), Mapping),
            )
            is not None,
        },
    )
    return return_code


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        print(json.dumps({"ok": False, "error": message}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)


def _add_identity(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", required=True)
    parser.add_argument("--worktree")
    parser.add_argument("--task-ref")
    parser.add_argument("--branch")
    parser.add_argument("--repository-identity")
    parser.add_argument("--handoff", help="managed handoff in JSON or YAML")
    parser.add_argument("--tmux-socket")
    parser.add_argument("--tmux-bin", default="tmux")


def _add_prompt(parser: argparse.ArgumentParser, *, required: bool = True) -> None:
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument("--prompt-file")
    group.add_argument("--prompt-stdin", action="store_true")


def _parser() -> argparse.ArgumentParser:
    parser = _JsonArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    launch = subparsers.add_parser("launch")
    _add_identity(launch)
    _add_prompt(launch, required=False)
    launch.add_argument("--codex-bin", default="codex")
    inspect = subparsers.add_parser("inspect")
    _add_identity(inspect)
    resume = subparsers.add_parser("resume")
    _add_identity(resume)
    _add_prompt(resume)
    resume.add_argument("--codex-bin", default="codex")
    resume.add_argument("--fresh", action="store_true")
    resume.add_argument("--revalidated", action="store_true")
    advance = subparsers.add_parser("advance")
    _add_identity(advance)
    advance.add_argument("--phase-snapshot", required=True)
    advance.add_argument("--expected-attempt-id", required=True)
    advance.add_argument("--revalidated", action="store_true")
    advance.add_argument("--codex-bin", default="codex")
    cleanup = subparsers.add_parser("cleanup")
    _add_identity(cleanup)
    internal = subparsers.add_parser("_run")
    internal.add_argument("--state-dir", required=True)
    internal.add_argument("--mode", choices=("fresh", "resume"), required=True)
    internal.add_argument("--codex-bin", required=True)
    internal.add_argument("--thread-id")
    internal.add_argument("--attempt-dir")
    return parser


def _prompt(args: argparse.Namespace) -> str:
    if getattr(args, "prompt_file", None):
        return _resolve(args.prompt_file).read_text(encoding="utf-8")
    if getattr(args, "prompt_stdin", False):
        return sys.stdin.read()
    return ""


def _arguments(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any] | None]:
    handoff = _load_data(args.handoff) if args.handoff else None
    if handoff is not None:
        task_ref, worktree, branch, repository = _handoff_identity(handoff)
        explicit = {
            "task_ref": args.task_ref,
            "worktree_path": args.worktree,
            "branch": args.branch,
            "repository_identity": args.repository_identity,
        }
        inferred = {
            "task_ref": task_ref,
            "worktree_path": worktree,
            "branch": branch,
            "repository_identity": repository,
        }
        for key, value in explicit.items():
            if value is not None and value != inferred[key]:
                raise TmuxWorkerError(f"explicit {key} contradicts handoff")
        return inferred, handoff
    missing = [
        name
        for name, value in (
            ("--task-ref", args.task_ref),
            ("--worktree", args.worktree),
            ("--branch", args.branch),
        )
        if not value
    ]
    if missing:
        raise TmuxWorkerError("missing identity arguments: " + ", ".join(missing))
    return {
        "task_ref": args.task_ref,
        "worktree_path": args.worktree,
        "branch": args.branch,
        "repository_identity": args.repository_identity,
    }, None


def _discover_inspect_arguments(args: argparse.Namespace) -> dict[str, Any]:
    if not args.task_ref:
        raise TmuxWorkerError("inspect discovery requires --task-ref")
    primary, common = _repository(args.repo)
    repository = args.repository_identity or _canonical_repository(primary, common)
    state_dir = _state_dir(primary, repository, args.task_ref)
    manifest = _read_manifest(state_dir)
    branch = manifest.get("branch")
    worktree = manifest.get("worktree")
    if not isinstance(branch, str) or not branch or not isinstance(worktree, str) or not worktree:
        raise TmuxWorkerError("worker manifest lacks branch or worktree identity")
    session = stable_session_name(repository, args.task_ref)
    if manifest.get("canonical_repository") != _canonical_repository(primary, common):
        raise TmuxWorkerError("worker manifest canonical repository no longer matches Git")
    if manifest.get("tmux_socket") != args.tmux_socket:
        raise TmuxWorkerError(
            "worker manifest tmux socket mismatch; refusing cross-server discovery"
        )
    _validate_manifest(
        manifest,
        repository=repository,
        task_ref=args.task_ref,
        branch=branch,
        worktree=_resolve(worktree),
        state_dir=state_dir,
        session=session,
    )
    return {
        "task_ref": args.task_ref,
        "worktree_path": worktree,
        "branch": branch,
        "repository_identity": args.repository_identity,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command == "_run":
        try:
            return _run_worker(
                _resolve(args.state_dir),
                args.mode,
                args.codex_bin,
                args.thread_id,
                _resolve(args.attempt_dir) if args.attempt_dir else None,
            )
        except (TmuxWorkerError, OSError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2
    try:
        if (
            args.command == "inspect"
            and not args.handoff
            and args.task_ref
            and (not args.worktree or not args.branch)
        ):
            identity, handoff = _discover_inspect_arguments(args), None
        else:
            identity, handoff = _arguments(args)
        common = {
            "repo_path": args.repo,
            **identity,
            "tmux_socket": args.tmux_socket,
            "tmux_bin": args.tmux_bin,
        }
        if args.command == "launch":
            if handoff is None and not (args.prompt_file or args.prompt_stdin):
                raise TmuxWorkerError("launch requires --handoff or prompt input")
            result = launch_worker(
                **common,
                prompt=_prompt(args),
                handoff=handoff,
                codex_bin=args.codex_bin,
            )
        elif args.command == "inspect":
            result = inspect_worker(**common)
        elif args.command == "resume":
            result = resume_worker(
                **common,
                prompt=_prompt(args),
                fresh=args.fresh,
                revalidated=args.revalidated,
                codex_bin=args.codex_bin,
            )
        elif args.command == "advance":
            result = advance_worker(
                **common,
                phase_snapshot=_load_data(args.phase_snapshot),
                expected_attempt_id=args.expected_attempt_id,
                revalidated=args.revalidated,
                codex_bin=args.codex_bin,
            )
        else:
            result = cleanup_worker(**common)
    except (TmuxWorkerError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
