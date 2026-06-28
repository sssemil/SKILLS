---
name: gh-brutal-pr-review
description: "Review GitHub pull requests with brutal multi-perspective scrutiny and direct GitHub PR comments. Uses BRUTAL.md for local, Linear, or Gitlear context and supports local no-ticket PR review."
---

# GH Brutal PR Review

Run a GitHub-native PR review. Use `BRUTAL.md` to decide whether product context
comes from local repo docs, Linear, or Gitlear.

## Required Context

1. Read `../brutal-shared/backend-resolver.md`.
2. Resolve the backend. In `local` mode, issue/ticket context is optional.
3. Read `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, README, CI workflows, package
   manifests, and relevant repo docs.
4. Load `references/rust.md` when Rust files or Cargo manifests are touched.

## Hard Rules

- Use GitHub comments only. Never approve or request changes automatically.
- Post live comments by default. Use dry-run only when the user asks for
  preview/no-post or when a safety guard blocks live posting.
- Stop before posting if the PR head SHA changed after context collection.
- Do not post to fork/external PRs unless the user explicitly allows it.
- Validate every finding against the current diff and surrounding code.
- Patch only generated inline comments authored by the active `gh` user and
  starting with the canonical marker `<!-- gh-brutal-pr-review:... -->`.
- Ignore legacy Linear/Gitlear generated comments when posting; the finding
  fixer handles legacy queues.
- Normal mode queues only `CRITICAL` and `MAJOR` inline findings. In explicit
  all-findings/fix-loop mode, also queue concrete line-mappable `MINOR`/`NIT`.

## Workflow

1. Resolve the PR from URL, number, branch, or current branch with `gh`.
2. Gather `gh pr view`, full diff, checks, issue comments, review comments, and
   review states. Record repo, PR number, head SHA, base branch, and fork state.
3. Resolve backend context:
   - `local`: use `BRUTAL.md`, repo docs, PR title/body, commits, and changed
     files as product context. If a local task id is referenced, read it.
   - `linear`: extract Linear identifiers/URLs from branch, PR title/body,
     commits, and linked issue text. Resolve exactly one issue in the configured
     project, then read issue body, comments, links, relations, and state.
   - `gitlear`: extract display keys/internal ids/search terms. Resolve exactly
     one issue in the configured project, then read raw issue Markdown for body,
     comments, labels, status, and project membership.
4. Write `/tmp/gh-brutal-pr-review-<repo-slug>-pr-<number>.md` containing PR
   metadata, diff, checks, backend context, repo rules, changed files, callers,
   tests, language profile notes, and verification results.
5. Launch five reviewers when available:
   - product/backend alignment
   - core correctness and architecture
   - reliability, testing, and error handling
   - performance, security, and concurrency
   - simplicity and maintainability
6. Merge duplicates, discard false positives, validate line mappings, and split
   output into inline findings and summary-only findings.
7. Build a payload for the helper:

```json
{
  "repo": "OWNER/REPO",
  "pr_number": 123,
  "head_sha": "abc123",
  "summary_markdown": "Review summary...",
  "findings": [],
  "inline_severities": ["CRITICAL", "MAJOR"]
}
```

In normal mode, omit `inline_severities`; the helper defaults to CRITICAL/MAJOR.
In all-findings mode, include all severities.

Post comments:

```bash
skill_dir="<path-to-gh-brutal-pr-review>"
python3 "$skill_dir/scripts/post_github_review.py" --payload review.json
```

Use dry-run only when explicitly requested:

```bash
skill_dir="<path-to-gh-brutal-pr-review>"
python3 "$skill_dir/scripts/post_github_review.py" --payload review.json --dry-run
```

## Final Response

Report PR, backend/context ref, head SHA, posting result, inline count, safety
blockers, findings by severity, and checks run.
