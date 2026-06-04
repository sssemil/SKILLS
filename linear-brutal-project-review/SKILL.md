---
name: linear-brutal-project-review
description: Systematically reviews a project subsystem-by-subsystem with resumable .brutal-workspace state and creates Linear review finding issues for CRITICAL and MAJOR problems.
---

Hybrid local-state / Linear-backed brutal project review. Use this when the
user asks for `$linear-brutal-project-review`, asks to review a project into
Linear, or asks for `brutal-project-review` behavior where findings become
Linear issues instead of local workspace task files.

This skill preserves the subsystem-by-subsystem review discipline, manifest
state tracking, subsystem reports, resume behavior, and review rigor of
`brutal-project-review`. The only intentional workflow difference is that
CRITICAL and MAJOR findings become Linear issues rather than
`workspace/tasks/todo` tickets.

## Hard Rules

- First read the repo's `AGENTS.md`.
- `AGENTS.md` must name the Linear project to use. Accept clear wording such as
  `Linear project: <name>` or "Use the Linear project `<name>`".
- If the Linear project name is missing, stop and ask the user to add or provide
  it. Do not guess from prior conversations or old local files.
- Resolve the project and team through Linear MCP before creating or updating
  any review artifacts, including `.brutal-workspace` files.
- If Linear MCP tools are unavailable, stop and report that review findings
  cannot be persisted. Do not fall back to local task files.
- Never create new `workspace/review-state`, `workspace/tasks`, or
  `workspace/plans` files.
- Use `.brutal-workspace/review-state/` as the only local review-state
  directory.
- `.brutal-workspace` is local resumable state. The skill may create and update
  it, but must not commit it unless the user explicitly asks.
- Before writing `.brutal-workspace`, ensure `.brutal-workspace/` is ignored by
  the local repo, preferably through `.git/info/exclude`. Do not modify tracked
  ignore files unless the user explicitly asks.
- Use only these labels: `type:plan`, `type:task`, `type:review-finding`.
- Put severity, subsystem, component, source, confidence, local IDs,
  dependencies, acceptance criteria, verification, and file references in issue
  bodies/comments, not labels.
- Create Linear issues only for CRITICAL and MAJOR findings by default.
- Recommend `$linear-task-worker` for fixes. Do not recommend the local
  `task-worker` workflow.

## Step 0: Resolve Project Context

Before any state initialization, review scoping, or artifact creation:

1. Read `AGENTS.md`.
2. Extract the Linear project name.
3. Resolve the Linear project through Linear MCP using exact lookup when
   possible.
4. Identify the project team from the project result. If exactly one team is
   associated with the project, use it. If multiple teams are associated, ask
   the user which team to use. If no team is discoverable from the project
   result, ask the user for the Linear team before resolving statuses.
5. Resolve the team's issue statuses. Use `Todo` for new finding issues when it
   exists. If `Todo` does not exist, ask the user which unstarted intake status
   to use before creating findings.
6. Read referenced workflow docs if present, such as `docs/linear-workflow.md`.
7. Read `TARGET.md` if present.
8. Check git status and note uncommitted changes; do not edit repo code during
   the review workflow unless the user explicitly changes the request.

If multiple Linear projects match, ask the user to choose. If no project
matches, ask the user to correct `AGENTS.md` or create/provide the project.

## Step 1: Check For Existing Local State

After the Linear project has been resolved, check for an existing manifest:

```bash
ls -la .brutal-workspace/review-state/manifest.json 2>/dev/null
```

If `manifest.json` exists:

- Read it and inspect subsystem statuses.
- If `linear_project_id` or `linear_project_name` does not match the resolved
  project, stop and ask whether to archive the old state and start a fresh run.
- Before updating missing fields in the manifest, ensure `.brutal-workspace/` is
  ignored through `.git/info/exclude` or an existing ignore rule.
- If `linear_team_id`, `finding_intake_status_id`, or their names are missing
  from an older manifest, resolve them and update the manifest before review.
- If `parent_issue_id` or `parent_issue_identifier` exists, resolve that Linear
  issue. If it no longer exists, create or locate a replacement parent issue and
  update the manifest.
