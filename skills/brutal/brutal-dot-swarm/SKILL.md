---
name: brutal-dot-swarm
description: Drain an approved Dot Spec task graph through native subagent workers while preserving the unchanged Brutal Swarm scheduling rules. Use when parallel Dot Spec execution is required; tmux is unsupported because the unchanged controller hard-codes brutal-worker.
---

# Brutal Dot Swarm

Wrap `$brutal-swarm` scheduling with Dot Spec assignments.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md`, `../brutal-swarm/SKILL.md`, and `../brutal-swarm/references/parallel-execution.md`.
2. Require `execution.worker_runtime: subagent`. Stop before provisioning or claim when tmux is selected or implied.
3. Validate every selected task's change id, base/spec digests, owned operations, activation responsibility, and verifier.
4. Preserve ordinary Brutal behavior outside this wrapper; never route a non-opted-in task into a Dot Spec run.

## Run The Base Scheduler

Apply `$brutal-swarm` unchanged for graph normalization, concurrency, blockers, worktrees, claims, stacked branches, phase transitions, recovery, and supervisor ownership.

Override only worker selection: hand each exact task to one persistent native worker using `$brutal-dot-worker`, not `$brutal-worker`. Include the immutable Dot Spec assignment in every fresh phase context. Mutable snapshots may add actual digests and evidence but never replace approved values.

Do not mix Dot Spec and ordinary workers in one run. Do not use the unchanged tmux helper for Dot Spec assignments.

## Return

Return the base swarm status plus each task's approved and actual digests, activation state, evidence state, and exact blocker.
