# Runtime Complete Architecture R1 — Executable LEGO Plan

Status: RW3_IN_PROGRESS_R09_QUALIFIED_R10_NEXT
Truth role: planning projection, not Runtime project truth
Source revision: `fd3f166024587e9c943207fc8987cff436f43098`

This plan evolves the already-operational Runtime by strangler-style internal extraction. It does **not** recreate the retired Execution Fabric R1, does not rewrite Runtime, and does not widen Runtime authority.

## Current progress checkpoint — 2026-09-24

- R00/R01: implemented baseline/invariant and verification partition.
- R02: first WorkspaceState extraction integrated; residual extraction remains evidence-driven.
- R03: JobIdentityContract + AttemptLifecycleContract implemented and verified.
- R04: **implemented** as `ReservationContract` on `e48b2eab5fb743efa3b50cb1eceae4539e1c99a7`. It owns durable capacity-holder/acquire/hold/release and terminal reservation-target laws only; queue/priority/scheduling remain explicitly out of scope.
- R04 verification: integrated `e48b2eab` is byte-identical to verified candidate `4131cbe0` across the five R04 responsibility files. Candidate owner gate `job-01a0cd18-695a-7dc3-b07a-a712d3bd2a31` PASS (`exitCode=0`), including the slow reference-model property gate; the equivalent R04 patch on an earlier base also passed focused real-system fast-success and timeout-descendant-pipe acceptance.
- RW1 is **COMPLETE**: R05 Artifact/Release state ownership and R06 RegistryStorageBoundary are integrated; Registry semantic schema remains v6.
- R07 `AuthorityContract` is **IMPLEMENTED AND CURRENT-MAIN QUALIFIED** on `163db3230483ec932fa8152fb1c9e6bd756e59d5`. Existing execution families compile internally only after exact replay lookup; the public Tool surface and current authority semantics are unchanged. `runtime:verify` PASS: `job-01a0cf0f-a02a-76b3-8cc0-59f2e5abd896`.
- RW2 is **COMPLETE**. R08 ordinary execution is integrated on `397dee5ef0caa296283253c03da5f277f4fa2a8d`, reduced immutable-input on `40c414a3901c4383a9d7d122fe7716effbe8506e`, trusted immutable-input on `645d50cd51c8efe772de762610e045ea112fb78c`, and credential-bound trusted on `c52737fd7bc2b6ccf71418719b220070a620da5f` via integration `897e504916fca4078847005a4b78198042b1c01b`. Exact post-integration owner qualification `job-01a0d323-f7ca-7351-8f5c-1d01b4877ca6` PASS. All four effect-opaque families now compile through the same internal `AuthorityContract + OperationCircuitCompiler` seam into the existing `SubmitRequest` without changing replay, request identity, Registry v6, provider/materialization ownership, or semantic-completion boundaries. Runtime self-release remains separate. RW3/R09 ExecutionProviderSPI is next.
- RW3 is **IN PROGRESS**. R09 `ExecutionProviderSPI` is qualified on `fd3f166024587e9c943207fc8987cff436f43098` with full Runtime owner gate `job-01a0d34d-18e1-7140-b577-c34c0c660b4a` PASS. The private static seam freezes common obligations and non-weakenable R1 provider guarantees while preserving distinct Linux/Windows owner/evidence types; it adds no provider marketplace, plugin discovery, cross-node router, public Tool schema, or persisted provider schema. R10 LocalLinuxProvider is next; R11 follows only after Linux proves the seam on real systemd/cgroup acceptance.

## Global rules

1. Preserve current observable laws before moving code.
2. Keep the 23 public MCP Tools strongly typed.
3. Keep Registry semantic schema at v6 unless an explicitly reviewed semantic migration is unavoidable.
4. Structural refactors must preserve replay, ambiguity, cancellation, recovery, release, rollback, and evidence behavior.
5. Do not create a generic Effect framework, provider marketplace, scheduler, workflow engine, or central approval layer.
6. A replacement is accepted only when its assumptions are discharged and its guarantees are no weaker than the current path.
7. Delete old aggregation only after the replacement has exact current evidence.
8. Any change to Linux dispatch/supervision requires exact-candidate real-system acceptance; any Windows provider change requires native Windows acceptance.

