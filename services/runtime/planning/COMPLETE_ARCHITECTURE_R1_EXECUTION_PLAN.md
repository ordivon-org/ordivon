# Runtime Complete Architecture R1 — Executable LEGO Plan

Status: RW0_IN_PROGRESS
Truth role: planning projection, not Runtime project truth
Source revision: `75dc93c56e367535cbff0d50921d188798c9de5e`

This plan evolves the already-operational Runtime by strangler-style internal extraction. It does **not** recreate the retired Execution Fabric R1, does not rewrite Runtime, and does not widen Runtime authority.

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

The first actual implementation queue is deliberately small:

1. **R00-A** — write invariant manifest.
2. **R00-B** — map every invariant to proving tests/evidence.
3. **R01-A** — produce test taxonomy without moving files.
4. **R01-B** — split one low-conflict test category and prove zero behavior change.
5. **R02-A** — census Workspace responsibilities currently inside `engine.rs/types.rs/registry.rs`.
6. **R03-A** — census Job/Attempt responsibilities and transaction seams.
7. **R07-A** — read-only Tool→Authority composition matrix.
8. **R12-A** — read-only recurring control primitive census.
9. **R13-A** — read-only evidence claim/scope/witness matrix.

Only after items 1–4 are green should production Rust module extraction start.
