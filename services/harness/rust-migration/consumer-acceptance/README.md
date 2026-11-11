# Consumer qualification: digest-valid, semantically invalid Run Contract

## Historical P0 RED (independent consumer counterexample)

At source baseline `6d97f2a08265152a2771addb87877f85e2338c40`, the Rust PostgreSQL reader accepted a complete CAS/Journal/Revision-consistent historical Run whose Contract had an empty `providerId`. The original Python `HarnessRunContract.from_dict` and `PostgresHarnessStore.validate_run_history` rejected it. This proves byte integrity and event graph consistency do **not** imply Run Contract semantic validity.

The falsifier was independently authored as test-only commit `a377fcfe109ff56fcdc1f4ba96f8104fb50f50a6` and cherry-picked into A's isolated worktree as `5990ae6db497`. A actually reran the intentional **RED** on private PostgreSQL 18, Runtime Job `job-01a1c8a4-0e8f-77d2-ada8-2dd4d92a606c` (exit 101): Python rejected the invalid Run, Rust incorrectly accepted it. This is a synthetic **scratch-DB** counterexample, not evidence of production data corruption.

## A's versioned semantic gate: independently reproducible GREEN

The Rust PG reader now calls `contract_semantics::validate_contract` before treating a Run as a valid readback. The validator consumes A's borrowed, sealed canonical representation rather than creating a second JSON representation or a new Writer. It implements Python `HarnessRunContract.from_dict` v1/v2 rules: exact field sets; Python-compatible trimmed identities; bound references and per-list uniqueness; SHA256 digest format; budget and completion object requirements; privacy booleans/content policy; creation/deadline arbitrary-precision integer ordering; v1 correlation/links, and v2's absence of correlation. It uses the mature Rust `jsonschema` Draft 2020-12 meta-schema implementation for explicitly selected structured completion dialects; networking resolvers are disabled.

A true Python 3.15.1 source differential fixture, `crates/harness-pg/tests/contract_source_oracle.py`, compares **306 canonical versions** against the Rust `contract_source_parity.rs` consumer (51 accepted and 255 rejected, exact pass/fail parity). Included cases cover C0 Python strip controls, very wide integers, v1/v2, duplicate and invalid refs, privacy, schema modes and legacy trace context. The unusual Python `schemaVersion=True` acceptance as version 1 is explicitly preserved for historical compatibility.

On fresh disposable PostgreSQL 18.6 the original five Python Store → Rust read-only cases still pass and the deliberate sixth malformed-contract Run is correctly rejected: **RED→GREEN**. Rust test/format/strict Clippy, source differential, PostgreSQL test read-only role INSERT/UPDATE `f|f`, Dependabot ownership seven tests and GitHub repository governance all pass in qualifying Runtime Job `job-01a1c8af-cf78-7461-ab03-fec8e73c5bbc`.

Run the independent PG falsifier in an isolated Linux toolchain with `HARNESS_CONSUMER_FALSIFY_CONTRACT=1 bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh`. Run the Python source differential with `cargo test --manifest-path services/harness/Cargo.toml --locked --offline -p ordivon-harness-pg --test contract_source_parity -- --nocapture`. The PG harness fixture creates a fresh private cluster under `/tmp` and does not consult production PG DSNs.

## Qualification limits

The result is **source-only Rust readback qualification** for the tested Python Contract domain. A complete historical Run also requires accurate event payload semantics, Provider/Tool effect lifecycle, privacy exposure, independent consumer acceptance and actual Runtime/Host continuity. Independent agent C has not yet supplied acceptance. Native Rust PG Writer/lease/fence, Provider/Tool dispatch, genuine effect reconciliation and production cutover are **not** implemented or authorized here. Keep the one A-owned GitHub PR #2085 **Draft**, do not merge/deploy based on this test alone.

## Second independent consumer matrix (2026-11-11)

The independent extra reviewer (not the original C-seat) extended the standalone scratch-PG falsifier with **24 genuinely Python-rejected Contracts** and **10 genuinely Python-valid v1/v2 Contracts**, each persisted through the genuine Python Store and then read with the SQL SELECT-only Rust role. The reviewer saw 24/24 wrong Rust acceptances at the old baseline; A integrated the *same underlying test scripts*, without rewriting their oracle, on top of the reviewed full semantic gate.

The independent matrix was imported as reviewed test/docs-only commits (original source commits `94bee564`, `8529c233`, `20a07cfb`), with this document retaining the newer A RED→GREEN chronology. In the new isolated A workspace, all **24 negative cases are correctly rejected** by the Rust Reader and all **10 positive current/legacy cases are accepted**, while original scratch PG tests remain **5/5** green. True PG18, Python validity checks, Cargo fmt/test --locked --offline --workspace --all-targets and strict Clippy all passed. Runtime Job: `job-01a1c8b6-b76a-7587-b91e-5c755d2a8e7b`.

Use the same opt-in scratch command shown above. In the updated corpus the opt-in Rust test executable runs `rejects_digested_but_semantically_invalid_legacy_contracts` and `accepts_source_valid_versioned_legacy_and_current_contracts`. Do not interpret the Rust test count as 24+10 individual Rust test functions: the two functions iterate over 34 independently constructed Python Store runs.

This extends source-only compatibility evidence; it does not authorize Provider/Tool execution, PG Writer replacement, model-visible content disclosure, production migration or automatic completion.
