# Capability Inventory

This inventory records abstraction type and lifecycle status for every current capability file.

## Lifecycle Policy

- `stable`: domain object contract with bounded semantics
- `workflow`: composite output or action contract
- `view`: product aggregate or artifact presentation contract
- `experimental`: temporary or still-mixed contract

## File Disposition

| File | Abstraction | Lifecycle | Disposition |
| --- | --- | --- | --- |
| `capabilities/domain/recommendations.py` | domain | stable | keep |
| `capabilities/workflow/analyze.py` | workflow | workflow | keep |
| `capabilities/workflow/reviews.py` | workflow | workflow | keep |
| `capabilities/view/dashboard.py` | view | view | reclassify |
| `capabilities/view/reports.py` | view | view | reclassify |
| `capabilities/view/audits.py` | view | view | reclassify |
| `capabilities/diagnostic/evals.py` | diagnostic | experimental | reclassify |
| `capabilities/diagnostic/validation.py` | diagnostic | experimental | split |

## Compatibility Wrappers

Top-level modules in `capabilities/*.py` remain as compatibility wrappers and should not accumulate new logic.