## Dependency graph

```text
RW0 Contract Freeze
 ├─ R00 Invariants
 └─ R01 Test Partition
       │
       ▼
RW1 State Ownership
 ├─ R02 Workspace
 ├─ R03 Job/Attempt
 │   ├─ R04 Reservation
 │   └─ R05 Artifact/Release State
 └─ R06 Registry Storage Boundary
       │
       ├──────────────┐
       ▼              ▼
RW2 Authority      RW4 Control/Evidence
 R07 Authority       R12 Control Primitives
 R08 Compiler        R13 Evidence Claim Model
       │              │
       ▼              │
RW3 Providers         │
 R09 Provider SPI     │
 ├─ R10 Linux         │
 └─ R11 Windows       │
       │              │
       └──────┬───────┘
              ▼
RW5 Interfaces/Operator
 R14 MCP Adapter
 R15 Operator Plane
              │
              ▼
RW6 Stability/Falsification
 R16 Stability Envelope
 R17 Cross-plane Falsification
              │
              ▼
RW7 Structural Closure
 R18 Delete obsolete aggregation
```

## RW0 — Freeze behavior before refactoring

### R00 — RuntimeInvariantFreeze

**Goal:** turn today's behavior into an explicit refactor fence.

**Inputs**
- `docs/runtime.md`
- `docs/effect-kernel.md`
- `docs/status.md`
- current MCP schema/tool catalog
- Registry v6 migrations
- current release/rollback receipts

**Create**
- a machine-readable invariant manifest under `planning/` or `docs/architecture/`;
- one row per invariant with owner, subject, positive rule, negative rule, and proving test.

**Minimum invariant set**
- Workspace source lineage and source-state CAS;
- Job request identity and exact replay;
- Job/Attempt separation;
- one active execution per Workspace;
- global durable reservation limit;
- no hidden queue;
- cancellation ownership;
- terminal commit and reservation release;
- Artifact digest identity;
- ambiguous/lost/orphaned behavior;
- provider commitment;
- immutable input and credential binding;
- release.apply/release.get exact effect replay;
- Tool error vocabulary;
- 23-tool public catalog.

**Acceptance**
```bash
cargo test --locked -q -p ordivon-runtime-core
cargo test --locked -q -p ordivon-runtime-mcp
python3 scripts/check_docs.py
```

**Fail if**
- an invariant has no proving test/evidence;
- an implementation detail is accidentally promoted to public law;
- Execution Fabric R1 semantics re-enter the plan.

### R01 — ContractTestPartition

**Goal:** make later extraction mechanically safe.

**Work**
- split `runtime/tests.rs` and `integration_tests.rs` by contract rather than chronology;
- preferred categories: `workspace`, `job_attempt`, `admission`, `provider`, `evidence`, `recovery`, `migration`, `property`.

**Acceptance**
- no assertion disappears;
- total tests stay equal or increase;
- each category can be run independently;
- no production behavior changes.

**Parallelism**
- R00 inventory and R01 read-only test classification may run in parallel;
- file movement waits until R00 invariant names are stable.

---

## RW1 — Extract durable state ownership

### R02 — WorkspaceStateModule

**Goal:** isolate Workspace semantics from the historical engine aggregation.

**Move first**
- pure Workspace identity/types;
- source-state digest rules;
- open/current revision distinction;
- lifecycle CAS/tombstone rules;
- Git-common-directory dependency fence.

**Do not move yet**
- provider dispatch;
- Job admission;
- Registry transaction implementation.

**Acceptance**
- `workspace.open/get/list/close` schemas unchanged;
- exact replay and source-state CAS tests unchanged;
- no new durable state.

### R03 — JobAttemptStateModule

**Goal:** isolate logical intent from physical realization.

**Move**
- request identity;
- replay conflict rules;
- Job resolution;
- Attempt generation/state;
- terminalization/ambiguity laws.

