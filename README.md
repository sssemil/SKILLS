# SKILLS

A collection of coding agent skills I use.

The brutal-\* family is based on this article - https://readyset.io/blog/brutal-review-and-the-new-80-20-rule

The brutal planning, project review, task worker, and GitHub PR review skills
use a repo-local `BRUTAL.md` file to choose local workspace files, Linear, or
Gitlear as the persistence backend. See
[`brutal-shared/BRUTAL.example.md`](brutal-shared/BRUTAL.example.md) for the
configuration shape.

## Brutal planning

The planning workflow is a composable, two-gate suite:

- [`brutal-plan`](brutal-plan/SKILL.md) orchestrates planning and publishes the
  approved parent plan and implementation tasks.
- [`brutal-grill`](brutal-grill/SKILL.md) resolves one repo-grounded decision at
  a time.
- [`brutal-spec`](brutal-spec/SKILL.md) synthesizes and stress-tests the
  decision-complete specification.
- [`brutal-tickets`](brutal-tickets/SKILL.md) produces approved tracer-bullet
  tickets and expand-contract sequences for wide refactors.
- [`brutal-wayfinder`](brutal-wayfinder/SKILL.md) persists investigation maps
  for work that needs research, prototypes, access, or multiple planning
  sessions before implementation can be specified.

`brutal-plan` writes nothing until the specification and complete ticket graph
have both been approved. Local and Linear tasks are staged outside the worker
intake queue until publication is complete. Wayfinder maps and questions use
the optional `type:investigation` label, so they cannot be selected by
`task-worker`.

This rework adopts the grilling, decision-complete specification, tracer-bullet,
expand-contract, and fog-of-war ideas from
[Matt Pocock's engineering skills](https://github.com/mattpocock/skills), while
retaining the Brutal `BRUTAL.md` backend model.

brutal-deepresearch is based on [Deep-Research-skills](https://github.com/Weizhena/Deep-Research-skills) by Weizhena.

brutal-reality is based on [Reality's Moat](https://davidbeyer.xyz/writing/realitys-moat) by David Beyer.

## License

See [LICENSE] file.
