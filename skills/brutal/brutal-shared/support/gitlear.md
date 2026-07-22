# Gitlear Work Store Support

Require a configured workspace name or key prefix and an exact project name.
Resolve the workspace first, then use the returned internal project id for all
project, document, issue, and raw-path operations.

Use Gitlear workspace, project, document, issue, comment, and member operations.
Map states to `todo`, `in-progress`, `in-review`, `done`, and `canceled`. Because
Gitlear has no staging state or relationship mutation, use prepare-before-create
and create complete children blocker-first in `todo`; mirror parent and blocker
references in bodies.

Read raw Markdown beneath the resolved workspace root whenever MCP snapshots
omit body, comments, status, project membership, or document content. Never
create local work-store artifacts for a resolved Gitlear store; local resumable
review state may live under `.brutal-workspace/` after excluding it through
`.git/info/exclude`.

To claim exact work, update the expected todo issue to `in-progress`, assign the
active member when supported, add a unique run comment, and re-read raw state,
status, assignment, and comments. Return `lost` unless all available ownership
signals still identify that run. Never remove blocker metadata to make stacked
work appear natively unblocked.
