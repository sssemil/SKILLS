---
version: 2
integrations:
  code_host: github
  work_store: local

execution:
  worker_runtime: tmux

providers:
  local:
    root: workspace

labels:
  plan: type:plan
  task: type:task
  review_finding: type:review-finding
  investigation: type:investigation

# Optional. Its presence opts in only modules listed by the manifest.
dot_spec:
  manifest: .dotspec/modules.yaml
  command: dotspec
  independent_verify: ./scripts/verify-contracts
---

# Brutal Workflow

Add project-specific workflow notes, verification commands, and links here.

Loose prose is accepted when it identifies one provider per required role. A
custom provider must name its role and document the complete contract from
`brutal-shared/support/contracts.md`.

When `providers.local.root` is relative, linked worker worktrees resolve it
against the repository's primary worktree so every worker shares one queue.

`execution.worker_runtime` accepts `tmux` or `subagent` and defaults to `tmux`
when omitted. Use `subagent` to keep workers in the invoking Codex session's
native collaboration tree instead of launching retained tmux sessions.

When `dot_spec` is present, follow `brutal-shared/dot-spec-contract.md`. Validate
the manifest and commands before planning or implementing an opted-in module.
Modules absent from the manifest keep the ordinary Brutal workflow.
