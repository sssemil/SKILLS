# SKILLS

A collection of coding agent skills I use.

The brutal-\* family is based on this article - https://readyset.io/blog/brutal-review-and-the-new-80-20-rule

The Brutal planning, project review, worker, swarm, and pull-request review skills
use a repo-local `BRUTAL.md` file to resolve one code host and one work store.
Built-in support covers GitHub plus local files, Linear, Gitlear, and Jira;
complete custom adapters can be described in the file. See
[`brutal-shared/BRUTAL.example.md`](brutal-shared/BRUTAL.example.md) for the
canonical shape. Legacy version-1 backend files and unambiguous prose remain
supported.

## Brutal planning

The planning workflow is a composable, two-gate suite:

- [`brutal-plan`](brutal-plan/SKILL.md) orchestrates planning and publishes the
  approved parent plan and implementation tasks.
- [`brutal-grill`](brutal-grill/SKILL.md) resolves one repo-grounded decision at
  a time.
- [`brutal-spec`](brutal-spec/SKILL.md) synthesizes and stress-tests the
  decision-complete specification.
- [`brutal-tickets`](brutal-tickets/SKILL.md) produces the fewest cohesive,
  decision-complete implementation scopes.
- [`brutal-wayfinder`](brutal-wayfinder/SKILL.md) persists investigation maps
  for work that needs research, prototypes, access, or multiple planning
  sessions before implementation can be specified.

`brutal-plan` writes nothing until the specification and complete ticket graph
have both been approved. Work-store adapters stage or prepare complete tasks
outside the worker intake queue until publication is ready. Wayfinder maps and
questions use `type:investigation`, so `brutal-worker` cannot select them.

## Brutal execution

- [`brutal-worker`](brutal-worker/SKILL.md) owns one exact task through an
  isolated worktree, one stacked pull request, and a clean uncapped Brutal
  review/fix loop.
- [`brutal-swarm`](brutal-swarm/SKILL.md) asks for a concurrency cap and drains
  a task graph through parallel workers. It defaults to one retained tmux Codex
  session per task; `BRUTAL.md` can select native subagents instead. Independent
  roots run side by side, while single-blocker children target their blocker
  branches until those PRs merge.

## Brutal pull-request loops

- [`brutal-pr-review`](brutal-pr-review/SKILL.md) posts provider-native,
  individually actionable findings for the current open pull request.
- [`brutal-pr-finding-fixer`](brutal-pr-finding-fixer/SKILL.md) fixes generated
  findings one at a time.
- [`brutal-pr-fix-loop`](brutal-pr-fix-loop/SKILL.md) preserves the bounded
  three-pass review/fix behavior.
- [`brutal-inf-fix-loop`](brutal-inf-fix-loop/SKILL.md) repeats without a pass
  or no-progress cap until a fresh all-severity review has zero findings.

This rework adopts the grilling, decision-complete specification,
expand-contract, and fog-of-war ideas from
[Matt Pocock's engineering skills](https://github.com/mattpocock/skills), while
retaining the Brutal `BRUTAL.md` integration model.

brutal-deepresearch is based on [Deep-Research-skills](https://github.com/Weizhena/Deep-Research-skills) by Weizhena.

brutal-reality is based on [Reality's Moat](https://davidbeyer.xyz/writing/realitys-moat) by David Beyer.

## License

See [LICENSE] file.
