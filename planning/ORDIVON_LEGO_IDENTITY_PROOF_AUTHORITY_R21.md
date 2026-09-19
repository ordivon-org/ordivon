# ORDIVON LEGO — IDENTITY PROOF AUTHORITY R21

Date: 2026-09-19
Workspace: ws-ordivon-core-elimination-r21-20260919
Base: e934e14f0c84e347ce007844d1943c365927861d

## Classification

| LEGO | Meaning | Authority | Lifecycle | R21 |
|---|---|---|---|---|
| IdentityProofAdapter | asks external system whether a credential authenticates an identity | external authentication authority | live call | retain |
| IdentityProofObservation | one external verification result | observation only | ephemeral | retain |
| IdentityProofRecord | durable copy of that observation | evidence receipt, not authorization | immutable | keep projection |
| IdentityProofRecordStore | SQL persistence/access wrapper | no independent semantic authority | immutable persistence | eliminate |
| IdentityProofCoordinator.is_current | derives proof freshness | local deterministic interpretation | time-derived | retain |
| CredentialReferenceStore | locator metadata consumed by verification | local locator registry | immutable registration | retain |

## Data decomposition

IdentityProofRecord carries:
- request identity: client_proof_request_id
- subject coordinate: identity_id
- credential coordinate: credential_reference_id
- purpose
- authentication result
- principal_id
- issuer
- auth_method
- observed_at_ms
- expires_at_ms
- evidence_ref

Every field is immutable after verification.

## Replacement

IdentityProof/<client_proof_request_id>
  sequence 1
  IdentityProofRecorded
  payload = identityId / credentialReferenceId / purpose / authenticated / principalId / issuer / authMethod / observedAtMs / expiresAtMs / evidenceRef

The generic event id becomes IdentityProofRecord.id.

Access contracts:
- get(proof_id) -> ServiceEventStore.get(proof_id) -> projection
- exact replay(client_proof_request_id) -> IdentityProof aggregate sequence 1
- is_current(proof_id, at_ms) -> projection + clock, with no mutation

## Safety ownership retained

- IdentityProofAdapter remains the external authentication authority.
- CredentialReference issuer/resource remain verification inputs.
- issuer mismatch still fails closed.
- authenticated proof still requires principal_id.
- evidence_ref remains mandatory.
- exact request replay remains historical and does not call the adapter again.
- IdentityProofRecord does not mutate AgentIdentity.
- proof currentness remains derived and does not grant authorization by itself.

## Test fixture correction

The control-stability witness currently mutates identity_proof_records.expires_at_ms with SQL. That is not runtime behavior and violates the immutable-evidence model.

R21 replaces that fixture with a patched observation clock: proof bytes remain immutable; the second credential-header resolution observes a time after expires_at_ms and must fail before external secret material resolution.

## Dependency result

R20 removed the last downstream foreign key to identity_proof_records.
R21 has zero downstream FK authority.
CredentialReferenceStore is explicitly out of scope and must be re-audited after R21.

## Proof obligations

1. IdentityProofRecordStore absent.
2. identity_proof_records table absent.
3. service.identity_proof_records absent.
4. exact proof request replay returns same proof id and does not call adapter twice.
5. issuer mismatch still fails closed.
6. authenticated proof still requires principal_id.
7. is_current remains time-derived.
8. AuditEnvelopeProjector still projects proof evidence.
9. R14 credential binding/header resolution still consumes proof through IdentityProofCoordinator.
10. control-stability expiry witness uses clock progression, not SQL mutation.
11. legacy table fails closed.
12. no replacement proof Store/Registry class.
