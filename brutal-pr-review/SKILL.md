---
name: brutal-pr-review
description: Review an open pull request with brutal multi-perspective scrutiny, BRUTAL.md integration context, and provider-native generated findings. Use for normal PR review, all-severity fix-loop review passes, or a clean-pass check.
---

# Brutal PR Review

Review the current feature branch's open pull request through the code host
resolved from BRUTAL.md.

## Required Context

1. Read ../brutal-shared/integration-resolver.md and
   ../brutal-shared/support/contracts.md.
2. Reuse a managed worker's validated code host, work store, canonical local
   root, and exact pull request when supplied. Otherwise resolve one code host
   and one work store. Read both support modules.
3. Require an open pull request. Do not create one or fall back to a local-only
   branch review.
4. Read AGENTS.md, CLAUDE.md, TARGET.md, README, CI workflows, manifests, and
   relevant repo docs.
5. Load references/rust.md when Rust files or Cargo manifests are touched.

## Hard Rules

- Use provider comments only. Never approve, request changes, or merge.
- Post live comments by default. Use dry-run only when the user asks for a
  preview or a safety guard blocks live posting.
- Stop before posting when the pull-request head changes after context
  collection.
- Refuse fork/external writes unless the user explicitly allows them.
- Validate every finding against the current diff and surrounding code.
- Patch only owned comments beginning with an exact canonical marker.
- Recognize legacy markers for queue compatibility, but write only version 2
  markers.

## Review Records

Generate a unique safe-token review_id for every review invocation. Give each
finding a deterministic fingerprint and place these markers first in its body:

    <!-- brutal-pr-review:v2:<fingerprint> -->
    <!-- brutal-pr-review-occurrence:<review_id>:<reviewed_head_sha> -->

Use the stable fingerprint to patch an owned same-head finding. Replace its
occurrence marker on every review so a recurring finding becomes actionable
again. For every severity enabled in the current mode, post line-mappable
findings inline and non-line-mappable findings as individual top-level
pull-request conversation comments. Never hide an enabled finding only inside
the summary.

Normal mode queues CRITICAL and MAJOR. It still reports and counts validated
MINOR/NIT findings but does not create generated queue records for them.
Explicit all-findings/fix-loop mode queues CRITICAL, MAJOR, MINOR, and NIT. The
review result must count every validated finding so a clean pass means zero
findings of every severity.

## Workflow

1. Resolve pull-request metadata, diff, checks, comments, review state, base/head
   refs, head SHA, active user, and fork state through the code-host adapter.
2. Resolve linked product context through the work-store adapter. Search branch,
   title, body, commits, links, and changed files; require exactly one linked
   item only when the repository workflow requires one.
3. Write temporary review context under
   /tmp/brutal-pr-review-<provider>-<id>.md with metadata, diff, checks, product
   context, repo rules, callers, tests, and verification results.
4. Launch five reviewers when available:
   - product/work-store alignment
   - correctness and architecture
   - reliability, testing, and error handling
   - performance, security, and concurrency
   - simplicity and maintainability
5. Merge duplicates, discard false positives, validate severities and mappings,
   and retain discrete inline or top-level findings.
6. For GitHub, build this helper payload:

    {
      "repo": "OWNER/REPO",
      "pr_number": 123,
      "head_sha": "abc123",
      "review_id": "r-safe-token",
      "summary_markdown": "Review summary...",
      "findings": [],
      "inline_severities": ["CRITICAL", "MAJOR"]
    }

   In all-findings mode, include all four severities. Run
   scripts/post_github_review.py, adding --dry-run only when required.
7. Return the review id, reviewed head, validated and queued finding counts,
   counts by severity and placement, posting actions, checks, and safety
   blockers.

A review is clean only when validated_finding_count is zero.