**Acceptance**
- existing terminal Job replay never redispatches;
- response loss cannot manufacture a new Attempt;
- lost/orphaned/unknown remain explicit.

### R04 — ReservationStateModule

**Goal:** make durable capacity a small explicit state authority.

**Move**
- reservation acquire/release;
- one-active-per-Workspace;
- global-capacity checks;
- holder projection.

**Reject**
- priority;
- queueing;
- scheduling policy.

**Acceptance**
- restart reconstructs capacity from durable holders;
- rejected work remains `commitState=not_started`.

### R05 — ArtifactAndReleaseStateModule

**Goal:** isolate two distinct state domains without generalizing them.

**Artifact side**
- digest/name/kind/Attempt ownership;
- bounded output/result identity.

**Release side**
- release effect identity;
- release receipt projection;
- exact replay/readback.

**Reject**
- `EffectRegistry`;
- caller `effectClass`;
- generic physical dispatcher.

### R06 — RegistryStorageBoundary

**Goal:** Registry becomes persistence, not semantic god-object.

**Introduce only after R02–R05**
- narrow transactional storage interfaces;
- migration/query/index functions.

**Invariant**
- semantic state remains in the state modules;
- reconstructible indexes remain outside semantic migrations.

**Acceptance**
```bash
cargo test --locked -q -p ordivon-runtime-core
cargo test --locked -q -p ordivon-runtime-core query_indexes_are_recreated_without_advancing_schema_version
```

**Preferred commit sequence**
1. Workspace extraction.
2. Job/Attempt extraction.
3. Reservation extraction.
4. Artifact/Release extraction.
5. Registry boundary.

This keeps merge conflicts bounded and makes every step revertible.

---

## RW2 — Compile execution from orthogonal Authority LEGO

### R07 — AuthorityContract

**Goal:** represent current authority dimensions explicitly inside Runtime.

**Internal model should cover**
- target;
- profile;
- principal;
- Windows authority;
- immutable-input authority;
- credential authority;
- executable commitment;
- Host Dependency commitments;
- declared continuity scope.

**Map current public Tools**
- `workspace.exec`
- `workspace.execBound`
- `workspace.execBoundTrusted`
- `workspace.execCredentialBoundTrusted`

to explicit AuthorityContract variants.

**Important**
- do not introduce a public "universal authority JSON";
- do not let Runtime grant provider/domain permission;
- exact replay precedes current authority reinterpretation.

**Standing — implemented / verified on `163db3230483ec932fa8152fb1c9e6bd756e59d5`**
- `ordinary`, `immutable-input reduced`, `immutable-input trusted`, and `credential-bound trusted` are explicit internal variants;
- admission compiles the contract only after exact replay lookup returns no existing Job;
- widening combinations fail closed, including Windows/input/credential/Host-Dependency incompatibilities;
- public MCP Tool schemas, Registry schema v6, and provider/domain/Security authority ownership are unchanged;
- full current-main owner gate `job-01a0cf0f-a02a-76b3-8cc0-59f2e5abd896` passed `fmt`, owner environment, clippy, transactional Runtime tests, the extended Registry reference model, platform owner-boundary tests, and documentation checks.

### R08 — OperationCircuitCompiler

**Goal:** make one internal compiler produce the immutable physical plan.

Conceptual output:

```text
ExecutionCircuit =
  SourceContext
+ OperationIdentity
+ AuthorityContract
+ MaterializationPlan
+ PhysicalBudget
+ ProviderCommitment
+ EvidenceObligations
+ ReconciliationContract
```

**Migration strategy**
1. compile only `workspace.exec` through it;
2. prove schema, operation digest, plan bytes and behavior parity;
3. move `execBound`;
4. move `execBoundTrusted`;
5. move credential-bound trusted execution.

**Acceptance**
- old all-explicit request identity stays replay-compatible;
- omitted/delegated limits retain their existing identity semantics;
- no unenforceable metadata enters operation identity.

