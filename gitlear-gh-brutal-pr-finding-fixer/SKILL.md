---
name: gitlear-gh-brutal-pr-finding-fixer
description: Fix generated GitHub PR review findings from gitlear-gh-brutal-pr-review one at a time. Use when Codex is asked to run $gitlear-gh-brutal-pr-finding-fixer, handle generated Gitlear-aware PR review findings, address brutal PR review comments, reply to resolved GitHub review threads with how findings were handled, or commit fixes for gitlear-gh-brutal-pr-review output.
---

# Gitlear GH Finding Fixer

Resolve generated GitHub PR review findings produced by
`gitlear-gh-brutal-pr-review`. The queue is GitHub PR review comments, not
Gitlear issues.

## Hard Rules

- Use `gh` as the source of GitHub truth. Fail early if `gh` is unavailable or
  unauthenticated.
- Do not require or update Gitlear issues, statuses, or comments.
- Require a clean worktree before editing unless the user explicitly allows
  working with existing changes. Never revert user changes without explicit
  instruction.
- Select only top-level PR review comments whose body starts with
  `<!-- gitlear-gh-brutal-pr-review:<fingerprint> -->`. Exclude summary
  markers, issue comments, replies, and quoted markers.
- Treat comments with `in_reply_to_id` as replies, not queue items.
- Skip findings already handled by this skill. A handled item has a reply or PR
  issue comment starting with
  `<!-- gitlear-gh-brutal-pr-finding-fixer:<fingerprint> -->`.
- Process findings one at a time. Create one focused commit per finding, then
  push the PR branch before replying with the commit hash.
- Never force-push. Stop if a normal push is rejected.
- If a finding is invalid, stale, or already fixed, leave a handled reply with
  the disposition and do not commit.
- If the GitHub review thread is already resolved, still leave a reply
  explaining how the finding was handled. Do not resolve or unresolve threads
  unless the user explicitly asks.
- Stop before edits if the PR head/base, generated findings, or review-thread
  resolved state cannot be determined reliably.
- Process `MINOR` and `NIT` generated inline findings only when the user or an
  orchestrator explicitly asks for all-severities, all-findings, or fix-loop
  mode.

## Step 1: Resolve The PR

Resolve the target PR from an explicit URL, number, branch, or current branch:

```bash
gh pr view <target> --json number,url,title,body,baseRefName,headRefName,headRefOid,author,isCrossRepository,commits,files
gh pr diff <target>
gh pr checks <target>
```

Record `repo`, `pr_number`, `head_sha`, `headRefName`, `baseRefName`, and
whether the PR is from a fork. Do not push to fork/external PR branches unless
the user explicitly allows that workflow.

Check:

```bash
git status --short
```

If unrelated or ambiguous changes exist, stop and ask before editing.

## Step 2: Gather Review Comments And Threads

Fetch PR review comments and issue comments:

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate
gh api repos/{owner}/{repo}/issues/{number}/comments --paginate
```

Use PR review comments for the work queue. Use issue comments only to detect
prior handled markers from this skill.

Fetch all review threads with GraphQL and paginate both `reviewThreads` and
nested `comments` until `hasNextPage` is false. Capture each thread's `id`,
`isResolved`, and comment `databaseId`/`url` values. Map REST review comment
`id` to its thread through the matching `databaseId`.

If thread pagination, comment mapping, or resolved-state lookup is incomplete,
stop before edits.

## Step 3: Build The Queue

For each PR review comment:

1. Require `in_reply_to_id` to be absent or null.
2. Require the body to start exactly with
   `<!-- gitlear-gh-brutal-pr-review:<fingerprint> -->`.
3. Reject `<!-- gitlear-gh-brutal-pr-review:summary -->`.
4. Parse severity from `**Severity:** <level>`. If an older generated comment
   lacks severity, process it after known `CRITICAL` findings and before known
   `MAJOR` findings, preserving GitHub comment order.
5. Skip the finding if any reply or issue comment starts with
   `<!-- gitlear-gh-brutal-pr-finding-fixer:<fingerprint> -->`.

Sort unhandled findings by severity: `CRITICAL`, then `MAJOR`. In explicit
all-severities or fix-loop mode, continue with `MINOR`, then `NIT`.

If one code change clearly fixes multiple generated findings, finish the
current finding first, then reply to related fingerprints with the same commit
hash and disposition.

## Step 4: Fix One Finding

For the selected finding:

1. Read the full generated comment, changed file, surrounding implementation,
   relevant tests, and direct call sites.
2. Confirm the finding is still valid on the current PR head.
3. Add or update a focused failing test when practical.
4. Implement the smallest correct fix.
5. Run narrow verification first, then required repo checks.
6. Inspect `git diff` to ensure the change is scoped to this finding.
7. Commit with a message such as:

```text
Fix PR #123 finding <fingerprint>
```

8. Push the PR branch with a normal `git push`.

If invalid, stale, or already fixed, skip the edit/commit path and reply with a
`skipped` disposition.

## Step 5: Reply To The Review Thread

Reply to the top-level review comment using its REST `id`:

```bash
gh api --method POST \
  repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
  -f body='<reply markdown>'
```

Reply body:

```markdown
<!-- gitlear-gh-brutal-pr-finding-fixer:<fingerprint> -->
Handled: <fixed|skipped>
Thread state before reply: <resolved|unresolved>
Commit: <hash or none>
Verification: <commands and pass/fail result>
Notes: <short disposition, residual risk, or why no code change was needed>
```

For already-resolved threads, use the same reply format.

## Step 6: Continue Or Stop

After each pushed commit and handled reply:

- Re-fetch PR head, review comments, issue comments, and review threads.
- Stop if the PR head changed unexpectedly.
- Continue when the user asked for continuous processing.
- Otherwise report the one handled finding and stop.

## Final Response

Summarize PR, fingerprint, action taken, commit hash and push result,
verification result, reply status, whether the thread was already resolved, and
remaining unhandled generated findings if known.
