# Host R2.1 Contract-Driven Execution — Implementation Plan

> For agentic workers: adopt the already installed `obra-superpowers/writing-plans`, `matt-native/tdd`, `ecc-native/ai-regression-testing`, and `obra-superpowers/verification-before-completion`. Do not install a duplicate process framework. Execute each independent vertical slice with RED→GREEN and read the actual Owner test output.

**Goal:** Improve Host's semantic continuity and historical evidence truth without allowing stale Work hygiene to terminate a real Goal.
**Architecture:** Reuse Host PostgreSQL, R2.1 typed contracts, existing MCP/Doctor and pytest/Alembic. Keep implementation within natural Owner; foreign outcome remains foreign.
**Tech Stack:** Python 3.15.1, PostgreSQL 18, Psycopg, MCP, Pydantic, pytest/Hypothesis, Alembic, uv/mise, Lean/Z3 as appropriate.
**Spec:** `services/host/docs/HOST_R21_AGENT_EXECUTION_SPEC.md`.
**SourceCut:** `3b43977e682d8c7668f6371ffd998c7821e4312a`.

## Global constraints

- No weak-model benchmark, additional goal database, policy engine, universal compiler, or risk bureaucracy.
- The existing `works.current_revision` and `work_snapshots` contract must not silently lose historical semantics.
- Work `abandon` is never a synonym for idle cleanup or Goal cancellation.
- `SKIP`, `UNKNOWN`, `FAIL`, `PASS`, `SOURCE`, `MERGED`, `INSTALLED`, `CONSUMED` are distinct.
- Existing PG/schema and real consumer evidence outrank prose; production effects only after exact Owner readback.
- Follow `services/host/AGENTS.md`; work only in clean independent Runtime Git Workspace.

## Task A1 — Repair the executable Host focused-test entrypoint (first vertical slice)

**Files:** `services/host/mise.toml`, `services/host/README.md`, `services/host/tests/test_host_queue_qualification.py` (or a new small dedicated test if existing test has no fit).

**Interfaces:** Existing `mise run test:focused` and actual committed `tests/test_canonical_json_property.py`. No new API.

- [x] RED baseline already observed: `cd services/host && mise run test:focused` exits 4, `tests/test_canonical_property.py` missing.
- [ ] Write failing test that reads `mise.toml`, extracts the default literal for `HOST_PYTEST_NODE`, and verifies that the path exists under `services/host`; also assert README uses that exact path.
- [ ] Run `uv run --locked python -m pytest -q tests/test_host_focused_default.py`; expected FAIL before fix on the non-existent default.
- [ ] Replace the stale filename in `mise.toml` and README with `tests/test_canonical_json_property.py`.
- [ ] Run default `mise run test:focused`; expected PASS, plus `uv run ruff check tests/test_host_focused_default.py`.
- [ ] Commit source-only, with exact RED/GREEN evidence.

## Task B1 — Surface real history incompleteness without lying about retention

**Files:** `services/host/src/ordivon_host_v2/service.py`, `services/host/tests/test_social_work_fabric_postgres.py` or new `tests/test_host_history_doctor_postgres.py`.

**Interfaces:** `HostV2.status(detail='integrity'|'history')` and actual PostgreSQL work history. Preserve existing response JSON shape.

- [ ] Write a PG integration test with a Work current revision of 3, valid digest-matching revision 3, deliberately absent revision 2. `detail='history'` must contain a failed `work.snapshot_history_contiguous` and `detail='integrity'` must not describe *full history* as verified.
- [ ] Run test against disposable PostgreSQL 18; RED must expose intended bug, not an environment SKIP.
- [ ] Share/compose the existing grouped SQL predicate at the narrowest existing `HostV2.status` seam. Retain the more expensive payload-digest loop under `detail='history'`. Do not mark incomplete history PASS.
- [ ] GREEN both Doctor modes; assert current snapshot remains readable and revision 2 is explicitly unavailable, never fabricated.
- [ ] Run `mise run test:postgres:disposable`; capture exact exit and real DB count. No production mutation.
- [ ] Commit source-only with no schema version change.

## Task C1 — Decide history retention from actual consumers, not preference

**Files:** `services/host/src/ordivon_host_v2/work_queries.py`, `work_store.py`, `migrations/versions/`, `tests/test_work_snapshot_read_refinement.py`, R2.1 Spec (only if contract truly changes).

**Interfaces:** `work.get(workRef, revision?)`, CAS, PG schema. Audit actual Host/Gateway/Harness callers with `git grep` and installed MCP readback.

- [ ] Produce precise consumer graph of revisioned reads, downstream reliance on exact revision identity and receipt/history continuity; cite source cut.
- [ ] Choose **A**: maintain full revision sequence and repair only authentic retained rows; or **B**: explicitly version a bounded-retention contract with persistent native floor, contiguous retained suffix, typed `historical_unavailable`, and migration/DB tests. Do not use choice B only to hide an error.
- [ ] RED each affected real consumer and concurrent CAS test before any schema change; add negative missing-revision control.
- [ ] Implement chosen contract using Psycopg and Alembic exclusively; no second history DB, synthetic revisions or default archive.
- [ ] GREEN exact consumers, disposable PG18, rollback/readback, and `HostV2.status`.
- [ ] Commit only when current/historical read truth is consistent.

## Task D1 — Stop idle hygiene from mutating Goal standing

**Files:** Actual cleanup consumer script/tool discovered from `git grep` and Runtime/Host caller tracing; `services/host/tests/` only for Host-native seam; no arbitrary `goal_ref` column.