**Standing — R08 complete for all four effect-opaque execution families**
- `workspace.exec` / `workspace.execPlan` ordinary proposal admission compiles through `OperationCircuitCompiler::ordinary`; ordinary is integrated on `397dee5ef0caa296283253c03da5f277f4fa2a8d`;
- reduced `workspace.execBound` preserves materialization/preallocated-admission ownership and compiles through `OperationCircuitCompiler::immutable_input_reduced` on `40c414a3901c4383a9d7d122fe7716effbe8506e`;
- trusted `workspace.execBoundTrusted` preserves the trusted-local input boundary and compiles through `OperationCircuitCompiler::immutable_input_trusted`, integrated at `645d50cd51c8efe772de762610e045ea112fb78c`;
- `workspace.execCredentialBoundTrusted` preserves operator-owned encrypted credential materialization and Job-owned ciphertext lifecycle, then compiles through `OperationCircuitCompiler::credential_bound_trusted`; the slice is `c52737fd7bc2b6ccf71418719b220070a620da5f` and is integrated by `897e504916fca4078847005a4b78198042b1c01b`;
- every family emits the existing `SubmitRequest`; authority/request/materialization/plan drift fails closed, exact existing-Job replay remains ahead of current-world reinterpretation, and no public/persisted circuit schema, Registry migration, provider grant, or domain semantic-completion claim was introduced;
- exact integrated-commit full Runtime owner qualification `job-01a0d323-f7ca-7351-8f5c-1d01b4877ca6` passed, including the independent Registry reference-model property, Windows deployer, MCP/auth, owner-boundary and documentation gates;
- structured Runtime self-release remains a separate reconciliable effect and is intentionally outside the effect-opaque OperationCircuitCompiler family set.

---

## RW3 — Provider seams

### R09 — ExecutionProviderSPI

**Goal:** define obligations, not implementation inheritance.

Minimal obligations:

```text
capabilities
validate(plan)
realize(plan, attempt)
observe(owner)
cancel(owner)
reconcile(owner, evidence)
```

Provider guarantees must include:
- exact committed provider identity;
- one physical Attempt owner;
- terminal observation;
- process-tree cancellation;
- crash/restart reconciliation;
- scoped evidence.

**Reject**
- dynamic provider marketplace;
- cross-node router;
- plugin discovery system.

**Standing — R09 qualified**
- internal SPI code: `fd3f166024587e9c943207fc8987cff436f43098`;
- full Runtime owner qualification: `job-01a0d34d-18e1-7140-b577-c34c0c660b4a` PASS, including Core/transactional suites, independent Registry reference-model properties, Windows deployer, MCP/auth, owner-boundary, clippy/check, owner-environment and documentation gates;
- common obligations are `capabilities / validate / realize / observe / cancel / reconcile`;
- required guarantees fail closed if any provider weakens exact committed provider identity, single physical Attempt ownership, terminal observation, process-tree cancellation, crash/restart reconciliation, or scoped evidence;
- Linux and Windows intentionally retain different owner/observation/evidence types; R09 moves no physical OS mechanism;
- no public/persisted schema, dynamic provider registry/marketplace, plugin discovery, cross-node routing, or semantic-effect authority is introduced.

### R10 — LocalLinuxProvider

Extract:
- Runner commitment;
- systemd transient unit;
- cgroup budgets;
- trusted/contained profile realization;
- executable/Host Dependency path witnesses;
- Linux cancellation/reconstruction.

**Acceptance**
```bash
scripts/owner-environment test
scripts/owner-environment extended
sudo scripts/local-acceptance run
```

The real-system receipt must bind the exact candidate commit.

### R11 — WindowsNativeProvider

Extract:
- SCM lifecycle;
- native launcher;
- Job Object;
- limited/elevated authority;
- immutable-input ACL/presentation;
- Power Request;
- native reconstruction.

**Acceptance**
- native Windows acceptance on the exact candidate;
- no WSL/systemd dependency;
- elevated input-bound admission still fails closed.

**Parallelism**
- Provider SPI design may be reviewed in parallel with RW4.
- Linux extraction lands before Windows extraction to test the SPI with one implementation before adapting the second.

---

## RW4 — Reusable control and evidence, without Generic Fabric

### R12 — ControlPrimitives