- If any subsystem is `pending` or `in_progress`, keep the manifest and proceed
  to Step 3.
- If all subsystems are `done`, keep the manifest and proceed to Step 3 so the
  user can choose whether to re-review one subsystem or all subsystems.

If `manifest.json` does not exist, initialize a fresh review in Step 2.

## Step 2: Initialize Fresh Review

### 2.1 Create Or Locate Linear Parent Issue

Create or reuse a parent Linear issue labeled `type:plan` with title:

```text
Project Review: <repo or project name>
```

Reuse an existing parent only when it is in the resolved project, has
`Source: linear-brutal-project-review` in the body or comments, and clearly
matches the same repo/review run. Otherwise create a new parent.

Parent issue body:

```markdown
Source: linear-brutal-project-review
State: `.brutal-workspace/review-state/manifest.json`

## Summary
Subsystem-by-subsystem brutal project review. CRITICAL and MAJOR findings are
created as child or related Linear issues labeled `type:review-finding`.

## Status
- Pending: <count>
- In Progress: <count>
- Complete: <count>

## Review Scope
<subsystem list or pending discovery note>

## Finding Issues
<created Linear identifiers, or None yet>
```

Create a Linear project document for the full review manifest only when Linear
documents are available and useful. The local manifest remains authoritative for
resume behavior.

### 2.2 Create Local State Directory

```bash
mkdir -p .brutal-workspace/review-state/subsystems
mkdir -p .brutal-workspace/review-state/archive
```

Before writing source context, ensure `.brutal-workspace/` is listed in
`.git/info/exclude` so temporary context and local state do not pollute normal
`git status`. This is local-only repo metadata, not a tracked project change.

### 2.3 Discover Subsystems Dynamically

Do not hardcode subsystem names or paths. Discover them from the repository on
each fresh run.

1. Discover source and behavior-defining files:
   - Include: `.rs`, `.ts`, `.tsx`, `.js`, `.jsx`, `.css`, `.json`, `.sql`,
     `.toml`, and Markdown docs that define architecture or service behavior
   - Exclude generated/vendor/build folders: `.git`, `node_modules`, `target`,
     `dist`, `build`, `.next`, `coverage`, `vendor`
2. Derive subsystem paths from each source file using these rules:
   - If path matches `*/src/<segment>/...`, use `*/src/<segment>/`
   - If path is directly under `*/src/`, use `*/src/`
   - If path matches `*/app/...`, use `*/app/`
   - Otherwise, use the nearest package root that owns the file, such as
     `apps/<name>/`, `libs/<name>/`, `packages/<name>/`, `services/<name>/`,
     or `crates/<name>/`
3. Normalize subsystem paths:
   - Convert to repository-relative paths
   - Remove duplicates
   - Sort for deterministic ordering
4. Create subsystem metadata:
   - `id`: zero-padded sequential IDs (`01`, `02`, ...)
   - `name`: slug from path, lowercase, with `/` and `_` converted to `-`
   - `path`: normalized discovered path
   - `status`: `pending`
   - `report_path`: `null`

If no subsystems are discovered, report that no source files were found and
stop.

### 2.4 Create Manifest

Write `.brutal-workspace/review-state/manifest.json`:

```json
{
  "version": 1,
  "started_at": "<ISO timestamp>",
  "last_updated_at": "<ISO timestamp>",
  "linear_project_id": "<Linear project UUID>",
  "linear_project_name": "<Linear project name>",
  "linear_team_id": "<Linear team UUID>",
  "linear_team_name": "<Linear team name>",
  "finding_intake_status_id": "<Linear status UUID>",
  "finding_intake_status_name": "<Todo or selected intake status name>",
  "parent_issue_id": "<Linear parent issue UUID>",
  "parent_issue_identifier": "<KEY-123>",
  "selected_mode": null,
  "subsystems": [
    {
      "id": "01",
      "name": "<auto-generated-name>",
      "path": "<auto-discovered-path>",
      "status": "pending",
      "report_path": null
    }
  ],
  "linear_issues_created": []
}
```

Get timestamps with:

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

