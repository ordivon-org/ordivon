# Ordivon Agent Service — Interface Version, Credential Bridge, and Local Effect Reader R14

Status: **IMPLEMENTED / FINAL VERIFICATION PENDING**
Date: 2026-09-18
Base implementation: `0f9e76007c81c6ebd38dc22f58d1c23a2048632e`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r14-interface-credential-effect-delta.json`
Acceptance: `evidence/acceptance/agent-service-interface-credential-effect-r14.json`

## One-sentence result

R14 moves protocol compatibility into immutable interface/binding identity, connects secret-free CredentialReferences to transient HTTP credential material through current proof/policy checks, and plugs the existing Harness Browserless turn-effect fence into R13 as a narrow read-only production effect reader.

## 1. Protocol version is now durable routing identity

Before R14 the route contained transport and endpoint while A2A version could be selected by the final HTTP client.

R14 freezes:

```text
AgentInterfaceAdvertisement
  transport
  protocolVersion
  url
  securityRequirements
        ↓
TransportBinding
  transport
  protocolVersion
  endpoint
  securityRequirements
```

For newly advertised interfaces, protocolVersion is mandatory.

A2A versions use Major.Minor form. MCP versions use valid date-version form.

Historical rows from pre-R14 databases may have NULL protocol_version after schema migration. Those rows are historical only. R14 refuses to silently interpret them as a current version and requires explicit operator migration/re-advertisement.

A2AJsonRpcHttpClient now derives A2A-Version from the immutable Binding. An optional configured resolver may agree with it, but cannot override a conflict.

MCPTasksHttpClient likewise rejects a Binding that declares a different protocol version from the client implementation.

## 2. CredentialReference becomes usable without becoming a secret store

R10 created CredentialReference as an opaque locator.

R14 adds:

```text
CredentialReference
     +
current IdentityProof
     +
TransportBinding
     +
PolicyDecision
     ↓
TransportCredentialBinding
```

The durable binding stores only:

```text
binding_id
security_scheme
credential_reference_id
identity_proof_id
required_scopes
```

It contains no access token, client secret or Authorization header.

### Binding gate

Before the reference can be bound, R14 verifies:

```text
IdentityProof.identity == Delegation.sourceIdentity
IdentityProof.current == true
Credential.resource covers Binding.endpoint
Credential.requestedScopes ⊇ Binding.requiredScopes
PolicyDecision.grantedPermissions ⊇ Binding.requiredScopes
```

Thus a credential that is valid somewhere does not become authority for another Binding.

## 3. Secret material stays with the external authority

`CredentialMaterialProvider` is the external secret seam.

At HTTP-effect time:

```text
TransportCredentialBinding
      ↓
CredentialReference
      ↓
external CredentialMaterialProvider
      ↓
CredentialHeaderMaterial
      ↓
BoundCredentialHeaderProvider
      ↓
A2A / MCP HTTP request
```

Resolved material is rechecked for:

- issuer;
- resource;
- required scopes;
- expiry;
- header shape / CRLF injection;
- duplicate header ownership across security schemes.

The material is never inserted into Agent Service tables.

A real composition test injects an Authorization bearer header into an A2A request while simultaneously deriving A2A-Version from the same immutable TransportBinding; the bearer value is absent from persistent transport/credential tables and from client/header-provider reprs.

## 4. Local effect-substrate discovery

A cross-project scan found no universal Ordivon business-effect ledger.

It did find a real narrow effect authority in:

```text
/root/projects/ordivon-harness
  Browserless ChatGPT Web continuation path
```

The provider effect script owns a SQLite table:

```text
turn_effects
  turn_request_id
  prompt_digest
  target_coordinate
  state
  receipt_json
  updated_at_ms
```

Its critical ordering is:

```text
hydrate/validate target
      ↓
BEGIN IMMEDIATE
      ↓
insert UNKNOWN effect fence
      ↓
COMMIT
      ↓
send.click()
      ↓
observe provider state
      ↓
COMPLETED or remain UNKNOWN
```

That is a real durable effect fence, but only for this ChatGPT Web SEND family.

## 5. BrowserlessTurnEffectLedgerReader

R14 supplies a read-only `BrowserlessTurnEffectLedgerReader`.

It does not import Harness code and never mutates the Harness database.

Mapping:

```text
ledger missing
  -> complete=false
  -> UNKNOWN

turn_effects table missing
  -> complete=false
  -> UNKNOWN

authoritative table exists
exact turn row absent
  -> complete=true + zero effects
  -> NO_EFFECTS

row.state = UNKNOWN
  -> UNKNOWN effect
  -> replay blocked

row.state = COMPLETED
  -> COMMITTED effect
  -> no idempotency key
  -> PARTIAL_EFFECTS
  -> ordinary replay blocked
```

A COMPLETED receipt is accepted only when the receipt identity matches:

```text
turnRequestId
promptDigest
targetResource
receiptDigest
```

This reader is therefore a production reader for one domain-specific existing ledger, not a claim of universal effect coverage.

## 6. Authority conservation

R14 does not move existing authority.

```text
AgentInterface/Binding
  own durable compatibility/routing identity

CredentialReference
  owns secret-free external credential locator metadata

IdentityProof
  owns historical authentication evidence

PolicyDecision
  owns delegation authorization decision

external CredentialMaterialProvider
  owns actual secret material

Harness Browserless ledger
  owns one provider-effect family

R12
  owns durable quiescence/replay/claim-transfer records

R11
  owns semantic completion
```

## Explicit non-claims

R14 does not claim:

- a universal Ordivon effect ledger exists;
- Browserless turn_effects covers non-Browserless effects;
- protocol idempotency means business exactly-once;
- a valid credential is automatically authorized for every endpoint;
- pre-R14 NULL protocol versions can be guessed safely;
- provider completion proves semantic Task success.

The next expansion should be adapter-by-adapter: reuse natural effect authorities for each consequential provider family rather than building a generic second effect database inside Agent Service.
