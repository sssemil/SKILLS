# Brutal Backend Resolver

All canonical Brutal skills use this resolver before selecting, creating, or
updating plan/task/review artifacts.

## Configuration

Read `BRUTAL.md` from the target repo root. The required frontmatter is:

```yaml
version: 1
backend: local # local | linear | gitlear

project:
  name: ""
  team: ""

gitlear:
  workspace: ""

local:
  root: workspace

labels:
  plan: type:plan
  task: type:task
  review_finding: type:review-finding
```

The Markdown body may contain workflow notes, verification commands, or links to
repo docs. Treat `BRUTAL.md` as persistence configuration only; still read
`AGENTS.md`, `CLAUDE.md`, `TARGET.md`, and referenced docs for repo rules.

If `BRUTAL.md` is missing or incomplete:

1. Inspect legacy hints in `AGENTS.md` only to prefill questions.
2. Ask for backend and required fields.
3. Validate the selected backend before work starts.
4. Offer to create/update `BRUTAL.md`. If the user declines, proceed
   session-only only when backend validation succeeded and all required fields
   are known. Otherwise stop.

## Local Backend

Defaults:

- root: `workspace`
- plans: `<root>/plans`
- tasks: `<root>/tasks/{todo,in-progress,done}`
- review state: `<root>/review-state`

Use local files for all plan, task, and finding persistence. Labels are body
metadata, not filesystem names.

## Linear Backend

Required:

- `backend: linear`
- `project.name`
- `project.team` when the project cannot resolve to exactly one team

Resolve:

1. Use `list_projects` by exact `project.name` first.
2. If multiple projects match, ask the user to choose.
3. If no project matches, ask whether to create it or correct `BRUTAL.md`.
4. Resolve team from `project.team`; otherwise use the only team attached to the
   project. If multiple or none are discoverable, ask.
5. Resolve issue statuses for that team. Defaults are `Backlog`, `Todo`,
   `In Progress`, `In Review`, and `Done`.
6. Verify `BRUTAL.md` uses the canonical labels: `type:plan`, `type:task`, and
   `type:review-finding`.

Use Linear MCP:

- `save_project`, `list_projects`
- `save_document`
- `save_issue`, `list_issues`
- `save_comment`, `list_comments`
- `list_teams`, `list_issue_statuses`

Remote workflows must not create local `workspace/plans`, `workspace/tasks`, or
`workspace/review-state`.

## Gitlear Backend

Required:

- `backend: gitlear`
- `project.name`
- `gitlear.workspace` as workspace name or key prefix

Resolve:

1. Call `gitlear_workspace_get`; verify name or key prefix against
   `gitlear.workspace`.
2. Resolve `project.name` through `gitlear_project_list`.
3. Use returned internal `project.id` for issue `project`, docs, raw paths, and
   `gitlear_project_get`. Do not pass display keys to `gitlear_project_get`.
4. If no project matches, ask whether to create it with `gitlear_project_create`.
5. Status slugs are `todo`, `in-progress`, `in-review`, `done`, and `canceled`.
6. Current MCP snapshots may omit body, comments, status, project, and doc body.
   Read raw Markdown under `gitlear_workspace_get.root` whenever those fields
   matter.

Use Gitlear MCP:

- `gitlear_workspace_get`
- `gitlear_project_list`, `gitlear_project_create`, `gitlear_project_update`
- `gitlear_doc_create`, `gitlear_doc_update`
- `gitlear_issue_list`, `gitlear_issue_get`, `gitlear_issue_create`,
  `gitlear_issue_update`, `gitlear_issue_comment`
- `gitlear_member_list` when resolving assignees

Remote workflows must not create local `workspace/plans`, `workspace/tasks`, or
`workspace/review-state`.

## Shared Labels And Sources

Use exactly these labels:

- `type:plan`
- `type:task`
- `type:review-finding`

Store source, phase, subsystem, severity, dependencies, fingerprints,
acceptance criteria, and verification in bodies/comments, not labels.

New artifacts use canonical sources:

- `Source: brutal-plan`
- `Source: brutal-project-review`
- `Source: task-worker`
- `Source: gh-brutal-pr-review`

When deduping, also recognize legacy sources:

- `linear-brutal-plan`, `gitlear-brutal-plan`
- `linear-brutal-project-review`, `gitlear-brutal-project-review`
- `linear-task-worker`, `gitlear-task-worker`
- `linear-gh-brutal-pr-review`, `gitlear-gh-brutal-pr-review`
