---
name: linear-brutal-plan
description: Collaborative, multi-perspective feature planning with rigorous requirements interrogation. Creates Linear project documents and Linear issues instead of local workspace plan/task files.
---

Linear-backed brutal planning process. Use this when the user asks for
`$linear-brutal-plan`, asks to plan work in Linear, or asks for the brutal-plan
workflow without local workspace files.

This skill preserves the discipline of `brutal-plan`, but Linear is the only
persistent planning system.

## Hard Rules

- First read the repo's `AGENTS.md`.
- `AGENTS.md` must name the Linear project to use. Accept clear wording such as
  `Linear project: <name>` or "Use the Linear project `<name>`".
- If the Linear project name is missing, stop and ask the user to add or provide
  it. Do not guess from prior conversations.
- Resolve the project through Linear MCP before creating anything.
- If Linear MCP tools are unavailable, stop and report that planning cannot be
  persisted. Do not fall back to local files.
- Never create new `workspace/plans`, `workspace/tasks`, or
  `workspace/review-state` files. Read existing local files only as historical
  context when useful.
- Use only these labels: `type:plan`, `type:task`, `type:review-finding`.
- Put source, phase, component, severity, dependencies, local IDs, acceptance
  criteria, and implementation notes in issue bodies or comments, not labels.
- Use the workflow `Backlog -> Todo -> In Progress -> In Review -> Done`.

## Step 0: Resolve Project Context

1. Read `AGENTS.md`.
2. Extract the Linear project name.
3. Resolve the project with Linear MCP using exact lookup when possible.
4. Identify the project team from the project result.
5. Read any repo planning docs that `AGENTS.md` points to, such as
   `docs/linear-workflow.md`.

If multiple Linear projects match, ask the user to choose. If none match, ask
the user whether to create the project or correct `AGENTS.md`.

## Step 1: Understand The Request

Extract:

- explicit ask
- underlying problem
- affected users/systems
- known constraints
- ambiguous decisions

Check for `TARGET.md` in the repo root. If it exists, read it before asking
questions or planning.

## Step 2: Gather Codebase Context

Before asking questions, inspect the codebase enough to make questions specific:

- repo conventions from `AGENTS.md`
- affected crates/apps/modules
- prior art for similar behavior
- schemas, migrations, APIs, clients, DTOs, and tests likely to change
- dependent callers and compatibility constraints

Prefer `rg` and `rg --files`. Do not mutate repo files during planning.

## Step 3: Interrogate Requirements

Ask focused questions in rounds until the plan is decision-complete. Reference
actual code findings in the questions.

Cover:

- requirements and exact user-visible behavior
- scope boundaries and anti-goals
- edge cases and error handling
- performance, security, observability, data migration, and rollout needs
- acceptance criteria and verification commands
- 1-3 non-negotiable invariants

Stop early when acceptance criteria, scope, dependencies, and invariants are
clear. Do not proceed with unresolved plan blockers.

## Step 4: Confirm Requirements

Before plan analysis, summarize:

- confirmed requirements
- in scope / out of scope
- anti-goals
- non-negotiables
- assumptions
- open questions

Ask the user to confirm. Do not launch subagents or create Linear artifacts until
requirements are confirmed or the user explicitly asks to proceed with listed
assumptions.

## Step 5: Multi-Perspective Plan Review

Build an ephemeral context file in `/tmp/linear-brutal-plan-<slug>.md` for
subagents. The file should contain confirmed requirements, codebase context,
constraints, and acceptance criteria.

Launch parallel review subagents when available. Perspectives:

- Architecture and system design
- Data model and migration safety
- API, UX, and integration behavior
- Reliability, security, and observability

Each finding must be categorized:

- `PLAN BLOCKER`: must be resolved before implementation
- `IMPLEMENTATION NOTE`: must be carried into task bodies
- `SUGGESTION`: optional improvement

Validate findings against the repo before presenting them. Resolve all blockers
with the user.

## Step 6: Create Linear Plan Artifacts

After blockers are resolved, create:

1. A Linear project document containing the full plan.
2. A parent Linear issue with label `type:plan`.
3. Child task issues with label `type:task`.

Parent issue title:

```text
PLAN: <Feature Title>
```

Parent issue body shape:

```markdown
Source: linear-brutal-plan
Project document: <Linear document URL if available>

## Summary
<short summary>

## Key Decisions
- <decision and rationale>

## Implementation Tasks
- <child issue identifier/title>

## Acceptance Criteria
- [ ] <plan-level criterion>
```

Task issue body shape:

```markdown
Source: linear-brutal-plan
Plan: <parent issue identifier/title>
Phase: <phase number/name>

## Description
<specific implementation work>

## Acceptance Criteria
- [ ] <concrete, testable criterion>

## Implementation Notes
<patterns, constraints, edge cases, and review notes>

## Dependencies
- Blocked by: <Linear issue identifiers or None>
- Blocks: <Linear issue identifiers or None>
```

Create tasks in `Todo` unless the plan explicitly says they are future work, in
which case use `Backlog`.

Use Linear relationships for `blocked by`, `blocks`, or `related` dependencies
when the MCP tool supports them. Mirror the relationship text in the body.

## Step 7: Final Response

Report:

- Linear plan document title/link
- parent plan issue identifier
- child task identifiers in execution order
- key decisions
- known risks
- next recommended issue to start

Do not tell the user to run a local task-worker command. Recommend
`$linear-task-worker` for implementation.

## Quality Bar

The plan must be decision-complete. A task worker should not need to decide
schema shape, API shape, status flow, dependency order, or acceptance criteria.

Be direct, concrete, and skeptical. Push back on vague scope and hidden
complexity before anything enters Linear.
