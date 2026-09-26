# Gateway Capability AuthZ Contract R1

Date: 2026-09-23  
Status: **A01 CONTRACT IMPLEMENTED / A02 ARTIFACT.RUNTIME POLICY QUALIFIED / A03 GATEWAY ENFORCEMENT OPEN**

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
