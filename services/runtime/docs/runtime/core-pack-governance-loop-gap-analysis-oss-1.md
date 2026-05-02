# Core/Pack Governance Loop Gap Analysis — OSS-1

Status: **current** | Date: 2026-05-02 | Phase: OSS-1
Tags: `oss-1`, `gap-analysis`, `core-loop`, `cpr-1`
Authority: `supporting_evidence` | AI Read Priority: 2

## Loop Status Per Node

### 1. Intent — WHAT IS BEING PROPOSED?
**Status**: IMPLEMENTED, DORMANT
**Code**: domains/decision_intake/ (models, repository, service)
**Last exercised**: Phase 7P paper dogfood (Alpaca Paper)
**Gap**: No active dogfood cycle since Phase 7P close.
**CPR-1 action**: Reactivate intake for governance-only dogfood.

### 2. Context — WHAT INFORMATION SUPPORTS IT?
**Status**: IMPLEMENTED, DORMANT
**Code**: packs/finance/context.py, adapters/finance/ (AlpacaObservationProvider)
**Last exercised**: Phase 7P paper health check
**Gap**: Observation adapter works but not in active loop.
**CPR-1 action**: Connect observation to intake context.

### 3. Governance — IS IT ALLOWED?
**Status**: IMPLEMENTED, TESTED
**Code**: governance/risk_engine, governance/approval, governance/policy_source
**Tests**: 302 governance tests pass
**Last exercised**: ADP-2R/ADP-3 detector hardening (governance verification only)
**Gap**: RiskEngine validate_intake not exercised with real intake since Phase 7P.
**CPR-1 action**: Run RiskEngine against governance-only intake scenarios.

### 4. Execution — DID IT ACTUALLY HAPPEN?
**Status**: IMPLEMENTED, PAPER-ONLY
**Code**: execution/ (8 .py), orchestrator/ (16 .py)
**Adapter**: adapters/finance/paper_execution.py (paper-only)
**Gap**: PaperExecutionAdapter works; live execution is NO-GO (correct).
**CPR-1 action**: Exercise paper execution in governance dogfood loop.

### 5. Receipt — IS THERE EVIDENCE?
**Status**: IMPLEMENTED, ACTIVE
**Code**: domains/execution_records/, agent-output-contract.md
**Active in**: Every phase closure (ADP-2R, ADP-3, DG-1 receipts)
**Gap**: Receipts for meta-governance phases work; need to exercise for core loop phases.
**CPR-1 action**: Use existing receipt infrastructure.

### 6. Outcome — WHAT WAS THE RESULT?
**Status**: IMPLEMENTED, PARTIAL
**Code**: domains/finance_outcome/, domains/strategy/
**Gap**: Outcome models exist but only exercised during Phase 7P.
**CPR-1 action**: Capture governance-only outcomes from dogfood loop.

### 7. Review — DID THE RESULT MATCH EXPECTATIONS?
**Status**: IMPLEMENTED, ACTIVE
**Code**: governance/review/, HAP-3 ReviewRecord objects
**Active in**: ADP-3 structure-aware detection
**Gap**: ReviewRecord objects validated but not generated from live loop.
**CPR-1 action**: Generate ReviewRecords from governance dogfood outcomes.

### 8. Lesson — WHAT DID WE LEARN?
**Status**: IMPLEMENTED, DORMANT
**Code**: domains/journal/ (Review, Lesson, Issue), knowledge/ (8 .py)
**Gap**: FeedbackPacket model exists; no active feedback extraction pipeline.
**CPR-1 action**: Extract lessons from governance dogfood reviews.

### 9. CandidateRule — CAN EXPERIENCE BECOME A DRAFT RULE?
**Status**: IMPLEMENTED, STAGED
**Code**: domains/candidate_rules/ (draft_extraction, policy_proposal, review_service)
**Existing**: CR-7P-001, CR-7P-002, CR-7P-003 (3 advisory rules from Phase 7P)
**Gap**: Promotion pipeline exists but has not been exercised beyond Phase 7P.
**CPR-1 action**: Evaluate existing CandidateRules against new dogfood evidence.

### 10. Policy — SHOULD THE RULE BECOME AN ACTIVE CONSTRAINT?
**Status**: IMPLEMENTED, NO-GO
**Code**: domains/policies/ (PolicyRecord, state_machine, evidence_gate)
**Status**: CandidateRules only; Policy activation is NO-GO per Phase 5 closure.
**Gap**: Correctly gated. Policy should not be activated.
**CPR-1 action**: Maintain CandidateRule→Policy boundary. Do not activate.

## Gap Severity Summary

| Gap | Severity | Blocking CPR-1? | Resolution |
|-----|----------|-----------------|------------|
| Loop dormancy | HIGH | YES | Reactivate governance-only dogfood |
| Intent intake inactive | MED | YES | Restart decision_intake loop |
| Context stale | MED | NO | Observation adapter operational |
| Lesson extraction dormant | MED | NO | Build feedback pipeline |
| CandidateRule promotion | MED | NO | Evaluate existing CRs |
| Policy activation | N/A | N/A | Correctly NO-GO |

## CPR-1 Scope Recommendation

CPR-1 should reactivate nodes 1-8 (Intent through Lesson) in a governance-only
(no-live-action, no-policy-activation) dogfood cycle. Nodes 9-10 remain advisory/staged.

Supporting infrastructure to use:
- DG truth substrate for phase documentation and receipts
- ADP-3 detection as pre-commit governance verification
- Existing receipt integrity checker for closure verification
- Existing pr-fast baseline for gate validation

Explicitly NOT in CPR-1 scope:
- Live trading / broker access (NO-GO)
- Policy activation (NO-GO)
- Phase 8 (DEFERRED)
- Package publication (gated)
- Public repo creation (gated)
