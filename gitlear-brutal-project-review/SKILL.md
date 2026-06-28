---
name: gitlear-brutal-project-review
description: Systematically reviews a project subsystem-by-subsystem with resumable .brutal-workspace state and creates Gitlear review finding issues for CRITICAL and MAJOR problems. Use when Codex is asked to run $gitlear-brutal-project-review, review a project into Gitlear, or use brutal-project-review behavior backed by Gitlear.
---

# Gitlear Brutal Project Review

Hybrid local-state / Gitlear-backed brutal project review. Preserve the
subsystem-by-subsystem review discipline, local manifest resume behavior, and
review rigor of `brutal-project-review`; persist actionable findings in
Gitlear instead of local task files.

## Hard Rules

- First read the repo's `AGENTS.md`.
- `AGENTS.md` must include `Gitlear workspace: <name or key_prefix>` and
  `Gitlear project: <name>`. Stop if either is missing.
- Validate the active Gitlear MCP workspace with `gitlear_workspace_get`.
- Resolve the project with `gitlear_project_list`, then use the returned
  internal `project.id`; do not pass display keys to `gitlear_project_get`.
- If Gitlear MCP tools are unavailable, stop. Do not create local task files as
  a fallback.
- Never create new `workspace/review-state`, `workspace/tasks`, or
  `workspace/plans` files.
- Use `.brutal-workspace/review-state/` as the only local review-state
  directory. Ensure `.brutal-workspace/` is ignored through `.git/info/exclude`
  before writing it.
- Use only labels `type:plan`, `type:task`, and `type:review-finding`.
- Create Gitlear issues only for CRITICAL and MAJOR findings by default.
- Recommend `$gitlear-task-worker` for fixes.

## Gitlear Data Rules

- Issue statuses are path slugs: `todo`, `in-progress`, `in-review`, `done`,
  and `canceled`.
- Current MCP issue snapshots omit status, project, body, and comments. Read raw
  Markdown under `gitlear_workspace_get.root` when duplicate prevention, project
  membership, body content, or comments matter.
- Store dependencies, parent links, severity, component, confidence, local IDs,
  fingerprints, acceptance criteria, and verification in issue bodies/comments.
  Do not rely on Gitlear issue relationships; the current MCP does not expose
  relationship mutations.

## Step 0: Resolve Context

1. Read `AGENTS.md`.
2. Validate `Gitlear workspace:` against `gitlear_workspace_get`.
3. Resolve `Gitlear project:` through `gitlear_project_list` and record
   internal project id, display key, and name.
4. Read referenced workflow docs and `TARGET.md` if present.
5. Check git status and note uncommitted changes. Do not edit repo code during
   review unless the user explicitly changes the request.

## Step 1: Check Existing State

After resolving the Gitlear project, check:

```bash
ls -la .brutal-workspace/review-state/manifest.json 2>/dev/null
```

If the manifest exists:

- Read it and inspect subsystem statuses.
- If `gitlear_project_id` or `gitlear_project_name` differs from the resolved
  project, stop and ask whether to archive the old state and start fresh.
- If `parent_issue_key` exists, resolve it through Gitlear. If missing or
  invalid, create or locate a replacement parent issue and update the manifest.
- Continue to the review target selection when any subsystem is pending,
  in-progress, or done.

If no manifest exists, initialize a fresh review.

## Step 2: Initialize Fresh Review

Create or reuse a parent Gitlear issue labeled `type:plan` in the resolved
project:

```text
Project Review: <repo or project name>
```

Reuse an existing parent only when it is in the resolved project, has
`Source: gitlear-brutal-project-review` in body/comments, and clearly matches
the same repo/review run.

Parent body:

```markdown
Source: gitlear-brutal-project-review
State: `.brutal-workspace/review-state/manifest.json`

## Summary
Subsystem-by-subsystem brutal project review. CRITICAL and MAJOR findings are
created as Gitlear issues labeled `type:review-finding`.

## Status
- Pending: <count>
- In Progress: <count>
- Complete: <count>

## Review Scope
<subsystem list or pending discovery note>

## Finding Issues
<created Gitlear display keys, or None yet>
```

