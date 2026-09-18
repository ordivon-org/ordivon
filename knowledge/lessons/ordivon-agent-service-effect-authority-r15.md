# Ordivon Agent Service — Effect Authority R15

Status: **IMPLEMENTED / ACCEPTANCE PASS**
Date: 2026-09-18
Base main: `67b9f61ede96afc20a575882797cf99cfab42d19`
Architecture delta: `knowledge/graphs/ordivon-agent-service-r15-effect-authority-delta.json`

## Result

R15 separates semantic Session lifetime from delivery authority lifetime and adds one current local policy gate immediately before the first external delivery effect, while preserving exact-effect replay and all R12-R14 recovery/evidence contracts.

## Authority split

```text
SemanticSession -> continuity
route-time PolicyDecision -> historical route admissibility
EffectAuthorizationDecision -> current local authority for one exact external effect identity
Credential authority -> current credential material
remote provider -> remote authentication and authorization
```

`Session CLOSED` blocks new SessionItems and new DelegationEnvelopes. It is not itself an implicit revocation command for already-created effects. A PolicyAdapter may still use Session state as an input and deny a current effect.

## Effect-time law

Before the first external send for an immutable Binding, R15 asks the configured current PolicyAdapter again and durably freezes the result to that Binding. Missing policy authority or a current denial fails closed before `adapter.send()`.

Once the exact effect identity has an allowed decision, recovery of that same identity reuses the frozen decision. A new or failover Binding is a new effect identity and must obtain a new current decision.

Existing durable DeliveryReceipts replay locally without manufacturing another policy event.

## Initial verification

The dedicated R15 test set now covers five cases:

- current deny after route-time allow blocks provider send;
- Session close alone does not revoke an otherwise currently allowed exact effect;
- response-loss recovery reuses the frozen exact-effect authorization;
- existing receipt replay performs no new authorization;
- missing current effect PolicyAdapter fails closed before provider send.

Dedicated result: 5/5 PASS.

Final verification: 6 dedicated effect-authority tests PASS, 1 graph-identity regression test PASS, 188 Agent Service tests PASS, and 244 repository tests PASS. The 13-file architecture history replays to 90 unique node identities with zero hard collisions.
