# H-6: Plan-Only Receipt

> **Status**: PLANNING
> **Date**: 2026-04-26
> **Phase**: H-6 — Plan-Only ExecutionReceipt
> **Depends on**: H-1 (Real Model), H-2 (State Truth Boundary), H-4 (DecisionIntake), H-5 (Governance Hard Gate)

---

## Overview

H-6 closes the DecisionIntake → Governance → Receipt chain with a **plan-only** artifact.
The system can accept a validated intake, run it through governance, and produce an
ExecutionReceipt that records the governance decision — without ever touching a broker,
creating an order, or executing a trade.

This is the minimal viable control loop artifact: a decision was made, governance approved
it, and the receipt proves it.

---

## Goal

```
DecisionIntake (validated)
  → Governance RiskEngine.execute(intake)
    → governance_decision = "execute"
      → Plan-only ExecutionRequest created
        → Plan-only ExecutionReceipt persisted
```

The receipt is a **proof artifact** — it records that governance ran and approved a plan.
It does not execute anything.

---

## Non-Goals

H-6 explicitly does **NOT** touch:

| Non-goal | Why |
|----------|-----|
| Broker integration | No broker adapter, no broker registry |
| Order placement | No order object, no order state machine |
| Trade execution | No trade, no fill, no position update |
| Position management | Position is downstream of trade execution |
| Paper trading | No simulated execution |
| Outcome tracking | Outcome is downstream of execution |
| Review creation | Review is H-3 territory, already closed |
| KnowledgeFeedback | Feedback is H-3 territory, already closed |
| CandidateRule generation | Rules are H-3 territory |
| Recommendation creation | Recommendation is upstream of H-6 (analysis → recommendation → intake) |

H-6 is **pure plan artifact**. It bridges the gap between "governance says yes" and "something is recorded" without crossing into execution.

---

## Required Receipt Metadata

The plan-only `ExecutionReceipt` must carry these fields:

| Field | Value / Constraint | Notes |
|-------|--------------------|-------|
| `receipt_kind` | `"plan"` | Distinguishes from future `"live"`, `"paper"`, `"simulated"` |
| `broker_execution` | `false` | Hard constant for plan-only receipts |
| `side_effect_level` | `"none"` | No external system was touched |
| `decision_intake_id` | `string` | Links back to the validated intake |
| `governance_decision` | `"execute"` | Only `"execute"` intakes produce plan receipts |
| `governance_status` | `"execute"` | Mirrors governance outcome |
| `created_at` | ISO 8601 | Standard timestamp |
| `payload` | snapshot of intake payload at governance time | Immutable record of what was approved |

### Forbidden Fields in Plan-Only Receipts

| Field | Why forbidden |
|-------|---------------|
| `broker_order_id` | No order placed |
| `broker_trade_id` | No trade executed |
| `fill_price` | No fill occurred |
| `executed_quantity` | No quantity executed |
| `position_id` | No position affected |
| `outcome_id` | Outcome is downstream |
| `recommendation_id` | Recommendation is upstream, not part of execution |

---

## Expected Flow

### Happy Path: Validated intake → execute → plan receipt

```
1. DecisionIntake enters with status="validated", governance_status="not_started"
2. RiskEngine.validate_intake(intake) returns GovernanceDecision(decision="execute")
3. Intake governance_status updated to "execute"
4. ExecutionRequest created with:
     - request_kind = "plan"
     - decision_intake_id = intake.id
     - governance_decision = "execute"
5. ExecutionReceipt created with:
     - receipt_kind = "plan"
     - broker_execution = false
     - side_effect_level = "none"
     - decision_intake_id = intake.id
6. Receipt persisted via repository
7. API returns receipt with 201 Created
```

### Sad Paths

| Intake governance_decision | Can create plan receipt? | Why |
|----------------------------|--------------------------|-----|
| `"execute"` | Yes | Governance approved |
| `"reject"` | No | Governance blocked — no plan to record |
| `"escalate"` | No | Needs human intervention — not a plan yet |
| `"not_started"` | No | Governance hasn't run |
| Intake status `"invalid"` | No | Failed validation — cannot reach governance |
| Intake status `"draft"` | No | Incomplete — cannot reach governance |

