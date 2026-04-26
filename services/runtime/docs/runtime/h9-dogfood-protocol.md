# H-9: Dogfood Protocol

> **Date**: 2026-04-26
> **Status**: ACTIVE
> **Owner**: Ordivon
> **Scope**: Real/realistic Finance DecisionIntake usage against H-4 → H-8 control loop
> **Non-goals**: Feature development, API changes, ORM changes, broker integration, automatic trading, multi-factor systems, Coding Pack, Health Pack, P5
> **Last verified**: 2026-04-26

## Purpose

H-9 is the first real-world pressure test of the Ordivon Finance control loop.
It answers the hardest question:

> **Does Ordivon actually make high-consequence financial decisions more controllable, more reviewable, and harder to self-deceive about?**

The goal is **not** to pass tests. The goal is to discover whether H-4 through H-8
change behavior in practice — and whether the resulting data justifies P4 Closure
or demands a redesign before going further.

## Why H-9 Exists

H-4 through H-8 were built incrementally, each with passing tests:

| Stage | What | Status |
|-------|------|--------|
| H-4 | DecisionIntake validation with discipline rules | ✅ |
| H-5 | Governance hard gate (12 rules, reject > escalate > execute) | ✅ |
| H-6 | Plan-only Receipt (field-level, broker-free) | ✅ |
| H-6R | PG-backed full regression | ✅ |
| H-7 | Manual Outcome Capture + Review Link | ✅ |
| H-8 | Review Closure on Manual Outcome | ✅ |

But tests passing ≠ the system works under real use.

H-9 exists to bridge that gap. It forces Ordivon to face real decisions, real errors,
real bypass temptations, and real friction — and to record whether the control loop
actually constrains behavior.

## Entry Criteria

- [x] H-8 committed and tagged (`h8-review-outcome-closure`)
- [x] H-6R PG-backed full regression passing
- [x] Postgres + Redis containers available
- [x] Hermes Bridge running (optional: dogfood can use mock for intake, bridge for analysis)
- [ ] At least 10 dogfood runs planned
- [ ] Evidence report document created (`h9-evidence-report.md`)

## Dogfood Run Count Target

- **Phase 1 (H-9A)**: 10 real or realistic Finance DecisionIntake runs
- **Phase 2 (H-9B)**: 30+ runs before P4 Closure evidence

10 runs is the minimum to discover process friction, field uselessness, and bypass
temptations. 30 runs is the minimum to talk about loop stability.

## Valid Run Types

Every H-9 dogfood record must use the **Finance DecisionIntake** flow.
No other domain (no ContentIntake, no generic intake).

### Required Chain (Full Run)

```
DecisionIntake
  → Governance (PolicyEngine + RiskEngine)
  → Plan-only Receipt (broker_execution=false)
  → Manual Outcome (outcome_source=manual)
  → Review (outcome_ref → verdict → cause_tags)
  → Lesson / KnowledgeFeedback
```

### Allowed Partial Chains

Real systems don't always complete. These are valid dogfood runs:

| Partial Chain | Description | Counts Toward Goal |
|--------------|-------------|-------------------|
| intake → reject | Governance rejects the intake | ✅ Yes |
| intake → escalate | Governance escalates for human review | ✅ Yes |
| intake → execute → no action taken | Receipt generated but user chooses not to act | ✅ Yes |
| intake → plan receipt → outcome pending | Receipt exists but outcome not yet captured | ✅ Yes (pending) |

These are **not failures** — they're evidence of the system doing its job.

### Required Coverage Across 10 Runs

- At least **2 of 3** governance outcomes: reject / escalate / execute
- At least **3** full-chain runs to Review
- At least **3** Lessons generated

## Prohibited Actions

H-9 is a **read-only pressure test** of the existing H-4 → H-8 loop.
The following are **strictly prohibited** during H-9:

| Prohibited | Reason |
|-----------|--------|
| Broker execution (`broker_execution=true`) | H-6 is plan-only; broker gate is P4+ |
| Exchange import (CCXT, Binance API) | No live position/order import |
| Automatic PnL calculation | PnL is P4/P5 territory |
| Automatic CandidateRule generation | Rules are human-defined until P4 |
| Automatic Policy promotion | Policy changes require human review |
| Modifying source code | H-9 does not touch code |
| Modifying tests | No new tests, no test changes |
| Creating ORM tables/models | No schema changes |
| Adding API endpoints | No API expansion |
| Hermes Agent tool delegation | Dogfood uses the PFIOS API, not Hermes agent tools |
| Multi-factor decision intake | Single decision at a time |

## Single-Run Template

Each dogfood run MUST be recorded with this structure in `h9-evidence-report.md`:

