# Linear Work Store Support

Resolve the exact configured project first, then its team and workflow states.
Require a unique project and team before mutation.

Use Linear operations for project/document discovery, issue search and CRUD,
comments, teams, users, statuses, parent relationships, and blockers when
available. Map logical states to the project workflow, preferring `Backlog`,
`Todo`, `In Progress`, `In Review`, `Done`, and a canceled state. Use Backlog as
staging; create/update the plan document and parent before promoting complete
children to Todo.

Use canonical `type:*` labels. Mirror parent and blocker references in issue
bodies even when native relationships exist. Never create local work-store
artifacts for a resolved Linear store; local resumable review state may live
under `.brutal-workspace/` after excluding it through `.git/info/exclude`.

To claim exact work, require its expected workflow state, transition it to
`In Progress`, assign the active user, add a unique run comment, and re-read the
issue. Return `lost` if state, assignment, or a newer conflicting claim does not
prove ownership. Preserve blocker relationships while a child is developed on
its single blocker branch.
