# ORDIVON IDENTITY PROOF RECORD STORE ELIMINATION R21

Date: 2026-09-19
Status: EIGHTEENTH_PRODUCTION_DELETION
Parent: ORDIVON TRANSPORT CREDENTIAL BINDING STORE ELIMINATION R20

## Result

R21 removes IdentityProofRecordStore, identity_proof_records, and service.identity_proof_records.

IdentityProofRecord remains as an immutable projection over a generic ServiceEvent receipt.

Deleted authority:
- IdentityProofRecordStore
- identity_proof_records
- service.identity_proof_records
- agent_service.IdentityProofRecordStore export
- identity_proof_records.identity_id -> agent_identities.id
- identity_proof_records.credential_reference_id -> credential_references.id

## LEGO classification

IdentityProofAdapter = external authentication authority
IdentityProofObservation = ephemeral external verification result
IdentityProofRecord = immutable authentication evidence receipt
IdentityProofRecordStore = specialized persistence only
IdentityProofCoordinator.is_current = deterministic interpretation of record + clock
CredentialReferenceStore = retained locator registry

Only the specialized persistence Store was eliminated.

## Durable receipt

IdentityProof/<client_proof_request_id>
  sequence 1
  IdentityProofRecorded
  payload = identityId / credentialReferenceId / purpose / authenticated / principalId / issuer / authMethod / observedAtMs / expiresAtMs / evidenceRef

ServiceEvent.id becomes IdentityProofRecord.id.

Exact request replay reads the existing aggregate and does not invoke IdentityProofAdapter again.

## Security semantics retained

- identity must exist before verification
- CredentialReference is still loaded before external verification
- no adapter means fail closed
- adapter must return IdentityProofObservation
- issuer must be non-empty and must match CredentialReference issuer
- auth_method and evidence_ref must be non-empty
- authenticated=true still requires principal_id
- currentness is authenticated AND not expired at observation time
- IdentityProofRecord never mutates AgentIdentity or grants authorization

## Test fixture correction

The control-stability experiment previously mutated identity_proof_records.expires_at_ms directly through SQL.

R21 removes that invalid mutation. The proof remains immutable; the witness advances the clock past expires_at_ms with unittest.mock.patch.

Observed S5 result:
firstHeaderResolved = true
secondCallBlocked = true
materialProviderCalls = 1
classification = FAIL_CLOSED

This proves expiry is derived from immutable evidence + time and blocks before another external secret resolution.

## Destructive migration

An obsolete identity_proof_records table now fails closed during R10 initialization.
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
R21: 151
cumulative retired top-level types: 20

Structural audit:
observed classes = 151
legacy ceiling = 151
unexpected = []
retired overlap = []
old identity proof authority = none
identity_proof_records facade refs = none
direct proof SQL mutation = none

## Validation

R21 direct/trust/R14/effect targeted:
Ran 36 tests — OK

CORE_ZERO structural gate:
Ran 42 tests — OK

Control stability experiment:
9 scenarios completed; S5 credential expiry remained FAIL_CLOSED

Agent Service suite:
Ran 241 tests — OK (skipped=5)

Full repository suite:
Ran 340 tests — OK (skipped=5)

## Next audit

CredentialReferenceStore now has no downstream SQL foreign-key consumer.
R22 must freshly decompose it into locator identity, replay semantics, provider/reference/issuer/resource/scopes, and external secret ownership before any deletion.
