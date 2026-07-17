---
name: brutal-pr-finding-fixer
description: Fix generated pull-request findings from brutal-pr-review one at a time through the BRUTAL.md code-host adapter. Use for a single finding, continuous all-severity draining, or either PR fix loop.
---

# Brutal PR Finding Fixer

Drain generated provider findings, not work-store issues.

## Required Context

1. Read ../brutal-shared/integration-resolver.md,
   ../brutal-shared/support/contracts.md, and the selected code-host support
   module.
2. Reuse a managed worker's validated integrations and exact pull request when
   supplied. Otherwise resolve the same open pull request used by
   brutal-pr-review.
3. Read full conversation comments, review comments, and thread state before
   selecting work.

## Hard Rules

- Treat the code host as queue truth. Do not update the configured work store.
- Require a clean worktree before editing unless the user explicitly permits
  compatible existing changes.
- Process one finding at a time.
- Add or update a focused failing test when practical.
- Make one focused commit for each code-changing finding, push normally, then
  record its disposition. Never force-push.
- Stop on verification failure, push rejection, stale/ambiguous pull-request
  identity, incomplete thread state, or an inherited provider safety guard.
- Mark invalid, stale, or already-fixed findings as skipped without a commit.

## Queue And Handling Markers

Select owned top-level inline or conversation comments beginning with:

    <!-- brutal-pr-review:v2:<fingerprint> -->
    <!-- brutal-pr-review-occurrence:<review_id>:<reviewed_head_sha> -->

Reject summaries, quoted markers, and replies/disposition comments. Treat the
tuple (fingerprint, review_id) as the queue identity. A later occurrence for the
same stable fingerprint is new work.

Skip an occurrence only when a provider comment already starts with:

    <!-- brutal-pr-finding-fixer:v2:<fingerprint>:<review_id> -->

Also recognize legacy generated and handled markers from gh-brutal-pr-review,
linear-gh-brutal-pr-review, gitlear-gh-brutal-pr-review, and their finding
fixers.

Sort unhandled findings by CRITICAL, MAJOR, then in explicit
all-severities/fix-loop mode MINOR, NIT.

## Workflow

1. Snapshot pull-request metadata, current head/base, branch, fork state, checks,
   comments, and threads.
2. Select the next unhandled occurrence.
3. Read the finding, changed file, surrounding implementation, tests, and direct
   call sites.
4. Revalidate it against the current head.
5. Add/update a focused test when practical and implement the smallest correct
   behavior-preserving fix.
6. Run focused verification and required repo checks.
7. Inspect the diff, commit, push, then re-read the pull-request head.
8. Reply to an inline finding, or post a top-level disposition referencing the
   source conversation comment. Begin with:

    <!-- brutal-pr-finding-fixer:v2:<fingerprint>:<review_id> -->
    Handled: <fixed|skipped>
    Source: <provider comment id or URL>
    Reviewed head: <sha>
    Current head: <sha>
    Commit: <hash or none>
    Verification: <commands and pass/fail result>
    Notes: <short disposition>

In continuous mode, repeat selection until no unhandled occurrences remain or a
hard guard stops the run.

## Final Response

Report provider, pull request, final head, occurrence, action, commit/push,
verification, disposition posting, prior thread state, remaining queue counts
by severity, and any blocker.
