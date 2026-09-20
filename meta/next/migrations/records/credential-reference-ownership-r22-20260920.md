# Credential Reference Ownership Decision R22

Date: 2026-09-20
Status: CLOSED DECISION — stable rule moved to `policies/external-ownership-boundary.json`

## Outcome

`CredentialReferenceStore` is retained only as a thin cross-owner binding and replay guard. It is not the semantic authority for credential material, OAuth issuer metadata, protected-resource identity, or granted scopes.

The original R22 search assumed one replacement owner had to own locator + issuer + resource + scope. That decomposition was too coarse. Mature ownership is split:

| Data | Natural owner | Local role |
| --- | --- | --- |
| `provider/reference` | selected external credential/secret provider | opaque handle cached for binding; secret material forbidden |
| `issuer` | RFC 8414 / provider-native identity metadata when OAuth is not applicable | cached expected issuer for fail-closed comparison |
| `resource` | RFC 8707 + RFC 9728 / provider-native resource identity | cached least-privilege resource/audience ceiling |
| `requested_scopes` | OAuth authorization semantics + provider/domain policy | cached scope ceiling; never proof of a grant |
| token/header material | external `CredentialMaterialProvider` | transient only; never persisted here |
| `client_reference_id` + row identity | Agent Service replay/join boundary | immutable cross-owner binding identity |

## Why the local row remains

Identity proof occurs before a concrete transport binding is finalized, so the service still needs a confidential, immutable expected contract that constrains which issuer/resource/scopes may later be accepted from transient material. Removing those cached constraints today would widen credential reuse and weaken fail-closed behavior.

Moving locator metadata into the broad `ServiceEventStore` would also widen visibility without creating a better owner.

Therefore the local row remains, but its authority is deliberately narrow:

```text
external provider/native standards
        ↓
opaque handle + externally defined authorization semantics
        ↓
CredentialReferenceStore
        ↓
immutable binding / replay guard / cached least-privilege expectation
```

## Deletion condition

Delete the local binding only when the selected external provider can preserve all of the following without widening locator visibility:

1. stable replay identity;
2. confidential provider-handle resolution;
3. issuer/resource/scope restriction before effect;
4. exact conflict detection for replayed client references.

No replacement Ordivon credential registry, metadata service, or credential ontology is admitted.

## External authorities

- RFC 6749 — OAuth 2.0 Authorization Framework
- RFC 8414 — OAuth 2.0 Authorization Server Metadata
- RFC 8707 — Resource Indicators for OAuth 2.0
- RFC 9700 / BCP 240 — OAuth 2.0 Security Best Current Practice
- RFC 9728 — OAuth 2.0 Protected Resource Metadata

This file is migration history. The maintained machine rule is `policies/external-ownership-boundary.json`.
