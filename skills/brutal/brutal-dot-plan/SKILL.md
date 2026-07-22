---
name: brutal-dot-plan
description: Plan and publish work for opted-in Dot Spec modules by composing Dot Spec wrappers around the unchanged Brutal planning skills. Use for feature, refactor, migration, or authority-transfer plans that must produce an approved semantic delta and executable tasks.
---

# Brutal Dot Plan

Compose the normal Brutal planning workflow without changing its source skills.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-plan/SKILL.md`.
2. Resolve the base work-store integration exactly as `$brutal-plan` requires.
3. Resolve and validate `dot_spec` separately. Stop unless every affected module is opted in.
4. Retain the normalized graph and base identity before asking for approval.

## Run The Wrapped Gates

Follow `$brutal-plan` for route selection, approval timing, resumable publication, integration safety, and final reporting. Replace only its planning stages:

1. Use `$brutal-dot-grill` for the requirements brief.
2. Use `$brutal-dot-spec` for gate one and the immutable approved delta.
3. Use `$brutal-dot-tickets` for gate two and exact operation ownership.
4. Publish only after both gates pass.

Use these markers for wrapper-owned artifacts:

```markdown
Source: brutal-dot-plan
Base workflow: brutal-plan
Dot change: <change-id>
Dot delta: <normalized-delta-digest>
```

Preserve the base plan's parent, blocker, staging, and adapter rules. Before each write, search by wrapper source, change id, parent, and exact title. Recognize an older `Source: brutal-plan` artifact only when the same body also contains the exact Dot change and delta digest. Never deduplicate against unrelated ordinary plans. Keep this inventory for resumable publication.

The parent must carry the complete approved delta identity. Each child must carry only its owned operations plus the shared base and digest identities. Publication never edits the active canonical spec.

## Return

Report the work store, parent, dependency-ordered tasks, delta digest, activation tickets, and next unblocked task.
