---
name: rust-pr-review
description: >
  Review a Rust PR, branch, or local diff against main. Focus on correctness,
  smaller code, idiomatic Rust, ownership, error handling, unnecessary clones,
  needless allocation, async safety, tests, and maintainability.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Rust PR Review

Use this skill when asked to review a Rust pull request, branch, patch, or local diff.

The job is to review changed code against `main`, then report only findings that are worth the author's time.

Prefer concrete fixes. Avoid style churn.

## What this skill optimizes for

Review the diff as a Rust reviewer.

Prefer feedback that makes the code:

- correct
- smaller without becoming clever
- more idiomatic Rust
- easier to reason about
- safer around ownership, lifetimes, errors, and async boundaries
- cheaper in allocations, clones, locks, and repeated work
- better covered by tests

Do not nitpick formatting. Let `rustfmt` and Clippy handle mechanical style.

Do not optimize for fewer lines by itself. Optimize for code that preserves behavior, reduces complexity, and is harder to misuse.

## Scope

Review only changed code and the surrounding context needed to understand it.

Do not rewrite unrelated files.
Do not suggest broad architecture changes unless the diff introduced the problem.
Do not ask for refactors outside the touched area unless they are required for correctness or safety.
Do not change tests to make a refactor pass.
Do not remove error handling, logging, metrics, or user-facing behavior just to make code shorter.

When in doubt, prefer a small targeted comment over a broad rewrite.

## Step 1: Identify the review target

For a local branch:

```bash
git status --short
git branch --show-current
git diff --stat main...HEAD
git diff main...HEAD
git log --oneline main..HEAD
```

If `main...HEAD` is empty, check staged and unstaged changes:

```bash
git diff --staged --stat
git diff --staged
git diff --stat
git diff
```

If `main` is missing, inspect remotes and choose the likely base:

```bash
git remote -v
git branch -a
git merge-base origin/main HEAD 2>/dev/null || git merge-base origin/master HEAD
```

If the repository uses `master` instead of `main`, compare against `master`.

For a GitHub PR, prefer a separate worktree or read-only checkout. Do not switch the user's current branch unless explicitly asked.

Useful PR commands when `gh` is available:

```bash
gh pr view --json title,body,baseRefName,headRefName,author,commits,files
gh pr diff
gh pr checks
```

## Step 2: Get Rust context

Before making findings, inspect the Rust project shape:

```bash
find . -name Cargo.toml -maxdepth 4
```

Read the relevant `Cargo.toml` files and note:

- Rust edition
- `rust-version` / MSRV, if present
- workspace layout
- crate type: library, binary, proc macro, test helper, example
- relevant features
- lint settings
- major dependencies: `tokio`, `serde`, `thiserror`, `anyhow`, `tracing`, `clap`, database clients, HTTP clients

Read the changed files directly, not just the diff.

For any serious finding, read the whole function, trait impl, module, or unsafe block around the changed line.

Also inspect nearby code for:

- existing helper functions
- existing error types
- established naming patterns
- existing test style
- public API call sites
- feature-gated code paths

## Step 3: Run deterministic checks when practical

Prefer the project's own commands first. Check README, CI config, `justfile`, `Makefile`, `.github/workflows`, `xtask`, or repo docs for canonical commands.

