# Brutal Support Contracts

Support modules translate provider operations into these two role contracts.
An adapter is complete when every required behavior is native or has an
explicit behavior-preserving fallback.

## Code Host Contract

Provide operations to:

1. resolve the current repository, default branch, and open change for a
   feature branch
2. read base/head refs and SHAs, fork state, metadata, diff, files, checks,
   reviews, conversation comments, inline comments, and thread state
3. create or update owned inline findings and top-level findings
4. create review summaries and handled replies
5. map inline locations against the current diff
6. re-read and compare the head immediately before every external write
7. identify the active user and distinguish owned generated comments
8. push a named branch normally and find, create, or update one owned pull
   request when the calling skill requires task publication
9. read pull-request open, closed, draft, and merged state and change its base
   branch without merging it

Never approve, request changes, merge, force-push, delete a remote branch, or
create a pull request unless the calling skill and user explicitly authorize
that operation. A `$brutal-worker` invocation authorizes one ready pull request
for its exact task, never a merge.

## Work Store Contract

Provide operations to:

1. resolve workspace, project, current user, and stable artifact references
2. search and deduplicate by source, parent, exact title, and fingerprint
3. read and create/update plan parents, implementation tasks, investigations,
   and review findings with complete Markdown bodies
4. list queues and claim one exact artifact from an expected state; record a
   run marker, assign when supported, and re-read state and ownership before
   returning `acquired` or `lost`
5. move artifacts through `staged`, `todo`, `in_progress`, `in_review`, `done`,
   and `canceled`
6. represent parent and blocker relations natively or mirror them in bodies
7. preserve labels or equivalent body metadata for `type:plan`, `type:task`,
   `type:review-finding`, and `type:investigation`
8. report partial writes precisely enough for resumable retry

For an opted-in Dot Spec plan, preserve the approved change id, normalized
delta digest, base SHA, base-spec digests, requirement operations, activation
tickets, and approval record in complete bodies or opaque metadata. Adapters do
not interpret or weaken these values. Structured requirement queries are
optional; exact-body retrieval and source/title/parent deduplication remain
sufficient.

An adapter without a native `staged` state must use prepare-before-create:
finish every child body and dependency reference outside the intake queue,
then create children blocker-first only after the complete graph is ready.

## Shared Sources

Write canonical sources:

- `Source: brutal-plan`
- `Source: brutal-wayfinder`
- `Source: brutal-project-review`
- `Source: brutal-worker`
- `Source: brutal-pr-review`

When deduplicating, also recognize provider-prefixed legacy sources, including
`linear-*`, `gitlear-*`, `task-worker`, `linear-task-worker`,
`gitlear-task-worker`, `gh-brutal-pr-review`,
`linear-gh-brutal-pr-review`, and `gitlear-gh-brutal-pr-review`.

## Safety

Validate the exact operations required by the invoking skill before its first
mutation. Do not treat read access as proof of write, transition, relationship,
or comment access. Stop on ambiguous identity, missing credentials, unsupported
required operations, stale external state, or a partial write that cannot be
resumed safely.
