# Brutal Backend Resolver Compatibility

The version-1 singular backend resolver has moved to
[`integration-resolver.md`](integration-resolver.md). Treat legacy `backend` as
the `work_store` role and otherwise follow the new resolver and support modules.

Keep this file only so older skills and external references fail forward to the
current contract. New skills must read `integration-resolver.md` directly.
Resolve relative local roots against the primary git worktree so linked workers
share one queue.
