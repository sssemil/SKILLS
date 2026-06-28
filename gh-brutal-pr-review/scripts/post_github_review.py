#!/usr/bin/env python3
"""Post generated GitHub PR review comments, or preview them with --dry-run.

The script is intentionally conservative: it verifies the PR head SHA, refuses
unsafe inline mappings, patches only generated inline comments with this
skill's hidden markers, creates append-only summaries, and falls back to the
summary for anything that cannot be represented inline. Live posting is the
default; pass --dry-run to preview without writing.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TOOL = "gh-brutal-pr-review"
SUMMARY_MARKER = f"<!-- {TOOL}:summary -->"
FINGERPRINT_PREFIX = f"<!-- {TOOL}:"
FINGERPRINT_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
HUNK_RE = re.compile(r"^@@ -(?P<old>\d+)(?:,\d+)? \+(?P<new>\d+)(?:,\d+)? @@")
MAX_COMMENT_LENGTH = 65000
VALID_SEVERITIES = {"CRITICAL", "MAJOR", "MINOR", "NIT"}
DEFAULT_INLINE_SEVERITIES = frozenset({"CRITICAL", "MAJOR"})


class ReviewError(RuntimeError):
    pass


@dataclass(frozen=True)
class Finding:
    fingerprint: str
    severity: str
    body: str
    path: str | None = None
    line: int | None = None
    side: str | None = None
    start_line: int | None = None
    start_side: str | None = None
    fallback_reason: str | None = None

    @property
    def marker(self) -> str:
        return f"{FINGERPRINT_PREFIX}{self.fingerprint} -->"

    def can_post_inline(self, inline_severities: set[str]) -> bool:
        return (
            self.severity in inline_severities
            and not self.fallback_reason
            and bool(self.path)
            and isinstance(self.line, int)
            and self.line > 0
            and self.side in {"LEFT", "RIGHT"}
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", default="-", help="Review payload JSON path, or '-' for stdin")
    parser.add_argument("--dry-run", action="store_true", help="Preview planned actions without posting comments")
    parser.add_argument("--allow-fork", action="store_true", help="Allow posting to PRs from forked repositories")
    args = parser.parse_args()

    try:
        payload = read_payload(args.payload)
        repo, pr_number, head_sha, summary, findings, inline_severities = validate_payload(payload)
        require_gh()

        pr = gh_json(["api", f"repos/{repo}/pulls/{pr_number}"])
        verify_pr(repo, head_sha, pr, allow_fork=args.allow_fork or args.dry_run)
        author_login = authenticated_login()

        issue_comments = gh_json_paginated(f"repos/{repo}/issues/{pr_number}/comments?per_page=100")
        review_comments = gh_json_paginated(f"repos/{repo}/pulls/{pr_number}/comments?per_page=100")
        files = gh_json_paginated(f"repos/{repo}/pulls/{pr_number}/files?per_page=100")
        diff_index = build_diff_index(files)

        actions = plan_actions(
            repo,
            pr_number,
            head_sha,
            summary,
            findings,
            issue_comments,
            review_comments,
            diff_index,
            author_login,
            inline_severities,
        )
        if args.dry_run:
            print(json.dumps(actions, indent=2, sort_keys=True))
            return 0

        latest_pr = gh_json(["api", f"repos/{repo}/pulls/{pr_number}"])
        verify_pr(repo, head_sha, latest_pr, allow_fork=args.allow_fork)
        execute_actions(actions)
        print(json.dumps(summarize_actions(actions, status="posted"), indent=2, sort_keys=True))
        return 0
    except ReviewError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def read_payload(path: str) -> dict[str, Any]:
    try:
        if path == "-":
            return json.load(sys.stdin)
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ReviewError(f"invalid JSON payload: {exc}") from exc
    except OSError as exc:
        raise ReviewError(f"cannot read payload: {exc}") from exc


def validate_payload(payload: Any) -> tuple[str, int, str, str, list[Finding], set[str]]:
    if not isinstance(payload, dict):
        raise ReviewError("payload must be a JSON object")

    repo = require_str(payload, "repo")
    if "/" not in repo or repo.count("/") != 1:
        raise ReviewError("repo must be OWNER/REPO")

    pr_number = payload.get("pr_number")
    if not isinstance(pr_number, int) or pr_number <= 0:
        raise ReviewError("pr_number must be a positive integer")

    head_sha = require_str(payload, "head_sha")
    summary = require_str(payload, "summary_markdown")
    raw_findings = payload.get("findings", [])
    if not isinstance(raw_findings, list):
        raise ReviewError("findings must be a list")
    inline_severities = parse_inline_severities(payload)

    findings: list[Finding] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_findings):
        if not isinstance(raw, dict):
            raise ReviewError(f"findings[{index}] must be an object")
        fingerprint = require_str(raw, "fingerprint")
        if not FINGERPRINT_RE.fullmatch(fingerprint):
            raise ReviewError(
                f"invalid fingerprint for findings[{index}]: use only letters, numbers, dot, underscore, colon, or hyphen"
            )
        if fingerprint in seen:
            raise ReviewError(f"duplicate finding fingerprint: {fingerprint}")
        seen.add(fingerprint)
        severity = require_str(raw, "severity").upper()
        if severity not in VALID_SEVERITIES:
            raise ReviewError(f"invalid severity for {fingerprint}: {severity}")
        body = require_str(raw, "body")
        findings.append(
            Finding(
                fingerprint=fingerprint,
                severity=severity,
                body=body,
                path=optional_str(raw, "path"),
                line=optional_int(raw, "line"),
                side=optional_str(raw, "side"),
                start_line=optional_int(raw, "start_line"),
                start_side=optional_str(raw, "start_side"),
                fallback_reason=optional_str(raw, "fallback_reason"),
            )
        )

    return repo, pr_number, head_sha, summary, findings, inline_severities


def parse_inline_severities(payload: dict[str, Any]) -> set[str]:
    raw = payload.get("inline_severities")
    if raw is None:
        return set(DEFAULT_INLINE_SEVERITIES)
    if not isinstance(raw, list) or not raw:
        raise ReviewError("inline_severities must be a non-empty list")

    severities: set[str] = set()
    for index, value in enumerate(raw):
        if not isinstance(value, str) or not value.strip():
            raise ReviewError(f"inline_severities[{index}] must be a non-empty string")
        severity = value.upper()
        if severity not in VALID_SEVERITIES:
            valid = ", ".join(sorted(VALID_SEVERITIES))
            raise ReviewError(f"invalid inline severity {value!r}; expected one of: {valid}")
        severities.add(severity)
    return severities


def require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReviewError(f"{key} must be a non-empty string")
    return value


def optional_str(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ReviewError(f"{key} must be a string or null")
    return value or None


def optional_int(payload: dict[str, Any], key: str) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        raise ReviewError(f"{key} must be an integer or null")
    return value


def require_gh() -> None:
    if shutil.which("gh") is None:
        raise ReviewError("gh CLI is not available on PATH")


def gh_json(args: list[str]) -> Any:
    result = run_gh(args)
    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError as exc:
        raise ReviewError(f"gh returned non-JSON output for {' '.join(args)}") from exc


def gh_json_paginated(endpoint: str) -> list[Any]:
    data = gh_json(["api", endpoint, "--paginate", "--slurp"])
    if not isinstance(data, list):
        raise ReviewError(f"paginated GitHub response for {endpoint} must be a list")
    if all(isinstance(page, list) for page in data):
        return [item for page in data for item in page]
    return data


def authenticated_login() -> str:
    user = gh_json(["api", "user"])
    if not isinstance(user, dict) or not isinstance(user.get("login"), str) or not user["login"]:
        raise ReviewError("could not determine authenticated GitHub user")
    return user["login"]


def run_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(["gh", *args], check=False, capture_output=True, text=True)
    except OSError as exc:
        raise ReviewError(f"failed to run gh: {exc}") from exc
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise ReviewError(f"gh {' '.join(args)} failed: {stderr}")
    return result


def verify_pr(repo: str, head_sha: str, pr: Any, *, allow_fork: bool) -> None:
    if not isinstance(pr, dict):
        raise ReviewError("GitHub PR response must be an object")
    current_sha = pr.get("head", {}).get("sha")
    if current_sha != head_sha:
        raise ReviewError(f"PR head changed from {head_sha} to {current_sha}; regenerate review context")

    base_repo = pr.get("base", {}).get("repo", {}).get("full_name")
    head_repo = pr.get("head", {}).get("repo", {}).get("full_name")
    if base_repo and base_repo.lower() != repo.lower():
        raise ReviewError(f"payload repo {repo} does not match PR base repo {base_repo}")
    if head_repo and base_repo and head_repo.lower() != base_repo.lower() and not allow_fork:
        raise ReviewError("refusing to post to fork/external PR without --allow-fork")


def plan_actions(
    repo: str,
    pr_number: int,
    head_sha: str,
    summary: str,
    findings: list[Finding],
    issue_comments: Any,
    review_comments: Any,
    diff_index: set[tuple[str, str, int]],
    author_login: str,
    inline_severities: set[str],
) -> dict[str, Any]:
    if not isinstance(issue_comments, list):
        raise ReviewError("issue comments response must be a list")
    if not isinstance(review_comments, list):
        raise ReviewError("review comments response must be a list")

    existing_inline = collect_existing_inline(review_comments, author_login, head_sha)

    inline_actions = []
    summary_findings = []
    for finding in findings:
        if finding.can_post_inline(inline_severities):
            invalid_reason = invalid_inline_reason(finding, diff_index)
            if invalid_reason:
                summary_findings.append(summary_item(finding, invalid_reason))
                continue
            body = trim_comment(f"{finding.marker}\n**Severity:** {finding.severity}\n\n{finding.body}")
            existing = existing_inline.get(finding.marker)
            if existing and existing.get("commit_id") == head_sha:
                inline_actions.append(
                    {
                        "action": "patch_inline",
                        "comment_id": existing["id"],
                        "endpoint": f"repos/{repo}/pulls/comments/{existing['id']}",
                        "body": body,
                        "fingerprint": finding.fingerprint,
                    }
                )
            else:
                action = {
                    "action": "create_inline",
                    "endpoint": f"repos/{repo}/pulls/{pr_number}/comments",
                    "body": body,
                    "commit_id": head_sha,
                    "path": finding.path,
                    "line": finding.line,
                    "side": finding.side,
                    "fingerprint": finding.fingerprint,
                }
                if finding.start_line:
                    action["start_line"] = finding.start_line
                if finding.start_side:
                    action["start_side"] = finding.start_side
                inline_actions.append(action)
        else:
            summary_findings.append(summary_item(finding, finding.fallback_reason or "not eligible for inline comment"))

    summary_body = build_summary_body(summary, summary_findings)
    summary_action = {
        "action": "create_summary",
        "endpoint": f"repos/{repo}/issues/{pr_number}/comments",
        "body": summary_body,
    }

    return {
        "repo": repo,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "summary": summary_action,
        "inline": inline_actions,
        "summary_findings": summary_findings,
    }


def collect_existing_inline(comments: list[Any], author_login: str, head_sha: str) -> dict[str, dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        if comment_author(comment) != author_login:
            continue
        marker = marker_from_body(comment.get("body", ""))
        if not marker:
            continue
        if comment.get("commit_id") != head_sha:
            continue
        if marker in existing:
            raise ReviewError(f"multiple generated inline comments found for marker {marker}")
        existing[marker] = comment
    return existing


def comment_author(comment: dict[str, Any]) -> str | None:
    user = comment.get("user")
    if not isinstance(user, dict):
        return None
    login = user.get("login")
    return login if isinstance(login, str) else None


def marker_from_body(body: str) -> str | None:
    if not isinstance(body, str):
        return None
    if not body.startswith(FINGERPRINT_PREFIX):
        return None
    end = body.find("-->")
    if end == -1:
        return None
    marker = body[: end + 3]
    if marker == SUMMARY_MARKER:
        return None
    return marker


def build_diff_index(files: Any) -> set[tuple[str, str, int]]:
    if not isinstance(files, list):
        raise ReviewError("PR files response must be a list")
    index: set[tuple[str, str, int]] = set()
    for file_info in files:
        if not isinstance(file_info, dict):
            continue
        path = file_info.get("filename")
        patch = file_info.get("patch")
        if not isinstance(path, str) or not isinstance(patch, str):
            continue
        old_line: int | None = None
        new_line: int | None = None
        for raw_line in patch.splitlines():
            hunk = HUNK_RE.match(raw_line)
            if hunk:
                old_line = int(hunk.group("old"))
                new_line = int(hunk.group("new"))
                continue
            if old_line is None or new_line is None or raw_line.startswith("\\"):
                continue
            if raw_line.startswith("+"):
                index.add((path, "RIGHT", new_line))
                new_line += 1
            elif raw_line.startswith("-"):
                index.add((path, "LEFT", old_line))
                old_line += 1
            else:
                index.add((path, "LEFT", old_line))
                index.add((path, "RIGHT", new_line))
                old_line += 1
                new_line += 1
    return index


def invalid_inline_reason(finding: Finding, diff_index: set[tuple[str, str, int]]) -> str | None:
    assert finding.path is not None
    assert finding.side is not None
    assert finding.line is not None
    if (finding.path, finding.side, finding.line) not in diff_index:
        return "line is not present in the current PR diff"
    if finding.start_line is not None:
        start_side = finding.start_side or finding.side
        if start_side not in {"LEFT", "RIGHT"}:
            return "start_side must be LEFT or RIGHT"
        if finding.start_line <= 0:
            return "start_line must be positive"
        if start_side == finding.side and finding.start_line > finding.line:
            return "start_line must not be greater than line on the same side"
        if (finding.path, start_side, finding.start_line) not in diff_index:
            return "start_line is not present in the current PR diff"
    elif finding.start_side is not None:
        return "start_side requires start_line"
    return None


def summary_item(finding: Finding, reason: str) -> dict[str, Any]:
    return {
        "fingerprint": finding.fingerprint,
        "severity": finding.severity,
        "body": finding.body,
        "fallback_reason": reason,
    }


def build_summary_body(summary: str, summary_findings: list[dict[str, Any]]) -> str:
    parts = [SUMMARY_MARKER, summary.strip()]
    if summary_findings:
        parts.append("\n### Summary-only findings")
        for item in summary_findings:
            parts.append(
                f"\n- **{item['severity']}** `{item['fingerprint']}`: {item['body']}\n"
                f"  Fallback: {item['fallback_reason']}"
            )
    return trim_comment("\n\n".join(parts))


def trim_comment(body: str) -> str:
    if len(body) <= MAX_COMMENT_LENGTH:
        return body
    suffix = "\n\n[Truncated by gh-brutal-pr-review because the GitHub comment limit was reached.]"
    return body[: MAX_COMMENT_LENGTH - len(suffix)] + suffix


def execute_actions(actions: dict[str, Any]) -> None:
    for action in actions["inline"]:
        apply_action(action)
    apply_action(actions["summary"])


def apply_action(action: dict[str, Any]) -> None:
    if action["action"].startswith("patch_"):
        args = ["api", "--method", "PATCH", action["endpoint"], "-f", f"body={action['body']}"]
    elif action["action"] == "create_summary":
        args = ["api", "--method", "POST", action["endpoint"], "-f", f"body={action['body']}"]
    elif action["action"] == "create_inline":
        args = [
            "api",
            "--method",
            "POST",
            action["endpoint"],
            "-f",
            f"body={action['body']}",
            "-f",
            f"commit_id={action['commit_id']}",
            "-f",
            f"path={action['path']}",
            "-F",
            f"line={action['line']}",
            "-f",
            f"side={action['side']}",
        ]
        if "start_line" in action:
            args.extend(["-F", f"start_line={action['start_line']}"])
        if "start_side" in action:
            args.extend(["-f", f"start_side={action['start_side']}"])
    else:
        raise ReviewError(f"unknown action: {action['action']}")
    run_gh(args)


def summarize_actions(actions: dict[str, Any], *, status: str) -> dict[str, Any]:
    return {
        "status": status,
        "repo": actions["repo"],
        "pr_number": actions["pr_number"],
        "head_sha": actions["head_sha"],
        "summary": {
            "action": actions["summary"]["action"],
            "comment_id": actions["summary"].get("comment_id"),
        },
        "inline": [
            {
                "action": action["action"],
                "fingerprint": action.get("fingerprint"),
                "comment_id": action.get("comment_id"),
                "path": action.get("path"),
                "line": action.get("line"),
                "side": action.get("side"),
            }
            for action in actions["inline"]
        ],
        "inline_count": len(actions["inline"]),
        "summary_findings": len(actions["summary_findings"]),
    }


if __name__ == "__main__":
    raise SystemExit(main())
