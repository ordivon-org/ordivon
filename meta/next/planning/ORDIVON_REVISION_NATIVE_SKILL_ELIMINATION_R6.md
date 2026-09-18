# ORDIVON REVISION-NATIVE SKILL ELIMINATION R6

Date: 2026-09-19  
Status: THIRD_PRODUCTION_DELETION  
Parent: ORDIVON_INTERFACE_PROFILE_ELIMINATION_R5

## Result

R6 eliminates the second capability persistence surface rather than renaming it.

Deleted from the live production path:

- `CapabilityAdvertisementStore`
- `capability_advertisements`
- `service.capabilities`
- package export `agent_service.CapabilityAdvertisementStore`

Already retired in R4:

- `CapabilityAdvertisement`

No replacement `RevisionSkillStore`, `SkillRegistry`, or Ordivon-owned capability object was introduced.

Top-level Agent Service type debt:

```text
R3 baseline: 171
R4:          170
R5:          169
R6:          168
retired types: 3
```

## Replacement owner

Agent skills are now part of the immutable `AgentRevision.spec["skills"]` payload and use the A2A 1.0 `AgentSkill` field shape.

The live path is now:

```text
AgentRevision immutable spec
    └── skills: AgentSkill[]
          ├── A2A AgentCard projection
          └── delegation skill existence check
```

There is no second mutable/revision-scoped capability table.

## Behavioral preservation

R6 preserves the behaviors that had been attributed to the old store:

- AgentCard discovery projects the revision's skills.
- delegation fails closed when the requested skill id is absent.
- revision reconstruction preserves skills because the revision spec is already durable and content-addressed.
- input/output media types are normalized only at the A2A projection boundary.
- duplicate AgentSkill ids and malformed required fields fail closed when consumed.
- no authorization state is inferred from skill presence.

## Persistence deletion

Fresh R8+ databases no longer create:

```text
capability_advertisements
```

The CORE_ZERO profile records this under `retiredPersistenceSurfaces`.

Historical graph evidence that names `CapabilityAdvertisementStore` remains intentionally frozen as historical evidence. It is not a live production dependency.

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

This includes control-stability, failover, delivery response-loss, remote evidence, provider adapters, credentials, semantic reconstruction, and repository-wide CORE_ZERO / research / browser-security checks.

## Next deletion pressure

The next high-value target is the remaining interface persistence pair:

- `AgentInterfaceAdvertisementStore`
- `agent_interface_advertisements`

Unlike capability persistence, this table is still referenced by immutable `TransportBinding.interface_id`, so the next wave must first prove reconstruction/replay parity for binding identity before removing the table.

A secondary candidate is `PolicyDecision` / `PolicyDecisionStore`, but it should be attacked only after confirming which historical decision receipt semantics must survive OPA replacement.
