---
name: linear-task-worker
description: Autonomous Linear task worker that selects Linear issues, implements them with TDD, self-reviews, commits, pushes, and moves finished work to In Review.
---

Linear-backed autonomous task worker. Use this when the user asks for
`$linear-task-worker`, asks to work Linear tickets, or asks for task-worker
behavior without local workspace task files.

This skill preserves the implementation discipline of `task-worker`, but Linear
is the only persistent task state.

## Hard Rules

- First read the repo's `AGENTS.md`.
- `AGENTS.md` must name the Linear project to use. Accept clear wording such as
  `Linear project: <name>` or "Use the Linear project `<name>`".
- If the Linear project name is missing, stop and ask the user to add or provide
  it. Do not infer it from old local files or conversation memory.
- Resolve the project through Linear MCP before selecting work.
- If Linear MCP tools are unavailable, stop and report that tasks cannot be
  selected or updated. Do not fall back to local files.
- Never create or move `workspace/plans`, `workspace/tasks`, or
  `workspace/review-state` files.
- Use only these labels: `type:plan`, `type:task`, `type:review-finding`.
- Preserve implementation notes, severity, component, source, dependencies, and
  verification in issue bodies/comments, not labels.
- Move completed implementation work to `In Review`, not directly to `Done`.
- Commit and push completed, verified work promptly unless the repo rules say
  otherwise.

## Phase 0: Resolve Project And Repo Rules

1. Read `AGENTS.md`.
2. Extract and resolve the Linear project name.
3. Read referenced workflow docs if present.
4. Read `TARGET.md` if present.
5. Check git status.

If uncommitted changes exist:

- If they clearly belong to the current Linear issue, continue and include them.
- If they are unrelated or ambiguous, stop and ask before touching them.
- Never revert user changes unless explicitly told to.

## Phase 1: Select Work

Prefer issues in this order:

1. Issues in the resolved project assigned to the current user and `In Progress`.
2. Any `In Progress` issue in the resolved project if the user explicitly asked
   to continue active work.
3. Unblocked `Todo` issues in deterministic order, preferring lower Linear
   identifier or oldest creation date.

Only select issues labeled `type:task` or `type:review-finding`. Do not select
`type:plan` parent issues for implementation.

Skip issues that are blocked by another unresolved issue. If nothing is
available, report that there is no unblocked Linear work.

After selection:

- Move the issue to `In Progress`.
- Add a short comment: `Started work via linear-task-worker`.
- Read the full issue body, comments, links, and related/blocking issues.

## Phase 2: Plan The Implementation Locally

Before editing:

- identify affected files and existing patterns
- identify tests that should fail first
- identify verification commands from `AGENTS.md`, issue body, or repo scripts
- note any ambiguity that blocks implementation

If the issue is not decision-complete, comment with `BLOCKED:` explaining the
missing decision, move it to `Backlog`, and stop or pick the next unblocked
issue if the user requested continuous processing.

## Phase 3: Implement With TDD

For each requirement:

1. Write or update a focused failing test when practical.
2. Run the narrow test to confirm the failure when practical.
3. Implement the smallest correct change.
4. Run the narrow test to confirm success.
5. Refactor only when it removes real complexity or follows repo patterns.

Use repo commands from `AGENTS.md` first. If the repo has `./run`, prefer it over
raw package-manager commands.

## Phase 4: Reduce And Review

Before committing:

- inspect the full diff
- remove dead code, speculative abstraction, redundant wrappers, and accidental
  churn
- verify no unrelated user changes were included
- run formatting/checks required by the repo

Run a self-review. Use subagents when useful and available. Review from these
perspectives:

- correctness and regressions
- reliability and error handling
- security and secrets
- performance and resource usage
- simplicity and maintainability

Categorize findings:

- `CRITICAL`: must fix before completion
- `MAJOR`: must fix before completion
- `MINOR`: comment or fix if cheap
- `NIT`: optional

Fix all CRITICAL and MAJOR findings, then re-run relevant verification.

## Phase 5: Commit, Push, And Update Linear

When verification passes:

1. Commit atomic changes with a clear message.
2. Push the branch.
3. Add a Linear comment containing:
   - changed files summary
   - verification commands and pass/fail result
   - commit hash
   - any remaining risks or follow-ups
4. Move the issue to `In Review`.

Do not move to `Done` unless the user explicitly says review/acceptance is
complete.

## Phase 6: Continuous Mode

If the user asked to process multiple tasks:

- return to Phase 1 after each issue reaches `In Review`
- stop when no unblocked `Todo` or resumable `In Progress` issues remain
- report all processed issue identifiers, commits, and verification results

If repeated blockers prevent progress on the same issue, leave a precise
`BLOCKED:` comment and move on only when another unblocked issue exists.

## Final Response

Summarize:

- Linear issue worked
- commits pushed
- verification result
- final Linear status
- important risks or follow-ups

Keep the response concise and factual.
