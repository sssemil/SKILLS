#!/usr/bin/env python3
"""Build small, content-addressed context envelopes for Brutal workers."""

from __future__ import annotations

import hashlib
import fcntl
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Mapping, Sequence


MAX_PROMPT_BYTES = 2 * 1024
MAX_GUIDE_BYTES = 12 * 1024
MAX_GUIDE_LINES = 120
MAX_GUIDE_PROPOSALS = 5
MAX_GUIDE_PROJECTION_BYTES = 2 * 1024
DECISION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
MEDIA_TYPE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9!#$&^_.+\-/]*$")


class ContextError(ValueError):
    """Raised when a context artifact violates the harness contract."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _contained(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ContextError(f"path escapes runtime root: {path}")
    return resolved


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(value) + b"\n"
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


@contextmanager
def field_guide_lock(path: Path) -> Iterator[None]:
    lock_path = path.with_name(f"{path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def store_artifact(
    runtime_root: Path,
    content: bytes | str | Mapping[str, Any] | Sequence[Any],
    media_type: str = "application/json",
) -> dict[str, Any]:
    """Store immutable content once and return its exact reference."""

    root = runtime_root.resolve()
    if not MEDIA_TYPE.fullmatch(media_type):
        raise ContextError("media_type is invalid")
    if isinstance(content, str):
        payload = content.encode("utf-8")
    elif isinstance(content, bytes):
        payload = content
    else:
        payload = canonical_json(content) + b"\n"
    digest = hashlib.sha256(payload).hexdigest()
    relative = Path("artifacts") / digest[:2] / digest
    destination = _contained(root, root / relative)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != payload:
            raise ContextError(f"artifact collision at {destination}")
    else:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{digest}.", dir=str(destination.parent)
        )
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, destination)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
    return {
        "path": relative.as_posix(),
        "sha256": digest,
        "bytes": len(payload),
        "media_type": media_type,
    }


def validate_artifact_ref(runtime_root: Path, ref: Any) -> Path:
    if not isinstance(ref, Mapping) or set(ref) != {
        "path",
        "sha256",
        "bytes",
        "media_type",
    }:
        raise ContextError("artifact reference has invalid fields")
    if not isinstance(ref["path"], str) or not ref["path"]:
        raise ContextError("artifact path must be a non-empty string")
    path = PurePosixPath(ref["path"])
    if path.is_absolute() or ".." in path.parts:
        raise ContextError("artifact path must be runtime-relative")
    if not isinstance(ref["sha256"], str) or not SHA256.fullmatch(ref["sha256"]):
        raise ContextError("artifact sha256 is invalid")
    if (
        not isinstance(ref["bytes"], int)
        or isinstance(ref["bytes"], bool)
        or ref["bytes"] < 0
    ):
        raise ContextError("artifact bytes is invalid")
    if not isinstance(ref["media_type"], str) or not MEDIA_TYPE.fullmatch(
        ref["media_type"]
    ):
        raise ContextError("artifact media_type is invalid")
    destination = _contained(runtime_root, runtime_root / Path(*path.parts))
    try:
        payload = destination.read_bytes()
    except OSError as exc:
        raise ContextError(f"cannot read artifact {destination}: {exc}") from exc
    if len(payload) != ref["bytes"]:
        raise ContextError(f"artifact size mismatch: {ref['path']}")
    if hashlib.sha256(payload).hexdigest() != ref["sha256"]:
        raise ContextError(f"artifact digest mismatch: {ref['path']}")
    return destination


def _decision_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not DECISION_ID.fullmatch(value):
        raise ContextError(f"{label} must match {DECISION_ID.pattern}")
    return value


def _repo_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContextError(f"{label} must be a non-empty string")
    path = PurePosixPath(value.strip())
    if path.is_absolute() or ".." in path.parts or path.as_posix() in {"", "."}:
        raise ContextError(f"{label} must be repository-relative")
    return path.as_posix().rstrip("/")


def normalize_coordination(value: Any) -> dict[str, Any]:
    data = {} if value is None else value
    if not isinstance(data, Mapping):
        raise ContextError("coordination must be an object")
    owned_value = data.get("decisions_owned", [])
    consumed_value = data.get("decisions_consumed", [])
    surfaces_value = data.get("touch_surfaces", [])
    if not all(isinstance(item, list) for item in (owned_value, consumed_value, surfaces_value)):
        raise ContextError("coordination fields must be arrays")
    owned: list[dict[str, str]] = []
    for index, item in enumerate(owned_value):
        if not isinstance(item, Mapping) or set(item) != {"id", "statement"}:
            raise ContextError(f"decisions_owned[{index}] has invalid fields")
        decision_id = _decision_id(item["id"], f"decisions_owned[{index}].id")
        if not isinstance(item["statement"], str) or not item["statement"].strip():
            raise ContextError(f"decisions_owned[{index}].statement is required")
        owned.append({"id": decision_id, "statement": item["statement"].strip()})
    consumed = [
        _decision_id(item, f"decisions_consumed[{index}]")
        for index, item in enumerate(consumed_value)
    ]
    surfaces: list[dict[str, Any]] = []
    for index, item in enumerate(surfaces_value):
        if not isinstance(item, Mapping) or set(item) != {
            "path",
            "kind",
            "parallel_safe",
        }:
            raise ContextError(f"touch_surfaces[{index}] has invalid fields")
        kind = item["kind"]
        if kind not in {"file", "prefix"}:
            raise ContextError(f"touch_surfaces[{index}].kind is invalid")
        if not isinstance(item["parallel_safe"], bool):
            raise ContextError(f"touch_surfaces[{index}].parallel_safe must be boolean")
        surfaces.append(
            {
                "path": _repo_path(item["path"], f"touch_surfaces[{index}].path"),
                "kind": kind,
                "parallel_safe": item["parallel_safe"],
            }
        )
    ids = [item["id"] for item in owned]
    if len(ids) != len(set(ids)) or len(consumed) != len(set(consumed)):
        raise ContextError("coordination contains duplicate decision IDs")
    return {
        "decisions_owned": sorted(owned, key=lambda item: item["id"]),
        "decisions_consumed": sorted(consumed),
        "touch_surfaces": sorted(
            surfaces, key=lambda item: (item["path"], item["kind"])
        ),
    }


def build_task_capsule(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContextError("task capsule must be an object")
    task = value.get("task")
    if not isinstance(task, Mapping):
        raise ContextError("task capsule requires task")
    required = ("ref", "kind", "title", "goal", "acceptance_criteria", "blockers")
    if any(key not in task for key in required):
        raise ContextError("task capsule task is incomplete")
    for key in ("ref", "kind", "title", "goal"):
        if not isinstance(task[key], str) or not task[key].strip():
            raise ContextError(f"task.{key} must be a non-empty string")
    if not isinstance(task["acceptance_criteria"], list) or not isinstance(
        task["blockers"], list
    ):
        raise ContextError("task acceptance_criteria and blockers must be arrays")
    commands = value.get("verification_commands", [])
    artifacts = value.get("artifacts", {})
    if not isinstance(commands, list) or not all(
        isinstance(command, str) and command.strip() for command in commands
    ):
        raise ContextError("verification_commands must be non-empty strings")
    if not isinstance(artifacts, Mapping):
        raise ContextError("artifacts must be an object")
    for name, ref in artifacts.items():
        if not isinstance(name, str) or not name:
            raise ContextError("artifact names must be non-empty strings")
        if not isinstance(ref, Mapping) or set(ref) != {
            "path",
            "sha256",
            "bytes",
            "media_type",
        }:
            raise ContextError(f"artifact {name!r} has an invalid reference")
    return {
        "schema_version": 1,
        "task": {
            "ref": task["ref"].strip(),
            "kind": task["kind"].strip(),
            "title": task["title"].strip(),
            "goal": task["goal"].strip(),
            "acceptance_criteria": list(task["acceptance_criteria"]),
            "blockers": list(task["blockers"]),
        },
        "coordination": normalize_coordination(value.get("coordination")),
        "verification_commands": [command.strip() for command in commands],
        "artifacts": dict(artifacts),
    }


def build_phase_manifest(
    runtime_root: Path,
    *,
    phase: str,
    task_capsule: Mapping[str, Any],
    phase_snapshot: Mapping[str, Any],
    projections: Mapping[str, Any] | None = None,
    outputs: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], str]:
    normalized_capsule = build_task_capsule(task_capsule)
    for ref in normalized_capsule["artifacts"].values():
        validate_artifact_ref(runtime_root, ref)
    capsule_ref = store_artifact(runtime_root, normalized_capsule)
    snapshot_ref = store_artifact(runtime_root, phase_snapshot)
    projection_refs: dict[str, Any] = {}
    for name, content in sorted((projections or {}).items()):
        projection_refs[name] = store_artifact(runtime_root, content)
    manifest = {
        "schema_version": 3,
        "phase": phase,
        "task_capsule": capsule_ref,
        "phase_snapshot": snapshot_ref,
        "projections": projection_refs,
        "outputs": dict(outputs or {}),
    }
    for ref in (capsule_ref, snapshot_ref, *projection_refs.values()):
        validate_artifact_ref(runtime_root, ref)
    return manifest, digest_json(manifest)


def normalize_decision_registry(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ContextError("decision registry must be an array")
    decisions: list[dict[str, str]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, Mapping) or set(raw) != {"id", "statement"}:
            raise ContextError(f"decision registry item {index} has invalid fields")
        decision_id = _decision_id(raw["id"], f"decision registry item {index} id")
        statement = raw["statement"]
        if not isinstance(statement, str) or not statement.strip():
            raise ContextError(f"decision registry item {index} statement is required")
        decisions.append({"id": decision_id, "statement": statement.strip()})
    ids = [item["id"] for item in decisions]
    if len(ids) != len(set(ids)):
        raise ContextError("decision registry contains duplicate owners")
    return sorted(decisions, key=lambda item: item["id"])


def build_phase_prompt(phase: str, manifest_path: Path, context_digest: str) -> str:
    if not SHA256.fullmatch(context_digest):
        raise ContextError("context_digest is invalid")
    prompt = (
        "Use $brutal-worker for exactly one managed phase.\n"
        f"phase={phase}\nmanifest={manifest_path}\ncontext_digest={context_digest}\n"
        "Validate every referenced artifact before use. Return the phase result with "
        "this exact context_digest.\n"
    )
    if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise ContextError("managed phase prompt exceeds 2 KiB")
    return prompt


REVIEW_LENS_FIELDS: dict[str, frozenset[str]] = {
    "product": frozenset({"acceptance", "diff_summary"}),
    "correctness": frozenset({"diff", "relevant_code", "callers"}),
    "reliability": frozenset({"tests", "checks", "failure_summaries"}),
    "security-performance": frozenset(
        {"exposed_surfaces", "concurrency", "resource_summary"}
    ),
    "simplicity": frozenset({"diff", "style_guide"}),
}


def review_lens_projection(lens: str, context: Mapping[str, Any]) -> dict[str, Any]:
    allowed = REVIEW_LENS_FIELDS.get(lens)
    if allowed is None:
        raise ContextError(f"unknown review lens: {lens}")
    return {key: context[key] for key in sorted(allowed) if key in context}


def load_field_guide(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "revision": 0, "entries": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextError(f"cannot read Field Guide {path}: {exc}") from exc
    if (
        not isinstance(value, Mapping)
        or value.get("schema_version") != 1
        or not isinstance(value.get("revision"), int)
        or not isinstance(value.get("entries"), list)
    ):
        raise ContextError("Field Guide is malformed")
    return dict(value)


def _guide_fits(value: Mapping[str, Any]) -> bool:
    rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return (
        len(rendered.encode("utf-8")) <= MAX_GUIDE_BYTES
        and len(rendered.splitlines()) <= MAX_GUIDE_LINES
    )


def merge_field_guide(
    path: Path,
    proposals: Sequence[Mapping[str, Any]],
    *,
    current_blob_shas: Mapping[str, str],
) -> dict[str, Any]:
    """Merge evidence-backed worker proposals; only the controller calls this."""

    if len(proposals) > MAX_GUIDE_PROPOSALS:
        raise ContextError("a phase may propose at most five Field Guide entries")
    guide = load_field_guide(path)
    revision = guide["revision"] + 1
    existing: dict[str, dict[str, Any]] = {}
    for raw in guide["entries"]:
        if not isinstance(raw, Mapping) or not isinstance(raw.get("id"), str):
            continue
        evidence = raw.get("evidence", [])
        if not isinstance(evidence, list) or any(
            not isinstance(item, Mapping)
            or current_blob_shas.get(item.get("path")) != item.get("blob_sha")
            for item in evidence
        ):
            continue
        existing[raw["id"]] = dict(raw)
    for raw in proposals:
        if not isinstance(raw, Mapping):
            raise ContextError("Field Guide proposal must be an object")
        entry_id = _decision_id(raw.get("id"), "Field Guide proposal id")
        text = raw.get("text")
        tags = raw.get("tags", [])
        evidence = raw.get("evidence", [])
        if not isinstance(text, str) or not text.strip():
            raise ContextError("Field Guide proposal text is required")
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ContextError("Field Guide proposal tags are invalid")
        if not isinstance(evidence, list) or not evidence:
            raise ContextError("Field Guide proposal requires evidence")
        normalized_evidence: list[dict[str, str]] = []
        for item in evidence:
            if not isinstance(item, Mapping):
                raise ContextError("Field Guide evidence is invalid")
            repo_path = _repo_path(item.get("path"), "Field Guide evidence path")
            blob_sha = item.get("blob_sha")
            if not isinstance(blob_sha, str) or current_blob_shas.get(repo_path) != blob_sha:
                raise ContextError(f"Field Guide evidence is stale: {repo_path}")
            normalized_evidence.append({"path": repo_path, "blob_sha": blob_sha})
        existing[entry_id] = {
            "id": entry_id,
            "text": text.strip(),
            "tags": sorted(set(tags)),
            "evidence": sorted(normalized_evidence, key=lambda item: item["path"]),
            "last_used_revision": revision,
        }
    entries = sorted(
        existing.values(), key=lambda item: (item.get("last_used_revision", 0), item["id"])
    )
    value = {"schema_version": 1, "revision": revision, "entries": entries}
    while entries and not _guide_fits(value):
        entries.pop(0)
        value = {"schema_version": 1, "revision": revision, "entries": entries}
    if not _guide_fits(value):
        raise ContextError("Field Guide metadata exceeds its budget")
    atomic_json(path, value)
    return value


def project_field_guide(
    guide: Mapping[str, Any], *, touch_paths: Iterable[str], tags: Iterable[str] = ()
) -> dict[str, Any]:
    paths = tuple(_repo_path(path, "touch path") for path in touch_paths)
    wanted_tags = set(tags)
    selected: list[dict[str, Any]] = []
    for raw in guide.get("entries", []):
        if not isinstance(raw, Mapping):
            continue
        evidence_paths = [item.get("path", "") for item in raw.get("evidence", [])]
        path_match = any(
            evidence == path or evidence.startswith(path + "/") or path.startswith(evidence + "/")
            for evidence in evidence_paths
            for path in paths
        )
        if path_match or wanted_tags.intersection(raw.get("tags", [])):
            selected.append(dict(raw))
    selected.sort(key=lambda item: (-item.get("last_used_revision", 0), item["id"]))
    projection = {
        "schema_version": 1,
        "guide_revision": guide.get("revision", 0),
        "entries": selected,
    }
    while selected and len(canonical_json(projection)) > MAX_GUIDE_PROJECTION_BYTES:
        selected.pop()
        projection["entries"] = selected
    if len(canonical_json(projection)) > MAX_GUIDE_PROJECTION_BYTES:
        raise ContextError("Field Guide projection exceeds 2 KiB")
    return projection


def touch_field_guide(path: Path, entry_ids: Iterable[str]) -> dict[str, Any]:
    """Record controller-observed use so eviction is true deterministic LRU."""

    wanted = set(entry_ids)
    guide = load_field_guide(path)
    if not wanted:
        return guide
    revision = guide["revision"] + 1
    entries = [dict(entry) for entry in guide["entries"] if isinstance(entry, Mapping)]
    for entry in entries:
        if entry.get("id") in wanted:
            entry["last_used_revision"] = revision
    entries.sort(key=lambda item: (item.get("last_used_revision", 0), item["id"]))
    value = {"schema_version": 1, "revision": revision, "entries": entries}
    while entries and not _guide_fits(value):
        entries.pop(0)
        value["entries"] = entries
    if not _guide_fits(value):
        raise ContextError("Field Guide metadata exceeds its budget")
    atomic_json(path, value)
    return value
