# Host convergence P0–P2 closeout

Date: 2026-07-29
Status: implemented and locally accepted
Protocol authority: `ordivon-computing@5c6e225b90f25d4a0e8e0f99bf7590ecbd7ce1a5`
Protocol profile: `host-workload-v1`, distribution `0.3.0`

## 1. Result

Ordivon Game now implements the same immutable Host workload wire profile as Ordivon Host without moving Game World semantics into Host and without adding a second scheduler, DAG, wakeup daemon, or Runtime dependency.

The implemented path is:

```text
Game Goal / Actor Task configuration
→ TaskDescriptor
→ immutable Context
→ ModelInvocationIntent
→ ModelDecision
→ exact Decision admission
→ domain-owned proposal coordination
→ one semantic Effect
→ one DispatchEnvelope
→ GameWorldExecutor
→ one ObservationEnvelope
→ VerificationReceipt with per-Actor resultItems
→ TaskOutcome
```

The existing Game engine remains the executable compatibility oracle during convergence. The new protocol transcript is generated from the same retained Contexts, Decisions, Effects, Dispatches, World Events, and outcomes and is checked against normative cross-language vectors.

## 2. P0 — cross-language protocol

Game contains a strict TypeScript implementation of the promoted Protocol profile:

```text
src/host-contract/canonical.ts
src/host-contract/model.ts
src/host-contract/validate.ts
```

It implements:

- canonical UTF-8 JSON with recursively sorted keys;
- safe integers only;
- malformed Unicode surrogate rejection;
- `sha256:<64 lowercase hex>` semantic digests;
- exact field validation;
- kind-specific Decision candidate invariants;
- pure Decision admission with stable error codes.

The exact Computing vectors are frozen under:

```text
fixtures/host-workload-v1/
├─ manifest.json
└─ vectors.json
```

The manifest binds the fixture to the authoritative Computing revision and raw vector-file digest. It is a consumer snapshot, not a second protocol authority.

### Digest compatibility

Game World history continues using its historical bare SHA-256 digest:

```text
41d7bfd4...
```

Host workload objects use:

```text
sha256:41d7bfd4...
```

The two formats are converted only at the adapter boundary. Existing World replay identities and frozen fixtures were not rewritten.

## 3. P1 — single-Actor convergence

`SingleActorHostContractAdapter` reconstructs one complete immutable Host transcript from the existing single-Actor Host path.

The frozen successful workload produces:

```text
1   TaskDescriptor
10  CompiledContextEnvelope
10  ModelInvocationIntent
10  ModelDecision
10  AdmittedDecision
25  semantic Game Effects
25  executor requests
25  DispatchEnvelope
25  ObservationEnvelope
25  VerificationReceipt
1   TaskOutcome
```

The original result remains unchanged:

```text
World revision: 25
World digest: 41d7bfd4c1b36f0a8e38533be7f7e9b48b1625608c76c5ced1ddd3d0952d02d2
```

Calling contract synchronization again produces no new semantic event or object. Event identities and contract digests remain exact.

## 4. P2 — minimal multi-Actor convergence

The Team path is represented as:

```text
one shared Mission Goal
├─ Engineer Actor Task
├─ Medic Actor Task
├─ Security Actor Task
└─ one ordinary Coordinator Task
```

No Task graph tables or scheduler were added. Each round retains a bounded Goal snapshot containing the exact Actor Task revisions and Context identities used by the Coordinator.

The frozen Team workload produces:

```text
4   TaskDescriptor
54  CompiledContextEnvelope
54  ModelInvocationIntent
54  ModelDecision
54  AdmittedDecision
18  Goal Task snapshots
18  semantic Team Tick Effects
18  executor requests
18  DispatchEnvelope
18  ObservationEnvelope
18  VerificationReceipt
4   TaskOutcome
```

Each Team verification contains exactly three Actor-scoped `resultItems`. One joint Effect still maps to one Dispatch, one Observation, and one Verification; no `EffectGroup` was introduced.

The original Game outcome remains unchanged:

```text
World revision: 18
World digest: a8ef1f491c35720ed02e66f004ccd7f3466f78991dcafecd442ceae66b09ceb7
```

## 5. Ownership after implementation

### Host/Protocol-owned semantics

- TaskDescriptor and stable workload identity;
- Context, Invocation, Decision, and admission wire contracts;
- semantic Effect/Dispatch/Observation/Verification/Outcome identity;
- unresolved-delivery reconciliation rule;
- Goal-scoped Task revision references;
- per-Task result application semantics.