**Interfaces:** Real cleanup entrypoint, current Host Work API, natural Goal/Runtime owner readback.

- [ ] Locate the exact process or code that marked the live P0 Work abandoned; establish its actual authority and the four-hour predicate.
- [ ] Assert RED with a concrete idle but live-Goal example: time passing alone cannot cause `continuityDisposition='abandon'`; observed foreign Goal remains unaffected.
- [ ] Replace terminal mutation with ordinary active-set projection or native set-based Host record retention, respecting proven consumer closure; preserve explicit Goal-owner terminal decisions.
- [ ] GREEN negative controls (stale P0, no consumers, stale consumer snapshot, concurrent re-entry, response loss) and fresh Owner readback. No universal scheduler.
- [ ] Capture bounded PG transaction and practical recovery/rollback, then commit.

## Task E1 — Formalization and property-based refinement where it adds value

**Files:** Existing `services/host/formal/`, `.agents/skills/recursive-lego-calculus/references/` and/or existing Host tests, only when current implementation needs refinement.

**Interfaces:** H01/H02/H03 contract invariants from Spec.

- [ ] Reuse existing `tools/formal/RecursiveLegoRefinement.lean` conditional non-consumer theorem instead of writing a duplicate deletion calculus.
- [ ] State explicit assumptions for noninterference: Host-only SQL effect, closed/current consumer observation, natural-owner boundary; negative proof case when consumer closure is unknown.
- [ ] Exercise actual PG Work CAS and readback under Hypothesis/state-machine tests where a generated operation sequence exposes a new failure.
- [ ] Run `mise run formal:reply-source`, `formal:work-graph`, `formal:dag-theorem`, `formal:unicode-search` only for changed proof obligations; never infer PG installed currentness from a Lean theorem.
- [ ] Commit source-bound proof only if real implementation-refinement premise has been established.

## Task F1 — Retire dead documents and redundant declarations

**Files:** `services/host/docs/`, `planning/`, `AGENTS.md`, `README.md`, affected `tools/repo/` consumer checks.

- [ ] Trace real consumers of `SOCIAL_WORK_FABRIC_R1.md`, `SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md`, `planning/social-work-fabric-r1.json` and `planning/host-friction-observatory-r1.json`.
- [ ] Migrate only currently useful facts into active Host README/Spec; replace dead filename-presence tests with actual behavior contract tests.
- [ ] Remove obsolete files with `git rm` only after relevant consumers migrate; preserve Alembic 0001..0013 and any newer active migrations.
- [ ] Run native Host verification and repository architecture checks; commit intentional deletion rather than archiving duplicate shadow docs.

## Task G1 — Release and consumer acceptance

**Files:** existing Host packaging and GitHub workflow only if actual consumer demonstrates a gap.

- [ ] Perform spec-vs-diff and standards-vs-diff review from a fixed baseline, independent of implementer's narrative.
- [ ] Run `cd services/host && mise run verify`; report skips separately, require `mise run test:postgres:disposable` for database properties.
- [ ] Check `mcp-surface.json` versus native installed `tools/list`; don't equate a source manifest with live client availability.
- [ ] Merge appropriate PR after tests; exact GitHub branch/commit and CI reports become MERGED proof only.
- [ ] Publish only after native installed Host readback `host.status`, `work.get`, `attention.reentry`, Gateway consumer; report remaining UNKNOWN.
- [ ] No production Work deletion or schema cutover from a speculative proof or document approval.

## Progress ledger and dependency graph

`A1 -> B1 -> C1 -> D1 -> E1 -> F1 -> G1`; F1 documentation consumer work may begin independently after A1. The ledger lives in actual Git commits/PR and Host Work only when re-entry is needed; do not build a parallel plan state database.

Current: A1 RED verified. B1 has observed production counterexample but no new code yet. C1..G1 are not performed.

## Completion evidence

- exact source revision / changed files, actual exit codes and affected native tests;
- formal claim restricted to its proof and implementation-refinement boundary;
- installed service version/readback separately;
- consumer/Goal-native acceptance separately;
- explicit unresolved UNKNOWN with an executable next action.

No declaration of full implementation merely because this plan or A1 is present.

## 2026-11-09 source execution receipts (this branch, not production)

- A1 RED: `mise run test:focused` exited 4 with `file or directory not found: tests/test_canonical_property.py`.
- A1 test RED: `tests/test_host_focused_default.py` failed on missing default filename. After correcting `mise.toml` and README, default focused pytest returned 2 PASS; new path guard returned PASS; native Ruff import-order finding was corrected.
- B1 RED: disposable PostgreSQL 18 + Alembic schema 0013, `mise run test:postgres:disposable`: 441 passed, 1 failed, specifically `work.snapshot_history_contiguous` absent from integrity Doctor while current Work revision remained readable.
- B1 GREEN: same disposable PG18 suite: **442 passed in 54.89 s**. The grouped history predicate now appears under both integrity and history, without changing DB schema or repairing/forging revisions.
- Owner source verify: `mise run verify` returned **392 passed, 50 skipped** with Ruff/CrossHair, bounded Z3 DAG negative control and pinned Lean DAG/Unicode theorems. Skips are not PostgreSQL proof; separately run disposable PG18 was PASS.
- Outstanding C1..G1: historical consumer/retention decision, non-terminal cleanup integration, doc subtraction, PR/installed readback; no production Work mutation or full-history reconstruction.
