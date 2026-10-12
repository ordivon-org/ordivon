# Research Tool Qualification R1

This profile records task/operation-local qualification evidence for one Research use. It is not a registry, currentness owner, provider authority, or scientific authority.

A `QUALIFIED_IN_SCOPE` packet binds the current natural owner evidence, exact operation/interface, execution boundary, positive controls, action-changing negative controls, evidence references, and explicit non-claims. A `HOLD` packet records why qualification cannot be established without fabricating evidence.

External mutation or publication effects require an explicit effect-authorization owner. Qualification does not grant that authority.

## Procedure

1. Freeze the exact problem class and operation.
2. Resolve the canonical Tool/Skill/provider owner.
3. Read current owner generation/version at the observation cut.
4. Bind the interface, execution/effect boundary and evidence needed by this operation.
5. Run positive and action-changing negative controls.
6. Record evidence references and non-claims.
7. Emit `QUALIFIED_IN_SCOPE` or `HOLD`.
8. Requalify after action-changing owner/version/interface/effect changes or a falsifying counterexample.

## Research Mechanical Component

The sibling static component contract admits exactly:
`Probe | Normalize | Extract | Verify | Compare | Package | Effect Adapter`.

It does not own live availability, current provider status, Runtime Job identity, scientific judgment, or Study acceptance. An Effect Adapter must name its effect authorization owner and replay semantics.

Reuse/promotion remains owned by the existing Research reuse lifecycle. These contracts do not add a seventh disposition, Tool registry, currentness database, or new Research service.
