# Composition package instructions

Scope: `packages/composition/**`.

This package owns only generic, deterministic, task-local composition mechanics:
Cognitive Circuit validation/compilation, generic Composition Gate evaluation,
Interface Contract compatibility/currentness/admissibility evaluation, and deterministic
Composition Gate → verification-obligation / exact task-local verifier-binding mechanics.

It does not own method selection, capability discovery, workflow state, scheduling,
credentials, permissions, owner truth, seam-specific verification, verifier discovery or
ranking, generic verifier execution, or domain acceptance.

Rules:
1. Public schemas and Python APIs must remain deterministic and non-authoritative.
2. Seam-specific adapters stay with the concrete consumer/composition/study.
3. No provider catalog, workflow database, retry engine, verifier registry/ranker, or
   universal verifier may grow here.
4. Preserve `mechanicalClosure != domainAcceptanceEstablished`.
5. Run `mise run verify` before integration.
