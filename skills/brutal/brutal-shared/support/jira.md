# Jira Work Store Support

Implement the work-store contract through the Atlassian Jira operations. Do not
require Confluence: persist the complete approved specification in the plan
parent issue body.

## Resolve And Validate

1. Resolve exactly one accessible Atlassian site/cloud and Jira project, using
   `providers.jira.site` and `providers.jira.project` when supplied.
2. Discover issue types, fields, current user, link types, statuses, and valid
   transitions before mutation.
3. Require working search/JQL, issue read/create/edit, comment, transition, and
   issue-link operations. Stop if any is unavailable.
4. Discover logical state mappings, accepting explicit provider overrides.
   Require mappings for `todo`, `in_progress`, `in_review`, `done`, and
   `canceled` before queue work.

## Artifact Mapping

- Store plans and investigations as parent work items using configured issue
  types or the closest non-subtask type that accepts the complete body.
- Store tasks and review findings as child or linked work items.
- Use labels `type-plan`, `type-task`, `type-review-finding`, and
  `type-investigation` when Jira label syntax rejects colons; retain canonical
  `type:*` values in the body metadata.
- Use native parent fields and issue links where supported, and always mirror
  parent/blocker references in bodies.
- Use comments for progress, verification, commit hashes, and resumable partial
  failure records.

If no safe staging status exists, use prepare-before-create and create complete
children blocker-first in the configured intake status.

## Exact Claims

Before implementation, require the expected issue status, transition the exact
issue to logical `in_progress`, assign the active user when supported, and add
a unique run comment. Re-read status, assignee, links, and recent comments;
return `lost` on any conflicting claim or ownership ambiguity. Preserve native
blocker links for stacked work rather than marking dependencies complete early.
