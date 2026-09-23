# Intent / Constraint Field Census R1

Date: 2026-09-23
Status: **C01 COMPLETE — NO UNIVERSAL INTENT OBJECT**

Current evidence supports reuse of existing `objectiveRef` / bound-reference mechanics, not a new global Intent schema.

| Surface | Reusable structure | Owner-specific semantics |
| --- | --- | --- |
| Cognitive Circuit | objectiveRef, exact bindings | method/capability composition |
| HarnessRunContract | objectiveRef, bound refs | Run budget, deadline, privacy, Tool authority |
| Host WorkingCheckpoint | exact task/checkpoint identity | unresolved/constraints/nextActions continuity |
| Security | exact Principal/Grant/Effect identity | risk class and authorization |
| Capital | references/evidence | financial risk budgets/execution policy |
| Game | references/evidence | game/product objectives/design constraints |

`risk`, `budget`, `deadline`, `constraints`, and `completion` are not one cross-domain semantic type.

## C02 disposition

`C02 = NO_NEW_CONTRACT`.

The compiler should map caller/domain intent into the existing Cognitive Circuit objective reference and task-local bindings. Harness receives only one bounded Run authority. Domain constraints, risk, business deadlines, and semantic completion remain with their natural owners.

A new shared typed field is admitted only after at least three independent real consumers demonstrate the same authority and verification semantics.
