#!/usr/bin/env python3
"""Validate and compare opt-in Brutal Dot Spec manifests."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - JSON remains dependency-free
    yaml = None

SCHEMA_VERSION = 1
MATURITY = ("code-owned", "observed", "guarded", "spec-driven", "managed", "rebuildable")
AUTHORITY = {"spec", "code", "foreign"}
PROVENANCE = {"declared", "observed", "asserted", "inferred"}
OPERATIONS = {"add", "replace", "remove"}


class DotSpecError(Exception):
    pass


def load_data(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if yaml is not None:
        return yaml.load(text, Loader=_yaml_loader())
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise DotSpecError(f"{path}: YAML input requires PyYAML") from exc


def _yaml_loader() -> type[Any]:
    """Return a safe loader that keeps RFC3339 timestamps as strings."""
    assert yaml is not None

    class StringTimestampLoader(yaml.SafeLoader):
        pass

    StringTimestampLoader.yaml_implicit_resolvers = {
        key: list(resolvers)
        for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }
    timestamp_tag = "tag:yaml.org,2002:timestamp"
    for key, resolvers in StringTimestampLoader.yaml_implicit_resolvers.items():
        StringTimestampLoader.yaml_implicit_resolvers[key] = [
            resolver for resolver in resolvers if resolver[0] != timestamp_tag
        ]
    return StringTimestampLoader


def _list_key(value: Any) -> tuple[str, ...] | None:
    if not isinstance(value, dict):
        return None
    for keys in (("requirement_id", "module", "op"), ("id",), ("module",)):
        if all(key in value for key in keys):
            return tuple(str(value[key]) for key in keys)
    return None


def normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: normalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        items = [normalize(item) for item in value]
        keys = [_list_key(item) for item in items]
        if items and all(key is not None for key in keys):
            return [item for _, item in sorted(zip(keys, items), key=lambda pair: pair[0])]
        return items
    return value


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def require_mapping(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be a mapping")
        return {}
    return value


def require_list(value: Any, label: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    return value


def provenance_kind(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get("kind", ""))
    return ""


def load_graph(manifest_path: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    manifest = require_mapping(load_data(manifest_path), str(manifest_path), errors)
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{manifest_path}: schema_version must be {SCHEMA_VERSION}")
    modules_raw = require_list(manifest.get("modules"), f"{manifest_path}: modules", errors)
    modules: dict[str, dict[str, Any]] = {}
    base = manifest_path.parent
    for index, raw in enumerate(modules_raw):
        entry = require_mapping(raw, f"modules[{index}]", errors)
        module_id = str(entry.get("id", ""))
        if not module_id:
            errors.append(f"modules[{index}]: id is required")
            continue
        if module_id in modules:
            errors.append(f"duplicate module id: {module_id}")
            continue
        if entry.get("maturity") not in MATURITY:
            errors.append(f"{module_id}: invalid maturity {entry.get('maturity')!r}")
        authority = require_mapping(entry.get("authority"), f"{module_id}: authority", errors)
        if not authority:
            errors.append(f"{module_id}: authority must name at least one concern")
        for concern, owner in authority.items():
            if not str(concern) or owner not in AUTHORITY:
                errors.append(f"{module_id}: invalid authority {concern}={owner!r}")
        spec_ref = entry.get("spec")
        if not isinstance(spec_ref, str) or not spec_ref:
            errors.append(f"{module_id}: spec path is required")
            continue
        if Path(spec_ref).is_absolute():
            errors.append(f"{module_id}: spec path must be manifest-relative")
            continue
        spec_path = (base / spec_ref).resolve()
        try:
            spec_path.relative_to(base.resolve())
        except ValueError:
            errors.append(f"{module_id}: spec path escapes the manifest directory")
            continue
        try:
            spec = require_mapping(load_data(spec_path), str(spec_path), errors)
        except (OSError, ValueError, DotSpecError) as exc:
            errors.append(str(exc))
            continue
        modules[module_id] = {"entry": entry, "spec": spec, "path": spec_path}
    return manifest, modules, errors


def validate_graph(manifest_path: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    _, modules, errors = load_graph(manifest_path)
    errors.extend(validate_modules(modules))
    return modules, sorted(set(errors))


def validate_modules(modules: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    requirement_owners: dict[str, str] = {}
    evidence_ids: dict[str, str] = {}
    edges: dict[str, set[str]] = {module_id: set() for module_id in modules}
    for module_id, data in modules.items():
        entry = require_mapping(data.get("entry"), f"{module_id}: manifest entry", errors)
        spec = require_mapping(data.get("spec"), f"{module_id}: spec", errors)
        if spec.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"{module_id}: spec schema_version must be {SCHEMA_VERSION}")
        if spec.get("module") != module_id:
            errors.append(f"{module_id}: spec module must match manifest id")
        authority = require_mapping(entry.get("authority"), f"{module_id}: authority", errors)
        if not authority:
            errors.append(f"{module_id}: authority must name at least one concern")
        for concern, owner in authority.items():
            if not str(concern) or owner not in AUTHORITY:
                errors.append(f"{module_id}: invalid authority {concern}={owner!r}")
        if entry.get("maturity") not in MATURITY:
            errors.append(f"{module_id}: invalid maturity {entry.get('maturity')!r}")
        for raw_import in require_list(spec.get("imports", []), f"{module_id}: imports", errors):
            imported = raw_import.get("module") if isinstance(raw_import, dict) else raw_import
            if imported == module_id:
                errors.append(f"{module_id}: self import is forbidden")
            elif imported not in modules:
                errors.append(f"{module_id}: unknown imported module {imported!r}")
            else:
                edges[module_id].add(str(imported))
        requirements = require_list(spec.get("requirements"), f"{module_id}: requirements", errors)
        for index, raw in enumerate(requirements):
            req = require_mapping(raw, f"{module_id}: requirements[{index}]", errors)
            req_id = str(req.get("id", ""))
            if not req_id:
                errors.append(f"{module_id}: requirement id is required")
                continue
            if not req_id.startswith(f"{module_id}."):
                errors.append(f"{req_id}: id must be owned by module {module_id}")
            if req_id in requirement_owners:
                errors.append(f"duplicate requirement id: {req_id}")
            requirement_owners[req_id] = module_id
            if not isinstance(req.get("statement"), str) or not req["statement"].strip():
                errors.append(f"{req_id}: statement is required")
            concern = req.get("concern")
            if concern not in authority:
                errors.append(f"{req_id}: concern {concern!r} has no authority owner")
            kind = provenance_kind(req.get("provenance"))
            if kind not in PROVENANCE:
                errors.append(f"{req_id}: invalid active provenance {kind!r}")
            maturity = entry.get("maturity")
            if maturity in MATURITY[MATURITY.index("guarded") :] and not req.get("verification"):
                errors.append(f"{req_id}: {maturity} requirements need verification evidence")
            for field in ("scenarios", "invariants"):
                for item_index, raw_item in enumerate(require_list(req.get(field, []), f"{req_id}: {field}", errors)):
                    item = require_mapping(raw_item, f"{req_id}: {field}[{item_index}]", errors)
                    item_id = str(item.get("id", ""))
                    if not item_id:
                        errors.append(f"{req_id}: {field}[{item_index}] needs an id")
                    elif item_id in evidence_ids:
                        errors.append(f"duplicate evidence id: {item_id}")
                    else:
                        evidence_ids[item_id] = req_id

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(module_id: str, path: tuple[str, ...]) -> None:
        if module_id in visiting:
            errors.append("import cycle: " + " -> ".join((*path, module_id)))
            return
        if module_id in visited:
            return
        visiting.add(module_id)
        for imported in sorted(edges.get(module_id, ())):
            visit(imported, (*path, module_id))
        visiting.remove(module_id)
        visited.add(module_id)

    for module_id in sorted(modules):
        visit(module_id, ())
    return sorted(set(errors))


def git_repo_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(start.resolve()), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise DotSpecError(f"{start}: not inside a Git repository")
    return Path(result.stdout.strip()).resolve()


def git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise DotSpecError(f"{repo_root}: cannot resolve Git HEAD")
    return result.stdout.strip()


def require_clean_git(repo_root: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise DotSpecError(f"{repo_root}: cannot inspect Git worktree")
    if result.stdout:
        raise DotSpecError(f"{repo_root}: verification requires a clean Git worktree")


def valid_rfc3339(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return bool(re.search(r"(?:Z|[+-]\d{2}:\d{2})$", value))


def validate_delta(delta_path: Path, modules: dict[str, dict[str, Any]], check_base: bool) -> list[str]:
    errors: list[str] = []
    delta = require_mapping(load_data(delta_path), str(delta_path), errors)
    if delta.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{delta_path}: schema_version must be {SCHEMA_VERSION}")
    for key in ("change_id", "base_sha"):
        if not isinstance(delta.get(key), str) or not delta[key]:
            errors.append(f"{delta_path}: {key} is required")
    approval = require_mapping(delta.get("approval"), f"{delta_path}: approval", errors)
    if approval.get("status") not in {"draft", "approved"}:
        errors.append(f"{delta_path}: approval status must be draft or approved")
    if approval.get("status") == "approved":
        if not isinstance(approval.get("by"), str) or not approval["by"]:
            errors.append(f"{delta_path}: approved changes require approval.by")
        if not valid_rfc3339(approval.get("at")):
            errors.append(f"{delta_path}: approved changes require RFC3339 approval.at")
    base_specs = require_mapping(delta.get("base_specs"), f"{delta_path}: base_specs", errors)
    if check_base:
        try:
            actual_head = git_head(git_repo_root(delta_path.parent))
            if delta.get("base_sha") != actual_head:
                errors.append(f"{delta_path}: stale base SHA; expected {actual_head}")
        except DotSpecError as exc:
            errors.append(str(exc))
        for module_id, expected in base_specs.items():
            if module_id not in modules:
                errors.append(f"{delta_path}: unknown base module {module_id}")
            elif expected != digest(modules[module_id]["spec"]):
                errors.append(f"{delta_path}: stale base digest for {module_id}")
    seen: set[tuple[str, str]] = set()
    active_requirements = requirement_map(modules)
    for index, raw in enumerate(require_list(delta.get("operations"), f"{delta_path}: operations", errors)):
        op = require_mapping(raw, f"operations[{index}]", errors)
        module_id = str(op.get("module", ""))
        req_id = str(op.get("requirement_id", ""))
        if op.get("op") not in OPERATIONS:
            errors.append(f"operations[{index}]: invalid op {op.get('op')!r}")
        if module_id not in modules:
            errors.append(f"operations[{index}]: unknown module {module_id!r}")
        elif module_id not in base_specs:
            errors.append(f"operations[{index}]: base_specs is missing {module_id}")
        if not req_id.startswith(f"{module_id}."):
            errors.append(f"operations[{index}]: requirement id is not owned by {module_id}")
        identity = (module_id, req_id)
        if identity in seen:
            errors.append(f"duplicate operation for {req_id}")
        seen.add(identity)
        for key in ("ticket", "activates_with"):
            if not isinstance(op.get(key), str) or not op[key]:
                errors.append(f"operations[{index}]: {key} is required")
        if op.get("op") in {"add", "replace"} and not isinstance(op.get("after"), dict):
            errors.append(f"operations[{index}]: {op.get('op')} requires complete after value")
        elif isinstance(op.get("after"), dict) and op["after"].get("id") != req_id:
            errors.append(f"operations[{index}]: after.id must equal requirement_id")
        if op.get("op") in {"replace", "remove"} and (
            not isinstance(op.get("before_digest"), str) or not op["before_digest"]
        ):
            errors.append(f"operations[{index}]: {op.get('op')} requires before_digest")
        if check_base and op.get("op") == "add" and req_id in active_requirements:
            errors.append(f"operations[{index}]: add target already exists: {req_id}")
        if check_base and op.get("op") in {"replace", "remove"}:
            current = active_requirements.get(req_id)
            if current is None:
                errors.append(f"operations[{index}]: active requirement does not exist: {req_id}")
            elif op.get("before_digest") != digest(current[1]):
                errors.append(f"operations[{index}]: stale requirement digest for {req_id}")
    changed_modules: set[str] = set()
    for index, raw in enumerate(require_list(delta.get("module_changes", []), f"{delta_path}: module_changes", errors)):
        change = require_mapping(raw, f"module_changes[{index}]", errors)
        module_id = str(change.get("module", ""))
        if module_id in changed_modules:
            errors.append(f"duplicate module change for {module_id}")
        changed_modules.add(module_id)
        if module_id not in modules:
            errors.append(f"module_changes[{index}]: unknown module {module_id!r}")
        elif module_id not in base_specs:
            errors.append(f"module_changes[{index}]: base_specs is missing {module_id}")
        if not isinstance(change.get("before_digest"), str) or not change["before_digest"]:
            errors.append(f"module_changes[{index}]: before_digest is required")
        elif check_base and module_id in modules and change["before_digest"] != digest(module_contract(modules[module_id])):
            errors.append(f"module_changes[{index}]: stale module contract digest for {module_id}")
        for key in ("ticket", "activates_with"):
            if not isinstance(change.get(key), str) or not change[key]:
                errors.append(f"module_changes[{index}]: {key} is required")
        after = require_mapping(change.get("after"), f"module_changes[{index}]: after", errors)
        if after.get("maturity") not in MATURITY:
            errors.append(f"module_changes[{index}]: invalid maturity {after.get('maturity')!r}")
        elif module_id in modules:
            before_maturity = modules[module_id]["entry"].get("maturity")
            if before_maturity in MATURITY:
                before_index = MATURITY.index(before_maturity)
                after_index = MATURITY.index(after["maturity"])
                if after_index > before_index + 1:
                    errors.append(
                        f"module_changes[{index}]: maturity promotion must advance one stage"
                    )
        for concern, owner in require_mapping(after.get("authority"), f"module_changes[{index}]: authority", errors).items():
            if not str(concern) or owner not in AUTHORITY:
                errors.append(f"module_changes[{index}]: invalid authority {concern}={owner!r}")
    if not errors:
        candidate = copy.deepcopy(modules)
        for raw in delta.get("operations", []):
            module_id = raw["module"]
            requirements = candidate[module_id]["spec"]["requirements"]
            position = next(
                (index for index, item in enumerate(requirements) if item.get("id") == raw["requirement_id"]),
                None,
            )
            if raw["op"] == "add":
                requirements.append(copy.deepcopy(raw["after"]))
            elif raw["op"] == "replace" and position is not None:
                requirements[position] = copy.deepcopy(raw["after"])
            elif raw["op"] == "remove" and position is not None:
                requirements.pop(position)
        for raw in delta.get("module_changes", []):
            data = candidate[raw["module"]]
            after = raw["after"]
            data["entry"]["maturity"] = after["maturity"]
            data["entry"]["authority"] = copy.deepcopy(after["authority"])
            data["spec"]["imports"] = copy.deepcopy(after.get("imports", []))
            data["spec"]["seams"] = copy.deepcopy(after.get("seams", []))
        errors.extend(validate_modules(candidate))
    return sorted(set(errors))


def requirement_map(modules: dict[str, dict[str, Any]]) -> dict[str, tuple[str, dict[str, Any]]]:
    result: dict[str, tuple[str, dict[str, Any]]] = {}
    for module_id, data in modules.items():
        spec = data.get("spec")
        if not isinstance(spec, dict) or not isinstance(spec.get("requirements"), list):
            continue
        for req in spec["requirements"]:
            if isinstance(req, dict) and isinstance(req.get("id"), str) and req["id"]:
                result[req["id"]] = (module_id, req)
    return result


def module_contract(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "maturity": data["entry"].get("maturity"),
        "authority": data["entry"].get("authority", {}),
        "imports": data["spec"].get("imports", []),
        "seams": data["spec"].get("seams", []),
    }


def semantic_diff(before: dict[str, dict[str, Any]], after: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if set(before) != set(after):
        added = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        raise DotSpecError(
            f"module set changes are unsupported; added={added}, removed={removed}"
        )
    old, new = requirement_map(before), requirement_map(after)
    operations: list[dict[str, Any]] = []
    for req_id in sorted(set(old) | set(new)):
        if req_id not in old:
            module_id, req = new[req_id]
            operations.append({"op": "add", "module": module_id, "requirement_id": req_id, "after": req})
        elif req_id not in new:
            module_id, req = old[req_id]
            operations.append({"op": "remove", "module": module_id, "requirement_id": req_id, "before_digest": digest(req)})
        elif digest(old[req_id][1]) != digest(new[req_id][1]):
            module_id, req = new[req_id]
            operations.append({"op": "replace", "module": module_id, "requirement_id": req_id, "before_digest": digest(old[req_id][1]), "after": req})
    module_changes: list[dict[str, Any]] = []
    for module_id in sorted(set(before) & set(after)):
        old_contract = module_contract(before[module_id])
        new_contract = module_contract(after[module_id])
        if digest(old_contract) != digest(new_contract):
            module_changes.append({
                "module": module_id,
                "before_digest": digest(old_contract),
                "after": new_contract,
            })
    return {"schema_version": SCHEMA_VERSION, "operations": operations, "module_changes": module_changes}


def trace_graph(modules: dict[str, dict[str, Any]]) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []
    for req_id, (module_id, req) in sorted(requirement_map(modules).items()):
        entry, spec = modules[module_id]["entry"], modules[module_id]["spec"]
        trace.append({
            "requirement_id": req_id,
            "module": module_id,
            "concern": req.get("concern"),
            "authority": entry.get("authority", {}).get(req.get("concern")),
            "seams": req.get("seams", spec.get("seams", [])),
            "scenarios": [item.get("id") for item in req.get("scenarios", []) if isinstance(item, dict)],
            "invariants": [item.get("id") for item in req.get("invariants", []) if isinstance(item, dict)],
            "verification": req.get("verification", []),
            "spec_digest": digest(spec),
        })
    return {"schema_version": SCHEMA_VERSION, "trace": trace}


def verify_graph(
    manifest_path: Path,
    modules: dict[str, dict[str, Any]],
    head_sha: str,
    command: list[str],
) -> tuple[dict[str, Any], int]:
    if not command:
        raise DotSpecError("verify requires a command after --")
    repo_root = git_repo_root(manifest_path.parent)
    actual_head = git_head(repo_root)
    if head_sha != actual_head:
        raise DotSpecError(f"head SHA mismatch: expected {actual_head}, received {head_sha}")
    require_clean_git(repo_root)
    result = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if git_head(repo_root) != actual_head:
        raise DotSpecError("Git HEAD changed while independent verification ran")
    require_clean_git(repo_root)
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "head_sha": head_sha,
        "manifest": str(manifest_path),
        "module_spec_digests": {
            module_id: digest(data["spec"]) for module_id, data in sorted(modules.items())
        },
        "command": command,
        "exit_code": result.returncode,
        "passed": result.returncode == 0,
        "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
    }
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return evidence, result.returncode


def emit(value: Any, output: Path | None) -> None:
    text = json.dumps(normalize(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("manifest", type=Path)
    validate.add_argument("--delta", type=Path)
    validate.add_argument("--check-base", action="store_true")
    normalize_cmd = sub.add_parser("normalize")
    normalize_cmd.add_argument("path", type=Path)
    normalize_cmd.add_argument("--output", type=Path)
    digest_cmd = sub.add_parser("digest")
    digest_cmd.add_argument("path", type=Path)
    diff_cmd = sub.add_parser("diff")
    diff_cmd.add_argument("before", type=Path)
    diff_cmd.add_argument("after", type=Path)
    diff_cmd.add_argument("--output", type=Path)
    trace_cmd = sub.add_parser("trace")
    trace_cmd.add_argument("manifest", type=Path)
    trace_cmd.add_argument("--output", type=Path)
    verify_cmd = sub.add_parser("verify")
    verify_cmd.add_argument("manifest", type=Path)
    verify_cmd.add_argument("--head-sha", required=True)
    verify_cmd.add_argument("--output", type=Path, required=True)
    parse_argv = list(argv) if argv is not None else sys.argv[1:]
    verifier_command: list[str] = []
    if parse_argv and parse_argv[0] == "verify" and "--" in parse_argv:
        split_at = parse_argv.index("--")
        verifier_command = parse_argv[split_at + 1 :]
        parse_argv = parse_argv[:split_at]
    args = parser.parse_args(parse_argv)
    try:
        if args.command == "normalize":
            emit(load_data(args.path), args.output)
            return 0
        if args.command == "digest":
            print(digest(load_data(args.path)))
            return 0
        if args.command == "validate":
            modules, errors = validate_graph(args.manifest)
            if args.delta and not errors:
                errors.extend(validate_delta(args.delta, modules, args.check_base))
            if errors:
                for error in sorted(set(errors)):
                    print(error, file=sys.stderr)
                return 1
            print(f"valid: {len(modules)} module(s)")
            return 0
        if args.command == "verify":
            modules, errors = validate_graph(args.manifest)
            if errors:
                raise DotSpecError("; ".join(errors))
            evidence, returncode = verify_graph(
                args.manifest, modules, args.head_sha, verifier_command
            )
            emit(evidence, args.output)
            return 0 if returncode == 0 else 1
        before, before_errors = validate_graph(args.before if args.command == "diff" else args.manifest)
        if args.command == "diff":
            after, after_errors = validate_graph(args.after)
            if before_errors or after_errors:
                raise DotSpecError("; ".join(sorted(set(before_errors + after_errors))))
            emit(semantic_diff(before, after), args.output)
        else:
            if before_errors:
                raise DotSpecError("; ".join(before_errors))
            emit(trace_graph(before), args.output)
        return 0
    except (OSError, ValueError, DotSpecError) as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
