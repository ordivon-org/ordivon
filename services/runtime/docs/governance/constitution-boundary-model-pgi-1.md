# Constitution Boundary Model — PGI-1

Status: **CURRENT** | Date: 2026-05-03
Phase: PGI-1.07
Tags: `pgi`, `constitution`, `boundary`, `no-go`, `autonomy`
Authority: `source_of_truth` | AI Read Priority: 1

## Purpose

This model classifies the ten personal constitution rules from the
Philosophical Governance Layer.

Core rule:

```text
Values must be classified before they can govern action.
Unclassified values are orientation, not gates.
```

## Machine Matrix

```text
docs/governance/constitution-boundary-matrix-pgi-1.json
```

Allowed classifications:

| Classification | Meaning |
|----------------|---------|
| no_go_boundary | Supports existing hard boundary; does not create new active Policy. |
| review_gate | Must be considered before high-consequence action. |
| warning | Signals caution; does not block by itself. |
| learning_prompt | Shapes review and CandidateRule extraction. |
| orientation | Identity direction, not a rule. |

Allowed activation states:

| Activation status | Meaning |
|-------------------|---------|
| candidate_only | Candidate governance rule, not Policy. |
| advisory | Guidance only. |
| existing_no_go_support | Reinforces existing NO-GO boundary. |
| deferred | Not operational yet. |

Forbidden:

```text
active_policy
```

## Validator Seed

```text
scripts/validate_constitution_boundary_matrix.py
```

It checks:

- no action authorization
- no Policy activation
- valid classification
- valid activation state
- unique rule IDs
- review/closure condition for each rule

## Boundary

This model does not activate personal values as Policy. It prevents that mistake
by forcing classification and advisory status.

Next stage:

```text
PGI-1.08 - Ethical Triad Review
```