Update the parent Linear issue with the discovered subsystem count and scope.

## Step 3: Show Review State And Ask What To Review

Read the manifest and show all available subsystems before doing review work.

### 3.1 Display Review State

Print a concise table:

```markdown
| ID | Name | Path | Status | Started | Completed | Report |
| --- | --- | --- | --- | --- | --- | --- |
| <id> | <name> | <path> | <pending|in_progress|done> | <in_progress_at or -> | <completed_at or never> | <report_path or -> |
```

Also report:

- Manifest path: `.brutal-workspace/review-state/manifest.json`
- Linear parent issue: `<identifier>`
- Review cycle started: `started_at`
- Counts by status: pending, in_progress, done
- Created Linear finding issues: `linear_issues_created.length`

### 3.2 Ask For Review Target

Ask the user which subsystem to review now. Do not proceed until the user
answers.

Accepted responses:

- A subsystem `id`, `name`, or `path`: review only that subsystem.
- `all`: review every subsystem in manifest order, including previously
  completed subsystems.
- `pending`: review every subsystem whose status is `pending` or `in_progress`,
  in manifest order.
- `restart`: archive the current local manifest and reports, then return to
  Step 2 for fresh discovery.
- `cancel`: stop without changing review state.

For `restart`, move the existing manifest and subsystem reports under
`.brutal-workspace/review-state/archive/<timestamp>/`. Do not delete the old
`linear_issues_created` mappings permanently; preserve them in the archive so
duplicate Linear findings can be investigated later.

If the user chooses a subsystem that is already `done`, re-review it by setting
it back to `in_progress`.

### 3.3 Mark Selected Subsystems In Progress

For each subsystem selected for review:

1. Set subsystem status to `"in_progress"` before gathering context.
2. Add or update `"in_progress_at": "<ISO timestamp>"`.
3. Preserve any existing `"completed_at"` until Step 9 replaces it after the
   new review finishes.
4. Set manifest `selected_mode` to the user's chosen mode and update
   `last_updated_at`.
5. Update or comment on the parent Linear issue with the current counts.

For `all` or `pending`, run Steps 4 through 12 for each selected subsystem in
deterministic manifest order before reporting final completion.

## Step 4: Gather Subsystem Context

For the selected subsystem:

1. List all relevant files in the subsystem path:
   - Source files: `.rs`, `.ts`, `.tsx`, `.js`, `.jsx`, `.css`, `.json`
   - Related tests, migrations, APIs, clients, configs, SQL, TOML, and docs
2. Read the files fully enough to review them.
3. Build a context block containing:
   - Subsystem name and path
   - Applicable repo rules from `AGENTS.md`
   - Relevant target context from `TARGET.md`
   - List of files and content needed for review
4. Write the context block to:

```text
.brutal-workspace/review-state/context-<subsystem-id>.md
```

Context files are temporary, may contain source snippets or secrets, must not be
referenced from Linear issues, and must be deleted after each subsystem review.

## Step 5: Conduct Multi-Perspective Review

Launch five parallel review subagents when available. Each subagent must read
`.brutal-workspace/review-state/context-<subsystem-id>.md` as its first action;
subagents do not inherit context automatically.

Perspectives:

- Core logic and architecture
- Reliability, tests, and error handling
- Cleanliness, documentation, and repo rules
- Performance and security
- Code reduction and simplicity

Each finding must include:

- severity: CRITICAL, MAJOR, MINOR, or NIT
- confidence 0-100
- file and line reference
- code snippet when useful
- concrete explanation
- actionable fix
- implementation notes or verification hints when relevant

Severity definitions:

- `CRITICAL`: must fix before merge; correctness, data loss, security, or
  forbidden production panic/unwrap patterns
- `MAJOR`: should fix; significant design, reliability, performance, or test
  gap
- `MINOR`: worthwhile but not blocking
- `NIT`: optional cleanup

Use the same rigorous review perspectives and tone as `brutal-project-review`:
question correctness, design, test coverage, error paths, security, performance,
maintainability, and unnecessary code.

## Step 6: Synthesize And Validate Findings

After collecting findings:

