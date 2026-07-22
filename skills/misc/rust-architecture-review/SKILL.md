---
name: rust-architecture-review
description: Review Rust codebase architecture and recommend improvements. Use when the user asks to assess Rust crate or module structure, public surfaces, trait/interface depth, coupling, testability, ownership leaks, async boundaries, unsafe isolation, or refactoring opportunities that make Rust code easier to reason about and verify.
---

# Rust Architecture Review

Review Rust architecture for deep modules: small, honest interfaces with useful
behavior behind them. The default output is a chat-only Markdown report. Do not
edit files, create tasks, create Linear issues, write reports to disk, or open
browser artifacts unless the user separately asks.

## Vocabulary

Use these words consistently in findings:

- **Module**: anything with an interface and an implementation. In Rust this can
  be a crate, `mod`, type, trait, function, or vertical slice.
- **Interface**: everything callers must know to use the module correctly. In
  Rust this includes `pub` items, trait bounds, feature-gated APIs, error
  contracts, ownership and lifetime obligations, async and `Send`/`Sync`
  expectations, allocation behavior, and panic behavior.
- **Implementation**: the code behind the interface.
- **Depth**: leverage at the interface. A **deep** module hides meaningful
  behavior behind a small interface. A **shallow** module exposes nearly as much
  complexity as it contains.
- **Seam**: where behavior can vary without editing callers.
- **Adapter**: concrete code that satisfies an interface at a seam.
- **Leverage**: what callers get from depth.
- **Locality**: what maintainers get from depth: changes, bugs, and verification
  concentrated in one place.

Principles:

- **Deletion test**: if deleting a module makes complexity disappear, it was
  pass-through. If complexity reappears across callers, the module was earning
  its keep.
- **The interface is the test surface**: tests should prove behavior through the
  same surface callers use.
- **One adapter is hypothetical. Two adapters are real**: avoid trait seams when
  only one concrete implementation exists, unless a test or platform adapter is
  genuinely different.

## Explore

Start by reading project rules and architectural context when present:

- `AGENTS.md`, `CLAUDE.md`, `TARGET.md`, `CONTEXT.md`
- `docs/adr/`, architecture docs, design notes
- `Cargo.toml`, workspace manifests, crate manifests
- `rust-toolchain.toml`, `.cargo/config.toml`
- `clippy.toml`, `deny.toml`
- `justfile`, `Makefile`, CI workflows

Then inspect the Rust shape:

- discover workspace members and binary/library crates
- map important `src/lib.rs`, `src/main.rs`, `mod.rs`, and top-level modules
- inspect `pub`, `pub(crate)`, re-exports, feature gates, and trait surfaces
- trace callers for suspected shallow modules with `rg`
- inspect tests and integration-test entry points
- note semver constraints for library crates and deployment constraints for
  binary/internal crates

Do not mutate repository state during review.

## Rust Review Lens

Look for architecture friction that Rust makes visible:

- **Public surface sprawl**: too many exported types, helpers, or re-exports for
  callers to assemble correctly.
- **Trait overuse**: traits created for one implementation, mocking only, or
  speculative extension.
- **Concrete-type leakage**: callers forced to know storage, transport,
  allocation, locking, or serialization details.
- **Ownership leakage**: awkward lifetimes, borrowed data, clones, or `Arc`
  usage pushed onto callers because the module shape is wrong.
- **Concurrency leakage**: `Arc<Mutex<_>>`, channels, task handles, or lock
  ordering escaping into call sites.
- **Async leakage**: async boundaries chosen because internals are async, not
  because callers need an async interface.
- **Error leakage**: callers matching internal error details, using `anyhow`
  where typed errors are part of the contract, or exposing typed errors where
  callers cannot act on them.
- **Panic contracts**: production or library paths using `unwrap`, `expect`, or
  panic where callers need recoverable errors.
- **Unsafe spread**: `unsafe` code not isolated behind a narrow checked module,
  or missing `SAFETY` comments at the operation.
- **Feature-flag coupling**: callers forced to mirror internal feature
  combinations or conditional types.
- **Test-only extraction**: small functions/modules created only so tests can
  reach internals while the real behavior remains untested at the interface.
- **Hot-path cost leakage**: clones, allocations, boxing, dynamic dispatch, or
  serialization forced by a shallow interface.

Apply the deletion test to each suspect module. Prefer recommendations that
delete shallow wrappers or absorb scattered logic into one deeper module.

## Deepening Guidance

Choose the smallest refactor that improves leverage and locality.

- For in-process logic, collapse shallow modules and test through the new public
  or `pub(crate)` interface.
- For local-substitutable dependencies, keep the external interface concrete and
  test with the local substitute when available.
- For owned remote dependencies, use a port only when the production adapter and
  test adapter differ in real behavior.
- For third-party dependencies, hide the vendor contract behind a narrow module
  that returns domain-level outcomes.
- For binary/internal crates, prefer aggressive `pub(crate)` cleanup.
- For public library crates, preserve semver or explicitly mark proposed
  breaking changes.
- Prefer concrete types until real variation justifies a trait.
- Keep internal seams private to the implementation unless callers genuinely
  need variation.

Do not recommend broad rewrites. Recommend staged refactors that can be proven
with tests and reviewed incrementally.

## Report Format

Return a concise Markdown report in chat:

If no findings are found, say that clearly and omit empty sections.

```markdown
## Summary
- <one to three bullets on the architecture shape>

## Findings

### [<Severity>] <Title>
Confidence: <High|Medium|Low>
Files: `<path>`, `<path>`

Problem:
<what hurts and where complexity leaks>

Proposed refactor:
<specific module/interface change>

Rust notes:
<ownership, errors, async, traits, unsafe, semver, allocation, or test impact>

Tests:
- <behavior to prove through the interface>

Depth/locality:
<why the result hides more behavior or concentrates change>

## Speculative Candidates
- <only low-confidence ideas worth later exploration>

## Top Recommendation
<the first change to make and why>

## Optional Follow-up Plan
- <small ordered implementation steps if useful>
```

Severity:

- `Critical`: correctness, data loss, security, undefined behavior, or production
  panic/unwrap risk caused by architecture.
- `Major`: coupling, testability, public surface, error, async, or ownership
  problems likely to slow or break future work.
- `Minor`: cleanup that improves locality or clarity but is not urgent.

Confidence:

- `High`: directly supported by code and callers.
- `Medium`: supported by patterns but needs implementer confirmation.
- `Low`: plausible but not enough evidence for a finding; put these under
  Speculative Candidates.

## Guardrails

- Do not propose trait extraction just for mocking.
- Do not add a seam with one real adapter unless a second adapter is justified.
- Do not treat a Rust trait as the only form of interface.
- Do not recommend changing public library APIs without calling out semver
  impact.
- Do not delete shallow unit tests until replacement behavior tests exist.
- Do not present style preferences as architecture findings.
- Do not re-litigate ADRs unless current friction is strong enough to justify
  reopening the decision.
- Do not invent domain names when `CONTEXT.md` or docs already define them.

## When Asked To Design The Refactor

If the user picks a finding and asks for an implementation design, produce two
or three alternative Rust interfaces before recommending one:

- minimal interface: few entry points, maximum leverage
- caller-optimized interface: common case is trivial
- adapter-based interface: only when real variation exists

For each alternative, show:

- proposed types/functions/traits
- caller example
- hidden implementation details
- error and panic contract
- testing strategy
- semver or migration impact
