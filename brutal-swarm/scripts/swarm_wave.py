#!/usr/bin/env python3
"""Normalize a Brutal task graph and select one deterministic worker wave."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


TASK_TYPES = frozenset({"task", "review_finding"})
TASK_STATES = frozenset(
    {"todo", "in_progress", "in_review", "done", "canceled"}
)
PR_STATES = frozenset({"open", "closed", "merged"})


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

    normalized: dict[str, Any] = {
        "state": state,
        "branch": _optional_string(pr.get("branch"), f"{path}.branch"),
        "base_branch": _optional_string(
            pr.get("base_branch"), f"{path}.base_branch"
        ),
        "head_sha": _optional_string(pr.get("head_sha"), f"{path}.head_sha"),
        "clean": clean,
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
        "tasks": sorted(
            tasks,
            key=lambda task: (_order_sort_key(task["order_key"]), task["ref"]),
        ),
        "cycle_refs": sorted(_dependency_cycle_refs(tasks)),
    }


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
    if pr["clean"] is not True:
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
    candidates: list[
        tuple[int, int, tuple[int, str | int], str, dict[str, Any]]
    ] = []
    held: list[dict[str, Any]] = []

    for task in graph["tasks"]:
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
            )
        )

    candidates.sort(key=lambda item: item[:4])
    selected = [item[4] for item in candidates[:effective_limit]]
    for _, _, _, _, assignment in candidates[effective_limit:]:
        held.append(
            {
                "ref": assignment["ref"],
                "kind": assignment["kind"],
                "state": assignment["state"],
                "reason": "concurrency_limit",
            }
        )
    held.sort(key=lambda item: item["ref"])

    return {
        "root_base": graph["root_base"],
        "limit": effective_limit,
        "selected": selected,
        "held": held,
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
