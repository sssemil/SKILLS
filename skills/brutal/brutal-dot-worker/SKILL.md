---
name: brutal-dot-worker
description: Implement one exact task from an approved Dot Spec delta while preserving the unchanged Brutal Worker lifecycle. Use for standalone or native-subagent Dot Spec work, including review and finding-fix phases; the unchanged tmux runtime is intentionally unsupported.
---

# Brutal Dot Worker

Wrap `$brutal-worker` with fail-closed semantic boundaries.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-worker/SKILL.md`.
2. Require the exact task, change id, normalized delta digest, base SHA, applicable base-spec digests, owned operations, activation responsibility, and independent verifier.
3. Recompute every supplied identity before claim or mutation.
4. Stop if the managed runtime is `tmux`. The unchanged tmux controller invokes `$brutal-worker` directly and cannot enforce this wrapper.

## Run The Base Lifecycle

Apply `$brutal-worker` unchanged for ownership, isolated worktrees, provider safety, phase boundaries, commits, pushes, and task transitions.

In standalone or native mode, substitute `$brutal-dot-inf-fix-loop` for the base worker's `$brutal-inf-fix-loop`. Never invoke an ordinary review loop for an opted-in module.

Add these constraints:

- `work`: implement only owned operations; an activating PR updates canonical spec, code, tests, trace, and evidence atomically.
- `review`: use `$brutal-dot-pr-review` for the exact base/head snapshot.
- `fix`: use `$brutal-dot-pr-finding-fixer`; return semantic changes outside the delta to planning.
- `handoff`: recompute actual delta/spec digests and require independent evidence tied to the current head.
- `complete`: record activation only after the matching PR is verified merged.

Never change authority, compatibility, activation ownership, or mandatory evidence outside the approved delta.

## Return

Return the base worker result plus actual digests, requirement trace, independent evidence, and activation status. A mismatch is `blocked`, never clean.
