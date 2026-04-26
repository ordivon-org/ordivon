# Governance / Receipt / Review Loop

> **Status**: Canonical lifecycle document
> **Date**: 2026-04-26
> **Phase**: Docs-D2 — core baseline documentation
> **Depends on**: H-1 through H-6 closure; H-7 will extend this document

## Purpose

This document defines the lifecycle of the three core objects in the Ordivon control loop:

1. **Receipt** — Immutable record that a governed action was attempted
2. **Review** — Human or automated post-hoc assessment of an outcome
3. **CandidateRule** — Proposed policy derived from review lessons

It answers: where do these objects come from, what can they become, and how do they connect?

---

## The Control Loop (High Level)

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  Intelligence judges ──▶ Recommendation                           │
│                              │                                    │
│                              ▼                                    │
│  Governance gates ──────▶ GovernanceDecision                      │
│                              │                                    │
│                     ┌────────┼────────┐                           │
│                     │        │        │                           │
│                     ▼        ▼        ▼                           │
│                  deny    escalate  execute                        │
│                   │         │        │                            │
│                   ▼         ▼        ▼                            │
│               STOP     WAIT    ExecutionRequest                   │
│                                    │                              │
│                                    ▼                              │
│  Execution acts ───────────▶ ExecutionReceipt                     │
│                                    │                              │
│                                    ▼                              │
│  Outcome emerges ──────────▶ Outcome (fact)                       │
│                                    │                              │
│                                    ▼                              │
│  Experience learns ────────▶ Review ──▶ Lesson ──▶ CandidateRule  │
│                                                         │         │
│                                                         ▼         │
│  Policy updates ─────────────────────────────────▶ Policy         │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Receipts

### Definition

A receipt is an **immutable, append-only record** that a governed action was attempted. Receipts are proof artifacts. They do not execute anything.

### Receipt types

| Type | receipt_kind | Meaning | Introduced |
|------|-------------|---------|------------|
| Plan-only | `"plan"` | Governance approved a plan; no execution occurred | H-6 |
| Live (future) | `"live"` | Governance approved; broker executed | H-7+ |
| Paper (future) | `"paper"` | Simulated execution; no real money | Future |
| Rejected | N/A | No receipt created; governance blocked | H-5 |

### Receipt lifecycle

```
                    ┌──────────────┐
                    │  Not Started  │
                    └──────┬───────┘
                           │ Governance runs
                    ┌──────▼───────┐
                    │  Pending     │ ← GovernanceDecision = "execute"
                    └──────┬───────┘
                           │ Receipt created
                    ┌──────▼───────┐
                    │  Recorded    │ ← Immutable from this point
                    └──────────────┘
```

Receipts have no "cancelled" or "deleted" state. Once recorded, a receipt is permanent.

### Receipt invariants

| Invariant | Enforcement |
|-----------|------------|
| Receipt is immutable after creation | No update endpoint; only GET |
| Receipt requires a governance decision | Cannot create receipt without `governance_decision = "execute"` |
| Receipt references its intake | `decision_intake_id` is required |
| Receipt does not execute anything | Receipt creation is a write operation; no broker call |
| Receipt is idempotent for same intake | Repeated creation returns existing receipt |

### Receipt forbidden fields

| Field | Why forbidden |
|-------|---------------|
| `broker_order_id` | No order placed (plan-only) |
| `broker_trade_id` | No trade executed |
| `fill_price` | No fill occurred |
| `executed_quantity` | No quantity executed |
| `position_id` | No position affected |
| `outcome_id` | Outcome is downstream of execution |
| `recommendation_id` | Recommendation is upstream of decision |

---

## Reviews

### Definition

A review is a **human or automated post-hoc assessment** of an outcome. Reviews answer: "Did the action we took produce the result we expected?"

### Review lifecycle

```
┌──────────────┐
│   Pending    │ ← Review created, awaiting assessment
└──────┬───────┘
       │ Assessor (human or automated) evaluates
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌────┐  ┌──────┐
│Good│  │ Bad  │
└──┬─┘  └──┬───┘
   │       │
   │       ▼
   │  ┌─────────┐
   │  │ Lessons  │ ← Extracted from bad outcomes
   │  └────┬────┘
   │       │
   ▼       ▼
┌──────────────┐
│   Closed     │
└──────────────┘
```

### Review invariants

| Invariant | Why |
|-----------|-----|
| Review references an Outcome | Review assesses a specific outcome, not a general feeling |
| Review may generate Lessons | Lessons are extracted from reviews, not created independently |
| Review is durable | Reviews are stored facts, not ephemeral UI actions |
| Review does not change the Outcome | Outcome is immutable fact; Review is interpretation |

### What reviews feed

