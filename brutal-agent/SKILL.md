---
name: brutal-agent
description: "Orchestrate subsystem-by-subsystem hardening by combining backend-aware brutal-project-review and task-worker. Reviews one subsystem, drains generated CRITICAL/MAJOR work, repeats passes until no new major findings remain."
---

# Brutal Agent

Run the backend-aware hardening loop without dropping instructions from
`brutal-project-review` or `task-worker`.

## Required Context

1. Read `../brutal-shared/backend-resolver.md`.
2. Read `../brutal-project-review/SKILL.md`.
3. Read `../task-worker/SKILL.md`.
4. Resolve the backend before checking queues or review state.

## Loop

1. Drain existing resumable work first:
   - `local`: any `workspace/tasks/in-progress/` or `workspace/tasks/todo/`
   - `linear`: unblocked `In Progress` or `Todo` issues in the resolved project
     labeled `type:task` or `type:review-finding`
   - `gitlear`: unblocked `in-progress` or `todo` issues in the resolved project
     labeled `type:task` or `type:review-finding`
2. Start a pass. Record the current count of valid CRITICAL/MAJOR finding refs:
   - `local`: `tasks_created` in the review manifest
   - remote: `findings_created` in `.brutal-workspace/review-state/manifest.json`
3. Run `brutal-project-review` for the next pending subsystem.
4. Run `task-worker` continuously until generated work is drained or blocked.
5. Repeat subsystem review and task draining until every subsystem in the pass
   is done.
6. Compare final finding count to the pass baseline. If new CRITICAL/MAJOR work
   was created, start another pass. If not, stop after one final task drain.

## Safety

- Preserve all source-skill guardrails for dirty worktrees, backend ambiguity,
  missing MCP tools, blocked tasks, verification failure, push rejection, and
  user cancellation.
- Do not directly implement review or task logic in this skill; use it only for
  ordering and pass accounting.

## Final Response

Report backend, passes executed, subsystems reviewed, CRITICAL/MAJOR work
created in the last pass, commits pushed, blocked items, and remaining queues.
