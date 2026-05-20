# Debt Taxonomy (A1–A4)

## A1 — Direct Fix

Trivial, mechanical fix. Single location. No design implications.

Examples: typo, missing import, stale reference string.

Do NOT use A1 for: logic changes, behavioral changes, suppression of real issues.

## A2 — Logic Refinement

Rule intent ≠ rule execution. The logic works but is fragile, incomplete,
or creates maintenance burden. Fixable within the existing system boundary.

Examples: hardcoded list that should read from registry, ambiguous error
message, missing edge case in an otherwise correct function.

## A3 — System Redesign

Same drift will recur unless the mechanism changes. Crosses subsystem
boundaries. Requires design-level planning.

Examples: manual process that needs automation, architecture that doesn't
support a needed invariant, missing infrastructure capability.

## A4 — Debt Formalize

Cannot fix now. Must not forget. Requires project-level decision, external
dependency, or resource allocation that is not available.

Every A4 debt must have: close_criteria, due_stage, severity.

## Hard Rules

- Never reclassify A4 as A1 to make a phase look clean.
- Never close a debt without evidence of resolution.
- Stale debts (referencing deleted files/systems) must be verified before treatment.
