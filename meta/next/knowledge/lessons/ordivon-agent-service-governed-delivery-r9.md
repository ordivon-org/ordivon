# Ordivon Agent Service — Governed Delivery R9

Status: **IMPLEMENTED SEMANTIC/DELIVERY SUBSTRATE / CONCRETE REMOTE A2A-MCP PROVIDERS DEFERRED**
Date: 2026-09-18
Base implementation: `709faa6b1127de4d5f96ba3969c112db74112b55`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r9-governed-delivery-delta.json`
Acceptance: `evidence/acceptance/agent-service-governed-delivery-r9.json`

## One-sentence result

**R9 separates authorization, route selection, immutable transport binding, provider delivery, and remote correlation so a DelegationEnvelope can be governed and delivered without making A2A/MCP transport IDs part of Agent Service Task/Session truth.**

## R9 pipeline

```text
DelegationEnvelope
      ↓
PolicyEvaluationCoordinator
      ↓
PolicyAdapter
      ↓
PolicyDecisionStore
      ↓ allowed only
DelegationRoutePlanner
      ↓
AgentInterfaceAdvertisementStore
      ↓
TransportBindingStore
      ↓
DeliveryCoordinator
      ↓
DeliveryAdapter
      ↓
DeliveryReceiptStore
```

The route planner does not evaluate policy. The delivery adapter does not choose semantic intent. The receipt does not redefine Task or Session identity.

## AgentInterfaceAdvertisementStore

R8 capability metadata answers **what the Agent revision says it can do**. R9 interface metadata answers **where/how a governed delegation may be sent**.

One advertisement contains:

```text
AgentRevision
transport
URL
priority
security requirements
```

Security requirements are declarations such as an OAuth2 scheme and requested scopes. They are not tokens, credentials, authenticated principals, or proof that a caller is authorized.

A revision may expose multiple endpoints for the same transport. Identity is therefore:

```text
(revision, transport, URL)
```

not merely `(revision, transport)`.

The same exact interface is immutable; changing its priority/security declaration under the same identity fails closed.

## Policy: permissions are not OAuth scopes

The first R9 draft called policy output `granted_scopes`. Review rejected that terminology because OAuth scopes belong to transport/security protocols while an application policy decision may grant a different permission vocabulary.

R9 now uses:

```text
PolicyObservation.granted_permissions
PolicyDecision.granted_permissions
```

while interface security metadata can independently contain protocol-specific scopes.

## Durable PolicyDecision

A policy request has caller-chosen exact replay identity:

```text
client_policy_request_id
```

On first evaluation, the external `PolicyAdapter` returns:

```text
allowed / denied
reason
policy revision
application permissions
```

R9 persists the result as `PolicyDecision`.

An exact replay returns the historical decision without invoking the current policy adapter again. This prevents policy drift from rewriting whether a previously admitted decision happened.

The decision remains bound to one DelegationEnvelope; it cannot be reused for another delegation.

## Route planning

`DelegationRoutePlanner` requires:

```text
existing DelegationEnvelope
+
allowed PolicyDecision bound to that exact envelope
+
interfaces advertised by target AgentRevision
```

Only then may it create a route binding.

Preferred transport order is caller-provided routing intent, but the selected endpoint must exist in target revision advertisement.

## Multiple bindings per Delegation

The first R9 implementation forced one route per DelegationEnvelope. That was too restrictive because transport fallback would then require mutating intent or minting a fake second delegation.

R9 now supports:

```text
DelegationEnvelope D
   ├── Binding A: A2A primary
   └── Binding B: MCP fallback
```

Each binding is immutable and content-addressed by:

```text
DelegationEnvelope
PolicyDecision
AgentInterfaceAdvertisement
```

A route candidate therefore records **how this same semantic delegation may be delivered**, not a new semantic intent.

## TransportBinding is local route truth

TransportBinding stores:

```text
delegation id
policy decision id
interface id
transport
endpoint
security requirements
deterministic delivery_request_id
```

It deliberately does not store:

```text
remote A2A taskId
remote A2A contextId
remote MCP execution identity
```

Those values do not exist until delivery/provider admission and belong in the delivery correlation layer.

## DeliveryCoordinator and exact request identity

Each binding deterministically maps to one `delivery_request_id`.

```text
TransportBinding
   ↓
delivery_request_id
   ↓
DeliveryAdapter.send(...)
```

If the provider commits but the local response is lost before a `DeliveryReceipt` is persisted, retry uses the same exact delivery request identity.

R9 does **not** claim that arbitrary remote side effects are universally idempotent. Provider exact replay must be implemented by the concrete adapter/protocol/provider. The test transport demonstrates the intended contract by returning `admission=existing` on replay.

Once a local DeliveryReceipt exists, `DeliveryCoordinator.deliver(binding)` returns it directly and does not re-send.

## DeliveryReceipt owns remote correlation

DeliveryReceipt contains delivery/provider facts:

```text
binding id
delivery request id
provider admission
provider status
provider request id
optional remote task id
optional remote context id
```

A2A-like transports may return remote task/context IDs. MCP-like transports may not.

These fields never get copied into local Agent Service `Task` or `Session` records.

This preserves:

```text
local Task.id    != remote A2A taskId
local Session.id != remote A2A contextId
```

## A2A semantic boundary

Current A2A 1.0 defines Task IDs as service-side work-unit identifiers and context IDs as opaque correlation/grouping identifiers for remote interactions.

R9 therefore treats them as provider correlation facts rather than importing them into local semantic identity.

Agent Card interface/security declarations likewise describe how a remote agent may be contacted; they are not credential material.

## MCP semantic boundary

Current MCP separates transport/security authorization from application/session semantics. R9 follows that split:

```text
Interface security requirements
    ≠
PolicyDecision.granted_permissions
    ≠
Session continuity
```

## Composition dogfood

A full in-memory/SQLite composition was exercised with:

```text
source AgentIdentity
      ↓
Goal-bound Session
      ↓
DelegationEnvelope(review)
      ↓
allowed PolicyDecision(review.invoke)
      ↓
A2A primary binding
MCP fallback binding
      ↓
A2A-like DeliveryAdapter
      ↓
DeliveryReceipt(remote task/context)
```

Observed:

```text
bindingCount = 2
primaryTransport = a2a-jsonrpc
fallbackTransport = mcp
primaryHasRemoteTask = false
receiptRemoteTask = remote-task-dogfood
receiptRemoteContext = remote-context-dogfood
remoteTaskDiffersFromLocalTask = true
remoteContextDiffersFromLocalSession = true
taskHasRemoteTask = false
sessionHasRemoteContext = false
```

This proves the correlation boundary at composition level. It is not a claim of live remote A2A/MCP interoperability.

## What R9 deliberately does not claim

R9 does not yet include a concrete live remote implementation of:

```text
A2A JSON-RPC/HTTP delivery
A2A streaming delivery
MCP delegated delivery
OAuth token acquisition/storage/refresh
external identity proof
remote status reconciliation after initial delivery
```

Those remain replaceable providers above/below the R9 semantic contract.

## Next decomposition boundary

The next useful slice is **remote lifecycle / identity proof / audit**, not another router:

```text
IdentityProofAdapter
CredentialReference / secret boundary
RemoteDeliveryObserver
RemoteCorrelationReconciler
AuditProjector / TraceBridge
```

Concrete A2A and MCP adapters can then be implemented against the already-frozen binding/delivery contracts without changing Goal, Task, Session, Delegation or Policy semantics.