1. Combine duplicate or overlapping findings.
2. Filter irrelevant findings and false positives.
3. Validate file and line references against current code.
4. Validate suggested fixes for technical correctness and regression risk.
5. Downgrade or drop speculative findings.
6. Reassess severity.
7. Ensure each surviving finding has concrete acceptance criteria.

Number findings sequentially by subsystem id:

```text
<subsystem-id>-001
<subsystem-id>-002
```

Example: `03-001`.

## Step 7: Write Local Subsystem Report

Write findings to:

```text
.brutal-workspace/review-state/subsystems/<subsystem-name>.md
```

Report format:

````markdown
# Review: <Subsystem Name>

**Path**: <subsystem path>
**Reviewed**: <ISO timestamp>
**Status**: Complete
**Linear Parent**: <parent issue identifier>

## Summary
- CRITICAL: <count>
- MAJOR: <count>
- MINOR: <count>
- NIT: <count>

## Findings

### [CRITICAL] <finding-id>: <brief description>
**File**: `<path>:<line>`
**Confidence**: <0-100>
**Linear Issue**: <identifier or pending>

**Issue**:
<detailed explanation>

**Code**:
```<lang>
<problematic code snippet>
```

**Fix**:
<actionable fix>

**Acceptance Criteria**:
- [ ] <criterion>

---
````

Update the subsystem's `report_path` in the manifest. After Linear finding
issues are created or updated in Step 8, rewrite this report so each
`**Linear Issue**` field contains the final Linear identifier instead of
`pending`.

## Step 8: Create Or Update Linear Finding Issues

For each CRITICAL or MAJOR finding, create or update a Linear issue.

### 8.1 Duplicate Prevention

Use a deterministic fingerprint as the stable key:

```text
<subsystem-id>|<canonical-file>|<line-or-symbol>|<severity>|<normalized-title>
```

Normalize the title by lowercasing it, trimming whitespace, removing known
volatile tokens such as dates, timestamps, build IDs, and generated hashes, and
collapsing repeated spaces. Preserve meaningful numbers such as HTTP status
codes, size limits, timeouts, and version numbers. Store `finding_id`
separately; do not use the sequential finding ID as the duplicate-prevention
key because finding numbers can change between review runs.

Before creating an issue, search `linear_issues_created` for the same
fingerprint.

- If a matching open Linear issue exists, update the issue body or add a comment
  with the latest review details. Do not create a duplicate.
- If a matching Linear issue exists but is closed/done, add a comment noting
  that the finding reappeared and move it back to the resolved finding intake
  status only when the issue is still valid and the workflow allows that
  transition.
- If no matching issue exists, create a new Linear issue.
- If a finding materially changes file, impact, or fix, create a new finding ID
  and a new Linear issue rather than rewriting history. If only explanation,
  acceptance criteria, or suggested fix text changed, update/comment on the
  existing issue.

### 8.2 Issue Relationship And Status

Create finding issues in the resolved project using:

- label: `type:review-finding`
- state: resolved `finding_intake_status_id`
- parent relationship: prefer `parentId` pointing to the review parent issue
- fallback relationship: use `relatedTo` if `parentId` is unsupported

Always mirror the parent issue identifier in the issue body even when Linear
relationships are set.

### 8.3 Issue Title And Body

Issue title:

```text
Fix <subsystem>: <brief finding>
```

Issue body:

```markdown
Source: linear-brutal-project-review
Review Parent: <parent issue identifier/title>
Subsystem: <subsystem path/name>
Severity: <CRITICAL|MAJOR>
Finding ID: <subsystem-id>-001
Confidence: <0-100>
File: `<path>:<line>`
Fingerprint: `<subsystem-id>|<canonical-file>|<line-or-symbol>|<severity>|<normalized-title>`

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
<repo rules, relevant constraints, edge cases, and review notes>

## Verification
<specific verification commands from AGENTS.md, repo scripts, or best available narrow checks>

## Dependencies
- Blocked by: None, unless a real blocker was identified
- Blocks: None, unless this finding blocks another issue
- Related: <parent issue identifier and any related finding IDs>
```

