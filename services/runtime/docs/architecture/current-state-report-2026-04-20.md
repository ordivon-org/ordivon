# Current State Report 2026-04-20

> Historical snapshot only.  
> The current operational status report is [current-state-report-2026-04-21](./current-state-report-2026-04-21.md).

## Purpose

This report captures the repository's current state after the first, second, and current follow-on strengthening passes were completed for the single-agent PFIOS baseline.

It is not a future-state architecture note.
It records what is now true in code.

## Current Stage

PFIOS is now past the "single analyze workflow demo" stage.

The repository currently behaves as a single-agent baseline system with:

- bounded intelligence runtime execution
- workflow and intelligence run records
- governance decision language
- execution request / receipt for multiple action families
- traceability across main-chain objects
- outcome backfill from review completion
- derived knowledge extraction from persisted lessons and outcomes
- derived knowledge feedback packets
- governance-side advisory hint consumption
- review-family execution receipts
- review-facing outcome / trace / feedback surface
- minimum retry / compensation discipline in the analyze workflow

This is still not a full flywheel and not a multi-agent system.

## Most Real Main Chain

The most real chain in the repository is now:

`analyze request -> workflow_run -> intelligence_run -> governance decision -> recommendation -> execution request/receipt -> audit -> trace -> review completion -> outcome snapshot -> lesson extraction -> knowledge entry`

What is real in this chain:

- Hermes-backed analyze execution
- persisted `WorkflowRun`
- persisted `IntelligenceRun`
- persisted `AgentAction`
- governance `execute / escalate / reject`
- persisted `Recommendation`
- persisted execution request / receipt for:
  - `analysis_report_write`
  - `recommendation_generate`
- persisted `OutcomeSnapshot`
- persisted `Lesson`
- derived `KnowledgeEntry`
- derived `KnowledgeFeedbackPacket`
- advisory governance hint consumption in later analyze runs
- persisted execution request / receipt for `review_complete`

What is not yet real:

- automatic feedback from outcome into governance
- automatic feedback from knowledge into intelligence
- broader workflow families beyond the current analyze + review path
- complete outcome lifecycle policy
- first-class persisted feedback object

## Layer Reassessment

### Experience

Status: `In Progress`

Real now:

- pages and API surfaces are more truthful than before
- analyze governance language matches current backend decision model

Still weak:

- trace / outcome / feedback are still only partially surfaced
- object visibility still trails system truth

### Capability

Status: `In Progress`

Real now:

- capability contracts remain split by abstraction type
- review pending read path now goes through capability instead of router-local repo reads

Still weak:

- capability cleanup is not complete across all read-side compatibility facades

### Orchestration

Status: `In Progress`

Real now:

- analyze workflow is a formal workflow
- `WorkflowRun` persists step statuses
- step status now carries `attempt` and `recovery_action`
- `ReasonStep` has bounded retry
- `WriteWikiStep` compensation is explicit in workflow recovery detail

Still weak:

- recovery policy is minimal and only real on the analyze path
- no broader fallback strategy

### Governance

Status: `In Progress`

Real now:

- analyze uses explicit `execute / escalate / reject`
- key side effects are bounded by `ActionContext`
- audits share the same decision semantics

Still weak:

- governance is still not a full policy control plane
- policy source is still not centralized
- governance currently consumes hints only on the analyze path

### Intelligence

Status: `In Progress`

Real now:

- Hermes runtime is integrated
- intelligence IO contract is explicit
- `IntelligenceRun` is persisted

Still weak:

- task taxonomy is still narrow
- analyze remains the dominant real task family

### Execution

Status: `In Progress`

Real now:

- action catalog exists
- request / receipt is real for:
  - `analysis_report_write`
  - `recommendation_generate`

Still weak:

- execution adapter consolidation is not done
- only a small set of action families are receipt-backed
- `review_submit` and validation families are still outside execution receipts

### State

Status: `In Progress`

Real now:

