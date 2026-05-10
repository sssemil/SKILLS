---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: What will the next session be used for?
---

# Handoff Skill

Use this skill when the user wants the current conversation compacted into a handoff document so a fresh agent can continue the work.

## Instructions

Write a handoff document summarising the current conversation so a fresh agent can continue the work.

Save it to a path produced by:

```bash
mktemp -t handoff-XXXXXX.md
```

Read the file before you write to it.

Suggest the skills to be used, if any, by the next session.

Do not duplicate content already captured in other artifacts such as PRDs, plans, ADRs, issues, commits, or diffs. Reference those artifacts by path or URL instead.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the handoff document accordingly.

## Handoff Document Checklist

Include only information that helps the next agent continue the work:

- Current goal and requested outcome
- Key decisions already made
- Relevant constraints, preferences, or assumptions
- Files, paths, URLs, commits, issues, or artifacts to inspect
- Work completed so far
- Open questions or blockers
- Recommended next steps
- Skills the next session should use, when applicable
