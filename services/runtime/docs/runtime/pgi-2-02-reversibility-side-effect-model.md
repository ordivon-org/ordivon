# PGI-2.02 Reversibility and Side-Effect Classifier

Status: **CLOSED** | Date: 2026-05-03
Phase: PGI-2.02
Tags: `pgi`, `runtime-evidence`, `reversibility`, `side-effect`
Authority: `supporting_evidence` | AI Read Priority: 2

## Intent

Add a ReversibilityAssessment object so DecisionGate can distinguish local,
reversible work from high side-effect or irreversible choices.

## Constraints

- Does not authorize action.
- Does not open live trading or external side effects.
- Does not replace existing NO-GO boundaries.

## Actions

Created:

```text
docs/governance/reversibility-side-effect-model-pgi-2.md
scripts/validate_pgi_reversibility_assessment.py
tests/fixtures/pgi_reversibility_assessment/valid/local-doc.json
tests/fixtures/pgi_reversibility_assessment/invalid/high-side-effect-no-review.json
tests/fixtures/pgi_reversibility_assessment/invalid/unknown-external.json
tests/unit/governance/test_pgi_reversibility_assessment.py
```

## Evidence

Expected fixture behavior:

| Fixture | Expected |
|---------|----------|
| local doc | VALID |
| financial side effect without review | INVALID |
| external side effect with unknown reversibility | INVALID |

## Review

PGI-2.02 is locally closed as a seed side-effect classifier. It gives future
DecisionGate work a practical reason field: can this be undone, and what residue
does it leave?

## Rule Update

CandidateRule proposal:

```text
PGI-CR-011: High side-effect actions require review_required=true and cannot
use unknown reversibility.
```

Status: **candidate only**. This is not Policy.

## Next Action

```text
PGI-2.03 - Control Boundary Classifier
```
