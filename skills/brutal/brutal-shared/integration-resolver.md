# Brutal Integration Resolver

Use this resolver before any canonical Brutal skill reads or mutates external
workflow state. Resolve integrations by role, then load the selected support
modules from `support/`.

## Roles

- `code_host`: owns the feature change, review surface, checks, and review
  comments. GitHub is the only built-in code-host adapter in version 2.
- `work_store`: owns plans, tasks, investigations, review findings, queues, and
  product context. Built-ins are `local`, `linear`, `gitlear`, and `jira`.

Skills that do not operate on a pull request need only `work_store`.

## Canonical Configuration

Prefer this frontmatter, while accepting the compatibility and prose forms
below:

```yaml
---
version: 2
integrations:
  code_host: github
  work_store: jira

execution:
  worker_runtime: tmux

providers:
  jira:
    site: example.atlassian.net
    project: ENG

labels:
  plan: type:plan
  task: type:task
  review_finding: type:review-finding
  investigation: type:investigation
---
```

Provider-specific values may appear under `providers.<name>`, legacy top-level
sections, or clear Markdown prose. The Markdown body may also contain workflow
notes, verification commands, linked documentation, and a complete custom
adapter definition.

An optional `dot_spec` section enables the repository-local contract in
`dot-spec-contract.md`. Resolve its manifest and commands independently of the
integration roles. Absence means ordinary Brutal behavior; invalid configuration
for an opted-in module is a hard error, not a fallback signal.

## Worker Runtime

For `$brutal-swarm`, resolve `execution.worker_runtime` independently of the
integration roles. Accept exactly `tmux` or `subagent`, defaulting to `tmux`
when the field is absent. Reject other values instead of guessing or silently
falling back.

- `tmux`: launch one independent Codex CLI process per task in a retained tmux
  session.
- `subagent`: use the invoking Codex session's native collaboration workers.

Validate the selected runtime before provisioning worktrees or claiming tasks.
The `tmux` runtime requires both `tmux` and `codex`; missing executables are a
hard pre-claim error. Do not weaken or replace the user's Codex model, sandbox,
approval, or profile configuration.

## Deterministic Resolution

Resolve each required role independently in this order:

1. Use `integrations.<role>` when present.
2. Treat version-1 `backend` as `integrations.work_store`.
3. Otherwise collect built-in candidates from exact case-insensitive names,
   recognizable URLs, and provider-specific configuration sections:
   - GitHub: `github`, `github.com`, or a GitHub remote
   - local: `local`, `workspace`, or an explicit local root
   - Linear: `linear` or `linear.app`
   - Gitlear: `gitlear` or a configured Gitlear workspace
   - Jira: `jira`, `atlassian`, or an `atlassian.net` URL
4. Infer GitHub only when the current remote or resolved open PR uniquely
   identifies GitHub.
5. Select a candidate only when exactly one remains. If none or more than one
   remains, ask the user to identify the primary integration for that role.

Do not infer a custom adapter from incidental prose. Select it only when
`integrations.<role>` names it or the body explicitly declares its name and
role. Never mirror one role across multiple providers.

## Compatibility

Accept version-1 `backend: local|linear|gitlear`, its existing `project`,
`gitlear`, `local`, and `labels` sections, and all legacy source markers. Do not
rewrite a valid version-1 file or silently canonicalize loose prose.

If `BRUTAL.md` is missing or cannot resolve a required role:

1. Inspect repo remotes and `AGENTS.md` hints only to prefill a decision.
2. Ask only for missing or ambiguous role/provider identifiers.
3. Validate the selected adapter and required operations before mutation.
4. Offer to create or update `BRUTAL.md`; if declined, proceed session-only only
   when the complete adapter contract is known and validated.

## Validation Result

Before workflow mutation, retain a normalized result containing:

- selected adapter and role
- stable repository/change or workspace/project identity
- current user when the workflow needs assignment or ownership checks
- logical state and label mappings
- staging strategy and relationship fallbacks
- validated tool/credential availability
- adapter-specific safety constraints
- resolved worker runtime when the invoking skill is `$brutal-swarm`
- validated Dot Spec manifest, command, independent verifier, module ids,
  maturities, authorities, and normalized digests when `dot_spec` is configured

For a local work store, also retain its canonical absolute root. Resolve a
relative `providers.local.root` against the primary worktree returned by
`git worktree list --porcelain`, not against a linked worker checkout. Stop on
an ambiguous primary worktree. Pass the retained root to managed workers and
nested Brutal skills instead of resolving the relative path again.

Load `support/contracts.md`, then the selected provider module. Stop if a
required operation or identity cannot be proven.
