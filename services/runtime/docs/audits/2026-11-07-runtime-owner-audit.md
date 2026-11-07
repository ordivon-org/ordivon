---
schema_version: 1
id: runtime.owner-audit-2026-11-07
title: Runtime Owner Audit 2026-11-07
type: reference
profile: engineering
lifecycle: active
source_role: canonical
visibility: internal
owners:
  - ordivon-runtime
audience:
  - operator
  - builder
  - agent
updated: 2026-11-07
summary: Observed Runtime directory inventory, current/legacy backend distinction, cleanup classification, and LEGO convergence plan.
evidence_status: observed
readiness: REVIEW
applies_to:
  - ordivon-runtime
related:
  - runtime.model
  - runtime.operations
---
# Runtime Owner Audit — 2026-11-07

## Scope and evidence standing

Audited the source tree at Linux commit `f52091fb1c8f920b7114c813142d1e7795ae8664` in isolated Workspace `ws-gpt6-runtime-owner-audit-20261107-r1`. Windows read-only comparison used commit `73196dc2bc076f148e905b688fafa34d40486a9c`. Findings are **time-scoped source and service observations**, not installed release acceptance. No system data was deleted.

Linux tracked directory census: `crates` 125 files (~3.10 MB), `research` 132 (~1.53 MB), `scripts` 62 (~1.53 MB), `docs` 24 (~0.39 MB), `planning` 8 (~0.15 MB), `formal` 14 (~0.07 MB), `platform` 3 (~0.18 MB), `packaging` 11 (~0.03 MB). File counts exclude untracked/ignored working data. Code scans found 24 tracked files referencing `registry.sqlite3` and 15 referencing `rusqlite` (scans included docs/tests where indicated).

Linux service inspection found `ordivon-runtime.service` and `ordivon-runtime-pg-candidate.service` active together, with service main PIDs 133847 and 6026 in the sampled read-only state. Windows showed `OrdivonRuntimeR6Candidate`, `OrdivonRuntimePrivilegedBroker`, and `OrdivonRuntimePostgreSQL18` active. A running PostgreSQL server does not itself prove the Windows Runtime Registry uses PostgreSQL. The old Linux file `/var/lib/ordivon/registry/registry.sqlite3` existed and measured exactly 6,166,085,632 bytes; this is a priority retirement candidate, **not** yet approved for physical deletion because the legacy service is still running. `/var/lib/ordivon` is shared with other Owners. No installed backend or data was changed in this audit.

## Directory-by-directory disposition

| Directory | Current role | Decision / next proof |
| --- | --- | --- |
| `crates/ordivon-runtime-core/src/runtime/engine/` | admission, execution, reconciliation, terminal commit | KEEP; inspect cross-module state dependencies before additional extraction |
| `crates/ordivon-runtime-core/src/runtime/registry/` | SQLite-oriented durable lifecycle | RETIRE-CANDIDATE after complete PG consumer cutover; do not keep dual truth |
| `crates/ordivon-runtime-core/src/pg_*.rs`, `runtime/pg_runtime.rs` | PG admission/readback/native execution vertical | PROMOTE-CANDIDATE; verify installed writer, restart, recovery, cancellation, evidence |
| `crates/ordivon-runtime-core/src/universal/` | reusable runner, source state, filesystem and workspace operations | KEEP; identify reusable independent seams, avoid name-only crate splits |
| `crates/ordivon-runtime-core/src/bin/` | runner, doctor, inspect, repair, Windows deploy and fixtures | AUDIT every binary's build/packaging consumer; keep only qualified owner paths |
| `crates/ordivon-runtime-mcp/src/server/` | transport, schemas, auth, tool adapter | KEEP; thin transport, no second execution state |
| `platform/windows/` | native Windows launcher/broker/fixture | KEEP; tests and installed launcher identities are release consumers |
| `packaging/systemd/`, `packaging/windows/` | managed services and policies | KEEP; compare current installed service units before retiring configurations |
| `scripts/` | owner operation wrappers, tests, deployment, backup | KEEP selectively; find duplicate backends and dead scripts by exact call sites |
| `tests/` | real-system/Windows/contract verification | KEEP if they falsify active contracts; do not judge by rarity of failure |
| `formal/` | TLA+ state models and trace checks | KEEP verified consumers; label model version and scope; UNKNOWN is not PASS |
| `standards/` | owner-native standard representation | KEEP as candidate until generator/consumer and freshness validation |
| `research/` | formal foundations, owner roles, provenance | KEEP canonical entry + referenced historical proof; distinguish history from active authority |
| `planning/` | LEGO plans, inventories, prior release stages | CLASSIFY as active/closed/superseded; do not treat roadmap as source of current binary truth |
| `docs/` | operational and user-facing contract | FIX stale backend truth, remove ambiguous current-status claims |
| `evidence/` | previous integration receipts | KEEP when actual tests/docs reference them; otherwise prefer verified Git history |
| `examples/` | finite demo | KEEP only if demo acceptance still consumes it |
| `.github/`, `.ordivon/` | automation, ownership and publication | KEEP while release and CI consumers remain |
| root Cargo, Python, toolchain configs | build and pinning | KEEP while build consumers remain |

## Observed specific candidates

