# ORDIVON EVIDENCE RESOLVER REGISTRY ELIMINATION R23

Date: 2026-09-19
Status: NINETEENTH_PRODUCTION_DELETION
Parent: ORDIVON CREDENTIAL REFERENCE AUTHORITY R22

## Result

R23 removes EvidenceResolverRegistry and service.evidence_resolvers.

The deleted class was not a true registry: it owned no registration, discovery, lifecycle, or mutable resolver catalog.

## Replacement

EvidenceResolverRegistry.resolve(...)
  -> _resolve_evidence(artifact_reader, acceptance, observation)

No replacement Registry/Manager/Router class was introduced.

## Retained authority boundaries

- RuntimeArtifactReader remains the exact external artifact-reading port.
- artifact job/id correlation is still validated.
- artifact content SHA-256 is still recomputed.
- ArtifactDigestMismatch still fails closed.
- EvidenceBundle still normalizes in-memory facts and persists provenance rather than raw Runtime artifact bytes.
- EvidenceSemanticVerifier remains the semantic acceptance owner.
- TaskCompletionReconciler remains the lifecycle composition owner.

## CORE_ZERO ratchet

R3 baseline: 171
R20: 152
R21: 151
R22: 151 (CredentialReferenceStore intentionally retained)
R23: 150
cumulative retired top-level types: 21

Structural audit:
observed = 150
legacy ceiling = 150
unexpected = []
retired overlap = []
old EvidenceResolverRegistry/facade = none
replacement registry classes = none

## Validation

Direct evidence GREEN: Ran 12 tests — OK
Structural gate: Ran 18 tests — OK
Agent Service: Ran 243 tests — OK (skipped=5)
Full repository: Ran 342 tests — OK (skipped=5)

## Interpretation

R23 removes an accidental object boundary, not evidence capability.

The stable split is now:
RuntimeArtifactReader -> pure evidence normalization -> EvidenceSemanticVerifier -> TaskCompletionReconciler.
