---
name: gitlear-brutal-plan
description: Collaborative, multi-perspective feature planning with rigorous requirements interrogation. Creates Gitlear project documents and Gitlear issues instead of local workspace plan/task files. Use when Codex is asked to run $gitlear-brutal-plan, plan work in Gitlear, or use brutal-plan behavior backed by Gitlear.
---

# Gitlear Brutal Plan

Gitlear-backed brutal planning process. Preserve the discipline of
`brutal-plan`, but use Gitlear as the only persistent planning system.

## Hard Rules

- First read the repo's `AGENTS.md`.
- `AGENTS.md` must name both:
  - `Gitlear project: <name>`
  - `Gitlear workspace: <name or key_prefix>`
- If either value is missing, stop and ask the user to add or provide it.
- Validate the active Gitlear MCP workspace with `gitlear_workspace_get` before
  creating anything. If the name/key prefix does not match `AGENTS.md`, stop.
- Resolve the project with `gitlear_project_list`, then use the returned
  internal `project.id` for `gitlear_project_get`, issue `project`, and docs.
  Do not pass display keys to `gitlear_project_get`.
- If Gitlear MCP tools are unavailable, stop. Do not fall back to local
  `workspace/plans` or `workspace/tasks` files.
- Never create new `workspace/plans`, `workspace/tasks`, or
  `workspace/review-state` files. Read existing local files only as historical
  context when useful.
- Use only these labels: `type:plan`, `type:task`, `type:review-finding`.
- Put source, phase, component, dependencies, local IDs, acceptance criteria,
  and implementation notes in issue bodies or comments, not labels.
- Use issue statuses `todo`, `in-progress`, `in-review`, and `done`. Represent
  deferred or blocked work in issue body/comment text, not a fake backlog issue
  status.

## Gitlear MCP Notes

- Issue create fields: `title`, `status`, `priority`, `assignee`, `project`,
  `body`, `labels`.
- Issue update shape: `{ "key": "<issue id or display key>", "patch": { ... } }`.
- Project create fields: `name`, optional `key`, `status`, `priority`,
  `lead`, `description`, `labels`, and `target_date`.
- Doc create fields: `title`, deterministic `name`, `project`, `body`.
- Doc get/update uses doc filename/name, optionally scoped with `project`;
  display keys are not doc lookup keys.
- Current MCP snapshots omit issue body/comments/status/project, doc
  body/project, and project body. When those fields matter, read raw Markdown
  under `gitlear_workspace_get.root`; stop if filesystem access is unavailable.

## Step 0: Resolve Project Context

1. Read `AGENTS.md`.
2. Extract `Gitlear workspace:` and `Gitlear project:`.
3. Call `gitlear_workspace_get` and verify the workspace name or key prefix.
4. Resolve the project through `gitlear_project_list` by exact name first,
   allowing display-key matches only in the list result. If multiple projects
   match, ask the user to choose.
5. If no project matches, ask whether to create it. If confirmed, call
   `gitlear_project_create` with the `AGENTS.md` project name, then use the
   returned project.
6. Record the resolved internal project id and display key.
7. Read any referenced workflow docs and `TARGET.md` if present.

## Step 1: Understand The Request

Extract:

- explicit ask
- underlying problem
- affected users/systems
- known constraints
- ambiguous decisions

Before asking questions, inspect the codebase enough to make questions
specific: repo rules, affected modules, prior art, schemas, APIs, migrations,
tests, and dependent callers. Prefer `rg` and `rg --files`. Do not mutate repo
files during planning.

## Step 2: Interrogate Requirements

Ask focused questions in rounds until the plan is decision-complete. Cover
requirements, exact behavior, scope boundaries, edge cases, performance,
security, observability, migration, rollout, acceptance criteria, verification,
and 1-3 non-negotiable invariants.

Before creating Gitlear artifacts, summarize confirmed requirements, in/out of
scope, anti-goals, non-negotiables, assumptions, and open questions. Proceed
only after confirmation or explicit permission to use listed assumptions.

## Step 3: Multi-Perspective Plan Review

Build an ephemeral context file in `/tmp/gitlear-brutal-plan-<slug>.md` with
confirmed requirements, codebase context, constraints, and acceptance criteria.

Launch parallel review subagents when available:

- Architecture and system design
- Data model and migration safety
- API, UX, and integration behavior
- Reliability, security, and observability

Categorize findings as `PLAN BLOCKER`, `IMPLEMENTATION NOTE`, or `SUGGESTION`.
Validate findings against the repo and resolve all blockers with the user.

## Step 4: Create Gitlear Plan Artifacts

Create:

1. A Gitlear project document containing the full plan.
2. A parent Gitlear issue labeled `type:plan`.
3. Child task issues labeled `type:task`.

Use a deterministic doc name:

```text
PLAN <Feature Title>-<short-hash>
```

Parent issue:

```text
PLAN: <Feature Title>
```

Parent body:

```markdown
Source: gitlear-brutal-plan
Gitlear plan doc: <doc name and display key if returned>

## Summary
<short summary>

## Key Decisions
- <decision and rationale>

## Implementation Tasks
- <child issue display key/title>

## Acceptance Criteria
- [ ] <plan-level criterion>
```

Task body:

```markdown
Source: gitlear-brutal-plan
Plan: <parent issue display key/title>
Phase: <phase number/name>

## Description
<specific implementation work>

## Acceptance Criteria
- [ ] <concrete, testable criterion>

## Implementation Notes
<patterns, constraints, edge cases, and review notes>

## Dependencies
- Blocked by: <issue display keys or None>
- Blocks: <issue display keys or None>
```

Create tasks in `todo`. Mirror dependencies in body text because the current
Gitlear MCP does not expose parent/blocking relationship mutations.

## Final Response

Report:

- Gitlear plan document name/display key if returned
- parent plan issue display key
- child task display keys in execution order
- key decisions
- known risks
- next recommended issue to start

Recommend `$gitlear-task-worker` for implementation.
