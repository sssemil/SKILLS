---
name: task-worker
description: "Autonomous task worker that selects implementation tasks from the repo's BRUTAL.md backend, implements with TDD, self-reviews, commits, pushes, and moves completed work to review."
---

# Task Worker

Select and complete implementation tasks from the backend configured in
`BRUTAL.md`.

## Required Context

1. Read `../brutal-shared/backend-resolver.md`.
2. Resolve the backend and task queue before editing code.
3. Read repo rules from `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, and referenced
   workflow docs.
4. If `BRUTAL.md` is missing or incomplete, follow the resolver setup flow.

## Hard Rules

- Respect user changes. If the worktree is dirty, continue only when changes
  clearly belong to the selected task; otherwise ask before editing.
- Select only `type:task` or `type:review-finding` work. Do not implement
  `type:plan` parent artifacts.
- Move completed implementation work to review (`in-review`/`In Review`) unless
  the user explicitly says acceptance is complete.
- Commit atomic, verified changes and push unless repo rules say otherwise.

## Task Selection

Prefer tasks in this order:

1. In-progress work assigned to the current user.
2. Any in-progress work when the user asked to continue active work.
3. Unblocked todo work in deterministic order.

Backend queues:

- `local`: `<local.root>/tasks/in-progress/*/` then
  `<local.root>/tasks/todo/*/`. Never select `<local.root>/tasks/staged/`.
- `linear`: Linear issues in the resolved project labeled `type:task` or
  `type:review-finding`, preferring `In Progress`, then `Todo`.
- `gitlear`: raw Markdown issues under
  `projects/<project-id>/issues/in-progress/` then `todo/`.

If a candidate is not decision-complete, add a precise `BLOCKED:` note/comment
and leave it in the intake queue unless backend rules require a blocked state.

## Implementation Workflow

For the selected task:

1. Move it to in-progress and add a started comment/history entry.
2. Read the full task body, comments/history, links, dependencies, and relevant
   parent context.
3. Identify affected files, existing patterns, tests, and verification commands.
4. Implement with TDD when practical:
   - write/update a focused failing test
   - run the narrow test and confirm failure
   - implement the smallest correct fix
   - rerun the narrow test and confirm success
5. Reduce unnecessary code, speculative abstraction, redundant wrappers, and
   accidental churn.
6. Run required formatting/checks from repo instructions or the task body.
7. Self-review for correctness, reliability, error handling, security,
   performance, resource usage, simplicity, and maintainability. Fix all
   CRITICAL and MAJOR findings and re-run relevant checks.
8. Commit, push, and update the backend with changed files, verification
   commands/results, commit hash, and residual risks.
9. Move the task to review.

## Continuous Mode

If the user asked for continuous processing, return to selection after each
task reaches review. Stop when no unblocked todo or resumable in-progress work
remains.

## Final Response

Summarize backend, task worked, commits pushed, verification result, final task
status, and important risks or follow-ups.
