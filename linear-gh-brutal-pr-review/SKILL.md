---
name: linear-gh-brutal-pr-review
description: Review GitHub pull requests against their Linear tickets with brutal multi-perspective scrutiny and direct GitHub PR comments. Use when Codex is asked to run $linear-gh-brutal-pr-review, perform a Linear-aware GitHub PR review, check PR alignment with a Linear issue, inspect existing GitHub/Linear comments before reviewing, or post review comments directly to a GitHub PR. Supports Rust deeply via a Rust review profile and can be extended with additional language profiles.
---

# Linear GH Brutal PR Review

Run a Linear-aware, GitHub-native PR review. Gather the Linear ticket, GitHub
PR state, prior comments, diff, and code context; launch specialist reviewers;
validate findings; then post comment-only feedback to the PR.

## Hard Rules

- Use Linear as read-only context. Do not update Linear issues or comments.
- Use GitHub comments only. Never approve or request changes automatically.
- If the invocation does not clearly ask to comment/post on GitHub, prepare a
  preview or run `scripts/post_github_review.py --dry-run`.
- Stop before reviewing if exactly one Linear issue cannot be resolved.
- Stop before posting if the PR head SHA changed after context collection.
- Do not post speculative findings. Validate each finding against the diff and
  surrounding code first.
- Do not edit human GitHub comments. Only patch comments authored by the active
  `gh` user and starting with this skill's exact hidden marker.
- If subagent tooling is unavailable, stop unless the user explicitly allows a
  single-agent fallback.

## Step 1: Resolve The PR

Resolve the target PR from the explicit URL, number, branch, or current branch.
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

Record `repo`, `pr_number`, `head_sha`, whether the PR is from a fork, and the
base branch. Do not post to fork/external PRs unless explicitly allowed.

## Step 2: Resolve Linear Context

Extract possible Linear identifiers and URLs from the branch name, PR title,
PR body, commits, and linked issue text. Normalize to uppercase identifiers,
dedupe aliases, and resolve each candidate through Linear MCP.

- If exactly one Linear issue resolves, fetch full issue details with relations,
  releases, customer needs when available, attachments/links, and comments.
- If zero or multiple plausible issues resolve, ask the user for the intended
  Linear issue before continuing.
- Include Linear comments and issue state in the review context. Alignment
  findings should cite the relevant Linear requirement or comment.

## Step 3: Gather Code Context

Read repo instructions such as `AGENTS.md`, `CLAUDE.md`, `README`, CI workflows,
`justfile`, `Makefile`, and package manifests when relevant. Read every changed
file in full and inspect direct call sites, trait/interface implementations,
tests, feature flags, config schemas, and generated/public API boundaries touched
by the diff.

Load language profiles only when relevant:

- For Rust files or Cargo manifests, read `references/rust.md`.

Prefer project-specific verification commands. Run deterministic checks when
practical, but distinguish pre-existing failures from PR-caused failures.

## Step 4: Build Review Context

Write a complete context file:

```text
/tmp/linear-gh-brutal-pr-review-<repo-slug>-pr-<number>.md
```

Include:

- PR metadata, head SHA, checks, changed files, and full diff
- Linear issue body, comments, links, relations, and acceptance criteria
- Existing GitHub issue comments, review comments, review states, and checks
- Repo rules, relevant manifests, changed files, callers, and test context
- Loaded language-profile notes and verification results

Subagents must read this file first. Do not rely on inherited context.

## Step 5: Launch Reviewers

Launch all five reviewers in parallel. Each reviewer returns findings with:
severity, confidence, file/line/snippet, explanation, concrete fix, and whether
the finding should be inline or summary-only.

Reviewer perspectives:

- **Linear/Product Alignment**: verify the PR implements the Linear ticket,
  acceptance criteria, customer notes, and latest comments without hidden scope
  drift or missing behavior.
- **Core Correctness/Architecture**: verify algorithms, state transitions,
  public APIs, data flow, compatibility, and architectural placement.
- **Reliability/Testing/Error Handling**: verify tests, edge cases, error paths,
  panics, retries, cancellation, and failure behavior.
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

Merge duplicate findings, discard false positives, and validate every remaining
finding against the current diff and surrounding code. Do not forward subagent
claims blindly.

Prepare GitHub-ready output:

- Inline comments only for validated `CRITICAL` and `MAJOR` findings with exact
  current-diff line mappings.
- Summary-only comments for `MINOR`, `NIT`, cross-file concerns, Linear
  alignment summaries, verification output, and unmappable findings.
- Include confidence when it helps reviewers prioritize, but keep PR comments
  concise and actionable.

## Step 7: Post Or Preview GitHub Comments

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

Run dry-run unless the user clearly requested live PR comments:

```bash
python3 linear-gh-brutal-pr-review/scripts/post_github_review.py --payload review.json --dry-run
python3 linear-gh-brutal-pr-review/scripts/post_github_review.py --payload review.json
```

The script verifies the current head SHA, refuses unsafe inline mappings, avoids
duplicate generated comments with hidden fingerprints, and truncates oversized
comment bodies predictably.

## Final Response

Report the PR, Linear issue, number of inline comments posted or previewed,
summary comment status, checks run, and any blockers that prevented posting.
Keep the response concise and factual.
