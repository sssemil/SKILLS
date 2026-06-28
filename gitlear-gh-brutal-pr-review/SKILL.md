---
name: gitlear-gh-brutal-pr-review
description: Review GitHub pull requests against their Gitlear issues with brutal multi-perspective scrutiny and direct GitHub PR comments. Use when Codex is asked to run $gitlear-gh-brutal-pr-review, perform a Gitlear-aware GitHub PR review, check PR alignment with a Gitlear issue, inspect existing GitHub/Gitlear context before reviewing, or post review comments directly to a GitHub PR. Supports Rust deeply via a Rust review profile.
---

# Gitlear GH Brutal PR Review

Run a Gitlear-aware, GitHub-native PR review. Gather the Gitlear issue, GitHub
PR state, prior comments, diff, and code context; launch specialist reviewers;
validate findings; post comment-only feedback to the PR by default; then print
the same validated findings in the final response.

## Hard Rules

- Use Gitlear as read-only context. Do not update Gitlear issues or comments.
- Use GitHub comments only. Never approve or request changes automatically.
- Post GitHub comments by default after synthesis. Use dry-run only when the
  user explicitly asks for preview, dry-run, no-post, or when live posting is
  blocked by a safety guard.
- Always include validated review findings in the final response.
- Stop before reviewing if exactly one Gitlear issue cannot be resolved.
- Stop before posting if the PR head SHA changed after context collection.
- Do not post to fork/external PRs unless the user explicitly allows it; use
  dry-run or stop instead.
- Do not post speculative findings. Validate every finding against the diff and
  surrounding code first.
- Re-runs must create a new generated summary comment. Do not patch or delete
  earlier generated summaries.
- Do not edit human GitHub comments. Only patch generated inline comments
  authored by the active `gh` user and starting with this skill's exact hidden
  marker.
- Normal mode queues only `CRITICAL` and `MAJOR` findings as inline comments.
  Use all-findings mode only when an orchestrator or user explicitly asks for
  fix-loop, all-severities, or all-findings behavior.
- If subagent tooling is unavailable, stop unless the user explicitly allows a
  single-agent fallback.

## Gitlear Context Rules

- Read `AGENTS.md` and require `Gitlear workspace: <name or key_prefix>` and
  `Gitlear project: <name>`.
- Validate the active Gitlear MCP workspace with `gitlear_workspace_get`.
- Resolve the project with `gitlear_project_list`, then use the returned
  internal project id.
- Current MCP issue snapshots omit status, project, body, and comments. For
  issue body, comments, and project membership, read raw Markdown under
  `gitlear_workspace_get.root`.
- Verify the resolved issue belongs to the resolved project by checking its raw
  path under `projects/<project-id>/issues/<status>/`.

## Step 1: Resolve The PR

Resolve the target PR from an explicit URL, number, branch, or current branch.
Use `gh` and fail early if it is unavailable or unauthenticated.

Gather:

```bash
gh pr view <target> --json number,url,title,body,baseRefName,headRefName,headRefOid,author,commits,files,reviews,comments,reviewDecision,mergeStateStatus,isCrossRepository
gh pr diff <target>
gh pr checks <target>
```

