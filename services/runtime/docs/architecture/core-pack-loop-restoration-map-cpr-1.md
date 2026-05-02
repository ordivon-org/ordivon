# Core/Pack Loop Restoration Map — CPR-1

Status: **current** | Date: 2026-05-02 | Phase: CPR-1
Tags: `cpr-1`, `architecture`, `loop-map`, `core-pack`
Authority: `supporting_evidence` | AI Read Priority: 2

## Loop Architecture

```
                    ┌──────────────────────────────────────┐
                    │          TRUTH GOVERNANCE            │
                    │   DG registry / AI onboarding /      │
                    │   document freshness / wiki          │
                    └──────────────────────────────────────┘
                                      │
                                      ▼
┌─────────┐   ┌─────────┐   ┌─────────────┐   ┌───────────┐
│ INTENT  │──▶│ CONTEXT │──▶│ GOVERNANCE  │──▶│ EXECUTION │
│         │   │         │   │             │   │           │
│ Decision│   │ Coding  │   │ RiskEngine  │   │ Simulated │
│ Intake  │   │ Decision│   │ + Pack      │   │ / Local   │
│         │   │ Payload │   │ Policy      │   │           │
└─────────┘   └─────────┘   └─────────────┘   └───────────┘
                                                      │
                    ┌─────────────────────────────────┘
                    ▼
┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
│ RECEIPT │──▶│ OUTCOME │──▶│ REVIEW  │──▶│ LESSON  │
│         │   │         │   │         │   │         │
│ ExecRec │   │ 3 EXEC  │   │ 10/10   │   │ Gate    │
│         │   │ 5 REJECT│   │ matched │   │ findings│
│         │   │ 2 ESCAL │   │         │   │         │
└─────────┘   └─────────┘   └─────────┘   └─────────┘
                                                   │
                    ┌──────────────────────────────┘
                    ▼
┌─────────────────┐   ┌─────────────┐
│ CANDIDATERULE   │──▶│   POLICY    │
│                 │   │             │
│ Advisory only   │   │ NO-GO       │
│ Non-binding     │   │ Gated       │
└─────────────────┘   └─────────────┘
                    ▲                   ▲
                    │                   │
     ┌──────────────┴───────────────────┴──────────────┐
     │              ACTION GOVERNANCE                  │
     │   ADP detector / HAP TaskPlan+ReviewRecord /    │
     │   GOV-X gate matrix / OGAP protocol             │
     └─────────────────────────────────────────────────┘
```

## Layer Mapping

| Loop Node | Architecture Layer | Implementation | Status |
|-----------|-------------------|----------------|--------|
| Intent | L2 Domain State | domains/decision_intake/ | Implemented |
| Context | L3 Pack Platform | packs/coding/models.py | Implemented |
| Governance | L1 Core Control | governance/risk_engine/ | Implemented |
| Execution | L5 Adapter + L6 Evidence | execution/ + orchestrator/ | Implemented |
| Receipt | L6 Evidence | domains/execution_records/ | Implemented |
| Outcome | L2 Domain State | domains/finance_outcome/ | Implemented |
| Review | L7 Verification | governance/review/ + HAP-3 | Implemented |
| Lesson | L8 Learning | domains/journal/ + knowledge/ | Implemented |
| CandidateRule | L8 Learning | domains/candidate_rules/ | Implemented |
| Policy | L9 Policy | domains/policies/ | Gated (NO-GO) |

## CPR-1 Dogfood Evidence

- Script: `scripts/h9f_coding_dogfood.py`
- Runs: 10 simulated coding intakes
- Results: 10/10 passed (3 execute, 5 reject, 2 escalate)
- Risk level: AP-R0 (no live action, no external side effects)
- Capability class: C0-C3 (no C4/C5 touched)
- GOV-X gates: READY_WITHOUT_AUTHORIZATION for C0-C1, REVIEW_REQUIRED for C2-C3
- ADP-3 detector: Run against CPR-1 docs — no blocking findings
