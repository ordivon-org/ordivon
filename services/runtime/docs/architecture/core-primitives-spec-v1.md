# Core Primitives Spec v1

## Status

This document freezes the first explicit set of `core` primitives for PFIOS platformization.

It complements:

- [Architecture Baseline](./architecture-baseline.md)
- [Core / Pack / Adapter Baseline](./core-pack-adapter-baseline.md)
- [Current Code Classification Map v1](./current-code-classification-map-v1.md)
- [Finance Pack v1 Definition](./finance-pack-v1-definition.md)

It is a semantic contract, not a folder move.

## Purpose

PFIOS now has enough real system behavior that the next architectural step cannot remain implicit.

The purpose of this document is to freeze:

- which primitives belong to `core`
- what each primitive is allowed to mean
- what each primitive must not absorb from domain packs or adapters

This spec exists so future platformization does not:

- pull finance nouns into `core`
- let adapters define system semantics
- let mixed directories continue to blur stable system laws

## One-Sentence Rule

`core` contains only stable system laws.

If a concept is domain-specific, provider-specific, tool-specific, or backend-specific, it is not a `core` primitive.

## Primitive Families

PFIOS `core` should currently be treated as eight primitive families:

1. workflow primitives
2. governance primitives
3. execution primitives
4. state primitives
5. trace and audit primitives
6. knowledge primitives
7. runtime primitives
8. experience primitives

## 1. Workflow Primitives

These define how work runs.

### Stable primitives

- `Task`
- `Workflow`
- `Step`
- `Run`
- `StepResult`
- `RetryPolicy`
- `FallbackPolicy`
- `CompensationAction`
- `Pause / Resume / Cancel`

### Required semantics

- A `Workflow` is a bounded sequence of steps with explicit lifecycle.
- A `Run` is the persisted record of one workflow invocation.
- A `StepResult` must be inspectable and failure-aware.
- `RetryPolicy`, `FallbackPolicy`, and `CompensationAction` must describe recovery behavior explicitly.

### Must not absorb

- recommendation semantics
- review semantics
- finance outcome interpretation
- provider-specific execution logic

### Current repository anchors

- `orchestrator/runtime/`
- `domains/workflow_runs/`

## 2. Governance Primitives

These define what the system may do and how control is expressed.

### Stable primitives

- `DecisionLanguage`
- `ActionContext`
- `ApprovalRequirement`
- `Policy`
- `RiskFlag`
- `EligibilityCheck`
- `HumanReviewGate`

### Required semantics

- `DecisionLanguage` must stay bounded and universal.
- `ActionContext` must remain the mandatory descriptor for consequential action.
- `Policy` is the framework and source-of-truth mechanism, not the domain-specific policy content.
- `RiskFlag` and `EligibilityCheck` are gating concepts, not finance-only objects.

### Must not absorb

- recommendation status meaning
- finance-specific policy thresholds
- provider health logic
- runtime implementation details

### Current repository anchors

- `governance/decision.py`
- `governance/policy_source.py`
- policy and audit framework portions of `governance/`

## 3. Execution Primitives

These define how actions are formalized and proven.

### Stable primitives

- `ActionFamily`
- `ActionRequest`
- `ActionReceipt`
- `ActionResult`
- `FailureModel`
- `IdempotencyKey`
- `Heartbeat / Progress`
- `SideEffectClass`

### Required semantics

- `ActionRequest` must capture intent before consequential action.
- `ActionReceipt` must capture the outcome of one request.
- `FailureModel` must represent honest failure, not just error strings.
- `IdempotencyKey` must remain part of action discipline rather than domain semantics.
- `SideEffectClass` must remain a system-level classification.

### Must not absorb

- recommendation family meaning
- review family meaning
- validation family meaning
- connector implementation details

### Current repository anchors

- `domains/execution_records/`
- `execution/catalog.py`

## 4. State Primitives

These define fact, relation, and lifecycle truth.

### Stable primitives

- `EntityRef`
- `StateRecord`
- `LifecycleState`
- `StateTransition`
- `SourceOfTruth`
- `Relation`
- `TraceLink`
- `Outcome`
- `ArtifactRef`

### Required semantics

- `SourceOfTruth` determines where fact may be read from.
- `Relation` and `TraceLink` must describe real object linkage, not narrative implication.
- `LifecycleState` and `StateTransition` must constrain object evolution.
- `Outcome` must remain a result primitive even when current meaning is finance-shaped.

### Must not absorb

- recommendation-only lifecycle meaning
- review-only lifecycle meaning
- finance-specific symbol semantics
- report rendering implementation details

### Current repository anchors

- `state/trace/`
- state truth portions of `domains/*`
- `domains/workflow_runs/`
- `domains/intelligence_runs/`
- `domains/ai_actions/`

## 5. Trace And Audit Primitives

These define how causality and proof are represented.

### Stable primitives

- `AuditEvent`
- `EventType`
- `TraceBundle`
- `RequestReceiptRefs`
- `Actor`
- `Timestamp`
- `CausalityEdge`

