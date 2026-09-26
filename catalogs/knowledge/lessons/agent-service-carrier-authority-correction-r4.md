# Ordivon Agent Service — Carrier Authority Correction R4

Status: **IMPLEMENTED / LIVE READ-ONLY PROVIDER INTEGRATION / NO CUTOVER**
Date: 2026-09-17
Base implementation: `afa0f74577eb240fa8e12431e5606f9b4694f15e`
Architecture delta: `catalogs/knowledge/graphs/ordivon-agent-service-r4-authority-delta.json`
Acceptance: `evidence/acceptance/agent-service-carrier-r4.json`

## One-sentence result

**R4 replaces the misleading `HostAdapter` interpretation with a generic `CarrierProviderAdapter` and proves that the unchanged Agent Service Birth/Placement kernel can consume the existing Workstation-owned Agent Automation carrier as a real provider seam.**

## Why R2's N18 name was wrong

R2 named N18 `HostAdapter` because the initial decomposition treated Host as the likely local continuity/presence provider. Source and live-interface inspection falsified that assumption.

Current Host v2 explicitly defines itself as a durable semantic continuity and collaboration substrate. It owns revisioned WorkingCheckpoint persistence, Host-local semantic lifecycle, Board collaboration, exact re-entry navigation and News revisions. It explicitly does **not** own execution, assignment, deployment truth, Runtime/Git currentness or external-world truth.

The production Host MCP confirms this boundary: it exposes continuity, Board and News surfaces; it has no `ensure carrier`, `spawn agent`, `retire carrier`, or deployment observation API.

Therefore adding those effects to Host merely to satisfy Agent Service would create a new authority rather than adapt an existing one.

## Natural owner chain discovered

```text
Agent Service
  desired Agent placement / semantic readiness
        |
        v
CarrierProviderAdapter
        |
        v
Workstation v2 stable carrier
  /root/tools/bin/agent-automation
  release admission fence + immutable release delegation
        |
        v
Harness Agent Automation
  census / birth / reconcile
  provider-specific effect identity and ambiguity fencing
        |
        v
Temporal
  durable provider workflow lifecycle
        |
        v
Browserless
  browser lifecycle / queue / concurrency / health
        |
        v
ChatGPT provider resource
```

Host v2 remains orthogonal:

```text
Agent/Task semantic continuity
        <-> Host v2

Agent placement/materialization
        <-> CarrierProviderAdapter
```

This is an authority correction, not a Host feature deletion.

## R4 implementation

R4 adds:

```text
CarrierProviderAdapter
  ensure(placement, instance, revision)
  observe(placement)
  retire(placement, instance)
```

`HostAdapter` remains a compatibility alias so the R3 API does not break.

The first real provider is:

```text
AgentAutomationCarrierAdapter
```

It intentionally calls only the Workstation-stable operator entrypoint. Agent Service does not import Browserless or Temporal implementation details.

## AgentRevision carrier profile

The adapter consumes one exact provider profile from immutable AgentRevision state:

```json
{
  "carrier": {
    "kind": "agent-automation-browserless",
    "campaignId": "campaign:...",
    "agentId": "A01",
    "sharedPrompt": "...",
    "roleCard": "..."
  }
}
```

It compiles that profile into the existing current Agent Automation `CampaignLaunchSpec` contract:

```json
{
  "campaignId": "campaign:...",
  "sharedPrompt": "...",
  "roster": [
    {"agentId": "A01", "roleCard": "..."}
  ]
}
```

The frozen compiled spec is provider-local data. Browserless/Temporal concepts do not enter Agent Service's core tables.

## Provider-local durable placement binding

The first adapter draft kept `placementId -> revisionId` only in process memory. TDD immediately exposed that a fresh adapter process could not observe an existing placement.

R4 therefore persists a narrow provider-local binding receipt:

```text
carrier-bindings/agent-automation/<sha256(placementId)>.json
  placementId
  revisionId
```

The file is private (`0600`), deterministic, exact-replay compatible and fails closed if the same Placement is rebound to another Revision.

