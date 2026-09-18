# Ordivon Agent Service — Trust Boundary / Remote Lifecycle R10

Status: **IMPLEMENTED SEMANTIC TRUST + REMOTE OBSERVATION SLICE / SECRET PROVIDERS AND LIVE REMOTE ADAPTERS REMAIN EXTERNAL**
Date: 2026-09-18
Base implementation: `2ff2c1ad3decea4e9b00d245cc30caf1c5bc564e`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r10-trust-remote-delta.json`
Acceptance: `evidence/acceptance/agent-service-trust-remote-r10.json`

## Result

R10 closes four authority gaps left intentionally after governed delivery:

```text
credential locator != secret material
AgentIdentity != authenticated principal
remote provider terminal != local Task terminal
Audit != second state authority
```

The resulting path is:

```text
CredentialReference
       ↓
IdentityProofCoordinator
       ↓
IdentityProofAdapter
       ↓
IdentityProofRecord

DeliveryReceipt
       ↓
RemoteDeliveryObserver
       ↓
RemoteCorrelationReconciler
       ↓
RemoteDeliveryObservationStore
       ↓
existing evidence / semantic verifier path

all authoritative stores
       ↓
AuditEnvelopeProjector
```

## CredentialReferenceStore

`CredentialReference` records only metadata needed to locate and constrain externally managed credentials:

```text
client reference id
provider
opaque reference
issuer
resource
requested OAuth scopes
```

It deliberately has no fields for:

```text
access_token
client_secret
secret_material
```

R10 does not fetch a credential into Agent Service state. A concrete external adapter/provider may resolve the opaque reference when authentication is actually performed.

Exact replay of the same caller reference returns the existing record; conflicting reuse of the same caller identity fails closed.

## AgentIdentity != authenticated principal

`AgentIdentity` remains the stable semantic identity introduced in R8.

R10 adds `IdentityProofRecord` for a different fact:

```text
At time T, adapter A observed that credential reference C authenticated as principal P,
under issuer I and auth method M, for purpose X.
```

That record is evidence. It does not mutate `AgentIdentity` and does not add `principal_id` to the semantic identity object.

Authentication also does not bypass the R9 PolicyDecision path. Identity proof and authorization remain separate.

## Exact authentication replay

`IdentityProofCoordinator.verify(...)` accepts a caller-chosen exact request identity.

On first execution:

```text
IdentityProofRequest
   + CredentialReference
          ↓
IdentityProofAdapter.verify
          ↓
IdentityProofObservation
          ↓
issuer consistency checks
          ↓
IdentityProofRecord
```

On exact replay, the historical proof is returned before consulting the current adapter.

This prevents a changed or temporarily unavailable authentication provider from rewriting whether a prior proof request already committed.

## Issuer binding

The proof adapter returns the observed issuer. R10 requires:

```text
IdentityProofObservation.issuer == CredentialReference.issuer
```

Mismatch fails closed and no proof record is persisted.

Resource binding is supplied to the adapter through the immutable CredentialReference/request. Concrete provider adapters remain responsible for cryptographically/protocol-correct verification against that resource.

## Freshness is derived

Proof records are historical evidence, so they are not mutated into `EXPIRED` state.

Current usability is projected as:

```text
authenticated
AND
(expires_at_ms is null OR now < expires_at_ms)
```

This avoids creating another mutable lifecycle state for an immutable authentication receipt.

## Remote lifecycle is observation, not semantic completion

R9 records delivery admission/correlation. R10 can then poll or query remote providers through `RemoteDeliveryObserver`.

A snapshot contains:

```text
provider status
terminal flag
successful flag
remote task id
remote context id
artifact refs
evidence ref
observation time
```

These values are stored as append-only provider observations.

Even this observation:

```text
provider_status = TASK_STATE_COMPLETED
terminal = true
successful = true
```

does **not** directly change local Agent Service Task state.

The test explicitly confirms the local Task remains `PENDING` and receives no `TASK_SUCCEEDED` event.

Local success must still flow through the established semantic evidence path rather than accepting provider process/lifecycle status as business truth.

## Remote correlation stability

There are two valid ways remote task/context correlation can appear:

1. The initial DeliveryReceipt contains remote IDs.
2. The initial receipt has no remote IDs and the first later provider observation establishes them.

Both are supported.

Once a non-null remote task/context identity exists, later observations cannot change or clear it.

This prevents:

```text
local binding B
  -> remote task X
  -> later response silently claims remote task Y
```

from being accepted as ordinary progression.

Correlation mismatch fails before a snapshot is persisted.

## Observation deduplication

Identical consecutive provider observations return the existing latest snapshot instead of writing duplicate rows.

Meaningful state changes append a new monotonic sequence value.

The history survives service reconstruction.

## Audit is a projection

R10 deliberately does not create:

```text
audit_records
```

`AuditEnvelopeProjector` reads authoritative stores and emits bounded audit envelopes.

Identity-proof audit includes stable IDs and proof metadata but not the credential locator.

Remote-delivery audit includes local IDs, route/delivery identity, provider correlation and latest status, but not the DelegationEnvelope payload.

This prevents an audit subsystem from becoming both a shadow state authority and a secret/data exfiltration surface.

## R10 architecture

```text
AgentIdentity ------------------------------┐
                                             │
CredentialReferenceStore (N51)              │
       ↓                                     │
IdentityProofCoordinator (N53)               │
       ↓                                     │
IdentityProofAdapter (refined N16)           │
       ↓                                     │
IdentityProofRecordStore (N52)               │
                                             │
TransportBinding + DeliveryReceipt ----------┤
       ↓                                     │
RemoteDeliveryObserver (N55)                 │
       ↓                                     │
RemoteCorrelationReconciler (N56)            │
       ↓                                     │
RemoteDeliveryObservationStore (N54)         │
       ↓                                     │
Evidence / SemanticVerifier                  │
                                             │
Authoritative stores ------------------------┘
       ↓
AuditEnvelopeProjector (N57)
       ↓
future TraceBridge / telemetry sink
```

## What R10 does not claim

R10 does not implement or persist secret material. It also does not yet claim live interoperability for:

```text
Vault / OS keychain / cloud secret manager lookup
OAuth token acquisition or refresh
A2A authenticated HTTP client
MCP authenticated client
remote artifact retrieval
remote provider streaming/status adapters
OpenTelemetry export
```

Those remain replaceable provider integrations against the now-separated semantic contracts.

## Next boundary

The next useful slice should connect remote completion evidence back into the existing semantic verification pipeline without weakening it:

```text
Remote artifact/evidence resolver
        ↓
normalized evidence object
        ↓
existing SemanticVerifier
        ↓
local Task verdict
```

Concrete A2A/MCP adapters and secret-provider adapters can be implemented in parallel because the identity, credential-reference, route, correlation and observation boundaries are now explicit.
