# Custom Integration Support

Select a custom adapter only when `BRUTAL.md` explicitly names it as the primary
`code_host` or `work_store`. Require the body to document the complete selected
role contract from `contracts.md`.

The definition must provide:

- provider name, role, required tools, authentication check, and stable identity
- an exact operation or command for every contract behavior
- input identifiers and returned fields for every operation
- logical states, labels/metadata, staging, parent, and blocker behavior when it
  is a work store
- generated-comment ownership, inline mapping, head validation, and fork safety
  when it is a code host
- retry, partial-failure, and destructive-operation constraints

Validate every operation non-mutatingly before workflow mutation. Do not run a
partially documented custom adapter, degrade to read-only behavior, or invent
missing operations. Ask the user to complete the definition and stop.
