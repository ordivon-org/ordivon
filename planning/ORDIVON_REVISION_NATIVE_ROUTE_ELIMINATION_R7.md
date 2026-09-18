# ORDIVON REVISION-NATIVE ROUTE ELIMINATION R7

Date: 2026-09-19  
Status: FOURTH_PRODUCTION_DELETION  
Parent: ORDIVON_REVISION_NATIVE_SKILL_ELIMINATION_R6

## Result

R7 eliminates the remaining local interface persistence authority rather than renaming it.

Deleted from the live production path:

- `AgentInterfaceAdvertisementStore`
- `agent_interface_advertisements`
- `service.interfaces`
- package export `agent_service.AgentInterfaceAdvertisementStore`
- the foreign-key authority `transport_bindings.interface_id -> agent_interface_advertisements.id`

Already retired in R5:

- `AgentInterfaceAdvertisement`

No replacement `RouteProfileStore`, `InterfaceRegistry`, `RevisionRouteStore`, or universal cross-protocol interface class was introduced.

Top-level Agent Service type debt:

```text
R3 baseline: 171
R4:          170
R5:          169
R6:          168
R7:          167
retired types: 4
```

## Replacement ownership

Route declarations now live inside the immutable `AgentRevision.spec["routes"]` payload.

They are deployment/profile data consumed by protocol-specific adapters, not a new Ordivon protocol ontology.

The live path is:

```text
AgentRevision immutable spec
    └── routes[]
          ├── transport
          ├── protocolVersion
          ├── url
          ├── priority
          └── securityRequirements
                 ↓
        pure validation/projection
                 ↓
        TransportBinding
```

A stable `profileId` is derived from:

```text
revisionId
+ transport
+ protocolVersion
+ url
+ priority
+ securityRequirements
```

using canonical JSON + SHA-256.

That identifier is not a database entity authority. It is only content-addressed source identity material used when constructing an immutable TransportBinding.

## TransportBinding boundary

`TransportBinding` remains durable because it currently carries real replay/effect semantics:

- exact delegation and policy decision identity;
- selected transport and protocol version;
- exact endpoint;
- security requirement snapshot;
- deterministic delivery request identity;
- response-loss replay continuity.

R7 does not claim TransportBinding is irreducible. It only proves the interface table is not required to preserve these behaviors.

The binding now stores its source profile identifier as plain text. There is no foreign-key dependency back to a second interface state store.

## Behavioral preservation

After the deletion, Agent Service still preserves:

- deterministic route selection by explicit preference and priority;
- two distinct immutable bindings for primary/fallback routes;
- response-loss replay without duplicate remote effect;
- binding and receipt reconstruction after service restart;
- A2A and MCP protocol-version validation;
- credential scope/resource/issuer checks;
- secrets remaining transient;
- failover and quiescence behavior;
- same-failure-domain control-stability experiments.

## Destructive migration policy

If a database still contains the obsolete `agent_interface_advertisements` table, R9+ now fails closed on open.

There is deliberately no compatibility shim and no automatic silent migration.

An operator must perform an explicit destructive migration to the revision-native route schema.

This follows the current project rule: latest architecture only; compatibility debt is not accepted as a reason to preserve obsolete authority.

## Evidence

Agent Service regression suite after deletion:

```text
Ran 202 tests
OK (skipped=5)
```

Full repository regression suite:

```text
Ran 301 tests
OK (skipped=5)
```

The R9 delivery subset passes 9/9 and the R14 interface/credential subset passes 15/15.

The CORE_ZERO profile records:

- `AgentInterfaceAdvertisementStore` in `retiredLegacyTypes`;
- `agent_interface_advertisements` in `retiredPersistenceSurfaces`;
- the removed interface foreign key in `retiredForeignKeyAuthorities`.

## Next deletion pressure

The next strong candidate is the policy decision family:

- `PolicyDecision`
- `PolicyDecisionStore`
- `policy_decisions`
- `PolicyEvaluationCoordinator`

However, unlike capability/interface discovery, this family persists historical authorization decisions that are deliberately replayed without re-evaluating current policy. The next wave must first identify the mature owner for that decision receipt/evidence semantics—likely OPA decision logs/bundles plus provenance/evidence—not merely replace the class names.
