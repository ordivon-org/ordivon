# ORDIVON LEGO — CREDENTIAL REFERENCE AUTHORITY R22

Date: 2026-09-19
Workspace: ws-ordivon-core-elimination-r22-20260919
Base: d550ea1b0885c7b9a18fc14b6524efbe8d7b6700

## Decision

RETAIN_FOR_NOW.

CredentialReferenceStore is not currently equivalent to the immutable receipts removed in R20/R21.

## LEGO decomposition

| LEGO | Data | Authority | Lifecycle | Current owner | Decision |
|---|---|---|---|---|---|
| client reference identity | client_reference_id | exact replay key | immutable | CredentialReferenceStore | retain |
| provider locator | provider + reference | tells external secret provider where credential lives | immutable security metadata | CredentialReferenceStore | retain |
| issuer/resource contract | issuer + resource | constrains proof/material acceptance | immutable security metadata | CredentialReferenceStore | retain |
| requested scopes | requested_scopes | upper bound used before material resolution | immutable security metadata | CredentialReferenceStore | retain |
| secret/header material | actual token/header bytes | credential authority | ephemeral | CredentialMaterialProvider | external |

## Why R22 does not delete it

R20 and R21 moved immutable receipts into ServiceEventStore because those receipts only contained already-scoped execution/evidence coordinates.

CredentialReference contains provider locator metadata such as vault://... plus issuer/resource/scope metadata.

ServiceEventStore is a broad shared journal exposed through service.events and consumed by many internal modules/tests/scripts. Moving locator metadata into that journal would widen its distribution surface without providing a stronger owner.

Therefore:

0 downstream FK != safe to event-source.

The missing condition is:

replacement owner must preserve or improve confidentiality and authority scoping.

## Authority graph

CredentialReferenceStore
  -> supplies opaque locator metadata to IdentityProofCoordinator
  -> supplies issuer/resource/scopes to TransportCredentialBindingCoordinator
  -> supplies locator metadata to CredentialMaterialProvider

CredentialMaterialProvider
  -> remains the actual secret authority
  -> secret material is transient and never persisted locally

## Deletion condition

CredentialReferenceStore becomes deletable only after one of these is proven:

1. a mature external credential/secret manager owns locator + issuer/resource/scope metadata and Agent Service receives only a stable opaque handle; or
2. a separately access-controlled metadata authority replaces the local Store without broadening visibility; or
3. ServiceEventStore itself gains an explicit confidentiality partition that is stronger than the current dedicated table boundary.

Do not create a new custom CredentialReferenceRegistry merely to reduce the class count.

## External Ownership Boundary interpretation

R22 remains a valid exception under the stable External Ownership Boundary. The architecture policy reduces removable custom authority; it is not a target that overrides security boundaries.

CredentialReferenceStore is now classified as RETAIN_UNTIL_EXTERNAL_OWNER rather than an unexamined residual.

## Current next action

`EvidenceResolverRegistry` and the other low-reference elimination candidates named by the original R22 follow-up have already been retired. The remaining action for this decision is narrower: bind a mature credential/secret-manager metadata owner that can return a stable opaque handle without widening locator visibility, then rerun the replacement/parity audit. Until such an owner is actually bound, keep the dedicated metadata boundary.
