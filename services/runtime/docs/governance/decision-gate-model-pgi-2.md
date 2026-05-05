# DecisionGate Model — PGI-2

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-2.01
Tags: `pgi`, `decision-gate`, `practical-reason`, `review`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

DecisionGate is the first operational object that combines PGI-1 substrates.

Core rule:

```text
A high-consequence decision is not governable until claim, evidence,
confidence, failure path, constitution checks, ethical review, reversibility,
downside, and missing evidence are explicit.
```

## Inputs

| Input | Source |
|-------|--------|
| claim_ref | PGI-1.02 Claim and Argument Model |
| evidence_refs | PGI-1.03 EvidenceRecord |
| confidence_assessment_ref | PGI-1.05 ConfidenceAssessment |
| failure_predicate_ref | PGI-1.06 FailurePredicate |
| constitution_checks | PGI-1.07 Constitution Boundary Matrix |
| ethical_triad_review_ref | PGI-1.08 EthicalTriadReview |

## DecisionGate Fields

| Field | Meaning |
|-------|---------|
| decision_id | Stable local ID. |
| action_or_claim | Proposed decision or claim. |
| risk_level | low, medium, high, irreversible. |
| claim_ref | Claim model or claim object reference. |
| evidence_refs | Evidence references. |
| confidence_assessment_ref | Confidence object reference. |
| failure_predicate_ref | Failure predicate reference. |
| constitution_checks | Rule IDs and pass/warn/block results. |
| ethical_triad_review_ref | Ethical triad review reference. |
| reversibility | reversible, partially_reversible, irreversible, unknown. |
| downside | Maximum credible downside or harm. |
| decision_posture | READY_WITHOUT_AUTHORIZATION, DEGRADED, BLOCKED, NEEDS_REVIEW. |
| missing_evidence | Evidence gaps. |
| review_trigger | What reopens the gate. |
| authority_boundary | Required statement that the gate does not authorize execution. |

## Validator Seed

```text
scripts/validate_pgi_decision_gate.py
```

It rejects:

- missing required PGI-1 references
- READY_WITHOUT_AUTHORIZATION with missing evidence
- high/irreversible READY posture with unknown reversibility
- missing constitution checks
- authority boundary collapse

## Fixtures

```text
tests/fixtures/pgi_decision_gate/valid/ready-without-authorization.json
tests/fixtures/pgi_decision_gate/invalid/ready-with-missing-evidence.json
tests/fixtures/pgi_decision_gate/invalid/authorizes-execution.json
```

## Boundary

DecisionGate does not authorize execution, merge, deploy, trade, or external
action. It only classifies whether selected governance evidence is sufficient
for review.

Next stage:

```text
PGI-2.02 - Reversibility and Side-Effect Classifier
```