Start with mechanics already repeated in multiple places:
- Fence;
- Reservation;
- Drain;
- Revalidate;
- Compare-and-swap;
- Commit;
- Receipt;
- Rollback;
- Quarantine.

**Rule**
A primitive owns mechanics only. Operation-specific semantics remain in Release/Workspace/Lifecycle owners.

**First candidate**
Extract `Fence + Revalidate + CAS` because release and lifecycle already need these concepts.

**Reject immediately**
- generic Effect state machine;
- generic compensation engine;
- second durable workflow ledger.

### R13 — EvidenceClaimModel

Internal evidence grammar:

```text
EvidenceClaim
├── subject
├── claim
├── scope
├── witness
├── observation
├── boundary
└── limitation
```

**First mappings**
- Runner provider identity;
- Windows launcher identity;
- executable continuity;
- Host Dependency continuity;
- terminal evidence;
- release receipt.

**Acceptance**
- current serialized evidence remains readable;
- historical records do not need a migration merely because the internal model improves;
- every positive continuity statement has a scope and limitation.

---

## RW5 — Thin adapters

### R14 — MCPRequestAdapter

**Goal:** 23 public Tools stay ergonomic while internals become LEGO-centric.

**Migration**
- choose one execution Tool;
- move semantic work below the MCP adapter;
- compare generated Tool schema/output schema and `toolCatalogDigest`;
- only then migrate the remaining Tools.

**Structural-only acceptance**
- tool catalog digest unchanged;
- no client connector refresh required.

### R15 — OperatorPlaneDecomposition

Current large surfaces:
- deploy ~2k LOC;
- status ~1.5k LOC;
- lifecycle ~1.5k LOC;
- reclaim/cache smaller but substantial.

**First extractions**
- receipt read/write/validation;
- release/lifecycle fence helpers;
- status projection helpers;
- pure candidate/parity checks.

**Do not**
- move operator orchestration into another daemon;
- create another durable state store;
- hide CLI behavior behind an unobservable generic framework.

**Acceptance**
- release/rollback receipts remain exact;
- status health remains bounded by active state;
- scripts get smaller because duplicated mechanics disappear.

---

## RW6 — Falsification and stability envelope

### R16 — StabilityEnvelope

Draft only after the seams work.

Candidate stable laws:
- Workspace identity;
- Job/Attempt distinction;
- exact replay;
- Tool error envelope;
- Artifact identity;
- ambiguity preservation;
- migration/rollback law;
- evidence scope vocabulary.

Candidate evolvable surfaces:
- provider implementation;
- execution profiles;
- optional evidence extensions;
- operator ceilings.

Do **not** declare 1.0 until evidence supports the envelope.

### R17 — CrossPlaneFalsification

Maintain a seam matrix:

| Seam | Required attack |
| --- | --- |
| request → Job | response loss / conflicting replay |
| Job → Attempt | crash between commit and dispatch |
| plan → provider | provider digest drift |
| validate → use | executable/Host Dependency path drift |
| Attempt → terminal | daemon crash / evidence partial |
| cancel → physical owner | descendant survival race |
| release | ingress/drain/restart/probe/rollback faults |
| Workspace close | source-state and shared-Git dependency races |
| Linux provider | real systemd/cgroup |
| Windows provider | native Job Object/SCM |

No seam graduates from local unit success alone.

---

## RW7 — Structural closure

### R18 — StructuralClosure

Only after RW6.

Closure targets:
- `engine.rs` no longer hides Workspace/Job/Authority/Provider responsibilities;
- `registry.rs` is storage/migration/query rather than semantic aggregation;
- MCP Tools are thin;
- operator scripts have less duplicated mechanics;
- old compatibility paths are deleted only with replay/migration evidence.

**Success metric**
Not "more abstractions".

Success is:

```text
fewer hidden authorities
+ smaller hot files
+ fewer duplicate control paths
+ same or stronger evidence
+ same public behavior
+ less local machinery
```

## Multi-Agent execution lanes

Use parallelism primarily for read-only analysis and non-overlapping files. Avoid concurrent edits to `engine.rs`, `types.rs`, `registry.rs`, or `tools.rs`.

