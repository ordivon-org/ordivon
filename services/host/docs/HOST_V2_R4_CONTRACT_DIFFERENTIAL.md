# Host v2 R4 Contract Differential & Semantic Subtraction

Status: ACTIVE

R4 treats Host v1 as a behavioral/source oracle, not an implementation donor. Public compatibility is consumer-observable semantic compatibility or an explicitly reviewed deletion/change; matching tool names alone is insufficient.

## Current first-pass matrix

| Surface | R4 standing | Action |
|---|---|---|
| 13 MCP tool names | SAME | retain |
| Board search negative-result authority | REGRESSION repaired | preserve `false` |
| Historical v1 cursor bytes | INTENTIONALLY_DELETED | restart bounded query; do not preserve storage encoding |
| v2 pagination for task/news inventory | UNKNOWN / insufficient | earn a new stable cursor before production cutover |
| `host.status` production observability/integrity | REGRESSION / incomplete | rebuild from PostgreSQL/standard ops, not v1 storage machinery |
| WorkingCheckpoint typed semantic validation | UNKNOWN | consumer/differential evidence decides minimal retained invariant set |
| v1 scheduler-like Task states | INTENTIONALLY_CANDIDATE_FOR_DELETION | do not restore without a consumer failure |
| ContinuityLens as separate subsystem | INTENTIONALLY_DELETED | preserve only earned observable semantics |
| Runtime/Harness/provider proxying | INTENTIONALLY_DELETED | foreign owners remain authoritative |
| Alembic historical migration mutability | REGRESSION repaired | migrations must be immutable deltas |

## R4 gates

1. Every current public Host tool has input/output/failure/truth-boundary differential cases.
2. Every difference is classified SAME, INTENTIONALLY_DELETED, INTENTIONALLY_CHANGED, REGRESSION, or UNKNOWN.
3. REGRESSION and UNKNOWN cannot reach cutover.
4. Deleted v1 concepts are restored only after a real consumer or destructive test fails and mature external substrate cannot cover the requirement.
5. Real production-state migration is a later frozen-snapshot single-writer cutover; no long-lived dual write.

## R4 first executed cut — 2026-09-11

Mechanical signature comparison against current Host v1 found 12/13 tool top-level parameter-name surfaces identical. `host.status` remains the sole top-level signature mismatch (`detail`, `recentLimit` exist in v1 and are not yet implemented in v2).

Executed repairs in this cut:

- `board.search.negativeResultAuthoritative` restored to `false`.
- Alembic 0001 and 0003 no longer import mutable runtime `SCHEMA_SQL`; historical migrations are frozen SQL/deltas and both offline rendering and real 0001→0002→0003 upgrade succeed.
- `task.list` and `news.list` now use v2-native scope-bound PostgreSQL keyset cursors instead of returning `hasMore=false` after truncation. Historical v1 cursor bytes remain intentionally non-portable.
- Fresh isolated PostgreSQL verification passed 17/17 tests including MCP, concurrency/idempotency, rollback and both pagination paths; Ruff and `git diff --check` passed.

Executable-consumer census outside Host found no direct source-level consumers of `workStanding`, `continuityNavigation`, or `runtimeNavigationHint`. These derived v1 projections therefore remain deletion candidates rather than automatic migration requirements. This does not prove the underlying checkpoint information is unnecessary: the next gate is consumer-level continuation behavior using v2's opaque revision-fenced checkpoint payload.

Remaining R4 P0/P1 fronts:

1. Rebuild `host.status` as a PostgreSQL-native production observability/integrity contract or explicitly version it; do not copy SQLite/CAS Doctor machinery.
2. Differential-test full WorkingCheckpoint behavior (typed envelope, patch semantics, terminal transitions, writer provenance) and retain only consumer-earned invariants.
3. Add frozen production-state export/import and semantic equivalence verification before any writer cutover.
4. Replace direct `HostV2.initialize()` latest-schema bootstrap with migration-owned initialization for production paths.
5. Prove PostgreSQL restart/backup/restore/PITR plus release/cutover rollback before production authority moves.

### PostgreSQL-native host.status closure

`host.status` now preserves the v1 top-level input signature (`detail`, `recentLimit`) while replacing implementation-specific SQLite/CAS checks with v2-owned PostgreSQL invariants. `summary` reports interface, PostgreSQL authority counts, Board/News/continuity counts and bounded recent activity. `integrity` checks schema, current checkpoint/event coherence, committed command receipts, Board reply integrity and News revision continuity. `history` additionally checks per-Task history contiguity and recomputes every retained checkpoint canonical digest. Deployment identity remains explicitly `not-observed` until the v2 release layer owns an authenticated installed-release projection.

A destructive test mutates one current checkpoint digest and verifies `host.status(detail=integrity)` becomes unhealthy; restoring the exact digest returns the clean invariant state. Fresh PostgreSQL verification now passes 18/18 tests.

### Minimal WorkingCheckpoint write-boundary contract

R4 retains the public WorkingCheckpoint envelope only at the Host write boundary; it does not restore ContinuityLens or other derived semantic subsystems. MCP discovery now publishes v1/v2 complete-checkpoint schemas plus an exact-revision patch schema. `task.adopt` requires a complete checkpoint bound to the exact taskId. `task.checkpoint` permits bounded field patches only while continuity remains open, merges omitted fields from the exact expected revision, requires a complete checkpoint for a new complete/abandon transition, and prevents patch-only introduction of v2 workStanding into a v1 lineage. Writer labels remain provenance outside semantic checkpoint content: response-loss/equivalent replay cannot rewrite the writer already persisted by the committed revision.

Fresh PostgreSQL verification passes 20/20 tests including patch inheritance/replay, terminal partial-patch rejection, task identity mismatch, MCP schema publication and writer-provenance replay. No direct executable consumer evidence earned restoration of ContinuityLens/current-attention projections.
