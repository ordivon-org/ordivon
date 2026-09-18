# Host LEGO R2 — Measurement & Subtraction Program

Status: INITIAL / NON-PRODUCTION

## Purpose

Host is evaluated as a continuity system, not by tool count, Task count, Board volume, or feature count.

The irreducible loop is:

```text
work
  -> checkpoint
  -> durable continuity
  -> exact re-entry
  -> foreign-owner revalidation
  -> work
```

The target outcome is lower re-entry cost with fewer stale or duplicated actions while preserving strict authority boundaries.

## Kernel laws

1. **Claim persistence is not truth promotion.** Host may persist an exact caller-authored claim at an exact revision. Persistence never upgrades that claim into Runtime, Git, deployment, owner, or domain truth.
2. **Projection is not authority.** A derived Host projection may return navigation and may recommend exact re-entry. It must not mint priority, ownership, assignment, delivery, consumption, or execution authority.
3. **Continuity identity outlives implementation.** Task identity, revision, checkpoint lineage, mutation replay identity, and Board identity are durable semantics. PostgreSQL layout, cursor encoding, search implementation, MCP transport, and implementation language are replaceable.

## R2 decomposition

The Host kernel is split conceptually into:

- TaskLedger
- CheckpointHistory
- CommandReceipt
- BoardLog
- TaskRouteIndex
- ContinuityClaimContract

Read/projection surfaces are separate:

- ReentryProjection / `attention.delta`
- TaskInventoryProjection / `task.list`
- SearchProjection / `board.search`
- IntegrityProjection / `host.status`

Utilities and adapters are separate:

- CanonicalDigest
- CursorContract
- MCPAdapter

Substrate is separate:

- PostgresAuthority
- AlembicMigration
- immutable release/ops authority

NewsPublication remains implemented but is classified as an **optional bounded-context / separation candidate**, not part of the irreducible continuity kernel.

## Current empirical findings

### WorkingCheckpoint v2 standing

A repository census at the R2 planning cut found no runtime consumer of `workStanding` fields in current main outside checkpoint schema/validation. The fields are therefore **caller-authored claims**, not Host control state:

- attention
- executionAdmission
- valueNow
- progress
- lineage
- relatedTaskIds
- blockerKinds
- wake
- carrier

A cross-repository source census under `/root/projects` found no production/runtime consumer code. Remaining external source hits were frozen Research/Paper1 evaluation fixtures; one Media hit was a lexical false positive.

However, a live non-terminal Task census then found **233 of 266 open continuity records (87.6%)** are WorkingCheckpoint v2 and carry `workStanding`; only 33 are v1. This falsifies the stronger claim that the envelope is directly deletable. The correct standing is:

- **Host interpretation/control semantics:** subtraction candidate;
- **persisted v2 claim envelope:** widely present compatibility data;
- **direct schema deletion:** blocked until migration/compatibility evidence exists.

Selected live distributions: `ADMITTED_NOW=98`, `REENTRY_REQUIRED=58`, `BLOCKED=66`; `ACTIVE=105`, `WAIT=82`, `BACKGROUND=30`, `HOLD=15`; 470 related-task edges and 430 wake conditions are present in current open checkpoints.

### Currentness

Currentness experiments exist in non-main Git history, but current production/main Host does not contain the currentness projection. Treat those commits as an experimental projection family, not established Host authority.

### R7 compact reads

Candidate `c45379e` keeps `task.resume` as the exact checkpoint hydration boundary and contracts `task.list` to a compact discovery projection. It must be evaluated as a resource/outcome experiment before adoption.

## Measurement model

Activity metrics are diagnostic only:

- Task count
- Board message count
- event count
- tool count

Primary outcome/cost metrics:

| ID | Metric | Meaning |
|---|---|---|
| M01 | reentry_success_rate | fresh consumer reaches the correct current frontier |
| M02 | reentry_call_count | Host/owner calls required before safe continuation |
| M03 | reentry_payload_bytes_or_tokens | information cost of re-entry |
| M04 | stale_action_prevention_rate | stale plans stopped before effect |
| M05 | duplicate_work_rate | already-completed work repeated after re-entry |
| M06 | unrouted_or_missing_route_rate | collaboration that cannot recover an exact Task route |

