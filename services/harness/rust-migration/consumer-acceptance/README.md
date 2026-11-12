# Consumer qualification: digest-valid, semantically invalid Run Contract

## Historical P0 RED (independent consumer counterexample)

At source baseline `6d97f2a08265152a2771addb87877f85e2338c40`, the Rust PostgreSQL reader accepted a complete CAS/Journal/Revision-consistent historical Run whose Contract had an empty `providerId`. The original Python `HarnessRunContract.from_dict` and `PostgresHarnessStore.validate_run_history` rejected it. This proves byte integrity and event graph consistency do **not** imply Run Contract semantic validity.

The falsifier was independently authored as test-only commit `a377fcfe109ff56fcdc1f4ba96f8104fb50f50a6` and cherry-picked into A's isolated worktree as `5990ae6db497`. A actually reran the intentional **RED** on private PostgreSQL 18, Runtime Job `job-01a1c8a4-0e8f-77d2-ada8-2dd4d92a606c` (exit 101): Python rejected the invalid Run, Rust incorrectly accepted it. This is a synthetic **scratch-DB** counterexample, not evidence of production data corruption.

## A's versioned semantic gate: independently reproducible GREEN

The Rust PG reader now calls `contract_semantics::validate_contract` before treating a Run as a valid readback. The validator consumes A's borrowed, sealed canonical representation rather than creating a second JSON representation or a new Writer. It implements Python `HarnessRunContract.from_dict` v1/v2 rules: exact field sets; Python-compatible trimmed identities; bound references and per-list uniqueness; SHA256 digest format; budget and completion object requirements; privacy booleans/content policy; creation/deadline arbitrary-precision integer ordering; v1 correlation/links, and v2's absence of correlation. It uses the mature Rust `jsonschema` Draft 2020-12 meta-schema implementation for explicitly selected structured completion dialects; networking resolvers are disabled.

A true Python 3.15.1 source differential fixture, `crates/harness-pg/tests/contract_source_oracle.py`, compares **306 canonical versions** against the Rust `contract_source_parity.rs` consumer (51 accepted and 255 rejected, exact pass/fail parity). Included cases cover C0 Python strip controls, very wide integers, v1/v2, duplicate and invalid refs, privacy, schema modes and legacy trace context. The unusual Python `schemaVersion=True` acceptance as version 1 is explicitly preserved for historical compatibility.

On fresh disposable PostgreSQL 18.6 the original five Python Store → Rust read-only cases still pass and the deliberate sixth malformed-contract Run is correctly rejected: **RED→GREEN**. Rust test/format/strict Clippy, source differential, PostgreSQL test read-only role INSERT/UPDATE `f|f`, Dependabot ownership seven tests and GitHub repository governance all pass in qualifying Runtime Job `job-01a1c8af-cf78-7461-ab03-fec8e73c5bbc`.

Run the independent PG falsifier in an isolated Linux toolchain with `HARNESS_CONSUMER_FALSIFY_CONTRACT=1 bash services/harness/crates/harness-pg/tests/run_isolated_pg18.sh`. Run the Python source differential with `cargo test --manifest-path services/harness/Cargo.toml --locked --offline -p ordivon-harness-pg --test contract_source_parity -- --nocapture`. The PG harness fixture creates a fresh private cluster under `/tmp` and does not consult production PG DSNs.

## Independent B review of A Contract gate against complete reviewer corpus

A separate isolated A+B integration source uses B's clean Model ToolCall commit
`1fdf10ff55ba7da106f5ae531460dbfbd90fdb58` as its base, then cherry-picks
A's original P0 regression test and complete Contract semantic validator (A
source `5990ae6db497` and `4e543a5d2e19f36b494ce8004083d54e5851bdf2`).
This combines A's **one** canonical/PG implementation with B's Provider v4,
Domain ToolSurface, Model ToolCall and Evidence consumers in the existing
single Cargo workspace; it is **not** another PG Writer.

The B reviewer overlaid the *unmodified final test-only files* from the
independent consumer's original `20a07cfb2cfa9db20c45cc614a230afc8c30fb55`
commit: one disposable-PG fixture, the opt-in Rust test and the runner.
The same 24 SHA256-consistent but semantically invalid Contracts that Rust
previously misaccepted were **all rejected**, while all 10 legitimately
Python-admitted v1/v2 Contracts were **accepted**. Original PG18.6 5/5 still
passed with SELECT-only role (`INSERT/UPDATE=f|f`), and combined root Cargo
fmt/test --locked --offline / strict clippy succeeded. Exact B integration
Runtime job: `job-01a1c8b8-567e-751f-b89b-ec94934c56d5`.

This is independent source-level acceptance of this **finite** corpus and
Cargo compatibility, not full historical-domain equivalence and not original
C-seat signoff. The normal tests skip opt-in PG semantic cases; use the
explicit `HARNESS_CONSUMER_FALSIFY_CONTRACT=1` form above for this gate.

## Qualification limits

The result is **source-only Rust readback qualification** for the tested Python Contract domain. A complete historical Run also requires accurate event payload semantics, Provider/Tool effect lifecycle, privacy exposure, independent consumer acceptance and actual Runtime/Host continuity. Independent agent C has not yet supplied acceptance. Native Rust PG Writer/lease/fence, Provider/Tool dispatch, genuine effect reconciliation and production cutover are **not** implemented or authorized here. Keep the one A-owned GitHub PR #2085 **Draft**, do not merge/deploy based on this test alone.

## R20 — A durable UNKNOWN is not a permanently failed Tool

The cross-owner A+B source-only candidate now distinguishes two independent
properties: a Tool receipt with status UNKNOWN is **terminal for fresh
physical dispatch**, yet its outcome remains epistemically unresolved. The
original Runtime Owner may later identify the same Job by stable
clientRequestId, workspaceId and jobId and supply a determinate
observation through existing task.list/task.observe or workspace.patch.get.
The historical UNKNOWN receipt remains immutable, and a reconciled=true
OBSERVED/REJECTED/CANCELLED successor must bind its predecessor digest and
preserve any known native Job reference. A still-UNKNOWN Owner observation
adds no further receipt and never triggers another workspace.exec or
workspace.patch.

This is one source-level Tool Receipt transition shared by the existing
Python Continuity writer/recovery reader and the Rust B PostgreSQL
read-only consumer. protocol.tool_receipt_successor_allowed is the
Python source predicate; Rust B checks the corresponding versioned
typed Receipt references through A's unchanged single CAS Reader.
No second PG Writer, Journal, Scheduler, Runtime client, Tool registry
or external Effect authority is created.

On private PostgreSQL 18, Python production EventSourcedRunContinuity
builds actual UNKNOWN -> reconciled observed CAS and Journal records;
Rust B accepts that same-source history but rejects CAS-consistent
UNKNOWN -> observed without reconciliation and rejects a forged
change of Runtime Job identity. SQLite tests additionally prove that
a lost initial Runtime response can be reconciled to the original
Job later, that repeated UNKNOWN does not grow the Journal, and that
there is only one physical-call attempt to the fake Runtime interface.

**Scope:** Runtime Owner responses in the bridge tests are controlled
fixtures; the PostgreSQL tests do not send a real Runtime/Provider physical
request. This proves neither exactly-once effects nor production
authorization. A source-qualified prepared Tool Head is still not a
live Dispatch Permit; the Runtime/Provider Owner must prove physical
admission/receipt, and domain consumers must separately validate success.
