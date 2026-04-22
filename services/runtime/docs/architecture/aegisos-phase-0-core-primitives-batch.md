# AegisOS Phase 0 Core Primitive Freeze

## Status

This document records the Phase 0 batch completion for the working platform identity:

- external: `AegisOS`
- internal: `CAIOS`

Phase 0 was not a directory migration.

Phase 0 was a **primitive freeze pass** over the existing repository reality.

## What Was Frozen

The following eight primitives are now explicitly frozen as `Core` contracts:

1. `DecisionLanguage`
2. `ActionRequest / ActionReceipt`
3. `Outcome`
4. `FeedbackPacket`
5. `TraceLink`
6. `Task / Run`
7. `AgentRuntime`
8. `MemoryPolicy`

## What “Frozen” Means Here

Phase 0 does **not** mean every future platform behavior already exists.

It means:

- the primitive now has an explicit contract
- the primitive has validation rules
- the primitive has at least one live code anchor
- the primitive is connected to at least one real path
- future work must conform to the primitive instead of reinventing semantics locally

## Completed Primitive Freeze

### 1. DecisionLanguage

`GovernanceDecision` now carries:

- `decision`
- `reasons`
- `source`
- `evidence`
- `actor`
- `scope`

The allowed decision set remains:

- `execute`
- `escalate`
- `reject`

This is now the canonical decision primitive.

### 2. ActionRequest / ActionReceipt

`ExecutionRequest` and `ExecutionReceipt` now have stricter primitive validation:

- request status must be one of:
  - `pending`
  - `blocked`
  - `succeeded`
  - `failed`
  - `cancelled`
- receipt status must be one of:
  - `pending`
  - `succeeded`
  - `failed`

Success and failure semantics are now explicitly validated.

### 3. Outcome

`OutcomeSnapshot` now behaves as the current `Outcome` primitive anchor with:

- explicit subject semantics
- explicit trigger reason requirement
- explicit source-of-truth classification

It remains recommendation-shaped today, but its primitive semantics are now frozen for later generalization.

### 4. FeedbackPacket

`KnowledgeFeedbackPacket` is now frozen as:

- derived
- advisory-only
- not truth
- not policy

`KnowledgeHint` target semantics are now validated instead of being open-ended.

### 5. TraceLink

`TraceLink` is now the primitive name for relation records used by trace bundles.

Allowed relation states are frozen as:

- `present`
- `missing`
- `unlinked`

Narrative metadata is still forbidden from inventing truth relations.

### 6. Task / Run

`WorkflowRun` remains the current persisted run anchor.

`TaskRun` and `RunCheckpoint` now freeze the generalized interpretation layer for:

- run status
- blocked reason
- wake reason
- resume marker

This creates the abstraction base for later wake/resume work without forcing immediate storage migration.

### 7. AgentRuntime

`AgentRuntime` is now frozen as the provider-neutral runtime interface.

Current implementations:

- `MockReasoningProvider`
- `HermesAgentProvider`

Hermes is therefore now explicitly treated as a runtime implementation rather than the system body itself.

### 8. MemoryPolicy

`MemoryPolicy` now freezes the boundary between:

- transient context
- persisted memory
- feedback hints
- forbidden writes to canonical truth

The analyze-task builder now respects this policy when deciding whether hint-derived memory channels may be injected.

## Invariants Locked By Phase 0

Phase 0 freezes these core invariants:

1. governance decisions must be explicit and serializable
2. no success receipt means no success semantics
3. outcomes must not be invented when absent
4. feedback packets remain advisory-only
5. trace relations cannot be created from narrative-only metadata
6. run/checkpoint semantics must be explicit before wake/resume expansion
7. adapters may implement runtime behavior but may not define system meaning
8. hint injection must not rewrite canonical truth

## Test Coverage Used

### New primitive contract tests

- `tests/unit/test_phase0_core_primitives.py`

### Existing regression tests rerun

- `tests/unit/governance/test_governance_decision.py`
- `tests/unit/test_execution_record_service.py`
- `tests/unit/test_trace_service.py`
- `tests/integration/test_hermes_analyze_api.py`
- `tests/integration/test_trace_api.py`

### Checks

- `python -m compileall ...`
- `pnpm --dir apps/web exec tsc --noEmit`

## What Phase 0 Did Not Do

Phase 0 did **not**:

- extract finance into a physical pack directory
- move Hermes into a new top-level adapters tree
- create a generalized trace graph engine
- create a generalized outcome graph engine
- implement wake/resume runtime behavior
- implement approval flow

Those belong to the next phase.

## Next Phase

Phase 1 should now start from these five module groups:

1. `Governance` strengthening
2. `Intelligence` runtime abstraction strengthening
3. `Execution` platformization start
4. `State` graph and outcome strengthening
5. `Knowledge` progression from feedback packet toward candidate-rule preconditions

Compressed:

**Phase 0 froze meaning. Phase 1 should now strengthen behavior.**