A useful composite may later be defined as:

```text
ContinuityEfficiency =
    successful exact reentries
    / normalized reentry cost
```

No composite becomes canonical until its failure modes are tested.

## Experiment E01 — Fresh-agent re-entry

Create a set of frozen Tasks with known current frontier and a hidden adjudication key.

For each trial, give a fresh Agent only one allowed starting coordinate:

1. exact Task ID;
2. Board cursor before a routed message;
3. exact Board route anchor;
4. bounded task inventory result.

Measure:

- whether the Agent resumes the correct Task revision;
- number of Host calls before safe action;
- bytes/tokens read;
- foreign-owner revalidations requested;
- stale action attempts;
- duplicated work;
- false claims of completion or authority.

Do not give the Agent the original conversation transcript.

## Experiment E02 — R6 vs R7 compact task reads

Compare deployed R6 behavior with candidate `c45379e` using the same frozen Task corpus.

Measure:

- serialized response bytes for task discovery;
- DB query count/latency if instrumentable;
- Agent token consumption;
- number of follow-up `task.resume` calls;
- exact-reentry success;
- stale-write rejection;
- semantic errors caused by missing inventory detail.

Acceptance requires lower discovery cost without lowering exact-reentry correctness.

### E02 measured result — strong resource win

Using all 267 non-terminal live Tasks at the measurement cut, the deployed R6 `task.list` wire totaled **2,024,956 UTF-8 bytes** across six 50-item pages. Projecting those exact Tasks into the R7 candidate wire totaled **81,686 bytes**: a **95.97% reduction**, or about **24.79× smaller**.

The code-path structure contracts at the same time. R6 performs one inventory query and then two hydration queries per returned Task; for the observed 267 Tasks across six pages this is about **540 SQL statements**. R7 returns each page with one bounded join query, or **6 statements** for the same traversal. This is a static statement-count analysis, not a database-latency benchmark.

For `task.resume`, an 11-Task sample measured **169,215 bytes → 88,677 bytes**, a **47.60% reduction**, because R7 keeps one top-level checkpoint and makes the nested `task` object a compact identity/revision capsule.

The compact-read commit was transplanted by itself onto the R2 base as `b118559a87725e22237d22b218d40861838dae5e`. Verification found no currentness experiment code or schema references; pytest/Ruff/diff checks pass. A subsequent isolated PostgreSQL **18.6 / UTF-8** run completed Alembic `0001→0002→0003→0004` and the complete candidate suite passed **30/30 tests**, followed by Ruff and diff checks. The temporary cluster ran under the system `postgres` account and was stopped/removed after the run. E02 therefore passes the resource and database-integration gates; **fresh-consumer re-entry remains the final outcome gate before production admission**.

## Experiment E03 — workStanding consumer census

The source census found no production/runtime consumer code, but the live-data census found `workStanding` in 233/266 non-terminal checkpoints. Therefore the next experiment is **semantic contraction before schema deletion**.

Next steps:

1. construct a candidate that preserves v2 read/write/replay compatibility while removing any Host-side interpretation of standing fields;
2. run current Host tests plus representative downstream recovery/evaluation tests;
3. measure whether continuity outcomes change when the fields are treated purely as caller-owned payload;
4. only if that passes, design an explicit v2→simpler-envelope migration experiment.

Persistence alone is not proof of semantic necessity, but high live prevalence is a real compatibility constraint.

### E03 result — semantic contraction guard

Current Host already satisfies the narrower contraction hypothesis: no runtime module outside `checkpoint_contract.py` reads `workStanding`. R2 now freezes this as executable policy:

- runtime source outside the checkpoint contract must not consume `workStanding`;
- WorkingCheckpoint v2 must round-trip its caller-authored standing claim;
- an unrelated exact-revision checkpoint patch must preserve the standing claim unchanged.

Therefore E03 does **not** justify a production data migration. The useful subtraction is semantic: Host stores and validates the claim envelope while refusing to turn it into Host authority.