Also query GitHub API data that `gh pr view` omits or truncates:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate
gh api repos/{owner}/{repo}/issues/{number}/comments --paginate
gh api repos/{owner}/{repo}/pulls/{number}/reviews --paginate
```

Record `repo`, `pr_number`, `head_sha`, fork status, and base branch.

## Step 2: Resolve Gitlear Context

1. Read `AGENTS.md`.
2. Validate `Gitlear workspace:` against `gitlear_workspace_get`.
3. Resolve `Gitlear project:` through `gitlear_project_list`.
4. Extract possible Gitlear issue candidates from branch name, PR title, PR
   body, commits, and linked issue text:
   - display keys using the active workspace key prefix, such as `TQD-123`
   - internal ids matching the workspace prefix, when present
   - title/search terms through `gitlear_search` or `gitlear_issue_list`
5. Dedupe candidates and resolve each through `gitlear_issue_get` when
   available, or by matching raw Markdown files under the Gitlear workspace.
6. Require exactly one issue in the resolved project. If zero or multiple
   plausible issues remain, ask the user for the intended Gitlear issue before
   continuing.
7. Read the full raw issue body, comments, status, labels, and path-derived
   project membership. Alignment findings should cite the relevant Gitlear
   requirement or comment.

## Step 3: Gather Code Context

Read repo instructions such as `AGENTS.md`, `CLAUDE.md`, `README`, CI
workflows, `justfile`, `Makefile`, and package manifests when relevant. Read
every changed file in full and inspect direct call sites, trait/interface
implementations, tests, feature flags, config schemas, and generated/public API
boundaries touched by the diff.

Load language profiles only when relevant:

- For Rust files or Cargo manifests, read `references/rust.md`.

Prefer project-specific verification commands. Run deterministic checks when
practical, distinguishing pre-existing failures from PR-caused failures.

## Step 4: Build Review Context

Write a complete context file:

```text
/tmp/gitlear-gh-brutal-pr-review-<repo-slug>-pr-<number>.md
```

Include:

- PR metadata, head SHA, checks, changed files, and full diff
- Gitlear workspace/project identity
- Gitlear issue body, comments, labels, status, path, and acceptance criteria
- Existing GitHub issue comments, review comments, review states, and checks
- Repo rules, relevant manifests, changed files, callers, and test context
- Loaded language-profile notes and verification results

Subagents must read this file first. Do not rely on inherited context.

## Step 5: Launch Reviewers

Launch all five reviewers in parallel. Each reviewer returns findings with
severity, confidence, file/line/snippet, explanation, concrete fix, and whether
the finding should be inline or summary-only.

Reviewer perspectives:

- **Gitlear/Product Alignment**: verify the PR implements the Gitlear issue,
  acceptance criteria, notes, and latest comments without hidden scope drift or
  missing behavior.
- **Core Correctness/Architecture**: verify algorithms, state transitions,
  public APIs, data flow, compatibility, and architectural placement.
- **Reliability/Testing/Error Handling**: verify tests, edge cases, error
  paths, panics, retries, cancellation, and failure behavior.
- **Performance/Security/Concurrency**: verify allocation, hot paths, locks,
  async boundaries, permissions, injection, secrets, and resource growth.
- **Simplicity/Maintainability**: verify needless code, abstractions, naming,
  duplication, documentation, and local style.

Use severities:

- `CRITICAL`: correctness, safety, security, data loss, or production breakage.
- `MAJOR`: should fix before merge unless there is a clear reason.
- `MINOR`: useful improvement that should not block merge.
- `NIT`: optional cleanup.

## Step 6: Synthesize And Validate

Merge duplicates, discard false positives, and validate every remaining finding
against the current diff and surrounding code.

Prepare GitHub-ready output:

- Inline comments only for validated `CRITICAL` and `MAJOR` findings with exact
  current-diff line mappings.
- Summary-only comments for `MINOR`, `NIT`, cross-file concerns, Gitlear
  alignment summaries, verification output, and unmappable findings.
- In explicit all-findings mode, queue validated `CRITICAL`, `MAJOR`, `MINOR`,
  and `NIT` findings when concrete and line-mappable.

## Step 7: Post GitHub Comments And Print Review

Create a payload for `scripts/post_github_review.py`:

```json
{
  "repo": "OWNER/REPO",
  "pr_number": 123,
  "head_sha": "abc123",
  "summary_markdown": "Review summary...",
  "findings": [
    {
      "fingerprint": "stable-normalized-id",
      "severity": "CRITICAL",
      "path": "src/lib.rs",
      "line": 42,
      "side": "RIGHT",
      "start_line": null,
      "start_side": null,
      "body": "Finding body...",
      "fallback_reason": null
    }
  ]
}
```

Omit `inline_severities` in normal mode. In all-findings mode, set:

```json
"inline_severities": ["CRITICAL", "MAJOR", "MINOR", "NIT"]
```

Post live comments:

```bash
python3 /home/user/Workspaces/SKILLS/gitlear-gh-brutal-pr-review/scripts/post_github_review.py --payload review.json
```

Use dry-run only when explicitly requested:

```bash
python3 /home/user/Workspaces/SKILLS/gitlear-gh-brutal-pr-review/scripts/post_github_review.py --payload review.json --dry-run
```

The helper verifies current head SHA, refuses unsafe inline mappings, dedupes or
patches generated inline comments with `gitlear-gh-brutal-pr-review` hidden
markers, creates append-only summaries, and truncates oversized comments.

## Final Response

Use this shape:

```markdown
Posted:
- PR: <number/url>
- Gitlear: <display key>
- Head: <sha>
- Summary comment: <created|dry-run|blocked>
- Inline comments: <count>

Not posted:
- <None, or exact safety blocker>

Findings:
### CRITICAL
- <file:line> <finding and fix>
### MAJOR
- <file:line> <finding and fix>
### MINOR / NIT
- <summary-only findings if relevant>

Checks:
- <local and GitHub checks with pass/fail/pending and notable failure reason>
```
