---
name: brutal-pr-finding-fixer
description: Fix generated pull-request finding occurrences through the BRUTAL.md code-host adapter, one focused change at a time, with complete queue scans for material-convergence passes.
---

# Brutal PR Finding Fixer

Drain generated provider findings, not work-store issues.

## Required Context

1. Read `../brutal-shared/integration-resolver.md`,
   `../brutal-shared/support/contracts.md`, and the selected code-host module.
2. Reuse a managed fix phase’s validated integrations, exact pull request,
   review id, and base/head snapshot. Otherwise resolve the same open pull
   request used by `brutal-pr-review`.
3. Read full conversation comments, review comments, and thread state before
   selecting work. A cached count is not proof that the queue is drained.

## Hard Rules

- Treat the code host as queue truth. Do not update the work store.
- Require a clean worktree unless compatible existing changes were explicitly
  allowed. Process one occurrence at a time.
- Add or update a focused failing test when practical.
- Make one focused commit per code-changing occurrence, push normally, and
  record its disposition. Never force-push.
- Stop on verification failure, push rejection, stale/ambiguous PR identity,
  incomplete thread state, changed base identity, or inherited safety guards.
- Mark invalid, stale, or already-fixed occurrences skipped without a commit.

## Queue Identity

Select owned finding comments beginning with:

    <!-- brutal-pr-review:v2:<fingerprint> -->
    <!-- brutal-pr-review-occurrence:<review_id>:<reviewed_head_sha> -->

Reject summaries, quoted markers, and disposition replies. The queue identity
is `(fingerprint, review_id)`. A later occurrence for the same fingerprint is
new work. An occurrence is handled only when a provider comment starts with:

    <!-- brutal-pr-finding-fixer:v2:<fingerprint>:<review_id> -->

Recognize legacy generated/handled markers for compatibility. Sort unhandled
occurrences CRITICAL, MAJOR, MINOR, NIT. In a material-convergence fix phase,
scan and drain the full all-severity queue; do not stop after the material
subset or after a cached count reaches zero.

## Workflow

1. Snapshot PR identity, base/head, fork state, checks, comments, and threads.
2. Select and revalidate the next unhandled occurrence against the current
   implementation.
3. Implement the smallest correct fix and focused test.
4. Run focused verification and required checks.
5. Inspect, commit, push, and re-read the PR head.
6. Reply inline or post a top-level disposition beginning with the handled
   marker and recording source, reviewed/current heads, commit, verification,
   and concise notes.
7. Re-read the complete queue and repeat until no unhandled occurrence for the
   review remains or a hard guard stops.

In managed mode, perform only the `fix` phase. For v3, read only the exact
finding-occurrence queue referenced by the manifest and echo its context
digest; retained v2 attempts return a v2 checkpoint. Exit without running the
next review. Same-thread resume is only for an interrupted fix attempt.

Redirect verbose test, diff, and provider output to run-local temporary logs.
Return status and duration; on failure include no more than the last 200 lines
or 16 KiB, whichever is smaller.

## Final Response

Report provider, pull request, reviewed and final snapshots, occurrence totals
and actions by severity, commits/pushes, verification, dispositions, a fresh
remaining-queue scan, and any blocker.