### Wave A
- Agent A: R00 invariant inventory.
- Agent B: R01 test taxonomy, read-only until invariant names freeze.
- Agent C: build current Tool→Authority→Provider→Evidence composition matrix.
- Agent D: build current control-primitive duplication census across deploy/lifecycle/cache/Workspace close.
- Agent E: build evidence-claim matrix.

### Wave B
Serial hot-file implementation:
1. R02.
2. R03.
3. R04/R05 in parallel only if they no longer touch the same extracted state files.
4. R06.

### Wave C
- R07 AuthorityContract.
- R08 one-Tool compiler pilot.
- parity gate.
- remaining execution Tools.

### Wave D
- R09 SPI contract.
- R10 Linux extraction.
- Linux real-system acceptance.
- R11 Windows extraction.
- Windows native acceptance.

### Wave E
- R12 control extraction and R13 evidence model can proceed in parallel after interfaces freeze.
- Then R14/R15 adapter thinning.

### Wave F
- R16 stability envelope.
- R17 fault matrix.
- R18 deletion.

## Per-slice verification ladder

Every implementation slice should use the smallest applicable prefix and escalate when physical semantics change:

```bash
cargo fmt --all -- --check
cargo test --locked -q -p ordivon-runtime-core
cargo test --locked -q -p ordivon-runtime-mcp
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
python3 scripts/check_docs.py
scripts/owner-environment test
scripts/owner-environment extended
```

If Linux dispatch/provider/control changes:

```bash
sudo scripts/local-acceptance run
```

If Windows provider changes:

```text
run native Windows Runtime acceptance on the exact candidate revision
```

Before shared-main integration:

```bash
mise run runtime:verify
git diff --check
```

After serialized main integration:

```bash
mise run repo:ci
tools/repo/migration/check-primary-main.sh /root/projects/ordivon
```

## Stop / rollback rules

Stop a slice rather than "fix forward" when:
- Tool catalog/schema changes during a structural-only task;
- Registry semantic version changes unexpectedly;
- a replay becomes redispatch;
- UNKNOWN/lost/orphaned becomes success or retry permission;
- a provider extraction weakens physical ownership/cancellation/reconciliation;
- a new abstraction requires a second durable lifecycle;
- Runtime starts owning Task/workflow/domain truth;
- real-system evidence disagrees with unit tests.

Rollback unit is the smallest completed LEGO extraction commit, not the whole program.

## Immediate executable queue

The old bootstrap queue through R04 is complete. The current queue is:

1. **R07-CLOSED** — `AuthorityContract` implemented on `163db3230483ec932fa8152fb1c9e6bd756e59d5`; reopen only for a proven authority/replay regression.
2. **R08-CLOSED** — ordinary, reduced immutable-input, trusted immutable-input and credential-bound trusted execution all compile through one internal OperationCircuitCompiler into the existing `SubmitRequest`; integrated closure is `897e504916fca4078847005a4b78198042b1c01b` and exact post-integration owner qualification `job-01a0d323-f7ca-7351-8f5c-1d01b4877ca6` PASS.
3. **R09-CLOSED-CANDIDATE** — private static ExecutionProviderSPI qualified at `fd3f166024587e9c943207fc8987cff436f43098` with full owner gate `job-01a0d34d-18e1-7140-b577-c34c0c660b4a` PASS; integrate under current-main fencing, then reopen only for a proven SPI-contract regression.
4. **R10-NEXT** — move LocalLinuxProvider behind the SPI and prove real systemd/cgroup acceptance on the exact candidate without changing Runner wire semantics.
5. **R11 after R10** — adapt WindowsNativeProvider without pretending SCM/Job Object semantics equal systemd/cgroup semantics.
6. **R12/R13** may proceed only behind their dependency and ownership fences; keep launch-token timing/late-result reconciliation in the separate supervisor-evidence lane.

Do not reopen R04 for launch-evidence timing/reconciliation races already reproduced on a clean baseline; those remain with the reconciliation/supervisor evidence owner.
