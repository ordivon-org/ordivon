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

## 2026-11-09 C1 grounded consumer and collaboration increment

**SourceCut at continuation**: GitHub main `a7d70e83945b7418f41b9636f0803d1544e84355` (25 commits ahead of original Plan basis) has independently applied the same `HostV2.status` integrity/history completeness fix. The initial Host PR #1976 was rebase-conflicting; **resolution**: keep smaller upstream `service.py` implementation, replay own exact PostgreSQL negative test and focused-entrypoint correction, and rebase our PR onto current main. Never preserve a redundant parallel implementation merely for authorship.

**Revision read consumers actually discovered**:
- Host public `work.get(workRef, revision?)` in `mcp_work_tools.py` / `work_queries.py`, with stored digest verification and typed conflict on missing revision.
- Gateway forwards `revision` as an optional passthrough; it does not implement historical semantics.
- Host Owner Guide / README use latest re-entry; tests `test_work_snapshot_read_refinement.py`, `test_work_query_boundary.py`, `test_mcp_domain_errors.py` exercise optional historical API.
- No active Host internal service directly consumes historical snapshots for scheduling/Goal standing. **This negative result is limited to the checked source and cannot establish that no external user/Agent calls revisioned reads.**

**Current live production Work revision=1 readback**:
- PASS: Windows Runtime PG continuation; Linux Runtime PG continuation.
- CONFLICT: abandoned Windows PG-first Runtime cutover, abandoned Linux PG cutover, completed Host SourceCut E2E acceptance.
- Current Doctor: `detail=history` unhealthy, `work.snapshot_history_contiguous invalidWorks=3`, current-pointer and retained-digest checks OK.
- No production rows were altered. Do not fabricate lost history or silently waive its contract.

**Cross-agent Space**: posted a material peer review request in existing Space `space:ordivon-task-portfolio-and-proof-gates-r1:20261101`, Topic `topic:ordivon-task:02-r21-formal-refinement:20261101`, Message sequence **25739** (2026-11-09 23:20 CST). Asked for exact source/consumer review, 4h cleanup caller and duplicate PR exposure; the message is collaboration, not authorization or a peer response. Separately scoped PRs #1977 (method-router/agent delivery), #1978 (repo architecture contract), #1971 (SourceCut admission) own other boundaries. This Host PR must not duplicate their implementation.

**Next bounded implementation task (C1; do not skip to production deletion):**
1. Add missing-revision negative behavior to existing disposable PostgreSQL test: after deliberate deletion of revision 1, `WorkStore.get_work(w, 1)` must raise typed `ConflictError`, current `get_work(w)` remains valid, and both Doctor modes explicitly fail. This is an actual public consumer read seam; do not alter another owner's API.
2. Run one isolated disposable PG18 acceptance and `mise run verify`; store exact PASS/SKIP evidence, then update and publish PR #1976 using the real upstream fix.
3. Keep full history until an explicit *provider-independent* historical-retention decision is made from actual consumers; any change to retained floors must be a separate versioned migration/contract refinement.
4. Find actual hygiene caller by Host Message writer, Git/Runtime traces or executing agent's evidence. A Host-only `work.snapshot.commit` cannot guarantee a third-party Agent will never choose abandoned based on age; the fix belongs at the real caller/contract seam, not a generic Host foreign-Goal lookup.
5. Confirm peer observations in the Space before assuming cooperation or claiming consensus. Revalidate latest main/PR before merge.

**Acceptance for C1 source slice:** external Goal unchanged, historical missing never projects to fabricated success, Host current read and history Doctor agree at the intended scopes, PG tests PASS, no source duplicate; current installed PG integrity remains explicitly failing until a later real retention repair. No weak-model experiments.

## 2026-11-09 C1 actual source verification receipts

- Rebase onto current main source `a7d70e83945b7418f41b9636f0803d1544e84355` retained upstream `service.py` implementation and removed our duplicate during Git conflict resolution.
- Consumer-rooted refinement extended `test_host_history_doctor_postgres.py` to assert `ConflictError(no revision 1)` after deliberately removing revision 1 **only in a disposable PostgreSQL 18 test database**, while current `work.get` remains valid.
- `mise run test:postgres:disposable`: **443 passed in 52.19s**, exit 0. Native PG18, migrations 0001..0013, Ruff, and full Host integration verified.
- `mise run verify`: **392 passed / 51 skipped**, exit 0. Native CrossHair source obligations, Z3 DAG 40 obligations with negative control, and Lean DAG/Unicode theorems ran; skipped DB cases not counted as PG evidence (independent disposable PG18 PASS above).
- Production Host `history` remains unhealthy `invalidWorks=3`; this source PR is not a repair of missing data or a production release.
- Space review question at `message:host-r21-formal-spec-peer-consumer-review-20261109-2319` (sequence 25739); peer responses and installed acceptance tracked independently.


## 2026-11-10 actual Host consumer-closure execution addendum (reviewed before edits)

**Current SourceCut:** `8346863be965da34371944679d063fd9fd0358ac`. Former header `3b43977...` is historical authoring source; PR #1976 has **MERGED**, so Tasks A1/B1 and earlier C1 *first source regression* are already delivered and must NOT be rerun as new development tickets. Runtime/Host installed effect remains a separate acceptance. Global canonical Spec is the already-existing `docs/architecture/AGENT_CONTRACT_EXECUTION_SPEC_R1.md` adopted by #1992; do not create another global one or edit #1993 competing worktree.

