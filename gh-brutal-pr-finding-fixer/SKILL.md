---
name: gh-brutal-pr-finding-fixer
description: "Fix generated GitHub PR review findings from gh-brutal-pr-review one at a time. Also handles legacy Linear and Gitlear generated PR review markers."
---

# GH Brutal PR Finding Fixer

Resolve generated GitHub PR review findings produced by `gh-brutal-pr-review`.
The queue is GitHub PR review comments, not backend issues.

## Hard Rules

- Use `gh` as the source of GitHub truth.
- Do not update Linear, Gitlear, or local task state from this fixer.
- Require a clean worktree before editing unless the user explicitly allows
  working with existing changes.
- Never force-push. Stop if a normal push is rejected.
- Process findings one at a time. Create one focused commit per code-changing
  finding, push, then reply with the commit hash.
- If a finding is invalid, stale, or already fixed, leave a handled reply with
  the disposition and do not commit.
- If the GitHub review thread is already resolved, still leave a reply
  explaining how it was handled.

## Queue Markers

Select top-level PR review comments whose body starts with one of:

- `<!-- gh-brutal-pr-review:<fingerprint> -->`
- `<!-- linear-gh-brutal-pr-review:<fingerprint> -->`
- `<!-- gitlear-gh-brutal-pr-review:<fingerprint> -->`

Reject summary markers, replies, issue comments, and quoted markers. Skip any
finding already handled by a reply or issue comment starting with:

```markdown
<!-- gh-brutal-pr-finding-fixer:<fingerprint> -->
```

Also recognize legacy handled markers from `linear-gh-brutal-pr-finding-fixer`
and `gitlear-gh-brutal-pr-finding-fixer`.

Sort unhandled findings by severity: `CRITICAL`, `MAJOR`, then in explicit
all-severities/fix-loop mode `MINOR`, `NIT`.

## Workflow

1. Resolve PR metadata, diff, checks, head/base SHA, branch, and fork status.
2. Fetch PR review comments, issue comments, and GraphQL review threads.
3. Select the next unhandled generated finding.
4. Read the full generated comment, changed file, surrounding implementation,
   relevant tests, and direct call sites.
5. Confirm the finding is still valid on the current PR head.
6. Add/update a focused failing test when practical.
7. Implement the smallest correct fix.
8. Run focused verification and required repo checks.
9. Inspect the diff for scope, commit, push, and reply to the top-level review
   comment.

Reply body:

```markdown
<!-- gh-brutal-pr-finding-fixer:<fingerprint> -->
Handled: <fixed|skipped>
Thread state before reply: <resolved|unresolved>
Commit: <hash or none>
Verification: <commands and pass/fail result>
Notes: <short disposition>
```

## Final Response

Summarize PR, fingerprint, action, commit hash, push result, verification,
reply status, prior thread state, and remaining unhandled generated findings.