Common Rust checks:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-features
```

For workspaces, narrow the package if the full workspace is too large:

```bash
cargo clippy -p <package> --all-targets --all-features -- -D warnings
cargo test -p <package> --all-features
```

If all features are impossible because of mutually exclusive features, use the feature set relevant to the changed crate.

Other useful checks:

```bash
cargo check --all-targets
cargo test -p <package> <test_name>
cargo test --doc
cargo bench --no-run
```

If checks fail, distinguish existing failures from failures caused by the diff.

Do not bury compiler or Clippy findings under speculative review comments. Deterministic tool output comes first.

## Step 4: Review priorities

### 1. Correctness

Look for:

- behavior changes not covered by tests
- panics on user input, config, filesystem, network, or parsed data
- silent error swallowing
- changed ordering, filtering, retries, deduping, or default behavior
- overflow, truncation, sign conversion, and lossy casts
- path handling problems
- UTF-8 assumptions
- partial writes, partial reads, cancellation, cleanup, and rollback bugs
- serialization/deserialization compatibility changes
- public API behavior changes without migration notes or tests
- feature flag behavior changes
- concurrency behavior that differs between single-threaded and multi-threaded runtimes
- nondeterminism introduced into tests or production behavior

Examples worth flagging:

```rust
let value = input.parse::<u64>().unwrap();
```

If `input` can come from a file, CLI, network, environment variable, or user input, this should return an error with context.

```rust
let path = base.join(user_supplied);
```

If `user_supplied` can contain absolute paths or `..`, this may escape `base`.

### 2. Idiomatic ownership and borrowing

Prefer:

- `&str` over `&String`
- `&[T]` over `&Vec<T>`
- `&Path` over `&PathBuf`
- borrowed parameters when the function only reads
- owned parameters when the function stores, consumes, or transfers ownership
- moving values instead of cloning when ownership is already available
- `Cow<'a, str>` or `Cow<'a, [T]>` when ownership is conditional
- `Arc<T>` only when shared ownership is real
- `Rc<T>` for single-threaded shared ownership, if already used and appropriate
- lifetime elision when explicit lifetimes add no useful information

Flag:

- `.clone()` used only to appease the borrow checker
- `.to_string()` / `.to_owned()` on hot or repeated paths
- cloning inside loops
- collecting into `Vec` just to iterate once
- taking `String`, `PathBuf`, or `Vec<T>` when a borrow would work
- broad `'static` bounds used to dodge lifetime design
- unnecessary lifetime parameters
- APIs that force callers to allocate
- converting borrowed data to owned data too early

Good comment:

```md
This takes `String`, but the function only reads it. Taking `&str` avoids forcing callers to allocate and still lets existing `String` callers pass `name.as_str()`.
```

### 3. Error handling

Prefer:

- `Result<T, E>` for expected failures
- `?` for propagation
- `thiserror` for library error types
- `anyhow` / `eyre` at app boundaries, if already used
- `.with_context(...)` or equivalent at I/O, parse, network, and config boundaries
- `ok_or_else` / `map_err` when errors need construction or context
- typed errors when callers need to branch on failure kind

Flag:

- production `unwrap`
- production `expect` on recoverable failure
- panic paths in library code
- string errors where callers need structure
- errors logged and then discarded
- `map_err(|_| ...)` that destroys useful diagnostics
- returning `Option` when the caller needs to know why something failed
- using `anyhow::Error` deep inside reusable library APIs when a typed error would be better

Acceptable uses of `unwrap` / `expect`:

- tests
- examples where failure would obscure the example
- constants or invariants that cannot fail, with a clear explanation
- code where the invariant is already checked immediately before

Even then, prefer comments that explain the invariant.

### 4. Smaller and clearer code

Suggest simplifications when they preserve behavior.

Good simplifications:

- early returns instead of deeply nested branches
- delete dead branches and unused helpers
- merge duplicate match arms
- replace manual `Option` / `Result` plumbing with `?`, `ok_or_else`, `map`, `map_err`, `transpose`, `flatten`, or `is_some_and`
- remove intermediate `Vec`s when an iterator can flow directly
- use `entry()` for map insert/update logic
- use `then_some` / `then` for simple conditional values
- use `matches!` for simple enum checks
- use `let Some(x) = ... else { ... };` when it makes the happy path clearer
- use `strip_prefix`, `strip_suffix`, `split_once`, or `rsplit_once` instead of manual indexing
- use `retain` instead of rebuilding a collection when mutating in place is clearer
- use `mem::take` or `Option::take` when moving out of a field intentionally

Bad simplifications:

- dense iterator chains that hide stateful logic
- clever one-liners
- removing error context
- changing user-facing strings, logs, metrics, or serialized output unless asked
- changing tests to fit a refactor
- refactoring unrelated code
- replacing a clear loop with an iterator chain that needs side effects and mutation anyway

Example useful simplification:

```rust
let Some(config) = maybe_config else {
    return Ok(None);
};

let value = parse_config(config)?;
Ok(Some(value))
```

This is often clearer than nested `match` when the happy path is the main path.

### 5. Traits and APIs

Prefer:

- small, cohesive traits
- `From` for infallible conversions
- `TryFrom` for fallible conversions
- newtypes for domain identifiers and validated values
- `#[must_use]` on builders and meaningful return values
- `pub(crate)` before `pub`
- sealed traits when external impls would be a breaking-compatibility trap
- `impl Trait` or generics when dynamic dispatch is not needed
- `Box<dyn Trait>` only when runtime heterogeneity or object safety is actually needed
- explicit ownership semantics in names and signatures

Flag:

