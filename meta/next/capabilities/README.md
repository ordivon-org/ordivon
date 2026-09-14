# Capabilities

A capability is independent of the specific tool that provides it.

Capability records should eventually capture only evidence-backed fields such as:

- capability identity and problem classes served;
- **natural semantic authority / object whose lifecycle the capability owns**;
- inputs/outputs;
- preconditions/postconditions;
- side effects and reversibility;
- authority/risk requirements;
- deterministic vs agentic behavior;
- cost/latency/resource characteristics where relevant;
- compatible standards/methods;
- available providers/tools;
- activation trigger / evidence threshold for introducing operational state;
- applicable validators and the boundary beyond which provider success is insufficient.

Existing Runtime, Network, Artifact, Distribution and other systems should be exposed here as replaceable capability providers rather than absorbed as identity-defining Ordivon subsystems.

For cross-provider routing, use `docs/CAPABILITY_AUTHORITY_MAP_R1.md`. It maps primitives to their natural authorities, mature provider candidates, activation triggers, do-not-build boundaries and verification boundaries. It is a catalog/routing view, not a permanent dependency topology.
