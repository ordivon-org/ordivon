# Ordivon Agent Service — Identity / Capability / Session / Delegation R8

Status: **IMPLEMENTED / TRANSPORT-NEUTRAL SEMANTIC SLICE / NOT YET A2A-MCP DELIVERY**
Date: 2026-09-18
Base implementation: `e3453718b54eb715b8a564d525a5f9dfd7014ff2`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r8-semantics-delta.json`
Acceptance: `evidence/acceptance/agent-service-semantics-r8.json`

## One-sentence result

**R8 creates the semantic objects that must exist before routing: stable Agent identity, immutable revision-scoped capability advertisement, transport-independent Session continuity, append-only Session items, and immutable transport-neutral Delegation envelopes.**

## Why R8 exists before MCP/A2A routing

The old R2 governed-capability cluster grouped:

```text
ServiceRouter
IdentityAdapter
PolicyAdapter
A2AAdapter
MCPAdapter
```

That shape was too transport-centric. A router cannot correctly route until the system can answer:

```text
Who is delegating?
Which stable Agent is the target?
Which exact AgentRevision advertises the capability?
Which semantic Session/Goal does this work belong to?
Which Task is being delegated?
What payload and evidence contract were requested?
```

R8 supplies those answers without selecting a transport.

## AgentIdentity != AgentInstance

`AgentIdentityStore` binds one stable identity to one `AgentDefinition`.

```text
AgentDefinition
     ↓
AgentIdentity       stable semantic identity
     │
     ├── AgentRevision v1
     │      └── AgentInstance A
     │
     └── AgentRevision v2
            └── AgentInstance B
```

An Instance may be born, replaced or retired without changing the semantic Agent identity.

AgentIdentity stores:

```text
identity id
AgentDefinition id
stable name
description
```

It does not store provider placement, birth request, session state, access token or credential material.

## CapabilityAdvertisement != permission

`CapabilityAdvertisementStore` records immutable metadata for one exact AgentRevision:

```text
revision id
capability key
description
input modes
output modes
tags
```

The same `(revision, capability key)` is exact-replay safe. Attempting to mutate its meaning fails closed.

This object says:

```text
this revision advertises capability X
```

It does **not** say:

```text
caller Y is authorized to invoke X
```

Policy remains a later node.

## Session is continuity, not transport

R8 implements R2 `N07 SessionStore` as semantic continuity state:

```text
Session
├── client session identity
├── initiator AgentIdentity
├── optional Goal binding
├── OPEN / CLOSED lifecycle
└── ordered SessionItem history
```

There is intentionally no:

```text
MCP connection id
HTTP connection id
socket id
process id
A2A remote task id
```

A transport may reconnect while the same semantic Session continues.

## Initiator is not owner/authority

The first R8 draft called the Session field `owner_identity_id` and temporarily required delegation source identity to equal that owner.

That was rejected during review because it conflated continuity provenance with authorization.

R8 now uses:

```text
initiator_identity_id
```

The initiator records who created the continuity anchor. It does not grant or restrict permission to delegate. Future PolicyEvaluator logic owns that decision.

## SessionItemStore

Conversation/continuity history is its own brick:

```text
SessionItem
├── session id
├── caller-provided client item id
├── monotonic sequence
├── role
├── JSON content
├── optional producer AgentIdentity
└── timestamp
```

Exact replay of the same client item returns the existing item. Conflicting replay fails closed.

Closing a Session prevents new items.

## DelegationEnvelope != Assignment

R5 already owns local execution Assignment:

```text
Task -> Assignment -> Runtime Job
```

R8 adds a different object:

```text
DelegationEnvelope
```

It means:

```text
within Session S,
source Agent identity/instance asks
specific target Agent identity/revision
to address Task T
using advertised capability C
with payload P
and expected evidence contract E.
```

It contains no transport selection and no remote Task ID.

A future router may bind the same semantic envelope to A2A or another approved transport without changing what was delegated.

## Delegation consistency laws

Before creating a new envelope R8 verifies:

- Session exists and is OPEN;
- source AgentInstance belongs to source AgentIdentity;
- target AgentRevision belongs to target AgentIdentity;
- target revision advertises the requested capability;
- Task exists;
- when Session is Goal-bound, Task belongs to the same Goal.

The envelope itself grants no permission. Policy evaluation is deliberately absent from R8.

## Exact replay precedence

For a known `client_delegation_id`, exact replay is resolved before current Session state is consulted.

That means:

```text
create delegation
response lost
Session later closes
retry exact same client_delegation_id
    ↓
