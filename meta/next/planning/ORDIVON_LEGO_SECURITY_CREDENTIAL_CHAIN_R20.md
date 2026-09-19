# ORDIVON LEGO — SECURITY / CREDENTIAL AUTHORITY CHAIN R20

Date: 2026-09-19
Workspace: ws-ordivon-core-elimination-r20-20260919
Base: 514f3a74b27cf74f23318778af32aba2782cb6c5

## 1. Problem graph

TransportBinding
  -> immutable endpoint + securityRequirements + grantedPermissions
  -> TransportCredentialBinding
     -> selects one CredentialReference + IdentityProof for one security scheme
     -> stores references only; never secret bytes
     -> IdentityProofRecord
        -> external authentication observation + expiry/evidence
        -> CredentialReference
           -> opaque locator + issuer/resource/requested scopes
           -> CredentialMaterialProvider
              -> external secret authority; transient headers only

## 2. LEGO classification

| LEGO | Authority / lifecycle | R20 disposition |
|---|---|---|
| TransportBinding | immutable route/security coordinate | retain |
| TransportCredentialBinding | immutable association receipt | eliminate specialized Store/table |
| IdentityProofRecord | authentication evidence with time-sensitive currentness | retain |
| CredentialReference | opaque external credential locator metadata | retain |
| Credential material | actual secret authority, ephemeral | external provider retains ownership |
| Policy grant | frozen authorization input | TransportBinding retains snapshot |

## 3. TransportCredentialBinding decomposition

The legacy Store combines four concerns: exact client request replay; uniqueness of (binding_id, security_scheme); canonical immutable receipt; enumeration of scheme bindings for one TransportBinding.

### A — request identity LEGO

TransportCredentialBindingRequest/<client_binding_request_id>
  sequence 1
  TransportCredentialBindingRequestCommitted
  -> transportCredentialBindingId

Purpose: exact replay and request-id conflict detection.

### B/C — scheme ownership + canonical receipt LEGO

coordinate = sha256(canonical_json([binding_id, security_scheme]))

TransportCredentialSchemeBinding/<coordinate>
  sequence 1
  TransportCredentialBindingRecorded
  -> clientBindingRequestId
  -> bindingId
  -> securityScheme
  -> credentialReferenceId
  -> identityProofId
  -> requiredScopes

Purpose: replaces UNIQUE(binding_id, security_scheme); generic event id becomes TransportCredentialBinding.id; a different proof/reference cannot rebind the same scheme.

### D — binding index LEGO

TransportCredentialBindingIndex/<binding_id>
  sequence N
  TransportCredentialBindingIndexed
  -> transportCredentialBindingId
  -> securityScheme

Purpose: BoundCredentialHeaderProvider can enumerate every configured scheme without a specialized SQL Store.

## 4. Security boundaries that must NOT move

- scheme must be declared by immutable TransportBinding
- identity proof must be authenticated and current
- proof identity must equal Delegation source identity
- credential requested scopes must cover Binding-required scopes
- frozen policy grant must cover Binding-required scopes
- credential resource must cover Binding endpoint
- resolved material issuer/resource/scopes must match frozen metadata
- material expiry remains checked at use time
- resolved headers remain transient and are never persisted
- CR/LF and duplicate-header checks remain unchanged

## 5. Authority / persistence distinction

External secret authority: CredentialMaterialProvider
External authentication authority: IdentityProofAdapter observation
Local currentness evaluation: IdentityProofCoordinator.is_current
Local immutable association receipt: TransportCredentialBinding

Only the last item is migrated in R20.

## 6. Deletion dependency order

R20 TransportCredentialBindingStore
  -> after removal, re-audit IdentityProofRecordStore
  -> only after that, re-audit CredentialReferenceStore

This is a dependency hypothesis, not automatic permission to delete R21/R22.

## 7. R20 proof obligations

1. TransportCredentialBindingStore absent.
2. transport_credential_bindings table absent.
3. service.transport_credential_records absent.
4. Exact request replay returns the same receipt id.
5. Request-id conflict fails closed.
6. Different evidence for the same Binding+scheme fails closed.
7. Multiple schemes remain enumerable.
8. Header resolver still validates current proof and resource/scope/material drift.
9. No secret/header material persists in event payloads.
10. Legacy table fails closed.
11. No replacement specialized Store/Registry.
12. CORE_ZERO decreases by exactly one only after full regression.

## 8. Non-goals

R20 does not delete CredentialReferenceStore or IdentityProofRecordStore, does not move authentication authority into ServiceEvent, does not persist secret material, and does not alter TransportBinding or policy authority.

Transformation:

specialized immutable association table
  -> generic immutable receipt + uniqueness coordinate + index stream

not:

security subsystem
  -> generic events
