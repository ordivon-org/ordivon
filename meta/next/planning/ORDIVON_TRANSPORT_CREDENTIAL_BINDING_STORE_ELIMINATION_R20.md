# ORDIVON TRANSPORT CREDENTIAL BINDING STORE ELIMINATION R20

Date: 2026-09-19
Status: SEVENTEENTH_PRODUCTION_DELETION
Parent: ORDIVON REMOTE DELIVERY OBSERVATION STORE ELIMINATION R19

## Result

R20 removes the specialized TransportCredentialBindingStore, transport_credential_bindings table, and service.transport_credential_records surface.

TransportCredentialBinding remains only as a projection over generic immutable ServiceEvent receipts.

Deleted authority:

- TransportCredentialBindingStore
- transport_credential_bindings
- service.transport_credential_records
- package export agent_service.TransportCredentialBindingStore
- FK authorities from the deleted table to transport_bindings, credential_references, identity_proof_records

No replacement credential-binding Store/Registry class was introduced.

## LEGO decomposition used before deletion

The chain was decomposed as:

TransportBinding = immutable route/security coordinate
TransportCredentialBinding = immutable association receipt
IdentityProofRecord = time-sensitive authentication evidence
CredentialReference = opaque external credential locator
CredentialMaterialProvider = external secret authority

Only the association receipt was migrated in R20.

## Generic receipt design

### Exact request replay

TransportCredentialBindingRequest/<client_binding_request_id>
  sequence 1
  TransportCredentialBindingRequestCommitted
  -> transportCredentialBindingId

### Scheme single ownership + canonical binding receipt

coordinate = sha256(canonical_json([binding_id, security_scheme]))

TransportCredentialSchemeBinding/<coordinate>
  sequence 1
  TransportCredentialBindingRecorded
  -> bindingId
  -> securityScheme
  -> credentialReferenceId
  -> identityProofId
  -> requiredScopes

This replaces UNIQUE(binding_id, security_scheme).

### Binding index

TransportCredentialBindingIndex/<binding_id>
  sequence N
  TransportCredentialBindingIndexed
  -> transportCredentialBindingId
  -> securityScheme

This preserves multi-scheme enumeration for BoundCredentialHeaderProvider.

## Security boundaries preserved

R20 intentionally retains:

- CredentialReferenceStore
- IdentityProofRecordStore
- IdentityProofCoordinator
- IdentityProofAdapter
- CredentialMaterialProvider
- TransportBinding.security_requirements
- TransportBinding.granted_permissions

These checks remain unchanged:

- scheme must exist in immutable TransportBinding
- proof must be authenticated and current
- proof identity must equal Delegation source identity
- requested scopes must cover required scopes
- policy grant must cover required scopes
- credential resource must cover endpoint
- resolved material issuer/resource/scopes must match
- resolved material expiry is checked at use time
- transient headers are never persisted
- CR/LF and duplicate-header validation remain in header resolution

## Secret persistence boundary

R20 stores only ids/scopes in ServiceEvent payloads. Resolved secret/header material still comes exclusively from CredentialMaterialProvider and remains ephemeral.

## Destructive migration

A database containing the obsolete transport_credential_bindings table fails closed during R14 initialization.

No compatibility shim or silent migration is retained.

## CORE_ZERO ratchet

R3 baseline: 171
R4: 170
R5: 169
R6: 168
R7: 167
R8: 165
R9: 164
R10: 162
R11: 161
R12: 160
R13: 159
R14: 158
R15: 157
R16: 156
R17: 155
R18: 154
R19: 153
R20: 152
cumulative retired top-level types: 19

Structural audit:

observed top-level Agent Service classes = 152
legacy ceiling = 152
unexpected new classes = []
retired overlap = []
old TransportCredentialBindingStore/table = none
transport_credential_records facade refs = none
replacement binding stores = none

## Validation

R20 direct GREEN:
Ran 20 tests — OK

Cross-layer credential/effect/trust/failover regression:
Ran 68 tests — OK

CORE_ZERO / structural deletion gate:
Ran 32 tests — OK

Agent Service regression suite:
Ran 238 tests — OK (skipped=5)

Full repository regression suite:
Ran 337 tests — OK (skipped=5)

## Next deletion pressure

R20 removes the final local FK consumers of identity_proof_records and credential_references from transport credential binding.

R21 must freshly audit IdentityProofRecordStore before any deletion. It may be immutable evidence, but currentness, audit projection, exact replay, external verifier authority, and any remaining consumers must be proved first.

CredentialReferenceStore must not be removed merely because R20 removed one consumer.
