---
name: opencode-delegate
description: Delegate coding work to OpenCode through safe-opencode. Use when Codex should plan, call sandboxed OpenCode for implementation, review git diff, and validate instead of writing the main code itself.
---

# Safe OpenCode Delegate

Use this skill when the user wants Codex to orchestrate coding work while OpenCode performs the implementation inside the safe-claude sandbox.

Codex is the planner, reviewer, and validator.

OpenCode is the implementer.

Run OpenCode only through:

```bash
safe-opencode run
```

Do not use plain `opencode` for delegated implementation.

## Default stance

Do not write the main implementation yourself.

Use `safe-opencode` for:

- implementation
- refactors
- migrations
- bug fixes
- test generation
- repetitive edits
- boilerplate
- mechanical cleanup

Codex remains responsible for:

- understanding the request
- choosing scope
- writing the OpenCode job
- reviewing the diff
- running validation
- deciding whether the patch is acceptable

## Command

Primary command:

```bash
safe-opencode run --model deepseek/deepseek-v4-pro --title "codex-delegate: <short-task-name>" "<single focused job>"
```

If the DeepSeek model ID is wrong, discover the installed model name:

```bash
safe-opencode models deepseek
```

Then rerun with the exact `provider/model` value shown.

If `safe-opencode` is missing, check:

```bash
command -v safe-opencode
safe-opencode --help
```

If it is not installed, report that blocker. Do not silently fall back to plain `opencode`.

## Operating loop

### 1. Inspect first

Before delegation, run:

```bash
git status --short
```

Then inspect enough of the repo to know:

- likely edit locations
- existing patterns
- tests
- package scripts
- validation commands
- user changes already present

Do not delegate blind.

### 2. Send one focused job

The OpenCode prompt must be narrow and operational.

Use this shape:

```text
You are implementing one focused change in this repository.

Goal:
<specific goal>

Scope:
- Inspect: <files/directories>
- Edit only files needed for the goal.
- Keep the diff minimal.
- Preserve public APIs unless the task requires changing them.
- Follow existing project style.

Tests:
- Add or update tests if useful.
- Use the existing test framework.
- Do not invent a new test setup.

Do not:
- Rewrite unrelated code.
- Reformat whole files.
- Rename things unnecessarily.
- Change dependency versions unless required.
- Touch secrets, env files, generated files, vendored files, or lockfiles unless required.
- Run destructive commands.

Stop after the patch.
```

Run:

```bash
safe-opencode run --model deepseek/deepseek-v4-pro --title "codex-delegate: <short-task-name>" "<prompt>"
```

### 3. Review the patch

Always run:

```bash
git diff --stat
git diff
```

Read the diff yourself.

Reject or repair patches with:

- unrelated edits
- broad rewrites
- formatting churn
- fake tests
- missing edge cases
- dependency churn
- hardcoded local paths
- swallowed errors
- accidental lockfile changes
- changes to user work that existed before this task

### 4. Validate

Run the smallest useful validation command.

Prefer project-native commands:

```bash
npm test
npm run test
npm run typecheck
npm run lint
pnpm test
pnpm typecheck
pytest
go test ./...
cargo test
```

Only say validation passed when the command actually passed.

### 5. Repair loop

If validation fails because of the OpenCode patch, send one narrow follow-up:

```bash
safe-opencode run --model deepseek/deepseek-v4-pro --title "codex-delegate: fix <short-task-name>" "Fix only this validation failure from the previous patch:

<error output>

Constraints:
- Keep the current approach unless clearly wrong.
- Make the smallest change.
- Do not rewrite unrelated code.
- Do not add dependencies.
- Stop after the fix."
```

Then rerun:

```bash
git diff
<validation command>
```

Use at most two OpenCode repair passes before doing a tiny Codex cleanup or reporting the blocker.

## Direct Codex edits

Codex may edit directly only for:

- tiny fixes after OpenCode’s patch
- reverting unrelated changes
- import cleanup
- typo fixes
- one small missing assertion
- validation command adjustments

Do not take over the main implementation unless `safe-opencode` fails.

## Reporting

End with:

- what OpenCode changed
- what Codex changed, if anything
- files touched
- validation commands run
- failures or skipped validation
- remaining risks

## Hard rules

- Always use `safe-opencode`, not `opencode`.
- Never accept OpenCode output without reading `git diff`.
- Never claim tests passed unless they passed.
- Never hide `safe-opencode` failures.
- Never delegate validation judgment.
- Never let OpenCode broaden scope.
- Preserve existing user changes.
