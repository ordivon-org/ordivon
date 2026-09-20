# Legacy Distribution differential — R1

Source audited: `ordivon-media/src/ordivon_studio/distribution.py`, 475 lines.

| Legacy block | Lines | R1 disposition | Replacement |
| --- | ---: | --- | --- |
| `_profile` | 36 | EXTERNALIZE | provider/Postiz/OpenAPI facts |
| `CURRENT_CARRIER_PROFILES` | 151 | DELETE | provider-native/current external catalog |
| `_EFFECT_AUTHORITY_REQUIREMENTS` | 60 | DELETE | provider-native authorization observations |
| `carrier_profile` | 12 | DELETE | external adapter observation |
| `correction_disposition` | 15 | EXTERNALIZE | provider-native capabilities/current constraints |
| `plan_delivery` | 110 | REPLACE | OPA cross-provider policy over external facts |
| `delivery_key` | 22 | RETAIN SEMANTICS, NOT IMPLEMENTATION | RFC 8785 + SHA-256 occurrence verifier |
| `PUBLIC_EFFECTS` | 11 | REPLACE | explicit effect mode supplied by intent owner |
| `ACTIONABILITY` | 9 | RETAIN SMALL VOCABULARY | OPA decision output |
| local digest/string helpers | 12 | DELETE | JSON Schema + RFC 8785 implementation |

The clearly provider-maintenance-specific blocks (`_profile`, carrier catalog, effect-authority catalog, lookup, correction) total **274 lines / 57.7%** of the old module before considering the 110-line planner replacement. No provider-specific token is present in the v2 runtime Rego policy.

## Residual migration law

Code is not migrated because it has tests. A behavior migrates only when it represents a cross-provider invariant that remains necessary after mature external substrates are composed.

The surviving exact-occurrence identity is upgraded rather than copied: v2 hashes an RFC 8785 JCS projection containing `intentId`, provider, opaque account reference, artifact SHA-256 (or null), and effect name/mode. Adapter choice is deliberately excluded so the same logical provider effect does not become a different occurrence merely because dispatch moves between Postiz and a provider-native adapter.

`occurrenceRef` remains a reconciliation coordinate only. It grants no provider idempotency, safe retry, publication acceptance, desired-state authority, or proof of external effect.
