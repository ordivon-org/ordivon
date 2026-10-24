# LEGO 2.1 — four-owner transition-system seam

**Status:** bounded formal model and falsification evidence, not a deployed owner implementation, a universal LEGO registry, or a new mathematical engine.

## Mature mathematical core

LEGO 2.1 treats a LEGO as a **consumer-conditioned replaceable responsibility**, rather than automatically a file, Tool, Skill or Agent. Its familiar coordinates `(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` are optional semantic views: minimize them to the question being answered.

For this owner boundary, reuse the standard typed transition-system model `(S, Init, Next)`, invariant checking by TLC, and **assume–guarantee** contracts on its seams. The existing `packages/composition` Cognitive Circuit, JSON Schema and Verification Obligation remain responsible for typed ports, caller-authored gate requirements, exact digests and bound verifier identities. This model is not their replacement.

- **Host:** maintains Work continuity; it may record verified acceptance, but does not create the domain verdict.
- **Harness:** proposes a bounded Agent action, not physical dispatch authority.
- **Network:** observes route readiness, not effect permission.
- **Runtime:** owns physical admission, dispatch, ambiguity and terminal standing.
- **Consumer/domain:** supplies an independent outcome witness; `ConsumerObserve` is an abstract oracle in this model.

In `Lego21OwnerBoundary.tla`, TLC checks at-most-once physical dispatch, that neither a ready route nor Harness proposal alone grants physical execution, that ambiguity never implies success, and that Host acceptance requires a consumer witness. `dispatchCount \in 0..2` deliberately permits the invalid value 2 in `TypeOK`, so at-most-once is an independently falsifiable invariant.

## Reuse the existing native checker

The Runtime owner pins both TLA+ tools digests in `services/runtime/formal/toolchain.lock.json`. Use the digest-verified tool; **no extra formal checker or package is introduced**.

```bash
export ORDIVON_TLA_TOOLS_JAR=/absolute/path/to/tla2tools-v1.7.4.jar
services/runtime/scripts/tla-formal verify
(
  cd packages/composition/formal
  java -cp "$ORDIVON_TLA_TOOLS_JAR" tla2sany.SANY Lego21OwnerBoundary.tla
  java -cp "$ORDIVON_TLA_TOOLS_JAR" tlc2.TLC -workers 1 -config Lego21OwnerBoundary.cfg Lego21OwnerBoundary.tla
)
```

**2026-10-25 model evidence:** pinned TLC 2.19, 12 generated states, 10 distinct states, complete search depth 8, no errors. Independent temporary mutations (remove the Host consumer-evidence guard; remove the Runtime Network-readiness guard) each triggered the intended TLC invariant violation. These mutations were not committed.

**Claims explicitly excluded:** implementation refinement for Rust/Host/Harness/Network, current network availability, authorization, identity, consumer evidence authenticity, domain success, retries, liveness, unbounded safety and deadlock freedom. `CHECK_DEADLOCK FALSE` is intentional for terminal stuttering; no fairness property is included. Real acceptance needs existing natural-owner native tests mapping abstract transitions to their physical and semantic effects. Do not promote model PASS into reality PASS.

Foundations: Leslie Lamport's TLA+/TLC, established assume–guarantee contracts (e.g., Pacti), and existing JSON Schema Draft 2020-12 port contracts.
