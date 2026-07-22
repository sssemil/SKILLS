---
name: brutal-dot-project-review
description: Review project subsystems against active Dot Specs while preserving the unchanged Brutal Project Review workflow. Use when opted-in modules need authority, provenance, drift, traceability, maturity, or rebuildability findings.
---

# Brutal Dot Project Review

Wrap `$brutal-project-review` with active-spec correctness checks.

## Preflight

1. Read `../brutal-shared/dot-spec-contract.md` and `../brutal-project-review/SKILL.md`.
2. Resolve the base work store exactly as the base skill requires.
3. Resolve and validate the Dot Spec graph separately.
4. Map opted-in modules to the base skill's subsystem inventory.

## Run The Base Review

Apply `$brutal-project-review` unchanged for resumable state, subsystem selection, reviewer perspectives, validation, and fingerprints.

For each opted-in subsystem, also inspect canonical requirements, authorities, provenance, imports, trace output, maturity evidence, approved deltas, and independent verification.

Treat unapproved semantic drift, conflicting authority, invalid imports, unguarded active requirements, false maturity claims, and missing activation evidence as correctness findings. Send uncertain observed behavior to `$brutal-observe`; do not canonize it as a defect.

## Persist Planning Inputs

Do not publish opted-in Dot Spec findings as executable `type:review-finding` work. Persist validated CRITICAL and MAJOR findings as non-executable `type:investigation` inputs with:

```markdown
Source: brutal-dot-project-review
Dot module: <module-id>
Dot finding: <deterministic fingerprint>
```

Include the base review's evidence and acceptance detail, but label the proposed semantic effect as unresolved. Deduplicate by source, module, and fingerprint. Route each input through `$brutal-dot-plan` for approval, operation ownership, and executable ticket publication. Never recommend the ordinary worker or swarm for these inputs.

## Return

Return the base project-review status plus Dot Spec coverage, drift findings, maturity gaps, investigation refs, the next unreviewed opted-in subsystem, and `$brutal-dot-plan` as the only execution route.
