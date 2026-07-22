# Rust Review Profile

Load this profile when a PR touches Rust files, Cargo manifests, Rust build
configuration, FFI boundaries, or generated Rust code.

## Context

Inspect the relevant `Cargo.toml` files and note edition, `rust-version` or
MSRV, workspace layout, crate type, feature flags, lint settings, and major
dependencies such as `tokio`, `serde`, `thiserror`, `anyhow`, `tracing`, `clap`,
database clients, and HTTP clients.

Read changed Rust files directly, not only the diff. For serious findings, read
the whole function, trait impl, module, unsafe block, or public API around the
changed line. Inspect nearby helpers, error types, test style, call sites, and
feature-gated paths.

Prefer project commands from repo docs or CI. Common checks are:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-features
cargo check --all-targets
cargo test --doc
```

For large workspaces, narrow to the affected package and relevant feature set.
If checks fail, distinguish existing failures from failures caused by the PR.

## Review Priorities

- Correctness: behavior changes, panics on external input, error swallowing,
  ordering/filtering/retry changes, overflow, path traversal, UTF-8 assumptions,
  partial reads/writes, cancellation, rollback, feature flags, and compatibility.
- Ownership: prefer `&str`, `&[T]`, and `&Path` over `&String`, `&Vec<T>`, and
  `&PathBuf` when only reading. Flag avoidable clones, early ownership, broad
  `'static` bounds, and APIs that force allocation.
- Errors: prefer `Result`, `?`, typed library errors, and contextual app-boundary
  errors. Flag production `unwrap`/`expect`, panic paths in libraries, string
  errors where callers need structure, and discarded diagnostics.
- Simplicity: prefer early returns, `let else`, `?`, `ok_or_else`, `transpose`,
  `flatten`, `matches!`, `entry`, `retain`, `strip_prefix`, `split_once`, and
  `Option::take` when they preserve behavior and clarity.
- APIs and traits: prefer narrow visibility, cohesive traits, `From`/`TryFrom`,
  newtypes for validated values, `#[must_use]` on meaningful returns, sealed
  traits where external impls would be a compatibility trap, and generics or
  `impl Trait` when dynamic dispatch is not needed.
- Async/concurrency: flag locks held across `.await`, blocking I/O in async
  code, ignored `JoinHandle`s, unbounded channels, missing cancellation/timeout
  behavior, lock ordering risks, and accidental serialization or concurrency.
- Performance: flag repeated allocation in loops, needless `format!`, one-use
  `Vec` collections, repeated parser construction, avoidable O(n^2), large
  clones, hot-path locks, and repeated filesystem/network calls.
- Unsafe: read the full safe wrapper and unsafe block. Verify aliasing,
  lifetimes, initialization, alignment, provenance, panic safety, `Send`/`Sync`,
  layout assumptions, and required `// SAFETY:` comments.
- Serialization and compatibility: check `serde`, wire formats, config, CLI,
  database rows, public structs, renamed fields, defaults, skipped fields, enum
  representation, unknown fields, optionality, and stable ordering.
- Tests: expect coverage for happy path, error path, empty input, boundaries,
  malformed input, timeout/cancellation, serialization compatibility, public API
  examples, feature-specific behavior, and bug regressions.

## Comment Style

Prefer concrete fixes over vague advice. Do not nitpick formatting handled by
`rustfmt` or Clippy. Do not suggest broad refactors unless the diff introduced
the problem. Do not remove error handling, logging, metrics, or user-facing
behavior just to make code shorter.

Good comments identify the exact ownership, error, async, unsafe, or behavior
problem and explain why the suggested replacement preserves behavior.

