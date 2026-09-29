# ReviewRecord contract

`assets/review-record.schema.json` is the machine-readable structural contract. The semantic verifier adds invariants that JSON Schema alone does not conveniently express.

## Required semantic invariants

1. Every `REALIZED` capability references at least one evidence item of type `LIVE_OWNER_RECEIPT` or `EXECUTED_VERIFICATION`.
2. Evidence references must resolve to an item in the same record.
3. Every milestone has at least one dependency (or explicit `NONE`), non-empty entrance criteria, and non-empty success criteria.
4. Every repeated finding disposition is one of `ARCHITECTURE_DECISION`, `FITNESS_FUNCTION`, `OPERATIONAL_CONTROL`, or `REDESIGN`.
5. Every risk theme references at least one finding.
6. A user decision includes at least two options or explicitly states why the decision is unary (for example legal/contractual acceptance); ordinary engineering unknowns belong in `unknowns`, not `decisions`.
7. Census confidence below `HIGH` must include at least one limitation.
8. `CURRENT_CODE_CONTRACT`, `INTENT_DOC`, and `HISTORICAL_CONTEXT` alone cannot support a `REALIZED` run-state claim.

## Stability

The schema is versioned independently from any one weekly report. Additive optional fields may be introduced in a backward-compatible revision; changing meanings or enum semantics requires a new schema version.

The ReviewRecord is an analytical projection. It never becomes an owner receipt or source of operational authority.