- primitive obsession in public APIs
- public fields that should be invariant-protected
- blanket trait bounds wider than needed
- needless `Send + Sync + 'static`
- `Deref` used as inheritance
- APIs that force allocation on callers
- public APIs that expose implementation details
- trait methods that make the trait impossible to object-safe without need
- unnecessary generic parameters that leak complexity into callers

Examples:

```rust
fn read_config(path: &Path) -> Result<Config>
```

is usually better than:

```rust
fn read_config(path: PathBuf) -> Result<Config>
```

when the function only reads the path.

```rust
pub(crate) struct Parser
```

is better than `pub struct Parser` unless downstream crates need it.

### 6. Async and concurrency

Look for:

- holding `MutexGuard`, `RwLockGuard`, or borrowed state across `.await`
- blocking I/O in async functions
- unbounded channels without a reason
- spawned tasks with ignored `JoinHandle`s
- cancellation paths that leak work or lose errors
- use of `std::sync::Mutex` in async hot paths
- lock ordering problems
- retries without backoff or cancellation
- `select!` branches that drop important futures unexpectedly
- async functions that never yield in long loops
- accidentally serial work where concurrency was intended
- accidentally concurrent work where ordering matters

Prefer:

- small lock scopes
- clone/move before `.await` when it releases a lock
- `tokio::task::spawn_blocking` for blocking work
- `try_join!` when failures should short-circuit
- `JoinSet` when managing many tasks
- bounded channels unless unbounded growth is intentional
- cancellation-safe APIs where needed
- explicit timeouts for network calls when the project uses timeouts elsewhere

Example issue:

```rust
let mut state = self.state.lock().await;
let response = self.client.fetch().await?;
state.last_response = Some(response);
```

The lock is held during network I/O. Prefer fetching outside the lock, then locking only to update state.

### 7. Performance and allocation

Only raise performance issues that are visible from the code or relevant to the changed path.

Look for:

- repeated allocation in loops
- needless `format!`
- `collect::<Vec<_>>()` only to iterate
- repeated regex/parser construction
- O(n²) scans introduced in changed code
- avoidable string copies
- large enum variants
- missing `with_capacity` when size is known
- avoidable locks on hot paths
- cloning large structs
- repeated filesystem or network calls inside loops
- using `contains` on a `Vec` in repeated membership checks where a `HashSet` would be clearer and cheaper

Prefer:

- `with_capacity` when size is known
- `entry()` for map insert/update
- lazy iterators without intermediate collections
- `write!` into an existing buffer instead of repeated `format!` in hot paths
- references and slices for zero-copy paths
- caching compiled regexes or parsers when construction is expensive

Do not request micro-optimizations without a concrete reason.

### 8. Unsafe

For any changed `unsafe`:

- read the full unsafe block and safe API around it
- identify the safety invariant
- check aliasing, lifetimes, initialization, alignment, provenance, and panic safety
- verify the safe wrapper prevents misuse
- require a `// SAFETY:` comment that explains why the block is valid

Unsafe issues are blocking when the invariant is wrong or unenforced.

Look for:

- invalid pointer casts
- unchecked indexing without a proven bound
- assuming layout without `repr(...)`
- incorrect `Send` / `Sync` impls
- creating references to uninitialized or aliased memory
- panic paths that leave data structures invalid
- safe APIs that allow callers to violate the unsafe invariant

### 9. Serialization and compatibility

For changes involving `serde`, wire formats, config, CLI args, database rows, or public structs, check:

- renamed fields
- default behavior
- skipped fields
- enum representation
- backward compatibility
- migration behavior
- unknown-field handling
- optional vs required fields
- stable ordering when output is compared or cached

Flag changes that break existing users without tests or migration notes.

### 10. Tests

Check whether changed behavior has tests.

Look for:

- happy path
- error path
- empty input
- boundary values
- malformed input
- async timeout/cancellation
- serialization compatibility
- public API examples or doctests
- feature-specific behavior
- regression tests for fixed bugs

Prefer behavior-focused test names:

```rust
returns_error_when_config_file_is_missing
does_not_retry_after_permanent_failure
preserves_existing_order_when_deduping
```

Flag tests that:

- assert implementation details instead of behavior
- rely on wall-clock timing without control
- depend on test order
- use real network services unless explicitly integration tests
- use broad snapshots that will churn constantly
- only test the new happy path when error behavior changed

## Severity

Use these buckets.

### Blocking

Only for issues that can break correctness, safety, security, data integrity, public API compatibility, or production behavior.

Examples:

