# Composition package instructions

Scope: `packages/composition/**`.

This package owns only generic, deterministic, task-local composition mechanics:
Cognitive Circuit validation/compilation, generic Composition Gate evaluation, and
Interface Contract compatibility/currentness/admissibility evaluation.

It does not own method selection, capability discovery, workflow state, scheduling,
credentials, permissions, owner truth, seam-specific verification, or domain acceptance.

Rules:
1. Public schemas and Python APIs must remain deterministic and non-authoritative.
2. Seam-specific adapters stay with the concrete consumer/composition/study.
3. No provider catalog, workflow database, retry engine, or universal verifier may grow here.
4. Preserve `mechanicalClosure != domainAcceptanceEstablished`.
5. Run `mise run verify` before integration.