return historical committed envelope
```

rather than misreporting that the historical operation never happened because current Session state changed.

A conflicting replay using the same identity but different payload/target/evidence contract fails closed.

## Goal-scoped Session

A Session may optionally bind to one Goal.

When it does, a DelegationEnvelope may reference only a Task attached to that Goal. This is semantic scope, not authorization.

It prevents continuity for Goal A from silently carrying a Task from Goal B.

## A2A Agent Card projector

R8 includes `A2AAgentCardProjector` as a pure projection, not an A2A transport implementation.

Inputs:

```text
AgentIdentity
exact AgentRevision
CapabilityAdvertisements
explicit supported interface declarations
```

Output includes A2A 1.0.0 discovery fields such as:

```text
protocolVersion
name
description
url / preferredTransport
supportedInterfaces
default input/output modes
skills
```

The projector does not expose:

```text
AgentInstance id
birth request
Session id/history
credentials
policy decisions
placement state
```

## Standards basis

R8 was checked against current external conventions on 2026-09-18:

### A2A Protocol 1.0.0

The current A2A specification defines Agent Card as discovery metadata for agent identity, capabilities/skills, supported interfaces and interaction/security requirements while allowing the remote agent implementation to remain opaque.

R8 therefore treats Agent Card as a projection, not Agent Service state authority.

### MCP 2026-07-28

The current MCP specification explicitly separates request/transport connection state from conversation/session continuity. An open connection or process must not be used as a proxy for a semantic Session.

R8 therefore contains no MCP connection identity inside `Session`.

### OpenAI Agents SDK

The SDK exposes Sessions as persistent conversation history and Handoffs as a separate delegation primitive.

R8 follows the same separation at the semantic level without depending on that SDK implementation.

## R8 architecture

```text
AgentDefinition
    ↓
AgentIdentityStore (N39)
    │
    ├──────── AgentRevision
    │              ↓
    │   CapabilityAdvertisementStore (N40)
    │
    └──── SessionStore (N07)
              ↓
       SessionItemStore (N41)
              ↓
     DelegationEnvelopeStore (N42)
              ↓
       future PolicyEvaluator
              ↓
       future ServiceRouter
          ┌───┴────┐
       A2AAdapter MCPAdapter
```

Discovery is separate:

```text
AgentIdentity
+
CapabilityAdvertisement
+
explicit interface declarations
        ↓
A2AAgentCardProjector (N43)
        ↓
public Agent Card
```

## What R8 deliberately does not implement

R8 does not yet implement:

```text
external authenticated identity proof
policy authorization
transport selection
A2A request/task delivery
MCP delegation delivery
remote-task correlation
transport retry receipt
OAuth/token handling
```

Those belong in the next slice after semantic identity and intent are frozen.

## Next decomposition boundary

R9 should introduce a governed delivery pipeline:

```text
DelegationEnvelope
      ↓
PolicyEvaluator
      ↓
DelegationRoutePlanner
      ↓
TransportBinding
      ├── A2AAdapter
      └── MCPAdapter
      ↓
DeliveryReceipt / RemoteCorrelation
```

Identity proof should remain another adapter feeding PolicyEvaluator; it must not mutate AgentIdentity semantic records.