- panic on external input
- unsound unsafe
- data loss
- race condition
- swallowed critical error
- test or build failure caused by the PR
- public API break in a library crate without versioning or migration plan
- security-sensitive path, auth, permission, or parsing bug

### Important

Should fix before merge unless there is a good reason.

Examples:

- unnecessary clone in a hot path
- missing error context at an important boundary
- public API forces allocation
- fragile async cancellation
- missing tests for changed behavior
- confusing ownership API
- duplicated code that already caused inconsistent behavior
- avoidable O(n²) behavior on expected input sizes

### Nice-to-have

Small idiom, cleanup, or maintainability improvements.

Examples:

- `&String` could be `&str`
- duplicated branches
- minor iterator cleanup
- `entry()` would simplify map update logic
- a small helper would remove repeated parsing code
- a test name could be more behavior-focused

Do not inflate severity. Many Rust idiom comments are nice-to-have unless they affect API design, correctness, or likely performance.

## Output format

Start with the result:

```md
Verdict: approve | approve with nits | changes requested
```

Use `changes requested` only when there is at least one blocking issue or an important issue that should clearly block merge.

Then use this structure:

````md
### Blocking

- `path/to/file.rs:123` — Title
  What is wrong.
  Why it matters.
  Suggested change:

  ```rust
  // replacement
  ```

### Important

- `path/to/file.rs:456` — Title
  What is wrong.
  Why it matters.
  Suggested change:

  ```rust
  // replacement
  ```

### Nice-to-have

- `path/to/file.rs:789` — Title
  Small cleanup or idiom suggestion.

### Things I would not change

Mention tempting rewrites that are not worth doing.

### Checks

- `cargo fmt --check`: pass/fail/not run
- `cargo clippy --all-targets --all-features -- -D warnings`: pass/fail/not run
- `cargo test --all-features`: pass/fail/not run
````

If there are no findings in a section, write `None`.

## Comment style

Be specific.

Bad:

```md
This is not idiomatic Rust.
```

Good:

```md
This takes `String`, but the function only reads it. Taking `&str` avoids forcing callers to allocate.
```

Bad:

```md
Can this be simpler?
```

Good:

```md
Both branches parse the same value and only differ in the fallback. Pulling the parse before the branch removes the duplicate error path.
```

Bad:

```md
Use iterators.
```

Good:

```md
This `collect::<Vec<_>>()` is only used by the next `for` loop. Keeping the iterator lazy avoids an allocation and removes the temporary vector.
```

Prefer patches over vague advice.

Do not report uncertain issues. If it might be a problem but you cannot prove it from the diff and surrounding code, put it under “Nice-to-have” or skip it.

## Suggested patch style

When suggesting code, keep the patch minimal.

Good:

```rust
fn normalize_name(name: &str) -> String {
    name.trim().to_ascii_lowercase()
}
```

Do not rewrite the whole module unless the bug requires it.

When changing signatures, mention likely call-site impact.

When suggesting a more idiomatic construct, include the exact replacement and why it preserves behavior.

## Rust idiom checklist

Use this checklist during review:

- Can owned parameters become borrowed parameters?
- Can `&String`, `&Vec<T>`, or `&PathBuf` become `&str`, `&[T]`, or `&Path`?
- Are there unnecessary `.clone()`, `.to_string()`, `.to_owned()`, or `format!` calls?
- Is a `Vec` collected only to be iterated once?
- Can nested `match` / `if let` become `?`, `let else`, `transpose`, `flatten`, or early returns?
- Is `unwrap` or `expect` reachable from production input?
- Are errors preserving enough context?
- Are trait bounds narrower than necessary?
- Is visibility narrower than necessary?
- Is dynamic dispatch actually needed?
- Are locks held across `.await`?
- Are blocking calls inside async code?
- Are spawned tasks observed, cancelled, or joined?
- Are unsafe invariants documented and enforced by the safe API?
- Are tests covering error behavior, not just the happy path?
- Did the PR change serialization, CLI, config, or public API compatibility?

## Non-goals

Do not:

- run large unrelated refactors
- debate formatting choices handled by `rustfmt`
- suggest nightly-only APIs unless the project already uses nightly
- suggest dependencies for tiny helpers
- change MSRV assumptions without checking `rust-version`
- remove explicit code just because it is longer
- replace simple loops with complex iterator chains
- make user-facing behavior change as part of cleanup
- turn every `String` into `Cow` by default
- turn every trait object into generics by default
- turn every clone into lifetime complexity

The best review is small, accurate, and easy for the author to apply.
