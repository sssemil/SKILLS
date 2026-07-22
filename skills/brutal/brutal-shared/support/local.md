# Local Work Store Support

Use the configured root, defaulting to `workspace`:

- plans: `<root>/plans`
- tasks: `<root>/tasks/{staged,todo,in-progress,in-review,done}`
- investigations:
  `<root>/investigations/<NNNN>-<slug>/{map.md,tickets/{todo,in-progress,done}}`
- review state: `<root>/review-state`

Use Markdown bodies as the source of labels, sources, parents, blockers,
assignees, comments/history, verification, and fingerprints. Allocate numeric
identifiers deterministically from existing artifacts. Use atomic directory
moves for queue transitions and stage plan children until the full graph is
ready.

Resolve `<root>` once to a canonical absolute path anchored at the primary git
worktree. Every linked worker uses that same path; never substitute its own
checkout-relative `workspace`. Claim an exact todo artifact with one atomic
rename to `in-progress`, add the run marker, then re-read its body. A missing
source path or unexpected destination means `lost`. Keep work-store state out
of task branches and task pull-request diffs.
