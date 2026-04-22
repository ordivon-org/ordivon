# AegisOS Phase 1 Core Load-Bearing Batch

## Purpose

This document records the Phase 1 batch that turns the frozen Phase 0 primitives into reusable behavior-level contracts.

Phase 1 does **not** perform:

- finance-pack extraction
- adapter directory relocation
- new finance product surfaces

Phase 1 does perform:

- governance behavior strengthening
- runtime abstraction cleanup
- execution platform contract start
- state graph/query strengthening
- knowledge consumption and pre-policy strengthening

## What Phase 1 Completed

### 1. Governance (`Core`)

- `GovernancePolicySource` is now the approved policy-read entrypoint on the analyze path.
- governance hint consumption is now formalized as an explicit advisory-only consumer contract.
- a new approval primitive now exists:
  - `ApprovalRecord`
  - `HumanApprovalGate`
- approval states are now:
  - `pending`
  - `approved`
  - `rejected`
  - `expired`
- `review_complete` can now be blocked until approval is present.

### 2. Intelligence (`Core`)

- `AgentRuntime` is now the runtime-facing interface used by orchestration/runtime callers.
- Hermes remains the only real runtime implementation, but it now behaves as a runtime implementation rather than the system body.
- `MemoryPolicy` is now used explicitly to gate hint-channel injection.
- `HintAwareContextBuilder` now formalizes intelligence-side hint injection into analyze context.
- hint data remains derived guidance:
  - not truth
  - not policy
  - not persisted memory

### 3. Execution (`Core`)

- review and validation adapters now conform to a shared family-level registry contract.
- `ExecutionAdapterRegistry` now exists.
- action-family resolution now occurs by family name:
  - `recommendation`
  - `review`
  - `validation`
- execution progress and heartbeat are now first-class observational records attached to execution requests.
- the first real long-running path using this contract is the existing analyze/recommendation execution path.

### 4. State (`Core`)

- the trace service is now explicitly elevated as a `TraceGraph` contract while preserving compatibility aliases.
- outcome traversal is now formalized through `OutcomeGraph`.
- checkpoint semantics are now stabilized through:
  - `blocked_reason`
  - `wake_reason`
  - `resume_marker`
- `WorkflowRun.lineage_refs` remains the persistence anchor in this phase.

### 5. Knowledge (`Core`)

- feedback generation and feedback usage are now distinct.
- `KnowledgeFeedbackPacketRecord` remains the packet object.
- `FeedbackRecord` now records downstream consumption/audit of feedback usage.
- the first recorded consumers are:
  - governance hint consumption
  - intelligence hint consumption
- recurring issue aggregation is now formalized as a contract rather than only a helper.
- `CandidateRule` now exists as a pre-policy object with non-active states only.

## New Core Types Added

- `ApprovalRecord`
- `HumanApprovalGate`
- `ExecutionAdapterContract`
- `ExecutionAdapterRegistry`
- `ExecutionProgressRecord`
- `TraceGraph`
- `OutcomeGraph`
- `CheckpointState`
- `FeedbackRecord`
- `CandidateRule`

## Invariants Preserved

- hints do not overwrite state truth
- approval absence does not fabricate success
- adapters do not define system meaning
- metadata cannot invent trace truth
- candidate rules do not auto-promote into policy
- Hermes remains an implementation, not a semantic owner

## Main-Chain Effects

The analyze/recommend/review path is now stronger in five specific ways:

1. governance reads policy through a central source
2. analyze receives explicit hint-aware context under `MemoryPolicy`
3. execution-family resolution now goes through a registry
4. progress/heartbeat records can attach to execution requests
5. feedback consumption becomes queryable and auditable

## Validation

Phase 1 was validated through:

- unit tests for:
  - approval
  - adapter registry
  - progress/heartbeat
  - hint-aware context
  - feedback record
  - candidate rule
  - checkpoint state
- integration tests for:
  - review approval-gated completion
  - analyze runtime path and feedback consumption records
  - trace and execution path regressions

## What Phase 1 Did Not Do

- no physical `core/pack/adapter` directory migration
- no finance-pack extraction
- no Hermes adapter relocation
- no wake/resume execution engine
- no public approval console
- no candidate-rule promotion into active policy
- no new finance feature surface

## Next Phase

The next correct batch is not another primitive freeze.

The next correct batch is:

1. Experience supervisor workspace strengthening
2. Orchestration handoff / wake-resume / fallback strengthening
3. Infrastructure scheduler / monitoring-history / runbook strengthening
4. Finance pack extraction planning
5. Hermes runtime adapter extraction
