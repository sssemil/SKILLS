#!/usr/bin/env python3
"""Create, inspect, and safely remove isolated Brutal task worktrees."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


class WorktreeError(RuntimeError):
    """A user-actionable worktree safety or Git error."""


@dataclass(frozen=True)
class Repository:
    primary: Path
    git_common_dir: Path


def _git(
    cwd: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise WorktreeError(detail)
    return result


def _resolve(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _parse_worktrees(raw: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for field in raw.split("\0"):
        if not field:
            if current:
                records.append(current)
                current = {}
            continue
        key, separator, value = field.partition(" ")
        if not separator:
            current[key] = True
        else:
            current[key] = value
    if current:
        records.append(current)
    return records


def _worktrees(repo: Repository) -> list[dict[str, Any]]:
    output = _git(repo.primary, "worktree", "list", "--porcelain", "-z").stdout
    records = _parse_worktrees(output)
    for record in records:
        if "worktree" in record:
            record["path"] = _resolve(record["worktree"])
    return records


def _repository(repo_path: str | Path) -> Repository:
    candidate = _resolve(repo_path)
    probe = _git(candidate, "rev-parse", "--is-inside-work-tree", check=False)
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        raise WorktreeError(f"not a non-bare Git worktree: {candidate}")

    top = _resolve(_git(candidate, "rev-parse", "--show-toplevel").stdout.strip())
    records = _parse_worktrees(
        _git(top, "worktree", "list", "--porcelain", "-z").stdout
    )
    if not records or "worktree" not in records[0]:
        raise WorktreeError("Git did not report a primary worktree")
    primary = _resolve(records[0]["worktree"])
    common_value = Path(
        _git(primary, "rev-parse", "--git-common-dir").stdout.strip()
    ).expanduser()
    common = (
        common_value.resolve(strict=False)
        if common_value.is_absolute()
        else (primary / common_value).resolve(strict=False)
    )
    return Repository(primary=primary, git_common_dir=common)


def _slug(value: str, fallback: str, limit: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (slug or fallback)[:limit].rstrip("-")


def _task_hash(task_ref: str) -> str:
    return hashlib.sha256(task_ref.encode("utf-8")).hexdigest()[:8]


def branch_name(task_ref: str, title: str) -> str:
    ref = _slug(task_ref, "task", 48)
    title_slug = _slug(title, "work", 72)
    return f"brutal/{ref}-{title_slug}-{_task_hash(task_ref)}"


def default_path(repo: Repository, run_id: str, task_ref: str) -> Path:
    safe_run = _slug(run_id, "run", 64)
    return repo.primary.parent / ".brutal-worktrees" / repo.primary.name / safe_run / _task_hash(task_ref)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _commit(repo: Repository, revision: str) -> str:
    if not revision:
        raise WorktreeError("base revision must not be empty")
    result = _git(
        repo.primary,
        "rev-parse",
        "--verify",
        "--end-of-options",
        f"{revision}^{{commit}}",
        check=False,
    )
    if result.returncode != 0:
        raise WorktreeError(f"base is not a commit in this repository: {revision}")
    return result.stdout.strip().lower()


def _metadata_key(branch: str, field: str) -> str:
    return f"branch.{branch}.brutal{field}"


def _metadata(repo: Repository, branch: str) -> dict[str, str | None]:
    values: dict[str, str | None] = {}
    for output_name, key_name in (("task_ref", "TaskRef"), ("base_sha", "BaseSha")):
        result = _git(
            repo.primary,
            "config",
            "--local",
            "--get",
            _metadata_key(branch, key_name),
            check=False,
        )
        values[output_name] = result.stdout.rstrip("\n") if result.returncode == 0 else None
    return values


def _set_metadata(repo: Repository, branch: str, task_ref: str, base_sha: str) -> None:
    _git(
        repo.primary,
        "config",
        "--local",
        _metadata_key(branch, "TaskRef"),
        task_ref,
    )
    _git(
        repo.primary,
        "config",
        "--local",
        _metadata_key(branch, "BaseSha"),
        base_sha,
    )


def _branch_for(record: dict[str, Any]) -> str | None:
    branch_ref = record.get("branch")
    prefix = "refs/heads/"
    if isinstance(branch_ref, str) and branch_ref.startswith(prefix):
        return branch_ref[len(prefix) :]
    return None


def _record_at(repo: Repository, path: Path) -> dict[str, Any] | None:
    return next((record for record in _worktrees(repo) if record.get("path") == path), None)


def create_worktree(
    repo_path: str | Path,
    task_ref: str,
    title: str,
    run_id: str,
    base: str,
    path: str | Path | None = None,
    branch: str | None = None,
) -> dict[str, Any]:
    if not task_ref.strip():
        raise WorktreeError("task ref must not be empty")
    if not run_id.strip():
        raise WorktreeError("run id must not be empty")
    repo = _repository(repo_path)
    base_sha = _commit(repo, base)
    selected_branch = branch or branch_name(task_ref, title)
    branch_check = _git(
        repo.primary,
        "check-ref-format",
        "--branch",
        selected_branch,
        check=False,
    )
    if branch_check.returncode != 0 or not selected_branch.startswith("brutal/"):
        raise WorktreeError(f"invalid Brutal task branch: {selected_branch}")
    target = _resolve(path) if path is not None else default_path(repo, run_id, task_ref)

    if _is_within(target, repo.primary):
        raise WorktreeError(f"worktree path must be outside the primary worktree: {target}")

    record = _record_at(repo, target)
    if record is not None:
        actual_branch = _branch_for(record)
        metadata = _metadata(repo, actual_branch) if actual_branch else {}
        if (
            actual_branch == selected_branch
            and metadata.get("task_ref") == task_ref
            and metadata.get("base_sha") is not None
        ):
            return {
                "action": "resumed",
                "path": str(target),
                "branch": selected_branch,
                "task_ref": task_ref,
                "base_sha": base_sha,
                "origin_base_sha": metadata.get("base_sha"),
                "base_changed": metadata.get("base_sha") != base_sha,
                "head": record.get("HEAD"),
            }
        raise WorktreeError(f"registered worktree collision at {target}")

    if target.exists():
        raise WorktreeError(f"filesystem path collision at {target}")

    existing_branch = _git(
        repo.primary,
        "show-ref",
        "--verify",
        "--quiet",
        f"refs/heads/{selected_branch}",
        check=False,
    )
    if existing_branch.returncode == 0:
        metadata = _metadata(repo, selected_branch)
        if metadata.get("task_ref") != task_ref or not metadata.get("base_sha"):
            raise WorktreeError(f"branch collision: {selected_branch}")
        registered = next(
            (
                item
                for item in _worktrees(repo)
                if _branch_for(item) == selected_branch
            ),
            None,
        )
        if registered is not None:
            raise WorktreeError(
                f"branch is already checked out at {registered.get('path')}: "
                f"{selected_branch}"
            )
        origin_base = str(metadata["base_sha"])
        ancestor = _git(
            repo.primary,
            "merge-base",
            "--is-ancestor",
            origin_base,
            selected_branch,
            check=False,
        )
        if ancestor.returncode != 0:
            raise WorktreeError(
                f"task branch no longer contains its recorded base: {selected_branch}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        _git(repo.primary, "worktree", "add", str(target), selected_branch)
        head = _git(target, "rev-parse", "HEAD").stdout.strip().lower()
        return {
            "action": "resumed",
            "path": str(target),
            "branch": selected_branch,
            "task_ref": task_ref,
            "base_sha": base_sha,
            "origin_base_sha": origin_base,
            "base_changed": origin_base != base_sha,
            "head": head,
        }

    target.parent.mkdir(parents=True, exist_ok=True)
    _git(repo.primary, "worktree", "add", "-b", selected_branch, str(target), base_sha)
    _set_metadata(repo, selected_branch, task_ref, base_sha)
    head = _git(target, "rev-parse", "HEAD").stdout.strip().lower()
    return {
        "action": "created",
        "path": str(target),
        "branch": selected_branch,
        "task_ref": task_ref,
        "base_sha": base_sha,
        "origin_base_sha": base_sha,
        "base_changed": False,
        "head": head,
    }


def inspect_worktree(repo_path: str | Path, path: str | Path) -> dict[str, Any]:
    repo = _repository(repo_path)
    target = _resolve(path)
    record = _record_at(repo, target)
    if record is None:
        return {
            "path": str(target),
            "registered": False,
            "primary_worktree": False,
            "exists": target.exists(),
            "branch": None,
            "task_ref": None,
            "base_sha": None,
            "head": None,
            "clean": None,
        }

    branch = _branch_for(record)
    metadata = _metadata(repo, branch) if branch else {"task_ref": None, "base_sha": None}
    clean = (
        _git(target, "status", "--porcelain", "--untracked-files=all").stdout == ""
        if target.exists()
        else None
    )
    return {
        "path": str(target),
        "registered": True,
        "primary_worktree": target == repo.primary,
        "exists": target.exists(),
        "branch": branch,
        "task_ref": metadata.get("task_ref"),
        "base_sha": metadata.get("base_sha"),
        "head": record.get("HEAD"),
        "clean": clean,
    }


def _literal_head(value: str, label: str) -> str:
    head = value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", head):
        raise WorktreeError(f"{label} must be a full hexadecimal commit ID")
    return head


def cleanup_worktree(
    repo_path: str | Path,
    path: str | Path,
    task_ref: str,
    pushed_head: str,
    pr_head: str,
) -> dict[str, Any]:
    if not task_ref.strip():
        raise WorktreeError("task ref must not be empty")
    repo = _repository(repo_path)
    target = _resolve(path)
    record = _record_at(repo, target)
    if record is None:
        raise WorktreeError(f"worktree is not registered: {target}")
    if target == repo.primary:
        raise WorktreeError("refusing to remove the primary worktree")

    branch = _branch_for(record)
    metadata = _metadata(repo, branch) if branch else {}
    if (
        branch is None
        or not branch.startswith("brutal/")
        or metadata.get("task_ref") != task_ref
        or metadata.get("base_sha") is None
    ):
        raise WorktreeError(
            "refusing to remove a worktree without matching Brutal task metadata"
        )

    status = _git(target, "status", "--porcelain", "--untracked-files=all").stdout
    if status:
        raise WorktreeError("worktree is not clean")

    local_head = _git(target, "rev-parse", "HEAD").stdout.strip().lower()
    pushed = _literal_head(pushed_head, "pushed head")
    pull_request = _literal_head(pr_head, "PR head")
    if local_head != pushed or local_head != pull_request:
        raise WorktreeError(
            "cleanup head mismatch: local HEAD, pushed head, and PR head must be equal"
        )

    _git(repo.primary, "worktree", "remove", str(target))
    return {
        "action": "removed",
        "path": str(target),
        "branch": branch,
        "head": local_head,
        "branch_deleted": False,
    }


class _JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        print(json.dumps({"ok": False, "error": message}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)


def _parser() -> argparse.ArgumentParser:
    parser = _JsonArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="create or safely resume a task worktree")
    create.add_argument("--repo", required=True)
    create.add_argument("--task-ref", required=True)
    create.add_argument("--title", required=True)
    create.add_argument("--run-id", required=True)
    create.add_argument("--base", required=True)
    create.add_argument("--path")
    create.add_argument("--branch")

    inspect = subparsers.add_parser("inspect", help="inspect a registered worktree")
    inspect.add_argument("--repo", required=True)
    inspect.add_argument("--path", required=True)

    cleanup = subparsers.add_parser("cleanup", help="remove a verified task worktree")
    cleanup.add_argument("--repo", required=True)
    cleanup.add_argument("--path", required=True)
    cleanup.add_argument("--task-ref", required=True)
    cleanup.add_argument("--pushed-head", required=True)
    cleanup.add_argument("--pr-head", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "create":
            result = create_worktree(
                args.repo,
                args.task_ref,
                args.title,
                args.run_id,
                args.base,
                args.path,
                args.branch,
            )
        elif args.command == "inspect":
            result = inspect_worktree(args.repo, args.path)
        else:
            result = cleanup_worktree(
                args.repo,
                args.path,
                args.task_ref,
                args.pushed_head,
                args.pr_head,
            )
    except (OSError, WorktreeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