Use Linear relationships for `blockedBy`, `blocks`, or `relatedTo` when the MCP
tool supports them. Mirror those relationships in the body.

### 8.4 Update Manifest

For each created or updated Linear issue, append or update an entry in
`linear_issues_created`:

```json
{
  "fingerprint": "<subsystem-id>|<canonical-file>|<line-or-symbol>|<severity>|<normalized-title>",
  "linear_id": "<Linear UUID>",
  "linear_identifier": "<KEY-123>",
  "finding_id": "<subsystem-id>-001",
  "subsystem_id": "<subsystem id>",
  "subsystem_name": "<subsystem name>",
  "severity": "<CRITICAL|MAJOR>",
  "file": "<path>:<line>",
  "title": "<normalized finding title>",
  "status": "<created|updated|reopened>",
  "created_at": "<ISO timestamp>",
  "updated_at": "<ISO timestamp>"
}
```

Update `last_updated_at` after writing Linear issue mappings.

Rewrite the local subsystem report after issue creation so each CRITICAL/MAJOR
finding includes its final Linear identifier. Do not create local task
directories. Do not commit the manifest or report.

## Step 9: Mark Subsystem Complete

Update the manifest:

1. Set subsystem status to `"done"`.
2. Add or replace `"completed_at": "<ISO timestamp>"`.
3. Preserve `"in_progress_at"`.
4. Set `"last_updated_at": "<ISO timestamp>"`.

## Step 10: Mirror Progress To Linear Parent

After each subsystem review, add a concise comment to the parent Linear issue:

```markdown
Review complete: <Subsystem>

- Report: `.brutal-workspace/review-state/subsystems/<subsystem-name>.md`
- Findings: <critical> CRITICAL, <major> MAJOR, <minor> MINOR, <nit> NIT
- Linear issues: <created or updated identifiers, or None>
- Remaining: <pending> pending, <in_progress> in_progress, <done> done
```

Update the parent issue body when useful to keep the status summary and finding
issue list current. The local manifest remains authoritative for resume state.
Compute counts after Step 9 so the just-reviewed subsystem is reported as
`done`, not `in_progress`.

## Step 11: Cleanup Context File

Delete the temporary context file before user-facing progress or final
reporting:

```bash
rm .brutal-workspace/review-state/context-<subsystem-id>.md
```

Do this even when the review found no CRITICAL or MAJOR issues. Also attempt
this cleanup before stopping on errors, Linear failures, user cancellation after
context creation, or interruption resumes.

## Step 12: Report Progress

Calculate and report:

- How many subsystems reviewed vs total
- Findings by severity for this subsystem
- How many Linear issues were created or updated
- Manifest path
- Linear parent issue identifier
- Remaining subsystem counts by status
- Next step based on the selected mode

Example:

```markdown
## Subsystem Review Complete: <subsystem-name> (<reviewed>/<total>)

**Findings**: <critical> CRITICAL, <major> MAJOR, <minor> MINOR, <nit> NIT
**Linear Issues**: <count> (<KEY-123>, <KEY-124>)
**Manifest**: `.brutal-workspace/review-state/manifest.json`
**Remaining**: <pending> pending, <in_progress> in_progress, <done> done

Run `$linear-brutal-project-review` again to choose another subsystem,
`pending`, or `all`, or run `$linear-task-worker` to fix created findings.
```

## Final Response

Report:

- subsystem reviewed
- finding counts by severity
- manifest path
- Linear parent issue/document
- created or updated CRITICAL/MAJOR issue identifiers
- remaining subsystem counts
- recommended next subsystem or `$linear-task-worker` for fixes

Be direct and findings-first. Avoid praise and vague summaries.

## Severity Categories

`CRITICAL` - Must fix before merge. Bugs, data corruption risks, security
issues, forbidden production `unwrap`, or panic in library/production paths.

`MAJOR` - Should fix. Significant design issues, missing error handling,
performance problems, reliability risks, or inadequate testing.

`MINOR` - Recommended fixes. Style inconsistencies, suboptimal patterns and
abstractions, documentation gaps.

`NIT` - Optional improvements. Minor style preferences or micro-optimizations.
