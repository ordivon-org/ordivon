# Ordivon Composition

This package is the bounded source owner for Ordivon's generic task-local composition
mechanics. It was extracted from historical \`meta/next\` without moving method selection,
capability discovery, seam-specific verification, workflow state, or domain truth.

## Public responsibilities

- Cognitive Circuit manifest validation and deterministic compilation.
- Generic verifier-owned Composition Gate result validation/evaluation.
- Interface compatibility, currentness, and evidence-admissibility evaluation.
- Deterministic Composition Gate → verification-obligation projection.
- Deterministic explicit authority-requirement → task-local authority-obligation projection.
- Exact task-local verifier-binding validation without discovery or ranking.
- Successor Contract predecessor/candidate binding and verifier-owned succession-gate
  evaluation.
- Deterministic non-authoritative Agent Run binding over already-selected exact references.
- Public JSON Schemas for those contracts.

## Non-claims

This package is not a planner, scheduler, capability registry, workflow engine, permission
system, credential store, domain verifier, verifier registry/ranker, generic verifier
executor, RSI controller, universal evaluator, promotion authority, Harness contract owner,
Agent runtime, or truth owner.
A mechanically closed circuit or resolved verifier binding does not establish domain
acceptance, and mechanically closed succession gates do not establish that a candidate is
globally better or authorized for promotion.

## Consumer boundary

Structure R2 S1B migrated the remaining \`meta/next\` consumers to the public
\`ordivon_composition\` API. The historical Next Python compatibility facades were removed
after repository-wide consumer inventory found no external path callers.

Successor Contract R1 adds a generic representation for an exact predecessor/candidate
transition without moving candidate generation, domain metrics, evaluation semantics,
promotion, release, or Git authority into this package.

Agent Run Binding R1 adds a disposable exact-reference projection for one prospective Agent
Run without moving Harness contract semantics, provider/tool selection, authorization,
execution, workflow, or domain acceptance into this package.

Authority Obligation R1 binds explicit caller-authored Circuit/stage/capability prerequisites
to exact external authority-contract references. It never infers effect coverage and always
leaves authority and execution authority false.

## Verification

Run \`mise run verify\` from this directory.