| Feed | Mechanism |
|------|-----------|
| Knowledge feedback | Lessons from past reviews are injected into future analysis tasks as hints |
| Candidate rules | Multiple reviews revealing the same pattern → CandidateRule proposal |
| Operator visibility | Review status is visible on the supervisor console |

---

## CandidateRules

### Definition

A CandidateRule is a **proposed policy** derived from review lessons. CandidateRules require explicit adoption before becoming active Policy.

### CandidateRule lifecycle

```
┌──────────────┐
│   Proposed   │ ← Generated from Lesson(s)
└──────┬───────┘
       │ Human reviews the candidate
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌─────┐ ┌────────┐
│Adopt│ │Reject  │
└──┬──┘ └───┬────┘
   │        │
   ▼        ▼
┌─────┐ ┌────────┐
│Policy│ │Archived│
└─────┘ └────────┘
```

### CandidateRule invariants

| Invariant | Why |
|-----------|-----|
| CandidateRule is not auto-adopted | Policy activation requires explicit human approval |
| CandidateRule references its source Lesson(s) | Traceability from policy back to the experience that generated it |
| CandidateRule can be rejected | Not every pattern should become policy |
| CandidateRule is not executable until adopted | CandidateRules are proposals; Policies are active |

### The feedback loop

```
Bad Outcome → Review → Lesson → CandidateRule → (human adopt) → Policy
                                                                    │
                                                                    ▼
                                                   Future governance uses new policy
                                                                    │
                                                                    ▼
                                                   Better outcomes (hopefully)
```

This is the learning loop. It is not real-time. It is not automated. It requires human judgment to close the loop from CandidateRule to Policy.

---

## Object Relationships

```
DecisionIntake ─────────────────────────────────────────────┐
      │                                                      │
      ├──▶ GovernanceDecision                                │
      │         │                                             │
      │         ├── "deny" → STOP (no receipt)                │
      │         ├── "escalate" → WAIT (no receipt)            │
      │         └── "execute" → ExecutionRequest ──▶ ExecutionReceipt
      │                                                      │
      └──▶ Recommendation (if this intake came from analysis) │
                                                              │
ExecutionReceipt ──▶ Outcome (emerges after execution)        │
                         │                                    │
                         └──▶ Review ──▶ Lesson ──▶ CandidateRule
                                                              │
CandidateRule ──▶ (human adopt) ──▶ Policy ◀──────────────────┘
                                        │
                                        └──▶ Future DecisionIntakes are governed by this policy
```

---

## What Happens When (Phase Map)

### H-6 (Current): Plan-Only Receipt

```
DecisionIntake → Governance → Plan-only ExecutionReceipt
```

Receipt proves governance ran and approved a plan. No execution, no outcome, no review.

### H-7 (Next): Manual Outcome Capture

```
Plan Receipt → (time passes) → Manual Outcome capture → Review creation
```

Introduces the Outcome and Review objects. Connects receipts to downstream assessment.

### H-8+ (Future): Automated Review + Feedback

```
Outcome → Automated Review → Lesson extraction → CandidateRule generation
```

Closes the learning loop. Lessons from past decisions influence future analysis.

---

## Data Integrity Rules

| Rule | Enforcement |
|------|------------|
| Receipt is immutable | No update/delete endpoint |
| Governance decision is immutable once set | State machine; cannot transition from "execute" to "reject" |
| Outcome references exactly one receipt | Foreign key constraint |
| Review references exactly one outcome | Foreign key constraint |
| Lesson references at least one review | Application-level constraint |
| CandidateRule references at least one lesson | Application-level constraint |
| Policy activation is logged as AuditEvent | Governance writes audit on policy change |

---

## Anti-Patterns

| Anti-pattern | Why it's wrong |
|-------------|---------------|
| Creating a receipt without governance | Governance is the gate; bypassing it loses auditability |
| Creating a review without an outcome | Reviews assess results; no result → nothing to review |
| Auto-adopting CandidateRules | Policy activation is a governance decision, not an automation |
| Modifying a receipt after creation | Receipts are immutable proofs; modification destroys auditability |
| Deleting a receipt | Even "wrong" receipts are historical facts; mark as superseded, never delete |
| Skipping review for bad outcomes | Every bad outcome is a learning opportunity; skipping review wastes it |

---

## Relationship to Other Documents

- [ordivon-system-definition.md](ordivon-system-definition.md) — Invariant 3: Governance gates every action; Invariant 4: Execution produces receipts
- [execution-request-receipt-spec.md](execution-request-receipt-spec.md) — Current execution receipt implementation
- [review-workflow-gap.md](review-workflow-gap.md) — Known gap: review workflow bypasses orchestrator
- [h6-plan-only-receipt-plan.md](../roadmap/h6-plan-only-receipt-plan.md) — H-6 implementation plan
- [state-truth-boundary.md](state-truth-boundary.md) — State truth boundary for persisted objects