### Required semantics

- `AuditEvent` must record system-proof events, not product narration.
- `TraceBundle` must represent a queryable relation bundle.
- `RequestReceiptRefs` must stay reusable across action families.
- `CausalityEdge` must describe actual system linkage, not inferred storytelling.

### Must not absorb

- finance-only event names as universal semantics
- UI-specific presentation logic
- storage backend details

### Current repository anchors

- `governance/audit/`
- `state/trace/`

## 6. Knowledge Primitives

These define how experience becomes reusable but non-truthful system guidance.

### Stable primitives

- `Lesson`
- `KnowledgeEntry`
- `FeedbackPacket`
- `Hint`
- `EvidenceBundle`
- `CandidateRule`
- `RecurringIssue`
- `FeedbackConsumptionRecord`

### Required semantics

- `Lesson` and `KnowledgeEntry` must remain derived from evidence-backed fact.
- `FeedbackPacket` must remain derived guidance, not truth rewrite.
- `Hint` must remain advisory.
- `CandidateRule` must remain distinct from active policy.
- `RecurringIssue` must remain an aggregation primitive, not a policy decision by itself.

### Must not absorb

- finance-specific extraction rules
- finance-specific recurring issue normalization
- runtime provider behavior
- UI rendering semantics

### Current repository anchors

- `knowledge/feedback.py`
- `domains/knowledge_feedback/`
- retrieval and recurring-issue primitives in `knowledge/`

## 7. Runtime Primitives

These define how bounded reasoning systems are hosted and invoked.

### Stable primitives

- `AgentRuntime`
- `TaskRuntime`
- `Session`
- `ContextBuilder`
- `MemoryPolicy`
- `ToolPolicy`
- `RuntimeHealth`
- `Wake / Sleep / Resume`

### Required semantics

- `AgentRuntime` and `TaskRuntime` must stay provider-neutral.
- `ContextBuilder` must remain a runtime contract, not a finance-specific prompt helper.
- `MemoryPolicy` must define runtime behavior, not finance hint content.
- `RuntimeHealth` must remain implementation-neutral.

### Must not absorb

- Hermes-specific payload shapes
- provider-specific auth and transport
- model-specific capability assumptions

### Current repository anchors

- task and runtime contracts in `intelligence/`
- provider-neutral portions of runtime/client abstractions

## 8. Experience Primitives

These define truthful front-end semantics.

### Stable primitives

- `WorkView`
- `ObjectView`
- `DetailPane`
- `SupervisorAction`
- `MissingState`
- `TrustTier`
- `StatusSurface`
- `TraceSurface`
- `OutcomeSurface`
- `HintSurface`

### Required semantics

- `MissingState` must distinguish empty from unavailable.
- `TrustTier` must distinguish fact, relation, signal, artifact, and derived guidance semantics.
- `TraceSurface`, `OutcomeSurface`, and `HintSurface` must stay semantic view primitives, not domain pages.

### Must not absorb

- finance dashboard layout
- finance recommendation card structure
- review-specific page flow

### Current repository anchors

- `apps/web/src/lib/semanticSignals.ts`
- state-surface helpers in `apps/web/src/components/state/`

## Cross-Family Invariants

The following invariants must hold across all core primitives.

### Invariant 1: core defines laws, not finance nouns

If a concept only makes sense for recommendations, reviews, symbols, or portfolios, it is not a `core` primitive.

### Invariant 2: core defines semantics, not implementations

If a concept only exists because of Hermes, DuckDB, a connector, or a transport, it is not a `core` primitive.

### Invariant 3: core must survive pack replacement

A valid `core` primitive should still make sense if Finance Pack v1 were replaced with Research Pack v1.

### Invariant 4: core must survive adapter replacement

A valid `core` primitive should still make sense if Hermes were replaced with another runtime and DuckDB were replaced with PostgreSQL.

## Current Extraction Targets

These are the first practical extractions implied by this spec.

### Target 1

Make `DecisionLanguage`, `ActionContext`, `ActionRequest`, `ActionReceipt`, `TraceLink`, `Outcome`, `FeedbackPacket`, and `TrustTier` explicit cross-domain contracts.

### Target 2

Separate provider/runtime payload shaping from runtime contracts in `intelligence/`.

### Target 3

Separate request/receipt discipline from recommendation/review/validation family meaning in `execution/`.

### Target 4

Separate knowledge primitives from finance extraction rules in `knowledge/`.

## Non-Goals

This spec does not:

- move directories into `core/` immediately
- define every field of every primitive
- erase the nine-layer architecture
- claim current directories are already pure

## Final Summary

`Core Primitives Spec v1` freezes the stable system laws that PFIOS should preserve across domains and adapters.

Those laws are:

- workflow
- governance
- execution discipline
- state truth
- trace and audit
- knowledge primitives
- runtime contracts
- experience semantics

Compressed:

**If it defines stable system order, it belongs in core. If it defines domain meaning, it belongs in a pack. If it defines implementation integration, it belongs in an adapter.**
