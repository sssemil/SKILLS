---
name: funcvec-dedupe-fixer
description: Use when the user wants Rust duplicate-function detection and cleanup with funcvec, especially crate-by-crate scans, duplicate triage, boilerplate refactors, or safe dedupe fixes across a Rust workspace.
---

# Funcvec Dedupe Fixer

Run a crate-by-crate **sieve**: discover candidates with `funcvec`, inspect the
code behind each hit, refactor only high-confidence duplication, and verify each
crate before moving on.

## Ground Rules

- Work one crate at a time. Do not batch edits across unrelated crates.
- Treat `funcvec` output as suspects, not proof.
- Prefer deleting duplication by reusing existing helpers, extracting a small
  private helper, or introducing a macro only when the repeated shape is real.
- Do not merge tiny getters, setters, builders, or forwarding methods unless a
  larger repeated pattern makes the refactor pay for itself.
- Preserve public APIs unless the user explicitly asked for breaking cleanup.
- Preserve error mapping, metrics, logging, tracing, auth, validation, endpoint
  names, serialization, and async behavior.
- Leave generated code alone unless the generator is also updated.

## Step 1: Build The Crate Queue

Identify workspace crates in deterministic order:

```bash
cargo metadata --no-deps --format-version 1
```

Use package manifest paths from metadata. Skip crates that cannot be built in
the current environment only after recording the exact blocker.

Completion criterion: every workspace package is either queued once or recorded
with a concrete skip reason.

## Step 2: Run The Sieve

For each queued crate, run a focused scan:

```bash
funcvec <crate-dir> --top-k 60 --min-lines 4 --min-tokens 20
```

If the output is dominated by trivial accessors or route wrappers, tighten:

```bash
funcvec <crate-dir> --top-k 80 --min-lines 6 --min-tokens 30 --threshold 0.98
```

When native Nomic is installed and useful for semantic ranking:

```bash
funcvec <crate-dir> --provider nomic --top-k 40 --threshold 0.95
```

Completion criterion: the crate has a saved candidate list in notes or the final
response, including command, candidate count, and the top repeated pattern.

## Step 3: Classify Candidates

Read the full bodies and immediate call sites for each candidate before editing.
Classify each as:

- **Fix**: same behavior is repeated and a small refactor removes real
  maintenance risk.
- **Template**: repeated service/client/DTO/route shape. Fix with a shared
  helper, macro, or generator change only when the pattern repeats enough.
- **Ignore**: accessors, setters, builders, tests, or deliberately parallel
  domain methods where abstraction would hide intent.
- **Defer**: plausible duplication, but public API, generated code, or missing
  tests makes the change too risky for this pass.

Completion criterion: every candidate considered for editing has a classification
and a stated reason tied to code, not just score.

## Step 4: Refactor One Pattern

Pick the highest-payoff **Fix** or **Template** in the current crate.

Before editing, identify:

- the smallest shared abstraction that removes the duplication
- the behavior that must remain identical
- tests that currently cover it, or the focused test to add
- public API and semver impact

Implement the smallest refactor that removes the repeated behavior. Avoid
renaming, reformatting, or moving unrelated code.

Completion criterion: the selected candidate pair or cluster no longer appears
as duplicated implementation after inspection, and no unrelated files changed.

## Step 5: Verify The Crate

Run the narrowest useful checks first:

```bash
cargo fmt --check
cargo test -p <package>
cargo clippy -p <package> --all-targets -- -D warnings
```

If the crate uses feature gates, use the feature set that covers the touched
code. If a check is too broad or blocked by unrelated failures, run a narrower
test and record the blocker.

Re-run `funcvec <crate-dir>` after the fix. The original cluster should either
be gone or reduced to intentional wrappers.

Completion criterion: formatting passes, relevant tests pass, clippy passes or
has a recorded unrelated blocker, and the original funcvec finding is resolved
or explicitly reclassified.

## Step 6: Continue Or Stop

After one verified refactor, decide whether to continue in the same crate:

- Continue if another high-confidence **Fix** remains in the crate.
- Move to the next crate if remaining hits are **Ignore** or **Defer**.
- Stop and report if a refactor changes public API, generated code, or shared
  behavior enough to need user approval.

Completion criterion: every crate processed has one of these outcomes:

- no actionable duplication
- refactor committed or ready to commit
- blocked with exact command/error/context
- deferred with reason and candidate list

## Final Report

Report in this shape:

```markdown
## Crates Scanned
- `<crate>`: <command>, <candidate count>, <outcome>

## Fixes
- `<crate>`: <what duplication was removed>, <files changed>, <tests run>

## Ignored Patterns
- <pattern>: <why abstraction would be worse>

## Deferred
- <candidate>: <why not fixed now>

## Verification
- <commands and results>
```

