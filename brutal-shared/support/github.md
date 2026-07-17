# GitHub Code Host Support

Implement the code-host contract with `gh`. Treat `gh` API responses as GitHub
truth even when another GitHub connector is available.

## Resolve And Validate

1. Require `gh` and authenticated API access.
2. Resolve repository and open PR from an explicit URL/number, branch, or the
   current branch. For the PR workflows, stop when no open PR exists.
3. Record repository, PR number, base/head refs, head SHA, base/head repository,
   fork state, and active login.
4. Read paginated files, issue comments, review comments, reviews, checks, and
   GraphQL thread state when thread resolution matters.

For `$brutal-swarm` and `$brutal-worker`, also resolve the repository default
branch and require authenticated normal push plus pull-request read/create/edit
access before provisioning work.

## Task Pull Requests

- Find an existing task pull request by both exact `brutal-worker` body marker
  and head branch before creating one.
- Push with normal `git push`; compare the remote head after every push.
- Create one ready pull request with explicit head and base branches. Patch only
  that matching pull request on resume.
- Read open, closed, merged, draft, head, and base state. Change the base only
  for the exact task pull request after re-reading its head.
- Treat a closed-unmerged pull request or mismatched marker/head as a blocker.
- Never merge, approve, request changes, force-push, or delete a remote branch.

## Findings

- Post line-mappable findings as PR review comments.
- Post non-line-mappable findings as individual PR conversation comments.
- Patch only comments authored by the active login whose body starts with an
  exact generated marker.
- Post summaries separately from finding records.
- Re-fetch the PR and compare the head SHA immediately before posting.
- Refuse fork/external PR writes unless the user explicitly permits them.

Use normal `git push` for code-changing commits. Never force-push; stop when a
normal push is rejected.