Create `.brutal-workspace/review-state/subsystems` and
`.brutal-workspace/review-state/archive`.

Discover subsystems dynamically from source and behavior-defining files,
excluding generated/vendor/build folders. Normalize subsystem ids as zero-padded
`01`, `02`, etc., with status `pending`.

Write `.brutal-workspace/review-state/manifest.json`:

```json
{
  "version": 1,
  "started_at": "<ISO timestamp>",
  "last_updated_at": "<ISO timestamp>",
  "gitlear_workspace_name": "<workspace name>",
  "gitlear_workspace_key_prefix": "<prefix>",
  "gitlear_project_id": "<internal project id>",
  "gitlear_project_name": "<project name>",
  "parent_issue_key": "<Gitlear internal issue id>",
  "parent_issue_display_key": "<KEY-123>",
  "selected_mode": null,
  "subsystems": [],
  "gitlear_issues_created": []
}
```

## Step 3: Select Review Target

Display a concise table of subsystems and ask the user for one of:

- subsystem id/name/path
- `all`
- `pending`
- `restart`
- `cancel`

For `restart`, archive the existing manifest and reports under
`.brutal-workspace/review-state/archive/<timestamp>/`.

Mark selected subsystems `in_progress` before gathering context and update the
manifest timestamp.

## Step 4: Review A Subsystem

For each selected subsystem:

1. Gather relevant files, tests, migrations, APIs, configs, SQL, TOML, and docs.
2. Write temporary context to
   `.brutal-workspace/review-state/context-<subsystem-id>.md`.
3. Launch five parallel reviewers when available:
   - Core logic and architecture
   - Reliability, tests, and error handling
   - Cleanliness, documentation, and repo rules
   - Performance and security
   - Code reduction and simplicity
4. Require each finding to include severity, confidence, file/line, explanation,
   actionable fix, and verification hints.
5. Synthesize, dedupe, validate, and severity-check findings.
6. Write the subsystem report to
   `.brutal-workspace/review-state/subsystems/<subsystem-name>.md`.
7. Delete the temporary context file before user-facing reporting.

## Step 5: Create Or Update Finding Issues

For each CRITICAL or MAJOR finding, build a deterministic fingerprint:

```text
<subsystem-id>|<canonical-file>|<line-or-symbol>|<severity>|<normalized-title>
```

Before creating, search:

- `manifest.gitlear_issues_created`
- current Gitlear issues in the resolved project by raw Markdown body

If the fingerprint exists on an open issue, update the body or add a comment.
If it was completed but the finding reappeared, comment and move it to `todo`
only when still valid. If no match exists, create a new issue.

Finding issue title:

```text
Fix <subsystem>: <brief finding>
```

Issue body:

```markdown
Source: gitlear-brutal-project-review
Review Parent: <parent issue display key/title>
Subsystem: <subsystem path/name>
Severity: <CRITICAL|MAJOR>
Finding ID: <subsystem-id>-001
Confidence: <0-100>
File: `<path>:<line>`
Fingerprint: `<fingerprint>`

## Issue
<validated explanation>

## Suggested Fix
<specific fix>

## Acceptance Criteria
- [ ] Investigate and confirm the issue
- [ ] Implement the fix
- [ ] Add or update tests if applicable
- [ ] Run repo verification

## Implementation Notes
<repo rules, constraints, edge cases, review notes>

## Verification
<specific verification commands>

## Dependencies
- Blocked by: None, unless a real blocker was identified
- Blocks: None, unless this finding blocks another issue
- Related: <parent issue display key and related finding IDs>
```

Append/update the manifest's `gitlear_issues_created` entries with fingerprint,
issue id, display key, finding id, subsystem, severity, file, title, status, and
timestamps.

## Step 6: Complete And Report

After each subsystem:

- mark it `done`
- update the parent issue with a progress comment
- update the subsystem report with final Gitlear issue display keys
- report findings by severity, created/updated issue keys, manifest path,
  parent issue, and remaining counts

Final response must be findings-first and recommend `$gitlear-task-worker` for
fixes.
