# State Truth Inventory

## Status

This document defines the current canonical fact objects for PFIOS as of `2026-04-19`.

It exists to answer one question:

**which persisted objects currently count as system truth, who owns their meaning, and what fact gaps still remain on the main chain?**

This inventory is intentionally narrower than a full domain map.
It is about persisted truth and ownership, not every dataclass in the repo.

## Classification Rules

Use these rules when deciding whether an object belongs in this inventory.

- A truth object must have a persisted record or an explicitly planned persisted record.
- A truth object must answer a factual question about what happened, what exists, or what state the system is in.
- A projection, convenience payload, page aggregate, or narrative summary is not a truth object by itself.
- Knowledge artifacts may still be persisted facts, but their meaning must remain experience-oriented rather than live operational truth.

## Current Canonical Fact Objects

| Object | Table / Store | Primary Owner | Layer Meaning | What It Records | Current Main-Chain Role | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `Analysis` | `analyses` | `domains/research` | State-backed domain fact | a completed analysis result plus metadata and lineage hooks | starts the analyze chain | metadata currently carries `agent_action_id`, `intelligence_run_id`, and `document_path` |
| `Recommendation` | `recommendations` | `domains/strategy` | State-backed domain fact | a recommendation derived from analysis with lifecycle fields | main product action object after governance allow | still mixes some lifecycle and convenience fields, but it is canonical fact |
| `Review` | `reviews` | `domains/journal` | State-backed journal fact | review work, expected outcome, observed outcome, and verdict | review/governance learning chain | review meaning belongs to Journal, not pure State |
| `OutcomeSnapshot` | `outcome_snapshots` | `domains/strategy` | State-backed domain fact | recommendation outcome observations and evidence refs | downstream result truth for recommendation effectiveness | remains strategy-owned because it measures recommendation outcome semantics |
| `AuditEvent` | `audit_events` | `governance/audit` | State-backed governance fact | event trace with linked entity ids and payload | proof of analysis/recommendation/review activity | audit is not the same as business truth, but it is canonical trace fact |
| `UsageSnapshot` | `usage_snapshots` | `state/usage` | Operational state fact | system usage counters and daily operational totals | operational monitoring and validation input | explicitly operational truth, not domain meaning |
| `AgentAction` | `agent_actions` | `domains/ai_actions` | State-backed intelligence artifact fact | structured AI action output, usage, tool trace, and summaries | AI action lineage for analyze | records the AI action artifact, not the runtime lifecycle itself |
| `IntelligenceRun` | `intelligence_runs` | `domains/intelligence_runs` | State-backed runtime fact | task request identity, trace id, pending/completed/failed runtime lifecycle | bounded Hermes analyze run trace | newly added to separate runtime invocation truth from `AgentAction` |
| `Issue` | `issues` | `domains/journal` | State-backed journal fact | validation/review/workflow issues with source refs | recurring issue and correction input | persisted fact today, but semantically belongs to learning/journal space |
| `Lesson` | `lessons` | `domains/journal` | State-backed knowledge fact | reusable learning extracted from reviews and sources | early knowledge loop persistence | persisted fact, but not live operational truth |

## Ownership Boundaries

### Research

- `Analysis` is the canonical record of what the system concluded during analyze.
- report summaries and page payloads may project it, but they do not replace it.

### Strategy

- `Recommendation` and `OutcomeSnapshot` are the canonical truth for recommendation lifecycle and downstream outcome semantics.
- UI-level recommendation cards are projections of this truth, not substitutes for it.

### Journal

- `Review`, `Issue`, and `Lesson` are persisted facts, but their semantic ownership remains journal/learning rather than generic operational state.
- Their storage does not make them equivalent to live state transitions for execution or workflow runtime.

### Governance

- `AuditEvent` is the canonical proof trail for what the system recorded as having happened.
- Audit does not own business meaning, but it owns trace fact.

### Operational State

- `UsageSnapshot` and `IntelligenceRun` are operational truth objects.
- `AgentAction` is a persisted AI artifact tied to that runtime, but it should not absorb runtime lifecycle responsibilities.

## Main-Chain Fact Map

The current analyze-centered fact chain is:

1. `IntelligenceRun`
2. `AgentAction`
3. `Analysis`
4. `Recommendation`
5. `AuditEvent`
6. `Review` (when review work exists)
7. `OutcomeSnapshot` (when outcome backfill exists)
8. `Lesson` / `Issue` (when learning extraction exists)

Today this chain is strongest through:

- `IntelligenceRun -> AgentAction -> Analysis -> Recommendation -> AuditEvent`

It is weaker through:

- `Recommendation -> Review`
- `Recommendation -> OutcomeSnapshot`
- `OutcomeSnapshot / Review -> Lesson`

## Canonical Metadata Links Already In Use

These links already exist in the main chain and should be treated as real trace hooks:

- `Analysis.metadata.agent_action_id`
- `Analysis.metadata.intelligence_run_id`
- `Analysis.metadata.document_path`
- `Recommendation.analysis_id`
- `Recommendation.latest_outcome_snapshot_id`
- `Review.recommendation_id`
- `Review.analysis_id`
- `AuditEvent.analysis_id`
- `AuditEvent.recommendation_id`
- `AuditEvent.review_id`
- `AuditEvent.outcome_snapshot_id`

## Missing Truth Objects

These truth objects are still missing or not yet first-class enough.

| Missing Object | Why It Matters | Priority | Suggested Owner |
| --- | --- | --- | --- |
| `WorkflowRun` | orchestrator still lacks a canonical run object for step status, failure reason, and workflow-level timing | P0 | `state/` or `orchestrator` with state-backed storage |
| `ExecutionReceipt` | meaningful actions still lack a canonical receipt fact separate from domain objects and audit payloads | P0 | `execution/` with state-backed persistence |
| `ReportRecord` | reports currently exist mostly as rendered artifacts and metadata, not as a first-class persisted fact object | P1 | likely `domains/reporting` or another state-backed reporting module |
| `ValidationRecord` | validation issues exist, but validation runs/signals are not yet a unified state truth family | P1 | `validation/` or `state/validation` |

## Non-Canonical Objects To Avoid Mislabeling

These should not be treated as truth objects on their own:

- API response payloads
- dashboard aggregates
- capability view projections
- wiki markdown content by itself
- report rendering output dictionaries
- AI narrative text that is not tied back to a persisted object

## Immediate Implications

This inventory changes the next-step interpretation in three ways:

1. `IntelligenceRun` is now part of the state truth baseline, not just an observability note.
2. `Issue` and `Lesson` are persisted facts but belong semantically to Journal/Knowledge, so they must not be treated as generic State ownership wins.
3. the next State task should focus on `WorkflowRun`, state transitions, and lineage hardening rather than inventing new convenience projections.

## Follow-on Work Unlocked

- harden recommendation/review/outcome state transitions
- add `WorkflowRun` as a first-class fact object
- add `ExecutionReceipt` as a first-class fact object
- formalize lineage queries across `Analysis`, `Recommendation`, `Review`, `OutcomeSnapshot`, `AuditEvent`, and `IntelligenceRun`
