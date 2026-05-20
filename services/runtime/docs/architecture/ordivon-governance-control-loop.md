# Ordivon Governance Control Loop

Status: `current`
Authority: `source_of_truth`
Purpose: Define the complete Ordivon line from reality disturbance to governed state update and policy feedback.
Supersedes: historical architecture loops, phase-flow notes, and deep-research control-loop prose.
Verification: document registry checks, red-team runner evidence, receipt/debt/policy lifecycle tests.

## Core Line

```text
Reality Disturbance
-> Observation
-> Declaration
-> Semantic Decomposition
-> Objectification
-> Admission
-> Evidence Binding
-> Authority Binding
-> State Classification
-> Gate Decision
-> Execution Plan
-> Execution
-> Trace / Receipt
-> Reconciliation
-> State Update
-> Disposition
-> Policy Candidate
-> Methodology Feedback
-> Next Intent
```

This is not a documentation workflow. It is a control loop for claims and
actions.

## Object Model

Every governed unit must reduce to these fields before it can affect state:

- `object_id`: stable identity.
- `object_type`: claim, intent, obligation, dispatch, observation, receipt,
  debt, policy candidate, policy, closure, suppression, or seal.
- `actor`: human, AI, service, adapter, checker, or workflow.
- `target`: bounded object or resource being claimed about or acted on.
- `scope`: what the object covers and what it excludes.
- `evidence_refs`: logs, tests, hashes, traces, receipts, or external records.
- `authority_refs`: signed token, owner review, policy decision, or human
  approval.
- `state`: governed state, not prose.
- `lifecycle`: allowed transitions and closure conditions.

Objects missing target, evidence boundary, or authority boundary are not ready
for execution.

## State Flow

```text
UNKNOWN
-> ADMITTED
-> UNVERIFIED
-> DEGRADED
-> READY_WITHOUT_AUTHORIZATION
-> AUTHORIZED
-> EXECUTED
-> OBSERVED
-> EXACT / NON_EXACT / SYSTEM_ERROR
-> CLOSED / DEBT_OPEN / SUPPRESSED_WITH_EXPIRY
```

`READY_WITHOUT_AUTHORIZATION` is intentionally separate from `AUTHORIZED`.
Readiness says enough evidence may exist to ask for action. Authorization says
the action may occur.

## The Three Inner Loops

Semantic loop:

```text
Reality -> Observation -> Declaration -> Objectification
```

Governance loop:

```text
Object -> Evidence -> Authority -> State -> Gate
```

Execution loop:

```text
Gate -> Execution -> Receipt -> Reconciliation -> State Update
```

The outer compounding loop is:

```text
State Update -> Debt -> Policy Candidate -> Methodology Feedback
```

## Gate Rules

- no signed valid authority, no side effect;
- no evidence-bound object, no closure;
- no comparator result, no success receipt;
- no verification receipt, no debt closure;
- no reviewer authority, replay result, rollout plan, and rollback plan, no
  policy promotion;
- no registered adapter source and dispatch reference, no trusted observation.

## Failure Modes

- Text directly updates state.
- AI-written observation becomes trusted evidence.
- Receipt is manually written as success.
- Duplicate dispatch consumes the loser token.
- Adapter ack is treated as success.
- Policy deny occurs after authority consumption or dispatch.
- Ledger drift is detected but not fail-closed.
- Suppression removes history instead of creating an expiring exception.

Each failure mode must have a negative test or red-team scenario before the
corresponding stage can claim governed standing.

## What This Changes In Implementation

- Every trusted path should expose request objects and validated constructors.
- Dispatch must be transactional: policy decision, authority use, ledger event,
  dispatch, observation, receipt, and debt must not split into half-state.
- Reconciliation must compare declared obligation against observed evidence,
  not trust adapter acknowledgements.
- Runner output, not hand-written fixtures, is the only input for dogfood seal
  generation.
