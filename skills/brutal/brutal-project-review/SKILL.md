---
name: brutal-project-review
description: "Systematically review a project subsystem-by-subsystem with resumable state tracking. Creates CRITICAL/MAJOR finding tasks through the work store resolved from BRUTAL.md."
---

# Brutal Project Review

Review the project one subsystem at a time and persist actionable CRITICAL/MAJOR
findings through the configured work-store adapter.

## Required Context

1. Read `../brutal-shared/integration-resolver.md`.
2. Resolve the work store and load its support module before initializing state
   or creating findings.
3. Read repo rules from `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, and referenced
   workflow docs.
4. If `BRUTAL.md` is missing or incomplete, follow the integration setup flow.

## State Rules

- The local adapter uses its configured review-state path and local tasks.
- Remote adapters use `.brutal-workspace/review-state/` only for resumable local
  review state. Exclude `.brutal-workspace/` through `.git/info/exclude` before
  writing it and never create local work-store artifacts.
- Preserve legacy manifest fields when resuming older runs, but write new
  entries with adapter-neutral keys where practical:
  `work_store`, `work_store_project`, `parent_ref`, `findings_created`.

## Workflow

1. Resolve or initialize the review manifest.
2. Discover subsystems dynamically from behavior-defining files. Exclude
   generated/vendor/build folders. Normalize ids as `01`, `02`, etc.
3. Show the subsystem table and ask what to review: id/name/path, `all`,
   `pending`, `restart`, or `cancel`.
4. For each selected subsystem:
   - mark it `in_progress`
   - gather relevant code, tests, migrations, APIs, configs, SQL, TOML, and docs
   - write temporary context under the resolved review-state directory
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

Before creating a finding, search existing state and work-store artifacts for the
same fingerprint and these legacy source markers:

```markdown
Source: brutal-project-review
Legacy sources: brutal-project-review, linear-brutal-project-review, gitlear-brutal-project-review
```

Create/update `type:review-finding` artifacts through the work-store adapter in
its logical `todo` state, add progress to the parent when one exists, and append
stable refs to the review manifest. Follow provider-specific read fallbacks and
prepare-before-create rules from the support module.

Finding bodies must include severity, subsystem, file/line, fingerprint,
confidence, issue explanation, suggested fix, acceptance criteria, implementation
notes, dependencies, and verification commands.

## Final Response

Lead with findings by severity. Include work store, created/updated finding refs,
manifest path, parent ref, reviewed subsystem count, remaining subsystem count,
and recommend `$brutal-swarm` for parallel fixes or `$brutal-worker` for one
exact finding.
