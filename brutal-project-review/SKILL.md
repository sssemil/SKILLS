---
name: brutal-project-review
description: "Systematically review a project subsystem-by-subsystem with resumable state tracking. Creates CRITICAL/MAJOR finding tasks through the repo's BRUTAL.md backend: local workspace files, Linear, or Gitlear."
---

# Brutal Project Review

Review the project one subsystem at a time and persist actionable CRITICAL/MAJOR
findings through the configured backend.

## Required Context

1. Read `../brutal-shared/backend-resolver.md`.
2. Resolve the backend before initializing state or creating findings.
3. Read repo rules from `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, and referenced
   workflow docs.
4. If `BRUTAL.md` is missing or incomplete, follow the resolver setup flow.

## State Rules

- `local` uses `workspace/review-state/` and local tasks.
- `linear` and `gitlear` use `.brutal-workspace/review-state/` only for local
  resumable review state. Ensure `.brutal-workspace/` is ignored through
  `.git/info/exclude` before writing it.
- Do not create `workspace/plans`, `workspace/tasks`, or
  `workspace/review-state` for remote backends.
- Preserve legacy manifest fields when resuming older runs, but write new
  entries with backend-neutral keys where practical:
  `backend`, `backend_project`, `parent_ref`, `findings_created`.

## Workflow

1. Resolve or initialize the review manifest.
2. Discover subsystems dynamically from behavior-defining files. Exclude
   generated/vendor/build folders. Normalize ids as `01`, `02`, etc.
3. Show the subsystem table and ask what to review: id/name/path, `all`,
   `pending`, `restart`, or `cancel`.
4. For each selected subsystem:
   - mark it `in_progress`
   - gather relevant code, tests, migrations, APIs, configs, SQL, TOML, and docs
   - write temporary context under the backend state directory
   - launch five reviewers when available: core correctness, reliability/tests,
     maintainability, performance/security, and simplification
   - synthesize, dedupe, validate, and severity-check findings
   - write the subsystem report
   - delete temporary context before stopping or reporting
5. Only create persisted work for validated `CRITICAL` and `MAJOR` findings by
   default.

## Finding Persistence

Use deterministic fingerprints:

```text
<subsystem-id>|<canonical-file>|<line-or-symbol>|<severity>|<normalized-title>
```

Before creating a finding, search existing state and backend artifacts for the
same fingerprint and these legacy source markers:

```markdown
Source: brutal-project-review
Legacy sources: brutal-project-review, linear-brutal-project-review, gitlear-brutal-project-review
```

Persist by backend:

- `local`: create/update `workspace/tasks/todo/<NNNN>-<slug>/ticket.md` and
  append to the local manifest.
- `linear`: create/update `type:review-finding` Linear issues in the resolved
  project and configured intake state; add progress comments to the parent
  issue.
- `gitlear`: create/update `type:review-finding` Gitlear issues in `todo`; read
  raw Markdown when body, comments, status, or project membership matter.

Finding bodies must include severity, subsystem, file/line, fingerprint,
confidence, issue explanation, suggested fix, acceptance criteria, implementation
notes, dependencies, and verification commands.

## Final Response

Lead with findings by severity. Include backend, created/updated finding refs,
manifest path, parent ref, reviewed subsystem count, remaining subsystem count,
and recommend `$task-worker` for fixes.
