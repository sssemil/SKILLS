#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "post_github_review.py"


class PostGithubReviewTests(unittest.TestCase):
    def test_dry_run_creates_inline_and_summary_fallback(self):
        with fake_gh() as env:
            payload = base_payload(
                findings=[
                    inline_finding("f1"),
                    {
                        "fingerprint": "f2",
                        "severity": "MINOR",
                        "body": "Small cleanup.",
                        "path": "src/lib.rs",
                        "line": 9,
                        "side": "RIGHT",
                        "start_line": None,
                        "start_side": None,
                        "fallback_reason": None,
                    },
                ]
            )
            result = run_script(payload, env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            planned = json.loads(result.stdout)
            self.assertEqual(planned["summary"]["action"], "create_summary")
            self.assertEqual(planned["inline"][0]["action"], "create_inline")
            self.assertEqual(planned["summary_findings"][0]["fingerprint"], "f2")
            self.assertNotIn("POST", " ".join(" ".join(call) for call in read_calls(env)))

    def test_live_mode_posts_by_default_and_reports_structured_result(self):
        with fake_gh() as env:
            result = run_script(base_payload(), env)
            self.assertEqual(result.returncode, 0, result.stderr)
            posted = json.loads(result.stdout)
            self.assertEqual(posted["status"], "posted")
            self.assertEqual(posted["repo"], "O/R")
            self.assertEqual(posted["pr_number"], 1)
            self.assertEqual(posted["summary"]["action"], "create_summary")
            self.assertEqual(posted["inline_count"], 1)
            self.assertEqual(posted["inline"][0]["action"], "create_inline")
            self.assertEqual(posted["inline"][0]["fingerprint"], "f1")
            flat = [" ".join(call) for call in read_calls(env)]
            self.assertTrue(any("POST repos/O/R/pulls/1/comments" in call for call in flat))
            self.assertTrue(any("POST repos/O/R/issues/1/comments" in call for call in flat))

    def test_patches_existing_generated_comments(self):
        with fake_gh(
            issue_comments=[
                generated_comment(10, "<!-- linear-gh-brutal-pr-review:summary -->\nold")
            ],
            review_comments=[
                generated_comment(20, "<!-- linear-gh-brutal-pr-review:f1 -->\nold", commit_id="abc123")
            ],
        ) as env:
            result = run_script(base_payload(findings=[inline_finding("f1")]), env)
            self.assertEqual(result.returncode, 0, result.stderr)
            posted = json.loads(result.stdout)
            self.assertEqual(posted["summary"]["action"], "patch_summary")
            self.assertEqual(posted["inline"][0]["action"], "patch_inline")
            calls = read_calls(env)
            flat = [" ".join(call) for call in calls]
            self.assertTrue(any("PATCH repos/O/R/issues/comments/10" in call for call in flat))
            self.assertTrue(any("PATCH repos/O/R/pulls/comments/20" in call for call in flat))

    def test_stale_head_sha_aborts(self):
        with fake_gh(head_sha="def456") as env:
            result = run_script(base_payload(), env, "--dry-run")
            self.assertEqual(result.returncode, 2)
            self.assertIn("PR head changed", result.stderr)

    def test_malformed_payload_fails(self):
        with fake_gh() as env:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--payload", "-"],
                input="{not json",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid JSON payload", result.stderr)

    def test_missing_gh_fails(self):
        payload = json.dumps(base_payload())
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--payload", "-", "--dry-run"],
                input=payload,
                text=True,
                capture_output=True,
                env={"PATH": tmp},
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("gh CLI is not available", result.stderr)

    def test_gh_api_failure_fails(self):
        with fake_gh(fail=True) as env:
            result = run_script(base_payload(), env, "--dry-run")
            self.assertEqual(result.returncode, 2)
            self.assertIn("gh api", result.stderr)

    def test_existing_inline_from_old_head_creates_new_comment(self):
        with fake_gh(
            review_comments=[
                generated_comment(20, "<!-- linear-gh-brutal-pr-review:f1 -->\nold", commit_id="oldsha")
            ],
        ) as env:
            result = run_script(base_payload(findings=[inline_finding("f1")]), env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            planned = json.loads(result.stdout)
            self.assertEqual(planned["inline"][0]["action"], "create_inline")

    def test_refuses_fork_without_explicit_allowance(self):
        with fake_gh(head_repo="Other/Fork") as env:
            result = run_script(base_payload(), env)
            self.assertEqual(result.returncode, 2)
            self.assertIn("refusing to post to fork", result.stderr)

    def test_dry_run_allows_fork_preview_without_posting(self):
        with fake_gh(head_repo="Other/Fork") as env:
            result = run_script(base_payload(), env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            planned = json.loads(result.stdout)
            self.assertEqual(planned["inline"][0]["action"], "create_inline")
            flat = [" ".join(call) for call in read_calls(env)]
            self.assertFalse(any("POST" in call or "PATCH" in call for call in flat))

    def test_preserves_hidden_markers_in_rendered_bodies(self):
        with fake_gh() as env:
            payload = base_payload(
                findings=[
                    inline_finding("f1"),
                    {
                        "fingerprint": "minor-1",
                        "severity": "MINOR",
                        "body": "Keep **markdown** intact.",
                        "path": None,
                        "line": None,
                        "side": None,
                        "start_line": None,
                        "start_side": None,
                        "fallback_reason": "summary-only",
                    },
                ]
            )
            result = run_script(payload, env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            planned = json.loads(result.stdout)
            self.assertIn("<!-- linear-gh-brutal-pr-review:summary -->", planned["summary"]["body"])
            self.assertIn("<!-- linear-gh-brutal-pr-review:f1 -->", planned["inline"][0]["body"])
            self.assertIn("Keep **markdown** intact.", planned["summary"]["body"])

    def test_invalid_inline_line_falls_back_to_summary(self):
        with fake_gh() as env:
            result = run_script(base_payload(findings=[inline_finding("f1", line=999)]), env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            planned = json.loads(result.stdout)
            self.assertEqual(planned["inline"], [])
            self.assertEqual(planned["summary_findings"][0]["fallback_reason"], "line is not present in the current PR diff")

    def test_quoted_marker_is_not_patched(self):
        with fake_gh(
            issue_comments=[
                {
                    "id": 10,
                    "body": "A human quoted this:\n<!-- linear-gh-brutal-pr-review:summary -->",
                }
            ]
        ) as env:
            result = run_script(base_payload(), env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            planned = json.loads(result.stdout)
            self.assertEqual(planned["summary"]["action"], "create_summary")

    def test_marker_by_different_author_is_not_patched(self):
        with fake_gh(
            review_comments=[
                generated_comment(
                    20,
                    "<!-- linear-gh-brutal-pr-review:f1 -->\nnot mine",
                    commit_id="abc123",
                    login="someone-else",
                )
            ]
        ) as env:
            result = run_script(base_payload(), env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            planned = json.loads(result.stdout)
            self.assertEqual(planned["inline"][0]["action"], "create_inline")

    def test_old_and_current_inline_markers_patch_current_comment(self):
        with fake_gh(
            review_comments=[
                generated_comment(20, "<!-- linear-gh-brutal-pr-review:f1 -->\nold", commit_id="oldsha"),
                generated_comment(21, "<!-- linear-gh-brutal-pr-review:f1 -->\ncurrent", commit_id="abc123"),
            ]
        ) as env:
            result = run_script(base_payload(), env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            planned = json.loads(result.stdout)
            self.assertEqual(planned["inline"][0]["action"], "patch_inline")
            self.assertEqual(planned["inline"][0]["comment_id"], 21)

    def test_final_head_change_aborts_before_live_posting(self):
        with fake_gh(head_shas=["abc123", "def456"]) as env:
            result = run_script(base_payload(), env)
            self.assertEqual(result.returncode, 2)
            self.assertIn("PR head changed", result.stderr)
            flat = [" ".join(call) for call in read_calls(env)]
            self.assertFalse(any("POST" in call or "PATCH" in call for call in flat))

    def test_case_only_repo_difference_is_not_treated_as_fork(self):
        with fake_gh(base_repo="O/R", head_repo="o/r") as env:
            result = run_script(base_payload(), env, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_unsafe_fingerprint_marker(self):
        with fake_gh() as env:
            result = run_script(base_payload(findings=[inline_finding("bad-->marker")]), env, "--dry-run")
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid fingerprint", result.stderr)


def base_payload(findings=None):
    return {
        "repo": "O/R",
        "pr_number": 1,
        "head_sha": "abc123",
        "summary_markdown": "Review summary.",
        "findings": findings or [inline_finding("f1")],
    }


def inline_finding(fingerprint, *, line=42):
    return {
        "fingerprint": fingerprint,
        "severity": "CRITICAL",
        "body": "This line is broken.",
        "path": "src/lib.rs",
        "line": line,
        "side": "RIGHT",
        "start_line": None,
        "start_side": None,
        "fallback_reason": None,
    }


def generated_comment(comment_id, body, *, commit_id=None, login="me"):
    comment = {"id": comment_id, "body": body, "user": {"login": login}}
    if commit_id is not None:
        comment["commit_id"] = commit_id
    return comment


def run_script(payload, env, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--payload", "-", *args],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def read_calls(env):
    return json.loads(Path(env["GH_FAKE_CALLS"]).read_text(encoding="utf-8"))


class fake_gh:
    def __init__(
        self,
        *,
        head_sha="abc123",
        head_shas=None,
        user_login="me",
        base_repo="O/R",
        head_repo="O/R",
        issue_comments=None,
        review_comments=None,
        files=None,
        fail=False,
    ):
        self.head_sha = head_sha
        self.head_shas = head_shas
        self.user_login = user_login
        self.base_repo = base_repo
        self.head_repo = head_repo
        self.issue_comments = issue_comments or []
        self.review_comments = review_comments or []
        self.files = files or [
            {
                "filename": "src/lib.rs",
                "patch": "@@ -40,5 +40,5 @@\n line 40\n line 41\n+This line is broken.\n line 43\n line 44",
            }
        ]
        self.fail = fail
        self.tmp = None

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        bin_dir = root / "bin"
        bin_dir.mkdir()
        state = {
            "head_sha": self.head_sha,
            "head_shas": self.head_shas,
            "user_login": self.user_login,
            "base_repo": self.base_repo,
            "head_repo": self.head_repo,
            "issue_comments": self.issue_comments,
            "review_comments": self.review_comments,
            "files": self.files,
            "fail": self.fail,
        }
        state_path = root / "state.json"
        calls_path = root / "calls.json"
        state_path.write_text(json.dumps(state), encoding="utf-8")
        calls_path.write_text("[]", encoding="utf-8")
        gh = bin_dir / "gh"
        gh.write_text(
            textwrap.dedent(
                """\
                #!/usr/bin/env python3
                import json
                import os
                import sys
                from pathlib import Path

                state = json.loads(Path(os.environ["GH_FAKE_STATE"]).read_text())
                calls_path = Path(os.environ["GH_FAKE_CALLS"])
                calls = json.loads(calls_path.read_text())
                calls.append(sys.argv[1:])
                calls_path.write_text(json.dumps(calls))

                if state.get("fail"):
                    print("forced failure", file=sys.stderr)
                    sys.exit(1)

                args = sys.argv[1:]
                endpoint = ""
                skip_next = False
                for arg in args[1:]:
                    if skip_next:
                        skip_next = False
                        continue
                    if arg in {"--method", "-f", "-F"}:
                        skip_next = True
                        continue
                    if not arg.startswith("-"):
                        endpoint = arg
                        break
                method = "GET"
                if "--method" in args:
                    method = args[args.index("--method") + 1]

                if method == "GET" and endpoint == "repos/O/R/pulls/1":
                    head_shas = state.get("head_shas") or [state["head_sha"]]
                    head_sha = head_shas.pop(0) if len(head_shas) > 1 else head_shas[0]
                    state["head_shas"] = head_shas
                    Path(os.environ["GH_FAKE_STATE"]).write_text(json.dumps(state))
                    print(json.dumps({
                        "head": {"sha": head_sha, "repo": {"full_name": state["head_repo"]}},
                        "base": {"repo": {"full_name": state["base_repo"]}}
                    }))
                elif method == "GET" and endpoint == "user":
                    print(json.dumps({"login": state["user_login"]}))
                elif method == "GET" and endpoint == "repos/O/R/issues/1/comments?per_page=100":
                    if "--slurp" in args:
                        print(json.dumps([state["issue_comments"]]))
                    else:
                        print(json.dumps(state["issue_comments"]))
                elif method == "GET" and endpoint == "repos/O/R/pulls/1/comments?per_page=100":
                    if "--slurp" in args:
                        print(json.dumps([state["review_comments"]]))
                    else:
                        print(json.dumps(state["review_comments"]))
                elif method == "GET" and endpoint == "repos/O/R/pulls/1/files?per_page=100":
                    if "--slurp" in args:
                        print(json.dumps([state["files"]]))
                    else:
                        print(json.dumps(state["files"]))
                else:
                    print("{}")
                """
            ),
            encoding="utf-8",
        )
        gh.chmod(0o755)
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{bin_dir}{os.pathsep}{env.get('PATH', '')}",
                "GH_FAKE_STATE": str(state_path),
                "GH_FAKE_CALLS": str(calls_path),
            }
        )
        return env

    def __exit__(self, exc_type, exc, tb):
        self.tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