## Experiment E04 — Currentness destroyer

Run only against the experimental currentness projection family.

Cases:

- missing owner observation;
- unavailable owner;
- generation mismatch;
- observation older than recorded basis;
- future-dated observation;
- expired validity interval;
- conflicting lease evidence;
- malformed timestamps;
- immutable basis.

Invariant:

```text
foreign uncertainty -> UNKNOWN or REENTRY_REQUIRED
```

Never:

```text
foreign uncertainty -> Host grants work authority
```

## Experiment E05 — News separation

Model and test Host with News removed from the continuity kernel graph.

Pass condition:

```text
Task continuity
+ Board collaboration
+ route recovery
+ exact resume
+ replay/fencing
```

remain complete.

If so, classify News as an optional Host capability/plugin or move it to the relevant intelligence/media package later. No physical migration is implied by this experiment.

## Experiment E06 — Feedback observability

For every future Host change, record:

- expected outcome metric affected;
- expected resource/cost change;
- authority boundary touched;
- falsifier;
- result.

A change with no demonstrated positive effect on continuity outcomes and no required compatibility obligation is a subtraction candidate.

## Promotion gate

A Host change may move toward main only when all are explicit:

1. **Owner:** which LEGO owns the semantics?
2. **Authority:** what truth does it own and what truth must it never claim?
3. **Evidence:** what raw evidence supports its projection?
4. **Consumer:** which concrete consumer requires it?
5. **Outcome:** what measurable continuity outcome should improve?
6. **Cost:** what added state, calls, bytes, latency, or cognitive load does it impose?
7. **Failure mode:** how does it fail closed?
8. **Substitution:** can a mature external substrate own this instead?
9. **Rollback:** how is the change removed without corrupting durable identity?

This document is a measurement and architecture program. It does not itself modify production authority.


## E01 fresh-consumer re-entry result — PASS

E01a locally checked 8 current non-terminal Host Tasks. For every sample, the `task.list` Task identity, revision, state, and checkpoint digest matched `task.resume(expectedRevision=...)` exactly: **8/8 pass**. Only metadata and digests are retained in the measurement record.

E01b froze a 12-case synthetic continuity corpus before provider calls. Treatment A used an R6-like full TaskView inventory; Treatment B used the R7 compact six-field summary. Both exposed the identical single `task_resume(taskId, expectedRevision)` Tool and no prior conversation context. All **24/24** calls completed with no provider error.

- A exact resume selection: **12/12 (100%)**
- B exact resume selection: **12/12 (100%)**
- mean provider request bytes: **15,204.8 → 6,925.8 (-54.45%)**
- mean prompt tokens: **3,804.7 → 2,050.7 (-46.10%)**
- mean request-token upper bound: **15,332.8 → 7,053.8 (-54.00%)**
- mean latency: **2,833.9 ms → 2,308.5 ms (-18.54%)**, descriptive only because provider latency was not a causal primary endpoint.

The preregistered E01 classification is **PASS**. Combined with E02's live-wire resource measurement and isolated PostgreSQL integration, the fresh-consumer outcome gate no longer blocks compact-read integration. This does not by itself authorize production deployment; an integrated candidate and release/cutover review remain separate gates.

## R7 integrated candidate verification

After E01 passed, the compact-read implementation was integrated with the R2/E03/E01 evidence chain. The candidate at verification time was `4dd46961180750a85cafb3bed4631a5b4f885a84`.

A fresh PostgreSQL **18.6 / UTF-8** cluster was initialized on an isolated temporary port. Alembic advanced the empty authority through `0001→0002→0003→0004`. With `ORDIVON_HOST_V2_TEST_DSN` bound to that cluster, the complete suite passed **30/30 tests with zero skips**. Ruff and `git diff --check` passed. A direct `host.status(detail=history)` probe reported healthy history, schema 4, surfaceVersion 8, and 13 tools. The temporary PostgreSQL cluster was stopped and removed.

This establishes an **integrated candidate**, not a production deployment. The remaining gate is release/cutover review against the currently installed Host release.
