# Windows execution authority factorization R1

Status: implementation ADR - compatibility-first

## Decision

Windows Runtime execution is modeled canonically as three separate facts:

- Broker authority: provider-internal privileged transport.
- Payload identity: service or active_user.
- Payload privilege: limited or elevated.

WindowsAuthority remains the legacy public compatibility profile during migration.

| Legacy value | Canonical identity | Canonical privilege |
|---|---|---|
| limited | service | limited |
| elevated | service | elevated |
| active_user | active_user | limited |

active_user x elevated is the fourth canonical cell and intentionally has no legacy flat representation.

## Compatibility fence

R1 adds canonical Core types and the legacy compiler only. It does not add a new public request field. Existing request serialization, operation/proposal identity digests, durable plans, exact replay, and live provider behavior must remain unchanged.

## Authority boundaries

- Runtime remains Windows Job/Attempt/process/artifact truth owner.
- LocalSystem privileged broker remains the privileged token-acquisition/launch seam.
- Gateway routes provider-defined contexts and owns no Windows privilege semantics.
- No password collection, synthetic UAC interaction, broad ACL relaxation, or second credential store.
- Windows immutable-input admission remains limited-only until independently graduated.

## Fourth-cell acceptance

Before active_user x elevated is advertised, native acceptance must prove admission-frozen SID/session, primary payload token, elevated state, High-or-higher integrity, enabled Builtin Administrators membership, exact broker/launcher digests, fail-closed absence behavior, and existing Job Object cleanup semantics. Fallback to service/SYSTEM identity is forbidden.

## R1 source closure

The ordinary execution contract now accepts optional `windowsContext={identity, privilege}`. Legacy `windowsAuthority` remains present for compatibility; because its wire default is `limited`, that default is treated as the compatibility sentinel when structured context is supplied, while non-default legacy values must agree with the structured context.

`runtime.describe` keeps the legacy `windowsAuthorities` projection and adds `windowsContexts`. Structured contexts are not statically advertised: Runtime probes each of the four canonical cells against the installed Windows provider and reports only the cells whose runtime-context evidence validates successfully.

The immutable-input/bound Windows entrypoint remains deliberately limited-only and does not gain a `windowsContext` field in this migration.

Source-level closure is not native graduation. `active_user x elevated` becomes available only after a Windows candidate with the new broker/launcher is deployed and WA22/WA23 prove the real LocalSystem broker path.