This is not a second Agent Service truth store: Agent Service still owns DesiredPlacement. The receipt only lets this provider reconstruct which immutable provider profile realizes that Placement.

## Standing reducer

The adapter consumes the existing Agent Automation census without inventing a new provider lifecycle:

| Agent Automation standing | Agent Service provider observation | ensure action |
|---|---|---|
| unrecorded | `UNRECORDED` | `birth` |
| prepared | `PROVISIONING` | fail closed until supported/observed |
| unknown | `AMBIGUOUS` | `reconcile` |
| submit-observed | `AMBIGUOUS` | `reconcile` |
| pre-effect-failed | `PRE_EFFECT_FAILED` | same-identity `birth` re-entry |
| human-required | `HUMAN_REQUIRED` | no automatic effect |
| bound | `READY` | no redispatch |
| ready-confirmed | `READY` | no redispatch |

`READY` here means durable provider materialization is bound and the Agent Service provisioning contract may close. It does not mean every future invocation is guaranteed to pass current provider authentication, policy, tool or network admission. Those checks remain at their natural per-invocation owners.

## Critical non-idempotent safety rule retained

R4 does **not** translate `UNKNOWN` or `SUBMIT_OBSERVED` into another Birth. Those states may already have crossed SEND, so the adapter invokes the existing `reconcile` surface.

Likewise `HUMAN_REQUIRED` remains a no-op at Agent Service `ensure()`: provider evidence says SEND has not occurred but human verification is required. Agent Service does not silently bypass that gate.

Only `PRE_EFFECT_FAILED` may re-enter Birth automatically because the existing provider contract proves the effect did not cross SEND and retains the same effect identity.

## Live evidence

The production Workstation stable carrier was observed directly:

```text
/root/tools/bin/agent-automation
exists: yes
executable: yes
```

`doctor` reported three healthy Browserless endpoints and a healthy existing birth ledger. At the observation cut the ledger contained:

```text
requests             313
bound                150
pre-effect-failed    129
unknown               27
submit-observed        6
human-required         1
prepared               0
effect ambiguous      33
```

These counts are an observed operational cut, not permanent Agent Service truth.

### Live smoke 1 — synthetic, effect-free

A never-materialized synthetic CampaignSpec was submitted only to `census`. The real Workstation carrier returned no recorded occurrence, and the adapter projected:

```text
UNRECORDED
```

No Birth/SEND operation was invoked.

### Live smoke 2 — existing bound provider resource

An existing provider-bound occurrence was read from the production Agent Automation registry/ledger and observed through the new adapter. The adapter projected:

```text
READY
```

Again, only `census` was used; no provider effect was admitted.

### Live smoke 3 — full Agent Service reconciliation

A temporary R4 Agent Service SQLite database created a local AgentDefinition, immutable AgentRevision, AgentInstance and DesiredPlacement that referenced the already-bound provider occurrence. The unchanged R3 PlacementReconciler then traversed the real provider seam:

```text
PROVISIONING
  -> CarrierProviderAdapter.ensure()      # bound => no effect
  -> CarrierProviderAdapter.observe()     # real Workstation census
  -> ProviderObserver
  -> READY
```

Observed result:

```text
before        PROVISIONING
after         READY
observedState READY
events        [AGENT_BIRTH_REQUESTED, AGENT_READY]
```

No new Browserless/ChatGPT Birth or SEND was performed.

## What remains intentionally unsupported

`retire()` currently fails closed. The present Agent Automation public surface has no provider-conversation retirement operation, and R4 does not invent one by deleting provider-local files or reinterpreting Host continuity.

A future provider can implement retirement independently behind the same `CarrierProviderAdapter` contract.

## R4 verdict

**THE LEGO SEAM HELD: correcting N18 from Host-specific to provider-neutral required no rewrite of the eight other Slice 1 semantic nodes, and the same PlacementReconciler successfully consumed both a test provider and the real Workstation/Harness Agent Automation provider.**
