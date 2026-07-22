#!/usr/bin/env python3
"""Run an editing child with one repository-relative writable directory."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Sequence


class ScopedEditError(RuntimeError):
    """Raised when the requested write boundary is invalid or violated."""


def writable_directory(ticket: str) -> str | None:
    lines = ticket.splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower() != "## writable directory":
            continue
        for value in lines[index + 1 :]:
            value = value.strip()
            if value.startswith("## "):
                break
            if value:
                return value.strip("`")
        raise ScopedEditError("Writable Directory heading has no value")
    return None


def resolve_directory(repository: Path, value: str) -> Path:
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or value.strip() == "":
        raise ScopedEditError("writable directory must be repository-relative")
    repository = repository.resolve()
    path = (repository / relative.as_posix()).resolve()
    if path != repository and repository not in path.parents:
        raise ScopedEditError("writable directory escapes the repository")
    if not path.is_dir():
        raise ScopedEditError("writable directory does not exist")
    return path


def _git(repository: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise ScopedEditError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def _changed_paths(repository: Path) -> set[str]:
    raw = _git(repository, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = raw.decode(errors="surrogateescape").split("\0")
    paths: set[str] = set()
    skip_rename_source = False
    for entry in entries:
        if not entry:
            continue
        if skip_rename_source:
            paths.add(entry)
            skip_rename_source = False
            continue
        if len(entry) < 4:
            continue
        status, path = entry[:2], entry[3:]
        paths.add(path)
        skip_rename_source = "R" in status or "C" in status
    return paths


def _inside(path: str, allowed: Path, repository: Path) -> bool:
    target = (repository / path).resolve()
    return target == allowed or allowed in target.parents


def run(
    repository: Path,
    directory: str,
    command: Sequence[str],
    prompt: str,
) -> dict[str, Any]:
    if not command or not all(isinstance(item, str) and item for item in command):
        raise ScopedEditError("edit sandbox command must be a non-empty string array")
    executable = shutil.which(command[0])
    if executable is None:
        raise ScopedEditError(f"edit sandbox command not found: {command[0]}")
    repository = repository.resolve()
    allowed = resolve_directory(repository, directory)
    if _changed_paths(repository):
        raise ScopedEditError("edit sandbox requires a clean worktree")
    result = subprocess.run(
        [executable, *command[1:], "exec", "-"],
        cwd=allowed,
        input=prompt,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    changed = sorted(_changed_paths(repository))
    outside = [path for path in changed if not _inside(path, allowed, repository)]
    if outside:
        raise ScopedEditError("child changed paths outside writable directory: " + ", ".join(outside))
    if result.returncode != 0:
        raise ScopedEditError(f"edit sandbox command exited {result.returncode}")
    return {
        "status": "edited",
        "writable_directory": allowed.relative_to(repository).as_posix() or ".",
        "changed_paths": changed,
        "output_tail": result.stdout[-16384:],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--directory", required=True)
    parser.add_argument("--command-json", required=True)
    parser.add_argument("--prompt-file", required=True)
    args = parser.parse_args(argv)
    try:
        command = json.loads(args.command_json)
        if not isinstance(command, list):
            raise ScopedEditError("edit sandbox command must be an array")
        value = run(
            Path(args.repo),
            args.directory,
            command,
            Path(args.prompt_file).read_text(encoding="utf-8"),
        )
    except (OSError, json.JSONDecodeError, ScopedEditError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps({"ok": True, **value}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
