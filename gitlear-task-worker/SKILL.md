---
name: gitlear-task-worker
description: Autonomous Gitlear task worker that selects Gitlear issues, implements them with TDD, self-reviews, commits, pushes, comments verification, and moves finished work to in-review. Use when Codex is asked to run $gitlear-task-worker, work Gitlear tickets, or use task-worker behavior without local workspace task files.
---

# Gitlear Task Worker

Gitlear-backed autonomous task worker. Preserve the implementation discipline
of `task-worker`, but use Gitlear as the persistent task state.

## Hard Rules

- First read the repo's `AGENTS.md`.
- `AGENTS.md` must include `Gitlear workspace: <name or key_prefix>` and
  `Gitlear project: <name>`. Stop if either is missing.
- Validate the active Gitlear MCP workspace with `gitlear_workspace_get`.
- Resolve the project through `gitlear_project_list`, then use the returned
  internal `project.id`.
- If Gitlear MCP tools are unavailable, stop. Do not fall back to local task
  files.
- Never create or move `workspace/plans`, `workspace/tasks`, or
  `workspace/review-state` files.
- Use only labels `type:plan`, `type:task`, and `type:review-finding`.
- Preserve implementation notes, severity, component, source, dependencies, and
  verification in issue bodies/comments, not labels.
- Move completed implementation work to `in-review`, not directly to `done`.
- Commit and push completed, verified work promptly unless repo rules say
  otherwise.

## Gitlear Data Rules

- Issue statuses are path slugs: `todo`, `in-progress`, `in-review`, `done`,
  and `canceled`.
- Current MCP issue snapshots omit status, project, body, and comments. For
  selection and completeness checks, inspect raw issue Markdown under
  `gitlear_workspace_get.root/projects/<project-id>/issues/<status>/`.
- Issue updates use `{ "key": "<issue id or display key>", "patch": { ... } }`.
- A blocked issue is any candidate whose body or latest relevant comment has a
  `BLOCKED:` section/comment or lists unresolved blocking display keys.

## Phase 0: Resolve Project, User, And Repo Rules

1. Read `AGENTS.md`.
2. Validate `Gitlear workspace:` against `gitlear_workspace_get`.
3. Resolve `Gitlear project:` and record internal project id.
4. Read referenced workflow docs and `TARGET.md` if present.
5. Resolve the current user:
   - Get git user name/email from the repo.
   - Compare with `gitlear_member_list` by email, GitHub username, and name.
   - If exactly one member matches, use that member handle/name.
   - If ambiguous, ask the user before applying assignee-specific preference.
6. Check `git status --short`.

If uncommitted changes exist:

- Continue only when they clearly belong to the selected Gitlear issue.
- Stop and ask when changes are unrelated or ambiguous.
- Never revert user changes unless explicitly told to.

## Phase 1: Select Work

Build candidates from raw Markdown files in the resolved project:

```text
projects/<project-id>/issues/in-progress/*.md
projects/<project-id>/issues/todo/*.md
```

Prefer:

1. `in-progress` issues assigned to the resolved current user.
2. Any `in-progress` issue in the resolved project when the user explicitly
   asked to continue active work.
3. Unblocked `todo` issues in deterministic order, preferring lower display key
   or oldest creation date.

Only select issues labeled `type:task` or `type:review-finding`. Do not select
`type:plan` parent issues.

Before moving a `todo` issue to `in-progress`, read its full body/comments and
confirm it is decision-complete. If it is not, add a `BLOCKED:` comment
explaining the missing decision and leave it in `todo`.

After selecting a complete issue:

- Move it to `in-progress` with `gitlear_issue_update`.
- Add `Started work via gitlear-task-worker`.
- Read the full body, comments, links, and any dependency text.

## Phase 2: Plan Locally

Before editing:

- identify affected files and existing patterns
- identify tests that should fail first
- identify verification commands from `AGENTS.md`, issue body, or repo scripts
- note blockers or ambiguities

If the issue stops being decision-complete, comment `BLOCKED:` with the exact
missing decision and move on only when another unblocked issue exists and the
user asked for continuous processing.

## Phase 3: Implement With TDD

For each requirement:

1. Write or update a focused failing test when practical.
2. Run the narrow test to confirm the failure when practical.
3. Implement the smallest correct change.
4. Run the narrow test to confirm success.
5. Refactor only when it removes real complexity or follows repo patterns.

Use repo commands from `AGENTS.md` first. If the repo has `./run`, prefer it.

## Phase 4: Reduce And Review

Before committing:

- inspect the full diff
- remove dead code, speculative abstraction, redundant wrappers, and accidental
  churn
- verify no unrelated user changes are included
- run required formatting/checks

Run a self-review for correctness, reliability, error handling, security,
performance, resource usage, simplicity, and maintainability. Fix all CRITICAL
and MAJOR findings, then re-run relevant verification.

## Phase 5: Commit, Push, And Update Gitlear

When verification passes:

1. Commit atomic changes with a clear message.
2. Push the branch.
3. Add a Gitlear issue comment containing:
   - changed files summary
   - verification commands and pass/fail result
   - commit hash
   - remaining risks or follow-ups
4. Move the issue to `in-review`.

Do not move to `done` unless the user explicitly says review/acceptance is
complete.

## Continuous Mode

If the user asked to process multiple tasks, return to selection after each
issue reaches `in-review`. Stop when no unblocked `todo` or resumable
`in-progress` issues remain.

## Final Response

Summarize:

- Gitlear issue worked
- commits pushed
- verification result
- final Gitlear status
- important risks or follow-ups