### Game-owned semantics

- authoritative World state and reducer;
- Actor observation and hidden-information rules;
- Objective predicates;
- authority policy and exact Grants;
- Message reachability;
- resource claims;
- legal proposal subset selection;
- TickPlan and TickBatch construction;
- mission success, failure, and score.

The adapter exposes Game-owned objects through opaque digests and bounded protocol projections. Host does not interpret Game commands or select compatible proposal subsets.

## 6. Executor boundary and recovery

`GameWorldExecutor` provides separate methods for delivery and observation:

```text
deliverCommand / deliverTeamTick
observeCommand / observeTeamTick
```

Delivery first checks the retained command receipt. Observation is a pure lookup and never calls the World reducer.

The accepted fault scenario is:

```text
World commit succeeds
→ response is lost before Host records Observation
→ fresh process opens the same Game database
→ observe finds the original retained receipt
→ no second World Tick is committed
→ transcript converges to exactly 18 Dispatches and 18 Observations
```

The complete legacy eight-point Team interruption matrix also remains green.

## 7. Persistence shape

No new generic Host database was added to Game.

Protocol objects reuse:

```text
host_artifacts
host_journal
```

Protocol semantic digests and legacy Game artifact digests remain distinct. A protocol object is immutable and journal events reference its semantic digest.

The existing `team_*` and single-Actor compatibility tables remain present for executable dual-run comparison. They are not claimed to be the final ownership boundary and are not deleted in P0–P2.

## 8. Embedded versus sidecar decision

P0–P2 select the conformance-backed embedded TypeScript form.

Measured on the frozen local workloads after batched persistence:

| Workload | Legacy run | Contract synchronization | Transcript entries |
|---|---:|---:|---:|
| Single Actor | 4,799 ms | 32 ms | 192 |
| Three-Actor Team | 7,481 ms | 79 ms | 350 |

Contract synchronization therefore occurs once at `run()` close and may also be called explicitly through `syncContract()`. It does not rescan the complete history after every `step()`.

A Python sidecar is not justified yet because it would add process, transport, environment, and cross-database failure boundaries before measured code deletion proves a net benefit.

## 9. Acceptance evidence

```text
Game tests:                 214/214
Coverage lines:              98.61%
Coverage branches:           90.13%
Coverage functions:          98.52%
TypeScript typecheck:         PASS
Web checks:                   PASS
Diff check:                   PASS
Cross-language vectors:       PASS
Single transcript replay:     PASS
Team transcript replay:       PASS
Response-loss recovery:       PASS
```

The frozen World digests, replay behavior, authority behavior, conflict selection, Mission Control behavior, Provider fallbacks, and historical fixtures remain unchanged.

## 10. Deferred migration

P0–P2 deliberately do not:

- delete legacy Game Host tables;
- replace every live transition with a Python Host call;
- introduce a network Host service;
- add a generic DAG, scheduler, mailbox runtime, or wakeup daemon;
- move Game coordination policy into Computing or Host;
- rewrite historical World or Host events.

Deletion should begin only after the embedded contract path is used as the executable authority for a bounded workload and the removable legacy code is measured directly. A sidecar should be reconsidered only if independent Host operation or a second non-TypeScript deployment proves that process separation removes more complexity than it adds.


## Successor status: unique authority cutover

The P0–P2 adapters documented above were migration scaffolding. They have now been deleted.

The production path is:

```text
Agent or Team domain cognition/session
→ EmbeddedHostAuthority
→ TaskDescriptor / Dispatch / Observation / Verification / TaskOutcome
→ GameWorldExecutor
→ authoritative Game World event
```

Single-Actor execution creates one Host workload Task per primitive World Effect. Team execution creates one Host workload Task per atomic Team Round. Game retains only domain sessions, authority, proposals, Tick plans, messages, and World truth.

A Python JSONL sidecar was tested as a competing hypothesis and rejected: its five-stage no-Provider lifecycle p95 was 286.873 ms with 879 production lines and a 196.120 ms startup, versus 111.843 ms, 212 lines, and 36.896 ms for the embedded authority. The sidecar code was not merged.

See `HOST-AUTHORITY-CUTOVER-P3-P6.md` and `HOST-AUTHORITY-CUTOVER-P3-P6.json`.
