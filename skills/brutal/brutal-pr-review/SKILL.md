---
name: brutal-pr-review
description: Review an open pull request with Brutal multi-perspective scrutiny, snapshot-safe BRUTAL.md context, and provider-native findings. Supports normal, strict all-findings, and material-convergence passes.
---

# Brutal PR Review

Review the exact open pull request resolved through BRUTAL.md.

## Required Context

1. Read `../brutal-shared/integration-resolver.md` and
   `../brutal-shared/support/contracts.md`.
2. Reuse validated integrations, canonical local root, and exact pull request
   from a managed phase. Otherwise resolve one code host and one work store and
   read both support modules.
3. Require an open pull request. Never create one or substitute a local diff.
4. Read applicable repository rules and only the docs/manifests needed to
   interpret the changed surface. Load `references/rust.md` for Rust changes.

## Hard Rules

- Use provider comments only. Never approve, request changes, merge, or write
  to forks without explicit permission.
- Stop before posting if either the base SHA or head SHA changes after context
  collection.
- Validate every finding against the current diff and surrounding code.
- Patch only owned comments beginning with an exact canonical marker. Recognize
  legacy markers for queue compatibility but write only v2 markers.

## Snapshot And Reviewer Isolation

Key a review context by provider/repository, pull-request ref, base branch,
base SHA, head branch, and head SHA. A matching head alone is insufficient: a
base-only change invalidates the context. Reuse verification only for that exact
snapshot and only while required checks still pass.

When native reviewer subagents are available, launch them with
`fork_turns: "none"` and give only the exact review snapshot. They must not
inherit the worker’s implementation conversation. If subagents are
unavailable, apply the same evidence isolation sequentially. Merge only
validated structured findings.

## Review Modes

- `normal`: validate all severities; publish/queue CRITICAL and MAJOR. Report
  MINOR/NIT only in the summary.
- `strict_all`: publish/queue all four severities. Clean means zero validated
  findings.
- `material_convergence`: validate all four severities. If CRITICAL or MAJOR
  exists, publish/queue all four. If neither exists, publish no actionable
  MINOR/NIT comments; include those residuals in the summary and return
  `materially_clean`. Zero findings returns `zero_findings`.

Every result includes `validated_finding_count`, `material_finding_count`,
counts by severity and placement, queued count, residual MINOR/NIT findings,
posting actions, checks, and completion kind when converged.

## Review Records And Posting

Generate a safe unique `review_id`. Give each finding a deterministic
fingerprint and begin its body with:

    <!-- brutal-pr-review:v2:<fingerprint> -->
    <!-- brutal-pr-review-occurrence:<review_id>:<reviewed_head_sha> -->

For each enabled severity, post line-mappable findings inline and other
findings as individual top-level comments. Never hide an enabled actionable
finding only in the summary.

For GitHub, send the final validated set to
`scripts/post_github_review.py`. Use `inline_severities` for the mode-derived
actionable severities: CRITICAL/MAJOR for normal or a converged material pass,
all four for strict mode or a material pass that found CRITICAL/MAJOR. Add
`--dry-run` only for an explicit preview or safety guard.

Before posting, re-read base/head SHAs. Return the review id, complete reviewed
snapshot, finding counts, queue counts, summary action, checks, and blockers.

Redirect verbose output to temporary logs. Report command status and duration;
on failure include at most the last 200 lines or 16 KiB, whichever is smaller.
