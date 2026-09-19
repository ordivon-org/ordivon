# ORDIVON A2A-NATIVE ELIMINATION R4

Date: 2026-09-19  
Status: FIRST_PRODUCTION_DELETION  
Parent: ORDIVON_CORE_ZERO_ENFORCEMENT_R3

## Result

R4 performs the first production-code deletion under the CORE_ZERO ratchet.

`CapabilityAdvertisement` is deleted as a top-level Ordivon type.

The migration store still exists temporarily because existing Agent Service call sites write revision-scoped discovery metadata into SQLite. Its public value is no longer an Ordivon object: it returns an A2A 1.0 `AgentSkill`-shaped dictionary.

Top-level Agent Service type debt:

```text
R3 baseline: 171
R4 current:  170
retired:       1
```

The R3 profile now records `CapabilityAdvertisement` in `retiredLegacyTypes` and removes it from the legacy ceiling. Reintroduction is therefore a test failure.

## External boundary correction

The A2A Agent Card projector now targets released A2A 1.0 semantics:

- no top-level `protocolVersion`;
- no top-level `url`;
- no top-level `preferredTransport`;
- `supportedInterfaces[]` carries `url`, `protocolBinding`, and `protocolVersion`;
- required Agent Card `version` is emitted;
- legacy internal `text` mode is normalized at the adapter boundary to `text/plain`;
- skills are emitted directly from A2A `AgentSkill`-shaped values.

Canonical reference:
https://a2a-protocol.org/latest/specification/

## What was not promoted

No replacement Ordivon capability class was introduced.
No universal capability ID was introduced.
No new semantic authority was introduced.
No compatibility wrapper was added around `CapabilityAdvertisement`.

The remaining `CapabilityAdvertisementStore` and `capability_advertisements` table are migration debt only.

## Next deletion targets

1. Eliminate `CapabilityAdvertisementStore` and its table by moving AgentSkill material to an external-native revision artifact/profile.
2. Split `AgentInterfaceAdvertisement` into protocol-owned declarations:
   - A2A `AgentInterface` for A2A endpoints;
   - MCP-native endpoint/capability configuration for MCP;
   - routing preference remains deployment/profile data, not an agent semantic primitive.
3. Remove local public API exports for retired discovery ontology.
4. Tighten the CORE_ZERO ceiling after every deletion batch.

## Gate status

This wave proves only discovery-boundary parity and anti-regression for the removed type. It does not claim all fifteen R1 deletion gates for Agent Service as a whole are closed.
