# Composition package instructions

Scope: \`packages/composition/**\`.

This package owns only generic, deterministic, task-local composition mechanics:
Cognitive Circuit validation/compilation, generic Composition Gate evaluation,
Interface Contract compatibility/currentness/admissibility evaluation, deterministic
Composition Gate → verification-obligation / exact task-local verifier-binding mechanics,
and exact predecessor/candidate Successor Contract binding with verifier-owned succession gates.

It does not own method selection, capability discovery, candidate generation, workflow state,
scheduling, credentials, permissions, owner truth, seam-specific verification, verifier
discovery or ranking, generic verifier execution, domain acceptance, promotion authority,
or an RSI controller.

Rules:
1. Public schemas and Python APIs must remain deterministic and non-authoritative.
2. Seam-specific adapters stay with the concrete consumer/composition/study.
3. No provider catalog, workflow database, retry engine, verifier registry/ranker, universal
   verifier, universal fitness function, or self-improvement controller may grow here.
4. Preserve \`mechanicalClosure != domainAcceptanceEstablished\` and
   \`mechanicalSuccessorClosure != promotionAuthorityEstablished\`.
5. Meta-improvement measurement remains study/domain evidence unless a narrower reusable
   mechanism earns promotion through repeated evidence.
6. Run \`mise run verify\` before integration.
