# Ordivon Composition

This package is the bounded source owner for Ordivon's generic task-local composition
mechanics. It was extracted from historical `meta/next` without moving method selection,
capability discovery, seam-specific verification, workflow state, or domain truth.

## Public responsibilities

- Cognitive Circuit manifest validation and deterministic compilation.
- Generic verifier-owned Composition Gate result validation/evaluation.
- Interface compatibility, currentness, and evidence-admissibility evaluation.
- Public JSON Schemas for those contracts.

## Non-claims

This package is not a planner, scheduler, capability registry, workflow engine, permission
system, credential store, domain verifier, or truth owner. A mechanically closed circuit
does not establish domain acceptance.

## Consumer boundary

Structure R2 S1B migrated the remaining `meta/next` consumers to the public
`ordivon_composition` API. The historical Next Python compatibility facades were removed
after repository-wide consumer inventory found no external path callers.

## Verification

Run `mise run verify` from this directory.