1. **P0**: `AGENTS.md` asserted “SQLite owns durable ... state” without distinguishing PG. Correct its truth boundary; treat PG as direction and resolve the active legacy writer before data deletion.
2. **P0**: `docs/quickstart.md` used an undefined `$repo` variable in its deploy snippet. Correct the command.
3. **P1**: Renamed `docs/runtime-vnext-decomposition.md` to [`docs/runtime-decomposition-history.md`](../runtime-decomposition-history.md) after finding zero literal filename references in tracked source; updated the document heading and marked it as historical implementation evidence, not live PG authority. The content was preserved.
4. **P1**: `runtime/registry.rs`, `runtime/inspection.rs` and supporting scripts still refer to the former SQLite store. Removal requires a verified absence of live consumers, not solely a grep result.
5. **P2**: `research/core/HISTORICAL-EF27.md` is referenced by 9 tracked files including provenance; do **not** delete by its historical title.
6. **P2**: `evidence/harness-h2-runtime-r2-live-d50f609-20260731.json` has 3 tracked consumers; keep until its acceptance contract is intentionally replaced.
7. **P2**: `standards/runtime_standard_native_r3_report.json` is referenced by its validation script and TOML; do not classify as disposable generated garbage.
8. **P2**: `planning/lego-plan-r1.json` is still referenced by verification material; do not remove before replacements are identified.

## Target minimal composition

Keep **one runtime execution kernel**, **one durable writer per node/epoch**, native **Linux/Windows providers**, a **thin MCP boundary**, and an **operator projection**. Keep Git Workspace and Artifact state distinct from Registry state. Route external long-running workflows to the existing Host/Harness/Temporal owner, not an invented Runtime business scheduler. Do not create a new crate merely because a source file is long; split only where a self-contained invariant can be tested and its dependencies narrowed.

Boundary contracts for capability/idea LEGOs:

- Workspace source identity (Git exact revision/digest) and Workspace close consumer fence.
- Durable Job/Attempt admission and exact replay (PG row truth).
- Native execution provider (systemd/cgroup or SCM/Job Object, with provider-identity commitment).
- Reconciliation (preserve unknown when execution outcome cannot be established).
- Evidence (bounded artifacts, digests, provenance, semantic-completion boundary).
- Resource/lifecycle policy (known owner, capacity, source validity, consumer reachability).
- Structured release (deployment receipt, not process exit as release proof).

Each LEGO definition should record `I, O, S, pre, post, inv, eff, c, epsilon, prov, unfold`, link the *actual consuming* implementation, and distinguish specification, model/validator, implementation. An unproved equivalence is not a migration permission.

## Mature implementation and theory references

- Rust API Guidelines: https://rust-lang.github.io/api-guidelines/naming.html — snake_case modules, clear conversion and feature names.
- Cargo/Rust module structure: https://doc.rust-lang.org/stable/book/ch07-00-managing-growing-projects-with-packages-crates-and-modules.html
- Git worktree: https://git-scm.com/docs/git-worktree — lifecycle and safe removal.
- systemd directory ownership: https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html — StateDirectory, CacheDirectory, RuntimeDirectory.
- systemd tmpfiles: https://www.freedesktop.org/software/systemd/man/latest/tmpfiles.d.html — age-scoped transient cleanup, not blanket state removal.
- Temporal idempotent Activity design: https://docs.temporal.io/ — outside Runtime physical Job/Attempt semantics.
- OpenTelemetry semantic conventions: https://opentelemetry.io/docs/specs/semconv/ — consistent trace attributes, not an alternative state ledger.
- TLA+ and TLC: https://docs.tlapl.us/ — concurrency model checking, bounded to modeled assumptions.
- cargo-nextest: https://www.nexte.st/ — standard Rust test execution.

## Acceptance and completion gates

- **Source P0**: stale AGENTS/quickstart fixed; current Git diff reviewed; affected docs contract passes.
- **Backend P0**: identify each live service binary, Registry backend, PG writer epoch, and caller endpoints; every current Job consumer reads and writes the same target PG source. No SQLite fallback remains in the deployed execution path.
- **PG functional**: real fresh admission, exact replay, Job observation, cancellation, terminal evidence, restart recovery, Workspace close, and concurrency correctness.
- **Windows**: confirm native target and PG backend independently; native provider tests cannot be replaced by Linux tests.
- **Cleanup**: only after absence of consumers, classify each candidate as remove/keep/unknown. Delete old SQLite operational data without historical migration if the live cutover is accepted, but not while the old writer is still active.
- **Formal/LEGO**: each replacement declares pre/post/invariants, evidence standing, and falsification. No new test for a claim already discharged by an existing stronger proof.
- **Deployment**: release receipt and installed source/binary equality; unmerged Workspace source changes do not count as installed.

## Next audited steps

1. Read service startup identity and Registry backend without exposing secrets.
2. Trace the caller graph from Gateway/Harness/Host to every Runtime endpoint.
3. Qualify a single PG writer and physical Linux/Windows acceptance.
4. Remove obsolete SQLite source and associated scripts/migrations only after exact consumer graph closure.
5. Recount tracked, ignored, and owner-managed data separately and reclaim only closure-proven candidates.