- main-chain fact objects are persisted
- state transition discipline exists for key objects
- trace is queryable
- outcome backfill is real

Still weak:

- full trace graph is still partial
- recommendation lifecycle is not yet synchronized with richer outcome policy

### Knowledge

Status: `In Progress`

Real now:

- minimal knowledge-layer objects exist
- evidence-linked knowledge invariants exist
- `LessonExtractionService` is real
- persisted lessons and outcomes can be extracted into `KnowledgeEntry`

Still weak:

- knowledge feedback into governance is now minimally real, but still advisory-only
- no knowledge feedback path into intelligence yet
- no retrieval or surfaced knowledge workflow

### Infrastructure

Status: `In Progress`

Real now:

- runtime startup and DB bootstrap are functional
- health surfaces exist

Still weak:

- infra responsibility is still scattered
- monitoring and runbook discipline remain weak

## What Changed In This Cycle

Compared with the previous state report, the repository gained five meaningful new behaviors:

### 1. Outcomes are now first-class backfilled fact

`ReviewService.complete_review()` now creates `OutcomeSnapshot` and updates `Recommendation.latest_outcome_snapshot_id`.

This means recommendation aftermath is now recorded as state, not only as narrative review text.

### 2. Knowledge is now extractable from fact

The repository no longer stops at persisted lesson rows.

It now supports:

- `Lesson -> KnowledgeEntry`
- `Lesson + OutcomeSnapshot -> KnowledgeEntry`

through `LessonExtractionService`.

### 3. Workflow recovery is now partly explicit

The analyze workflow now has:

- one bounded retry path for retryable Hermes failures
- explicit compensation recording for failed wiki persistence

This is still minimal, but it is no longer purely implicit behavior.

### 4. Knowledge feedback is now prepared and minimally consumed

The repository now supports:

- `KnowledgeFeedbackPacket`
- `knowledge_feedback_prepared` audit
- governance-side advisory hint consumption on the analyze path

This is still not policy rewrite and not intelligence memory, but feedback is no longer metadata-only.

### 5. Review completion is now an execution family

`review_complete` now has:

- `ExecutionRequest`
- `ExecutionReceipt`
- success/failure audit refs
- API response refs

This means the review path is no longer only a domain mutation path.

## Completed Tiers

### First Tier Completed

- `State | Lineage / Trace`
- `Governance | Decision Language`
- `Execution | Request / Receipt (second family)`
- `Knowledge | Knowledge Definition`

### Second Tier Completed

- `State | Outcome Backfill`
- `Knowledge | Lesson Extraction`
- `Orchestration | Retry / Fallback / Compensation`
- `Capability | API Boundary Cleanup`

### Follow-on Modules Completed

- `Knowledge | Knowledge Feedback`
- `Experience | Trace / Outcome / Knowledge Surface`
- `Execution | Additional Action Families / Adapter Consolidation`
- `Governance | Decision Language Centralization`
- `Execution | Review Family Execution`
- `Knowledge | Feedback Consumption into Governance`
- `Experience | Review / Outcome / Feedback Surface Extension`

## Next Priority Direction

The next phase should no longer focus on proving that the main chain exists.

The next useful direction is now:

1. `State | Trace Graph Deepening`
2. `Execution | Review Submit / Validation Family Execution`
3. `Knowledge | Feedback Consumption into Intelligence`
4. `Experience | Trace Detail / Trust-tier Discipline`
5. `Governance | Policy Source of Truth`

## Final Judgment

PFIOS is now a single-agent baseline system with real:

- truth objects
- decision language
- execution receipts
- outcome backfill
- derived knowledge
- derived and consumed governance feedback hints
- review-family execution receipts
- minimal workflow recovery

It is not yet a full learning flywheel and not a multi-agent organization.

The current system is strongest in:

- State
- Intelligence
- analyze-oriented Orchestration
- bounded Governance

The current system is weakest in:

- intelligence-side feedback consumption
- execution breadth beyond recommendation + review_complete
- richer trace/detail surface
- governance policy centralization
