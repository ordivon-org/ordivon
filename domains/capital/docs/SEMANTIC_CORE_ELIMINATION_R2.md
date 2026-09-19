# Market Capital Semantic-Core Elimination R2

Date: 2026-09-19
Status: ACCEPTED IMPLEMENTATION BASELINE

## Result

The former custom Market Capital semantic core is no longer an active component.

Deleted:
- src/market_capital/semantic.py
- contracts/semantic-core-v1.json
- tests/test_semantic_core.py

The removed abstractions included local truth-level classes, proof/witness wrappers, effect-disposition vocabulary, and an external-write admission wrapper.

## External ownership after elimination

| Concern | Owner after R2 | Local responsibility |
| --- | --- | --- |
| External financial write allow/deny | OPA 1.20.2 / Rego v1 | Supply explicit provider/verifier facts; fail closed |
| Venue order/fill reality | Authoritative venue APIs | Normalize and reconcile |
| Order lifecycle vocabulary | FIX Latest semantic reference; explicit legacy wire profiles | Venue-to-lifecycle mapping |
| Pending-capital accounting | TigerBeetle 0.17.9 | Narrow identity/mapping and restart reconciliation |
| Unknown/ambiguous execution outcome | Authoritative reconciliation | NO_MUTATION |
| Proven zero-effect terminal outcome | TigerBeetle | VOID_PENDING_TRANSFER |
| Positive execution | TigerBeetle | POST_PENDING_TRANSFER |
| Historical legacy evidence | Frozen fixtures | Preserve bytes/outcomes; do not reimplement obsolete semantics |

## Policy boundary

policy/market_controls.rego is the current allow/deny policy. Default is deny. Allow requires all of: policy state ADMITTED, externalFinancialWriteAllowed true, a bound provider write capability, and effect verifier standing IMPLEMENTED_BOUND_CURRENT.

The current policy input fails these conditions. External financial writes remain denied.

## Reconciliation boundary

UNKNOWN / AMBIGUOUS / PARTIAL_OPEN / CONTRADICTORY -> NO_MUTATION

PROVEN_NO_EFFECT / RECONCILED_ZERO_FILL_TERMINAL -> VOID_PENDING_TRANSFER

POSITIVE_EXECUTION -> POST_PENDING_TRANSFER

These outputs are accounting-resolution instructions, not a new cross-domain ontology.

## Runtime evidence

The following local canaries passed after semantic-core removal:
- OPA external-write policy deny;
- TigerBeetle R1 accounting/replay smoke;
- TigerBeetle R3.1 reservation-resolution smoke;
- TigerBeetle R3.2 intact-data restart/reconciliation smoke;
- Nautilus non-live episode -> venue/FIX reconciliation -> TigerBeetle resolution matrix.

No live endpoint, real-money effect, or external financial write was used.

## Verification

- canonical tests: 163 passed;
- git diff --check: PASS;
- exact scan for retired semantic-core symbols: zero active matches;
- non-live capital matrix: PASS;
- unknown state preserves pending accounting reservation with NO_MUTATION;
- exact posted-transfer replay remains idempotent;
- contradictory/incomplete restart state permits no automatic repair.

## Remaining local seams

The retained local code is limited to provider normalization, explicit policy inputs, identity binding, reconciliation mapping, deterministic account namespaces needed for TigerBeetle integration, and tests/evidence proving composition boundaries.

Future changes keep the same substitution rule: if an authoritative provider, mature component, or industry standard can own a mechanism directly, remove the local mechanism rather than wrapping it in another Market Capital abstraction.