### Repeated Plan Creation

Calling plan receipt creation twice for the same intake:

| Scenario | Behavior |
|----------|----------|
| Same intake, no prior plan receipt | Creates receipt (normal) |
| Same intake, prior plan receipt exists | Returns 409 Conflict or returns existing receipt (idempotent) |
| Same intake, governance re-evaluated to "reject" after prior "execute" | Returns 409 — governance state is immutable once decided |

Decision on idempotency vs conflict must be explicit in implementation.
Recommendation: **idempotent** — return existing receipt with 200 OK, not 409.
This matches the governance invariant: once `governance_status` is set, it does not change.

---

## Required Tests

### Unit Tests

1. **`test_plan_only_receipt_created_for_execute_intake`**
   - Given: validated DecisionIntake, governance returns "execute"
   - When: plan receipt endpoint called
   - Then: 201 Created, receipt_kind="plan", broker_execution=false, side_effect_level="none"

2. **`test_invalid_intake_cannot_create_plan_receipt`**
   - Given: DecisionIntake with status="invalid"
   - When: plan receipt endpoint called
   - Then: 400 or 422, no receipt persisted

3. **`test_rejected_intake_cannot_create_plan_receipt`**
   - Given: DecisionIntake with governance_decision="reject"
   - When: plan receipt endpoint called
   - Then: 422 Unprocessable, governance blocked

4. **`test_escalated_intake_cannot_create_plan_receipt`**
   - Given: DecisionIntake with governance_decision="escalate"
   - When: plan receipt endpoint called
   - Then: 422 Unprocessable, needs human review

5. **`test_repeated_plan_creation_is_idempotent`**
   - Given: intake already has a plan receipt
   - When: plan receipt endpoint called again
   - Then: 200 OK, returns existing receipt (idempotent)

6. **`test_plan_receipt_does_not_create_recommendation`**
   - Verify: no Recommendation row created as side effect of plan receipt

7. **`test_plan_receipt_does_not_create_outcome`**
   - Verify: no Outcome row created as side effect of plan receipt

8. **`test_plan_receipt_does_not_touch_broker`**
   - Verify: no broker adapter called, no order object created, no trade state change

### Integration Tests

9. **`test_plan_receipt_api_roundtrip`**
   - POST intake → validate → POST governance execute → POST plan receipt → GET receipt
   - Verify: full chain returns consistent receipt with correct metadata

---

## Implementation Location

| Component | Likely Path |
|-----------|-------------|
| Plan-only receipt model/schema | `execution/adapters/finance.py` or `execution/receipts.py` |
| Plan-only receipt endpoint | `apps/api/app/api/v1/finance_decisions.py` (extend existing) |
| Plan-only receipt tests | `tests/unit/test_h6_plan_only_receipt.py` |
| Integration test | `tests/integration/test_h6_plan_receipt_api.py` |

---

## Dependencies (Already Built)

| Dependency | Status | H-Stage |
|------------|--------|---------|
| DecisionIntake model + validation | ✅ Done | H-4 |
| FinanceDecisionValidationResult | ✅ Done | H-4 |
| RiskEngine.validate_intake | ✅ Done | H-5 |
| GovernanceDecision | ✅ Done | H-5 |
| ExecutionRequest model | ✅ Done | T-7 / Phase 0 |
| ExecutionReceipt model | ✅ Done | T-7 / Phase 0 |
| SQLAlchemy ORM (truth source) | ✅ Done | H-2 |
| Finance decisions API endpoint | ✅ Done | H-4 / H-5 |

---

## What H-6 Unlocks

- H-7 (future): Broker integration — plan receipt becomes the handoff point to real execution
- P4: Personal Control Loop can now produce plan artifacts without actual trading
- Auditability: every governance decision that says "execute" leaves a durable artifact

---

## Risks

| Risk | Mitigation |
|------|------------|
| Plan receipt model overlaps with existing ExecutionReceipt | Use receipt_kind discriminator; plan receipts are a subset |
| Repeated creation could create duplicate artifacts | Explicit idempotency test + implementation |
| Governance status mutation after receipt creation | Enforce governance immutability invariant |
