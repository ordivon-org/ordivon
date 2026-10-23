# Gateway Admission R1 — Security Owner Boundary

Date: 2026-09-22
Status: **CURRENT BOUNDARY / CAPABILITY AUTHZ OPEN**

## Purpose

This note binds the public Gateway ingress to existing Security semantics without making Gateway a Security implementation.

## Current verified ingress

Cloudflare Access is the current external identity/authentication owner for the public Gateway. Gateway verifies the Access assertion cryptographically and derives a stable pseudonymous Principal from verified issuer + subject.

That fact establishes **authenticated ingress attribution only**.

It does not by itself establish:

- a delegated Agent Grant;
- per-capability scope;
- effect permission;
- Runtime execution authority;
- Host semantic standing;
- domain completion.

## Required composition

```text
provider-native verified identity
  -> trusted Principal/Agent projection
  -> Security authorization semantics
  -> ALLOW / STEP_UP / DENY
  -> Gateway policy-enforcement seam
  -> natural owner
```

Security owns the authorization semantics; Gateway may enforce a decision but must not invent a parallel policy vocabulary.

## Interactive and workload separation

Interactive user authorization and first-party workload admission are distinct profiles.

- interactive admission may require OAuth Authorization Code + PKCE and Principal interaction;
- workload admission must use a machine/workload identity mechanism and must not require browser presentation during ordinary operation.

The same software process must not infer one profile from UI behavior. Profile selection must come from trusted configuration/identity context.

## Token boundary

An external bearer/access token is evidence for the resource server that validates it. It is not a generic internal Ordivon credential.

Gateway must not convert “client reached the public endpoint” into an owner-machine credential. Gateway-to-owner credentials remain owner-specific.

## Current gap

No claim is made that the current public Gateway has per-capability authorization for all exposed tools.

Until AF-S2 closes a concrete capability policy seam:

```text
verified Cloudflare Principal
!=
capability-scoped Security authorization
```

This is an explicit architecture gap, not an inferred denial and not an inferred grant.

## Workload provider

R1 deliberately leaves the production workload identity provider unresolved. Selection pressure must come from a real unattended consumer and deployment topology.

SPIFFE/SVID, provider-native service identity, OAuth client credentials, or another mature mechanism may satisfy the role later. Security owns the verification/policy semantics; credential material remains with the selected provider/secret owner.
