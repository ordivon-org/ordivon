# ORDIVON INTERFACE PROFILE ELIMINATION R5

Date: 2026-09-19  
Status: SECOND_PRODUCTION_DELETION  
Parent: ORDIVON_A2A_NATIVE_ELIMINATION_R4

## Result

R5 deletes `AgentInterfaceAdvertisement` as a top-level Ordivon type.

No replacement interface class was introduced.

The temporary `AgentInterfaceAdvertisementStore` still persists migration-era route rows because existing `transport_bindings.interface_id` references that table. Its public value is now an ordinary deployment route profile dictionary:

```text
profileId
transport
protocolVersion
url
priority
securityRequirements
```

This dictionary is not declared a protocol object or semantic authority.

Top-level Agent Service type debt:

```text
R3 baseline: 171
R4:          170
R5:          169
retired:       2
```

The CORE_ZERO ratchet now permanently retires:

- CapabilityAdvertisement
- AgentInterfaceAdvertisement

## Ownership split

The former local type mixed several different owners:

- A2A endpoint interoperability belongs to A2A AgentInterface / AgentCard projection.
- MCP endpoint/version configuration belongs to the MCP-facing adapter/deployment configuration.
- route priority is deployment policy/profile data.
- credential/security requirements are authorization/credential-binding inputs, not a new agent-interface ontology.
- immutable effect identity remains in the existing TransportBinding migration surface until its own deletion wave.

R5 deliberately does not invent a cross-protocol universal interface object.

## Behavioral preservation

The route planner still:

- requires an advertised route profile;
- honors explicit transport preference;
- selects deterministically by priority and stable profile identity;
- binds protocol version and endpoint into immutable TransportBinding identity;
- preserves response-loss replay behavior;
- fails closed for legacy rows without protocol version;
- stores security requirements but never credential material.

## Remaining migration debt

- AgentInterfaceAdvertisementStore
- agent_interface_advertisements
- CapabilityAdvertisementStore
- capability_advertisements
- TransportBinding
- TransportBindingStore
- transport_bindings

The table/store names are historical compatibility debt, not accepted architectural primitives.

## Next deletion pressure

The next useful attack is not to rename the stores. It is to identify which persisted rows can move into:

1. immutable agent revision artifacts / A2A AgentCard material;
2. MCP-native deployment configuration;
3. policy/credential references;
4. disposable route projections.

Only after foreign-key and replay parity is proven should the historical tables be removed.
