# Paper Trade Template

Use this template for each new Alpaca Paper trade. Copy and fill in all sections.
Delete this line and replace `PT-XXX` with the next trade ID from the ledger.

**⚠ PAPER ONLY — NOT LIVE TRADING. ALL PNL IS SIMULATED.**

---

# PT-XXX — [Brief Description]

Status: **IN_PROGRESS** | Date: YYYY-MM-DD | Phase: 7P-XXX

## 1. Intake

| Field | Value |
|-------|-------|
| symbol | |
| thesis / purpose | |
| setup | |
| entry_plan | |
| invalidation | |
| stop_condition | |
| max_paper_risk | |
| reason_not_to_trade | |
| market_data_freshness | |
| paper_account_state | |
| evidence_refs | |
| no_live_disclaimer | ✅ acknowledged |
| readiness_gate_9_checks | ✅ passed (list any failures) |

Decision: **PAPER_INTAKE_ACCEPTED / HOLD / REJECTED**

## 2. Plan Receipt

| Field | Value |
|-------|-------|
| decision | PAPER_INTAKE_ACCEPTED |
| allowed_action | Alpaca Paper order only |
| forbidden_action | Live order ❌, new entry while position open ❌ |
| order_type | market / limit |
| quantity | |
| paper_only | true |

## 3. Execution Receipt

| Field | Value |
|-------|-------|
| provider_order_id | |
| client_order_id | |
| symbol | |
| side | |
| order_type | |
| quantity | |
| submitted_at | |
| status | |
| environment | paper |
| live_order | false |
| source | alpaca-paper |

## 4. Fill Reconciliation

| Field | Value |
|-------|-------|
| status | |
| filled_qty | |
| filled_avg_price | |
| filled_at | |
| reconciliation_time | |

## 5. Outcome

| Field | Value |
|-------|-------|
| entry_price | |
| exit_price | (for closeouts) |
| paper_pnl | (simulated) |
| commission | $0.00 |
| slippage_estimate | |
| plan_followed | Y/N |
| deviation | |
| what_worked | |
| what_failed | |

**⚠ Paper PnL is simulated, not real.**

## 6. Formal Review (after closeout)

| Question | Answer |
|----------|--------|
| Loop complete? | |
| Boundaries held? | |
| Wording safe? | |
| Adapter sufficient? | |
| Receipts complete? | |
| Safety checks OK? | |
| CandidateRule? | |
| CR advisory only? | |
| Fixes before next? | |
| Next trade allowed? | |

## 7. CandidateRule / Lesson

| Field | Value |
|-------|-------|
| CR ID | CR-7P-XXX |
| observation | |
| status | advisory only — NOT Policy |
| linked_trade | PT-XXX |

## 8. New AI Context Note

What must a fresh AI understand after this trade is complete?

- [ ] Trade status (open / closed / reviewed)
- [ ] Whether next trade is allowed
- [ ] Any new CandidateRules (advisory)
- [ ] Live trading still deferred