```markdown
## Run H9-NNN

**Date**: YYYY-MM-DD
**Status**: complete / pending_outcome / rejected / escalated

### Intake
- decision_intake_id:
- symbol / asset:
- decision type: long / short / close / hold / wait
- thesis:
- stop_loss:
- max_loss_usdt:
- position_size_usdt:
- risk_unit_usdt:
- emotional_state: calm / anxious / excited / frustrated / neutral
- is_revenge_trade: true / false
- is_chasing: true / false

### Governance
- decision: execute / escalate / reject
- reasons:
- policy_refs:

### Plan Receipt
- execution_receipt_id:
- receipt_kind: plan
- broker_execution: false
- side_effect_level: none

### Manual Outcome
- finance_manual_outcome_id:
- outcome_source: manual
- observed_outcome:
- verdict: win / loss / breakeven / not_executed
- variance_summary:
- plan_followed: true / false / partial
- risk_realized: true / false
- notes:

### Review
- review_id:
- outcome_ref_type: finance_manual_outcome
- outcome_ref_id:
- verdict:
- cause_tags:
- lessons:
- followup_actions:

### Evidence
- AuditEvent ids:
- ExecutionRequest id:
- ExecutionReceipt id:
- Lesson ids:
- KnowledgeFeedback id:

### Reflection (required for every run)
- Did Ordivon change behavior? (yes / no / partial / N/A)
- Did the user attempt to bypass the system? (yes / no)
- Was the process too heavy? (yes / no / acceptable)
- Which field mattered most?
- What rule might be proposed later?
```

## Evidence Collection Rules

During H-9, evidence is collected automatically through existing PFIOS infrastructure.
The dogfood operator must ensure:

1. **Audit trail**: Every intake → decision → receipt → outcome → review produces
   AuditEvent rows. No intake should be executed without audit.
2. **Receipt integrity**: Every `execute` governance decision MUST have a corresponding
   ExecutionReceipt. If no receipt exists, the run is invalid.
3. **Outcome linkage**: Every Manual Outcome MUST reference a plan receipt.
   Unlinked outcomes are evidence of a process gap.
4. **Review completeness**: Every completed outcome SHOULD have a Review.
   Outcomes without reviews are recorded as "unreviewed" and count as friction evidence.
5. **No fabricated data**: Runs must reflect real or realistic decisions.
   Fake/synthetic runs with no real decision pressure do not count.

### What to Record Even When "Nothing Happened"

- **Rejected intakes**: Record the intake, governance decision, and rejection reasons.
  These are the most valuable data points — they prove the gate works.
- **Escalated intakes**: Record full intake + escalation reason.
- **No-action receipts**: Record receipt + reason for no action.

### What NOT to Record

- Duplicate runs (same intake submitted twice)
- Test-only runs (where the operator knows the expected outcome and scripts it)
- Backfill runs (inventing past decisions retrospectively)

## Completion Criteria

### H-9A (Document Phase) — Current

- [x] H-8 committed and tagged
- [ ] `h9-dogfood-protocol.md` created (this document)
- [ ] `h9-evidence-report.md` created
- [ ] No source code, test, ORM, or API modifications
- [ ] Documents committed and tagged (`h9-dogfood-protocol`)

### H-9B (Dogfood Execution Phase) — Future

- [ ] At least 10 dogfood runs recorded
- [ ] Each run has explicit status (complete / pending / rejected / escalated)
- [ ] At least 2 of 3 governance outcomes covered (reject / escalate / execute)
- [ ] At least 3 full-chain runs to Review
- [ ] At least 3 Lessons generated
- [ ] Bypass attempts explicitly recorded
- [ ] Useful/useless fields explicitly identified
- [ ] P4 readiness judgment rendered
- [ ] Evidence report committed and tagged (`h9-dogfood-evidence`)

## Failure Modes

| Failure Mode | Severity | Recovery |
|-------------|----------|----------|
| Zero rejections across 10 runs | High | The gate is too permissive or intakes are too safe |
| Zero escalations across 10 runs | Medium | Escalation thresholds may be too high |
| All intakes are "safe" (tiny position, no emotional pressure) | Medium | Not a real pressure test — escalate intake risk |
| Multiple bypass attempts succeed | Critical | Gate has a hole — fix before P4 |
| Process feels unbearable (user stops after 3 runs) | High | Process is too heavy — simplify before P4 |
| Zero useful fields identified | Critical | Intake form is collecting noise — redesign |
| Lessons generated but none actionable | Medium | Review structure produces noise, not signal |
| Evidence report columns remain empty | High | Evidence pipeline is broken — fix collection |
| Operator fabricates data to meet counts | Critical | Invalidates H-9 entirely — restart with real decisions |

## Relationship to P4 Closure

H-9 is the **gate-keeper** for P4. The P4 Closure evidence package must include:

1. H-9A protocol document (this document)
2. H-9B evidence report (populated)
3. Statement of readiness judgment

Without H-9 evidence, P4 Closure is premature — we would be certifying a control loop
that was never tested under real pressure.

---

*End of H-9 Dogfood Protocol*
