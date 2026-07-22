#!/usr/bin/env python3
"""Normalize a Brutal task graph and select one deterministic worker wave."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


TASK_TYPES = frozenset({"task", "review_finding"})
TASK_STATES = frozenset(
    {"todo", "in_progress", "in_review", "done", "canceled"}
)
PR_STATES = frozenset({"open", "closed", "merged"})
REVIEW_GATES = frozenset({"not_ready", "zero_findings", "materially_clean"})
STACK_READY_REVIEW_GATES = frozenset({"zero_findings", "materially_clean"})
DECISION_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


class InputError(ValueError):
    """Raised when scheduler input does not match the normalized contract."""


def _object(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InputError(f"{path} must be an object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{path} must be a non-empty string")
    return value.strip()


def _optional_bool(value: Any, path: str, default: bool = False) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise InputError(f"{path} must be a boolean")
    return value


def _normalize_ref(value: Any, path: str) -> dict[str, str]:
    ref = _object(value, path)
    return {
        "branch": _string(ref.get("branch"), f"{path}.branch"),
        "sha": _string(ref.get("sha"), f"{path}.sha"),
    }


def _optional_string(value: Any, path: str) -> str | None:
    return None if value is None else _string(value, path)


def _normalize_pr(value: Any, path: str) -> dict[str, Any] | None:
    if value is None:
        return None
    pr = _object(value, path)
    state = _string(pr.get("state"), f"{path}.state").lower()
    if state not in PR_STATES:
        expected = ", ".join(sorted(PR_STATES))
        raise InputError(f"{path}.state must be one of: {expected}")

    clean_value = pr.get("clean")
    clean = None
    if clean_value is not None:
        if not isinstance(clean_value, bool):
            raise InputError(f"{path}.clean must be a boolean")
        clean = clean_value

    review_gate_value = pr.get("review_gate")
    review_gate = None
    if review_gate_value is not None:
        review_gate = _string(review_gate_value, f"{path}.review_gate").lower()
        if review_gate not in REVIEW_GATES:
            expected = ", ".join(sorted(REVIEW_GATES))
            raise InputError(f"{path}.review_gate must be one of: {expected}")

    normalized: dict[str, Any] = {
        "state": state,
        "branch": _optional_string(pr.get("branch"), f"{path}.branch"),
        "base_branch": _optional_string(
            pr.get("base_branch"), f"{path}.base_branch"
        ),
        "head_sha": _optional_string(pr.get("head_sha"), f"{path}.head_sha"),
        "clean": clean,
        "review_gate": review_gate,
        "needs_reconcile": _optional_bool(
            pr.get("needs_reconcile"), f"{path}.needs_reconcile"
        ),
    }
    if "number" in pr:
        number = pr["number"]
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise InputError(f"{path}.number must be a positive integer")
        normalized["number"] = number
    return normalized


def _normalize_order_key(value: Any, path: str) -> str | int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise InputError(f"{path} must be a non-empty string or integer")
    if isinstance(value, str):
        return _string(value, path)
    return value


def _normalize_decision_id(value: Any, path: str) -> str:
    decision_id = _string(value, path)
    if not DECISION_ID.fullmatch(decision_id):
        raise InputError(f"{path} must match {DECISION_ID.pattern}")
    return decision_id


def _normalize_coordination(task: Mapping[str, Any], path: str) -> tuple[dict[str, Any], bool]:
    nested = task.get("coordination")
    if nested is not None and not isinstance(nested, Mapping):
        raise InputError(f"{path}.coordination must be an object")
    source = nested if isinstance(nested, Mapping) else task
    fields = ("decisions_owned", "decisions_consumed", "touch_surfaces")
    scoped = nested is not None or any(field in task for field in fields)
    values = [source.get(field, []) for field in fields]
    if not all(isinstance(value, list) for value in values):
        raise InputError(f"{path} coordination fields must be arrays")
    owned: list[dict[str, str]] = []
    for index, raw in enumerate(values[0]):
        item = _object(raw, f"{path}.decisions_owned[{index}]")
        if set(item) != {"id", "statement"}:
            raise InputError(
                f"{path}.decisions_owned[{index}] requires only id and statement"
            )
        owned.append(
            {
                "id": _normalize_decision_id(
                    item.get("id"), f"{path}.decisions_owned[{index}].id"
                ),
                "statement": _string(
                    item.get("statement"),
                    f"{path}.decisions_owned[{index}].statement",
                ),
            }
        )
    consumed = [
        _normalize_decision_id(raw, f"{path}.decisions_consumed[{index}]")
        for index, raw in enumerate(values[1])
    ]
    surfaces: list[dict[str, Any]] = []
    for index, raw in enumerate(values[2]):
        item = _object(raw, f"{path}.touch_surfaces[{index}]")
        if set(item) != {"path", "kind", "parallel_safe"}:
            raise InputError(
                f"{path}.touch_surfaces[{index}] requires path, kind, parallel_safe"
            )
        raw_path = _string(item.get("path"), f"{path}.touch_surfaces[{index}].path")
        surface_path = PurePosixPath(raw_path)
        if (
            surface_path.is_absolute()
            or ".." in surface_path.parts
            or surface_path.as_posix() in {"", "."}
        ):
            raise InputError(
                f"{path}.touch_surfaces[{index}].path must be repository-relative"
            )
        kind = _string(item.get("kind"), f"{path}.touch_surfaces[{index}].kind")
        if kind not in {"file", "prefix"}:
            raise InputError(f"{path}.touch_surfaces[{index}].kind is invalid")
        surfaces.append(
            {
                "path": surface_path.as_posix().rstrip("/"),
                "kind": kind,
                "parallel_safe": _optional_bool(
                    item.get("parallel_safe"),
                    f"{path}.touch_surfaces[{index}].parallel_safe",
                ),
            }
        )
    owned_ids = [item["id"] for item in owned]
    if len(owned_ids) != len(set(owned_ids)) or len(consumed) != len(set(consumed)):
        raise InputError(f"{path} coordination contains duplicate decision IDs")
    return {
        "decisions_owned": sorted(owned, key=lambda item: item["id"]),
        "decisions_consumed": sorted(consumed),
        "touch_surfaces": sorted(surfaces, key=lambda item: (item["path"], item["kind"])),
    }, not scoped


def _normalize_decision_registry(value: Any) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise InputError("decision_registry must be an array")
    decisions: list[dict[str, str]] = []
    for index, raw in enumerate(value):
        item = _object(raw, f"decision_registry[{index}]")
        if set(item) != {"id", "statement"}:
            raise InputError(f"decision_registry[{index}] requires only id and statement")
        decisions.append(
            {
                "id": _normalize_decision_id(item.get("id"), f"decision_registry[{index}].id"),
                "statement": _string(
                    item.get("statement"), f"decision_registry[{index}].statement"
                ),
            }
        )
    ids = [item["id"] for item in decisions]
    if len(ids) != len(set(ids)):
        raise InputError("decision_registry contains duplicate IDs")
    return sorted(decisions, key=lambda item: item["id"])


def _order_sort_key(value: str | int) -> tuple[int, str | int]:
    return (0, value) if isinstance(value, int) else (1, value)


def _dependency_cycle_refs(tasks: Sequence[Mapping[str, Any]]) -> set[str]:
    """Return refs participating in dependency cycles; ignore unknown refs."""

    edges = {task["ref"]: task["blockers"] for task in tasks}
    state: dict[str, int] = {}
    stack: list[str] = []
    positions: dict[str, int] = {}
    cycles: set[str] = set()

    def visit(ref: str) -> None:
        state[ref] = 1
        positions[ref] = len(stack)
        stack.append(ref)
        for blocker in edges[ref]:
            if blocker not in edges:
                continue
            blocker_state = state.get(blocker, 0)
            if blocker_state == 0:
                visit(blocker)
            elif blocker_state == 1:
                cycles.update(stack[positions[blocker] :])
        stack.pop()
        positions.pop(ref, None)
        state[ref] = 2

    for ref in edges:
        if state.get(ref, 0) == 0:
            visit(ref)
    return cycles


def _normalize_task(value: Any, index: int) -> dict[str, Any]:
    path = f"tasks[{index}]"
    task = _object(value, path)
    ref = _string(task.get("ref"), f"{path}.ref")
    task_type = _string(task.get("kind"), f"{path}.kind").lower()
    if task_type not in TASK_TYPES:
        expected = ", ".join(sorted(TASK_TYPES))
        raise InputError(f"{path}.kind must be one of: {expected}")
    state = _string(task.get("state"), f"{path}.state").lower()
    if state not in TASK_STATES:
        expected = ", ".join(sorted(TASK_STATES))
        raise InputError(f"{path}.state must be one of: {expected}")

    blockers_value = task.get("blockers", [])
    if not isinstance(blockers_value, list):
        raise InputError(f"{path}.blockers must be an array")
    blockers = [
        _string(item, f"{path}.blockers[{i}]")
        for i, item in enumerate(blockers_value)
    ]
    if len(set(blockers)) != len(blockers):
        raise InputError(f"{path}.blockers contains duplicate refs")
    if ref in blockers:
        raise InputError(f"{path}.blockers cannot contain its own ref")

    order_key = _normalize_order_key(task.get("order_key"), f"{path}.order_key")
    priority = task.get("priority")
    if priority is not None and (
        not isinstance(priority, int) or isinstance(priority, bool)
    ):
        raise InputError(f"{path}.priority must be an integer")

    def required_bool(field: str) -> bool:
        if field not in task:
            raise InputError(f"{path}.{field} is required")
        return _optional_bool(task[field], f"{path}.{field}")

    coordination, coordination_unscoped = _normalize_coordination(task, path)
    return {
        "ref": ref,
        "kind": task_type,
        "state": state,
        "order_key": order_key,
        "priority": priority,
        "blockers": sorted(blockers),
        "claimable": required_bool("claimable"),
        "decision_complete": required_bool("decision_complete"),
        "owned": required_bool("owned"),
        "branch": _optional_string(task.get("branch"), f"{path}.branch"),
        "base_branch": _optional_string(
            task.get("base_branch"), f"{path}.base_branch"
        ),
        "base_sha": _optional_string(task.get("base_sha"), f"{path}.base_sha"),
        "pr": _normalize_pr(task.get("pr"), f"{path}.pr"),
        "coordination": coordination,
        "coordination_unscoped": coordination_unscoped,
    }


def normalize_graph(payload: Any) -> dict[str, Any]:
    """Validate and normalize scheduler input without mutating it."""

    data = _object(payload, "input")
    root_base = _normalize_ref(data.get("root_base"), "root_base")

    tasks_value = data.get("tasks")
    if not isinstance(tasks_value, list):
        raise InputError("tasks must be an array")
    tasks = [
        _normalize_task(task, index)
        for index, task in enumerate(tasks_value)
    ]
    seen: set[str] = set()
    duplicates: set[str] = set()
    for task in tasks:
        if task["ref"] in seen:
            duplicates.add(task["ref"])
        seen.add(task["ref"])
    if duplicates:
        refs = ", ".join(sorted(duplicates))
        raise InputError(f"duplicate task refs: {refs}")

    limit_value = data.get("limit")
    if limit_value is not None:
        _validate_limit(limit_value)

    return {
        "root_base": root_base,
        "limit": limit_value,
        "decision_registry": _normalize_decision_registry(data.get("decision_registry")),
        "tasks": sorted(
            tasks,
            key=lambda task: (_order_sort_key(task["order_key"]), task["ref"]),
        ),
        "cycle_refs": sorted(_dependency_cycle_refs(tasks)),
    }


def _ancestor_refs(ref: str, by_ref: Mapping[str, Mapping[str, Any]]) -> set[str]:
    found: set[str] = set()
    pending = list(by_ref[ref]["blockers"])
    while pending:
        blocker = pending.pop()
        if blocker in found:
            continue
        found.add(blocker)
        if blocker in by_ref:
            pending.extend(by_ref[blocker]["blockers"])
    return found


def _surfaces_overlap(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if left["parallel_safe"] and right["parallel_safe"]:
        return False
    left_path = left["path"]
    right_path = right["path"]
    if left["kind"] == "file" and right["kind"] == "file":
        return left_path == right_path
    if left["kind"] == "prefix" and right["kind"] == "prefix":
        return (
            left_path == right_path
            or left_path.startswith(right_path + "/")
            or right_path.startswith(left_path + "/")
        )
    prefix = left if left["kind"] == "prefix" else right
    file_surface = right if left["kind"] == "prefix" else left
    return file_surface["path"] == prefix["path"] or file_surface["path"].startswith(
        prefix["path"] + "/"
    )


def _validate_limit(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise InputError("limit must be a positive integer")
    return value


def _blocker_base(
    task: Mapping[str, Any],
    by_ref: Mapping[str, Mapping[str, Any]],
    root_base: Mapping[str, str],
) -> tuple[dict[str, Any] | None, str | None, list[str]]:
    """Return (base, hold reason, relevant blocker refs)."""

    unresolved: list[Mapping[str, Any] | None] = []
    unresolved_refs: list[str] = []
    for blocker_ref in task["blockers"]:
        blocker = by_ref.get(blocker_ref)
        if blocker is None:
            unresolved.append(None)
            unresolved_refs.append(blocker_ref)
            continue
        pr = blocker["pr"]
        if blocker["state"] == "done" or (pr is not None and pr["state"] == "merged"):
            continue
        unresolved.append(blocker)
        unresolved_refs.append(blocker_ref)

    if not unresolved:
        return {
            "kind": "root",
            "branch": root_base["branch"],
            "sha": root_base["sha"],
        }, None, []
    if len(task["blockers"]) > 1:
        return None, "multi_blocker_waiting_for_merges", unresolved_refs
    if len(unresolved) > 1:
        return None, "multiple_unmerged_blockers", unresolved_refs

    blocker = unresolved[0]
    blocker_ref = unresolved_refs[0]
    if blocker is None:
        return None, "unknown_blocker", unresolved_refs
    if blocker["state"] == "canceled":
        return None, "canceled_blocker", unresolved_refs
    if not blocker["decision_complete"]:
        return None, "blocker_decision_incomplete", unresolved_refs
    pr = blocker["pr"]
    if pr is None:
        return None, "blocker_pr_missing", unresolved_refs
    if pr["state"] == "closed":
        return None, "blocker_pr_closed", unresolved_refs
    if pr["state"] != "open":
        return None, "blocker_not_ready", unresolved_refs
    review_ready = (
        pr["review_gate"] in STACK_READY_REVIEW_GATES
        if pr["review_gate"] is not None
        else pr["clean"] is True
    )
    if not review_ready:
        return None, "blocker_pr_not_clean", unresolved_refs
    if pr["branch"] is None or pr["head_sha"] is None:
        return None, "blocker_pr_head_missing", unresolved_refs
    return {
        "kind": "stacked",
        "branch": pr["branch"],
        "sha": pr["head_sha"],
        "blocker_ref": blocker_ref,
    }, None, unresolved_refs


def _candidate(
    task: Mapping[str, Any],
    by_ref: Mapping[str, Mapping[str, Any]],
    root_base: Mapping[str, str],
) -> tuple[int, dict[str, Any] | None, str | None, list[str]]:
    state = task["state"]
    pr = task["pr"]

    if state == "done":
        return 99, None, "done", []
    if state == "canceled":
        return 99, None, "canceled", []
    if state == "in_review":
        if pr is not None and pr["state"] == "merged":
            return 0, {
                "mode": "finalize",
                "base_branch": (
                    task["base_branch"] or pr["base_branch"] or root_base["branch"]
                ),
                "base_sha": task["base_sha"] or root_base["sha"],
                "stacked_on": (
                    task["blockers"][0] if len(task["blockers"]) == 1 else None
                ),
            }, None, []
        if pr is not None and pr["state"] == "open" and pr["needs_reconcile"]:
            base, reason, blocker_refs = _blocker_base(task, by_ref, root_base)
            if reason is not None:
                return 99, None, reason, blocker_refs
            assert base is not None
            return 1, {
                "mode": "reconcile",
                "base_branch": base["branch"],
                "base_sha": base["sha"],
                "stacked_on": base.get("blocker_ref"),
            }, None, []
        if pr is None:
            return 99, None, "review_pr_missing", []
        if pr["state"] == "closed":
            return 99, None, "review_pr_closed", []
        return 99, None, "awaiting_review", []
    if state == "in_progress" and not task["owned"]:
        return 99, None, "in_progress_not_owned", []
    if not task["decision_complete"]:
        return 99, None, "decision_incomplete", []
    if state == "todo" and not task["claimable"]:
        return 99, None, "not_claimable", []

    base, reason, blocker_refs = _blocker_base(task, by_ref, root_base)
    if reason is not None:
        return 99, None, reason, blocker_refs
    assert base is not None
    mode = "resume" if state == "in_progress" else "implement"
    priority = 2 if mode == "resume" else 3
    return priority, {
        "mode": mode,
        "base_branch": base["branch"],
        "base_sha": base["sha"],
        "stacked_on": base.get("blocker_ref"),
    }, None, []


def select_wave(payload: Any, limit: int | None = None) -> dict[str, Any]:
    """Return at most ``limit`` deterministic assignments and all held tasks."""

    graph = normalize_graph(payload)
    effective_limit = _validate_limit(limit) if limit is not None else graph["limit"]
    if effective_limit is None:
        raise InputError("limit is required in input or as --limit")

    by_ref = {task["ref"]: task for task in graph["tasks"]}
    registry_ids = {item["id"] for item in graph["decision_registry"]}
    owners: dict[str, list[str]] = {}
    for task in graph["tasks"]:
        if task["state"] in {"done", "canceled"}:
            continue
        for decision in task["coordination"]["decisions_owned"]:
            owners.setdefault(decision["id"], []).append(task["ref"])
    conflicted_owners = {
        ref: decision_id
        for decision_id, refs in owners.items()
        if len(refs) > 1
        for ref in refs
    }
    candidates: list[
        tuple[int, int, tuple[int, str | int], str, dict[str, Any], Mapping[str, Any]]
    ] = []
    held: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []

    for task in graph["tasks"]:
        if task["coordination_unscoped"]:
            warnings.append({"ref": task["ref"], "reason": "coordination_unscoped"})
        if task["ref"] in graph["cycle_refs"]:
            held.append(
                {
                    "ref": task["ref"],
                    "kind": task["kind"],
                    "state": task["state"],
                    "reason": "dependency_cycle",
                }
            )
            continue
        if task["ref"] in conflicted_owners:
            decision_id = conflicted_owners[task["ref"]]
            held.append(
                {
                    "ref": task["ref"],
                    "kind": task["kind"],
                    "state": task["state"],
                    "reason": "decision_domain_conflict",
                    "decision_id": decision_id,
                    "conflicts_with": sorted(
                        ref for ref in owners[decision_id] if ref != task["ref"]
                    ),
                }
            )
            continue
        ancestor_decisions = {
            decision["id"]
            for ancestor in _ancestor_refs(task["ref"], by_ref)
            if ancestor in by_ref
            for decision in by_ref[ancestor]["coordination"]["decisions_owned"]
        }
        unresolved = sorted(
            set(task["coordination"]["decisions_consumed"])
            - registry_ids
            - ancestor_decisions
        )
        if unresolved:
            held.append(
                {
                    "ref": task["ref"],
                    "kind": task["kind"],
                    "state": task["state"],
                    "reason": "unresolved_consumed_decision",
                    "decision_ids": unresolved,
                }
            )
            continue
        priority, assignment, reason, blocker_refs = _candidate(
            task, by_ref, graph["root_base"]
        )
        if assignment is None:
            hold: dict[str, Any] = {
                "ref": task["ref"],
                "kind": task["kind"],
                "state": task["state"],
                "reason": reason,
            }
            if blocker_refs:
                hold["blockers"] = blocker_refs
            held.append(hold)
            continue
        selected = {
            "ref": task["ref"],
            "kind": task["kind"],
            "state": task["state"],
            "coordination": task["coordination"],
            "coordination_unscoped": task["coordination_unscoped"],
            **assignment,
        }
        task_priority = (
            task["priority"] if task["priority"] is not None else sys.maxsize
        )
        candidates.append(
            (
                priority,
                task_priority,
                _order_sort_key(task["order_key"]),
                task["ref"],
                selected,
                task,
            )
        )

    candidates.sort(key=lambda item: item[:4])
    selected: list[dict[str, Any]] = []
    selected_tasks: list[Mapping[str, Any]] = []
    for _, _, _, _, assignment, task in candidates:
        conflict_ref: str | None = None
        for selected_task in selected_tasks:
            if any(
                _surfaces_overlap(left, right)
                for left in task["coordination"]["touch_surfaces"]
                for right in selected_task["coordination"]["touch_surfaces"]
            ):
                conflict_ref = selected_task["ref"]
                break
        if conflict_ref is not None:
            held.append(
                {
                    "ref": assignment["ref"],
                    "kind": assignment["kind"],
                    "state": assignment["state"],
                    "reason": "touch_surface_conflict",
                    "conflicts_with": [conflict_ref],
                }
            )
        elif len(selected) >= effective_limit:
            held.append(
                {
                    "ref": assignment["ref"],
                    "kind": assignment["kind"],
                    "state": assignment["state"],
                    "reason": "concurrency_limit",
                }
            )
        else:
            selected.append(assignment)
            selected_tasks.append(task)
    held.sort(key=lambda item: item["ref"])

    return {
        "root_base": graph["root_base"],
        "limit": effective_limit,
        "selected": selected,
        "held": held,
        "warnings": sorted(warnings, key=lambda item: item["ref"]),
    }


def _read_json(path: str) -> Any:
    try:
        raw = (
            sys.stdin.read()
            if path == "-"
            else Path(path).read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise InputError(f"cannot read input {path!r}: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def _write_json(path: str, value: Any, pretty: bool) -> None:
    rendered = json.dumps(
        value,
        indent=2 if pretty else None,
        sort_keys=pretty,
        separators=None if pretty else (",", ":"),
    ) + "\n"
    try:
        if path == "-":
            sys.stdout.write(rendered)
        else:
            Path(path).write_text(rendered, encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot write output {path!r}: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Select a deterministic parallel worker wave from a Brutal task graph."
    )
    parser.add_argument(
        "--input", "-i", default="-", metavar="PATH", help="JSON input file (default: stdin)"
    )
    parser.add_argument(
        "--output", "-o", default="-", metavar="PATH", help="JSON output file (default: stdout)"
    )
    parser.add_argument(
        "--limit", "-n", type=int, help="override the positive worker limit in the input"
    )
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = select_wave(_read_json(args.input), args.limit)
        _write_json(args.output, result, args.pretty)
    except InputError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
