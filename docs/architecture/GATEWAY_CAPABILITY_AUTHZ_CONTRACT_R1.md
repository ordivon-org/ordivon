# Gateway Capability AuthZ Contract R1

Date: 2026-09-23
Status: **HISTORICAL / SUPERSEDED (2026-11-07)**

This document records the retired Security v1 reference seam. The v1 evaluator and self-tests were removed after a consumer search found no tracked direct non-Security code adopter and a schema mismatch with current Gateway. Current enforcement code is `services/gateway/src/ordivon_gateway/capability_authz.py` (resource-bound v2/v3 decisions), with `authzen_authorizer.py` implementing an OpenID AuthZEN PDP client. Their presence does not prove installed production policy configuration; consult current Gateway deployment evidence.

## Boundaries

The new Security-owned `gateway-capability-authz-v1` seam binds:

`verified ingress Principal + requested Gateway capability + trusted Agent/Grant/Effect evidence`

to the existing Security Agent Admission decision.

It does not add an identity store, Grant resolver, Gateway policy database, effect executor,
or domain verifier.

## R1 qualification

`artifact.runtime` is the first narrow qualification target. Tests prove:

1. verified ingress Principal must equal the normalized Agent Admission Principal;
2. requested capability must equal the policy Effect action;
3. existing Security ALLOW/DENY semantics are preserved;
4. a denied decision has no authority projection or Effect admission;
5. other capabilities are explicitly unqualified rather than silently promoted by the R1 seam.

## Remaining boundary

Gateway does not yet invoke this contract before owner routing. Trusted Agent + Grant evidence
for the public Gateway path also remains open. Therefore current deployment must not be
described as capability-authorized merely because this Security contract is implemented.