### Cross-audit order completed before this source slice

- [x] Read current exact Git main/Host current source and actual production Host history Doctor.
- [x] Read official methods via existing local approved Matt TDD/domain-modeling/code-review; ECC ai-regression-testing/verification-loop; Superpowers writing-plans/verification-before-completion. Apply methods at real public seams, not multiple orchestration services.
- [x] Read Ordivon `recursive-lego-calculus`, `compositional-contracts`, `systems-engineering`, `stpa`, `fmea-fta`, `skill-supply-chain-audit`, `minimum-sufficient-representation`, `method-router`.
- [x] Post existing Space peer request seq25818 and receive independent reply seq25823.
- [x] Read production PG using `REPEATABLE READ READ ONLY`, collect three-Work revision/consumer reference matrix; post seq25843.
- [x] Receive independent response seq25845: C conditional accept, A revise, B reject; post response seq25855. Peer advice not considered installed acceptance.
- [x] Confirm actual structural references and negative inference: `63 message body mentions` are traces, not necessarily 63 live consumers; terminal age does not prove unreferenced Work.
- [ ] Finalize all affected code native tests and Git publication; installed PG historical corruption remains unmodified.

### Slice C2 — current-source public-consumer preservation (no production SQL writes)

**Files:** modify existing `services/host/tests/test_host_history_doctor_postgres.py`; update these existing Host Spec/Plan files. **Do not create another global Spec, custom GC engine or schema migration.**

**Consumption interfaces**: `WorkStore.get_work(workRef, revision?)`, `SocialStore.list_spaces(subject_ref=)`, `SocialStore.list_space_subjects`, `SocialStore.list_message_relations`, `SocialStore.get_message`, `HostV2.status(detail=integrity|history)`.

**Concrete trace**: create isolated actor → Work rev1 → Work rev2 completed → Space Subject link → Topic/Message → `references` MessageRelation → delete only rev1 in disposable PostgreSQL → assert exact current snapshot and digest → old rev returns ConflictError → Social navigation still finds Work identity → Doctor history remains error. Cleanup disposable test fixtures via native SQL, no production impact.

- [x] Run focused lint and isolated PG18 full owner test. If existing source produces PASS, classify as **new preservation regression coverage**, not a RED/GREEN implementation fix. Test behavior must come from real public API, no private SQL facades.
- [x] Run Owner native `mise run verify` and separately disposable PG18, report skip counts without treating skips as PG PASS.
- [ ] Two-axis peer review: **Standards** (Owner AGENTS/no duplicate abstraction/real API) and **Spec** (identity/current/history/Goal separation, no Doctor spoof, no destructive production effect).
- [ ] Commit exact scoped diff and submit GitHub PR; current branch/source/CI vs installed effects independently observed.
- [ ] Post PR+exact native evidence to existing Space. Do not wait for peer signoff before executable source check; do not claim production historical restoration.

### Slice D2 — disposition and real-Goal continuation (next independent owner ticket, not quietly part of this source test)

**Why:** work label `abandoned` is Host semantic disposition; its old P0 production Goal was carried forward to a new Work. Refuse a cleanup agent's `idle>=4h ⇒ abandoned` inference.

- [ ] Locate the *exact* historical cleanup caller/Agent script, not infer that Host's `work.snapshot.commit` API itself made the bad decision.
- [ ] Bind the caller to native Goal/Runtime/Host owner facts; replace age-only terminal changes with active-view pruning if independently justified.
- [ ] Add an actual negative control preserving a four-hour idle but live Goal; do not add a `Goal` DB/foreign-truth lookup into Host.
- [ ] Use existing PostgreSQL declarative set operations only when true candidate relations are closed and current. Preserve existing `RESTRICT` migration chain and non-FK Social reference consumers.
- [ ] Independently check released native service/consumer, not just source PASS.

### Closure/stop decision

For the present three real terminal Works, the decision **KEEP identity / preserve current / historical unreadable / Doctor FAIL** is evidence-based and *not a reason to HOLD all unrelated work*. Do not create a large permanent retention policy for these three rows without a domain consumer demonstrating value. Production history can become PASS only by authentic recovery or explicitly versioned, consumer-qualified policy change; this slice does neither.

### 2026-11-10 C2 native evidence (no installed/domain promotion)

- SourceCut 8346863be965da34371944679d063fd9fd0358ac; isolated Workspace ws-gpt6-host-formal-crossaudit-20261110-r1.
- `mise run test:postgres:disposable`: **444 passed in 54.98s**, exit 0; isolated PostgreSQL18 with Alembic schema 0013 and Ruff. The added test was green against unchanged service code: *contract-preservation coverage*, not claimed bug fix.
- `mise run verify`: **392 passed, 52 skipped in 17.41s**, exit 0; CrossHair source obligations, Z3 bounded DAG plus negative SAT, Lean DAG and Unicode general theorems. PostgreSQL DB tests skipped in this command but qualified by the separate disposable PG test.
- `git diff --check`: zero whitespace issues before commit; peer code-spec dual-axis request posted to existing Space seq25866, independent reply pending as of this artifact revision. Prior peer decision seq25845 adopted.
- Production Host remains `work.snapshot_history_contiguous invalidWorks=3`; no production PG write, historical revision backfill, schema change, Goal change or installed Host claim.
