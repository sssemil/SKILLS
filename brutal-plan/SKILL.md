---
name: brutal-plan
description: "Collaborative, multi-perspective feature planning with rigorous requirements interrogation. Creates implementation plans and tasks using the repo's BRUTAL.md backend: local workspace files, Linear, or Gitlear."
---

# Brutal Plan

Plan work until it is decision-complete, then persist the plan and executable
tasks through the backend configured in `BRUTAL.md`.

## Required Context

1. Read `../brutal-shared/backend-resolver.md`.
2. Resolve the backend before creating artifacts.
3. Read repo rules from `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, and any workflow
   docs they reference. `BRUTAL.md` controls persistence; repo instruction files
   control engineering conventions.
4. If `BRUTAL.md` is missing or incomplete, follow the setup flow in the
   resolver. Do not create plan artifacts until the backend is resolved.

## Planning Workflow

1. Understand the user's request: explicit ask, underlying problem, affected
   users/systems, constraints, and ambiguities.
2. Inspect the repo before asking questions. Use `rg`/`rg --files` to find
   affected modules, prior art, schemas, migrations, APIs, tests, and callers.
3. Ask focused questions until requirements are decision-complete. Cover exact
   behavior, scope boundaries, edge cases, rollout, security, observability,
   acceptance criteria, verification commands, anti-goals, and 1-3 invariants.
4. Confirm requirements before launching plan-review subagents or writing
   artifacts. Include confirmed requirements, in/out of scope, anti-goals,
   non-negotiables, assumptions, and open questions.
5. Build an ephemeral context file under `/tmp/brutal-plan-<slug>.md` with the
   confirmed requirements and repo context.
6. Launch parallel plan reviewers when available:
   - architecture and system design
   - data model and migration safety
   - API, UX, and integration behavior
   - reliability, security, and observability
7. Categorize findings as `PLAN BLOCKER`, `IMPLEMENTATION NOTE`, or
   `SUGGESTION`. Validate them against the repo and resolve all blockers.

## Persist Artifacts

Create one parent plan and child implementation tasks. Use these canonical
body markers for dedupe and migration from older backend-specific skills:

```markdown
Source: brutal-plan
Legacy sources: brutal-plan, linear-brutal-plan, gitlear-brutal-plan
```

Parent plan body must include:

- summary
- key decisions and rationale
- child task list in execution order
- plan-level acceptance criteria
- known risks

Task body must include:

- parent plan reference
- phase/order
- description
- concrete acceptance criteria
- implementation notes
- dependencies in body text
- verification commands

Persist by backend:

- `local`: write `workspace/plans/PLAN-<NNNN>-<slug>.md` and
  `workspace/tasks/todo/<NNNN>-<slug>/ticket.md`.
- `linear`: create/update a Linear project document, a parent `type:plan`
  issue, and child `type:task` issues in `Todo` unless explicitly deferred.
  Use Linear relationships when supported and mirror dependencies in bodies.
- `gitlear`: create/update a Gitlear project document, a parent `type:plan`
  issue, and child `type:task` issues in `todo`. Mirror dependencies in bodies;
  current Gitlear MCP does not expose relationship mutations.

## Final Response

Report the backend, plan artifact, parent issue/file, child tasks in execution
order, key decisions, known risks, and the next recommended task.
