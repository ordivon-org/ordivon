# ORDIVON LEGO — EVIDENCE SEMANTIC VERIFICATION R27

Date: 2026-09-19
Base: 65b91e75b2021908599eeb200c67a8f5140cb6d0

## Finding

EvidenceSemanticVerifier is a stateless semantic predicate shared by local and remote completion.

The single acceptance authority is important. The class instance is not.

## Semantic rule set

normalized evidence must contain string facts.text
stdout_contains / runtime_artifact_text_contains
  -> accepted iff acceptance.value is substring of text
stdout_equals
  -> accepted iff acceptance.value equals text
unsupported acceptance kind
  -> fail closed

## LEGO ownership

| LEGO | Owner | R27 |
|---|---|---|
| normalized evidence | EvidenceBundle | retain |
| local/remote acceptance rule | one pure semantic function | retain |
| local completion transaction | TaskCompletionReconciler | retain |
| remote completion transaction | RemoteTaskCompletionReconciler | retain |
| historical N13 graph identity | knowledge graph history | retain as history |
| EvidenceSemanticVerifier class | stateless wrapper | eliminate |

## Replacement

EvidenceSemanticVerifier.verify(acceptance, evidence)
  -> _verify_evidence_semantics(acceptance, evidence)

Both local and remote completion call the same function. No remote-specific semantic verifier is introduced.

## Proof obligations

1. EvidenceSemanticVerifier class absent from runtime.
2. service.semantic_verifier absent.
3. service.remote_semantic_verifier absent.
4. local and remote completion both call _verify_evidence_semantics.
5. missing/non-string normalized text still fails closed.
6. contains/equality acceptance semantics unchanged.
7. unsupported kinds still fail closed.
8. historical graph files are not rewritten as if the old class never existed.
9. no replacement SemanticVerifier/Gate/Manager class in evidence layer.
