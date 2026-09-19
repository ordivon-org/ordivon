# ORDIVON LEGO — EVIDENCE RESOLUTION R23

Date: 2026-09-19
Base: 4e782723cc187be9e9f8ec5610d2a49cdba41d41

## Finding

EvidenceResolverRegistry is not a registry.

It has no register/unregister operation, plugin discovery, dynamic resolver lifecycle, ownership catalog, or independently mutable state.

Its complete decision graph is:

acceptance.kind
  -> stdout_contains / stdout_equals: normalize Runtime stdout tail
  -> runtime_artifact_text_contains: read one artifact, validate identity and digest, normalize text

## LEGO classification

| LEGO | Role | Authority | R23 |
|---|---|---|---|
| RuntimeArtifactReader | reads exact Runtime-owned artifact bytes | external evidence port | retain |
| EvidenceResolverRegistry | two-branch normalization wrapper | no independent authority | eliminate |
| evidence resolution function | normalize evidence and verify artifact digest | pure function | use directly |
| EvidenceSemanticVerifier | interprets normalized evidence against acceptance | semantic verdict boundary | retain |
| TaskCompletionReconciler | lifecycle orchestration | task completion composition | retain |

## Replacement

EvidenceResolverRegistry.resolve(...)
  -> _resolve_evidence(artifact_reader, acceptance, observation)

No replacement Registry/Manager/Router class.

AgentServiceR6 keeps the RuntimeArtifactReader dependency and passes it directly to TaskCompletionReconciler.

## Proof obligations

1. EvidenceResolverRegistry absent.
2. service.evidence_resolvers absent.
3. stdout evidence normalization is unchanged.
4. artifact kind must still match exactly one descriptor.
5. artifact job/id correlation remains checked.
6. artifact SHA-256 remains recomputed and mismatch raises ArtifactDigestMismatch.
7. durable VerificationRecord still stores provenance rather than raw evidence bytes.
8. EvidenceSemanticVerifier remains separate.
9. no replacement Registry/Manager/Router class.
