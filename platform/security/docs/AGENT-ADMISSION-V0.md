# Agent Admission v0 — threat model and protocol profile

Status: EXPERIMENTAL INTERNAL PROFILE
Date: 2026-09-21

## 1. Goal

Agent Admission v0 tests one proposition:

> A website should admit a user-delegated software agent from verifiable identity,
> delegation, scope, risk, budget, and accountability — not from an inference that
> the caller looks human.

This profile does not define a new authentication, delegation, token, or
cryptographic protocol. It normalizes evidence already verified by the standards
that own those semantics and feeds the result into policy.

## 2. Security objects

The minimal model contains five semantic objects:

1. Principal — the human or organization that owns authority.
2. Agent — the software workload acting with its own cryptographic identity.
3. Grant — the bounded delegation from Principal to Agent.
4. Effect — one concrete requested side effect with stable identity.
5. Risk / approval context — whether the effect may execute automatically or
   requires Principal step-up.

Identity separations are mandatory:

~~~text
principalId != agentId != grantId != effectId != provider/resource identity
~~~

## 3. External-first standards profile

### Principal authentication

Primary: W3C WebAuthn Level 3 Recommendation (2026-08-25).

Ordivon does not verify authenticators inside Rego. A WebAuthn/RP component
verifies the ceremony and projects authenticated Principal evidence.

### Delegation — primary website lane

Primary production-oriented lane:

- OAuth 2.0 ecosystem;
- RFC 9700 / BCP 240 as the OAuth security baseline;
- RFC 9396 Rich Authorization Requests for structured authorization details;
- RFC 9449 DPoP for sender-constrained application-layer tokens where applicable.

The v0 policy consumes the verified semantic projection, not raw OAuth tokens.

### Delegation — experimental alternative lane

RFC 9635 GNAP is a Standards Track mechanism explicitly designed to delegate
authorization to a piece of software. It is suitable for a separate laboratory
lane. GNAP is not treated as an OAuth extension and the two wire protocols must
not be mixed into a private hybrid.

### Workload identity

SPIFFE/SVID is the preferred mature substrate for first-party Ordivon workloads
inside controlled trust domains. It is not a mandatory identity scheme for
arbitrary third-party public agents.

### Policy

OPA/Rego remains the stateless policy owner because Security v2 already uses it
for effect admission. Agent Admission does not create a second policy engine.

### Effect semantics

Ordivon continues to own only the application semantics that external identity
standards do not own:

- stable effectId;
- durable effect ledger/fence;
- exact-replay and ambiguous-outcome handling;
- provider evidence binding;
- human control transfer.

Authorization says what may happen. The effect system records and reconciles
what did happen.

## 3.1. Normalization trust boundary

The normalized JSON input is an internal policy projection, not a public wire
protocol. Public callers MUST NOT be allowed to self-assert fields such as
authenticated, verified, principalId, agentId, or grant scope.

The trusted ingress adapters must verify the owning protocol first and only then
construct this projection:

~~~text
public request
  -> WebAuthn / OAuth / DPoP / SPIFFE / GNAP verifier
  -> canonical identity + grant evidence
  -> normalized Agent Admission input
  -> OPA
~~~

Resource identifiers must be canonicalized before policy evaluation. Rego must
not be asked to resolve ambiguous URL/path normalization such as dot segments,
aliases, redirects, case-folding, or provider-specific resource equivalence.

remainingEffects is only a policy snapshot in v0. Production budget enforcement
requires a durable owner that atomically reserves/consumes budget around effect
admission; OPA itself is intentionally stateless.

## 4. Threat model

v0 is designed to reduce these threats:

| Threat | Control owner |
| --- | --- |
| Anonymous automated abuse | admission + rate/resource policy |
| Agent impersonation | DPoP / mTLS / SPIFFE / GNAP key binding |
| Stolen bearer token replay | sender-constrained credential where applicable |
| Confused deputy | audience + resource + action binding |
| Over-delegation | explicit grant actions/resources/risk ceiling |
| Prompt-injection-induced privilege escalation | policy ignores model intent beyond granted capability |
| Cross-user authority use | Principal-to-Grant binding |
| Cross-agent authority use | Agent-to-Grant binding |
| Replay / duplicate external effect | existing Ordivon effect fence/ledger |
| High-consequence autonomous action | effect-bound Principal step-up |
| Runaway automation | effect/rate/resource budgets |
| Stale/revoked authority | active/expiry checks; future revocation feed |
| Audit ambiguity | stable Principal/Agent/Grant/Effect identities |

v0 explicitly does not claim to:

- determine whether an agent has benign intent;
- solve prompt injection in general;
- prove a caller is human;
- bypass third-party anti-bot or human-verification controls;
- make authorization equivalent to successful execution.

## 5. Risk classes

~~~text
R0  public read / negligible consequence
R1  delegated private read
R2  bounded reversible write
R3  externally visible or operationally meaningful write
R4  high-consequence write requiring Principal step-up by default
R5  identity/recovery/root-authority or similarly critical action
~~~

A Grant carries both a maximum risk ceiling and a step-up threshold.

The initial website profile defaults to:

~~~text
R0-R3  eligible for automatic execution when the Grant allows it
R4     effect-bound WebAuthn step-up
R5     outside ordinary Agent grants; explicit exceptional policy required
~~~

## 6. Decision contract

The normalized policy result has exactly three outcomes:

- ALLOW
- STEP_UP
- DENY

ALLOW is permission only. It emits an authorityProjection that can be fed into
the existing effect-admission boundary.

STEP_UP means the effect remains unexecuted until a verified Principal approval
is bound to the same effectId.

DENY is terminal for the presented Grant/evidence state.

## 7. First website experiment

The first trial should expose only a tiny resource surface:

~~~text
article.read       R0/R1
comment.read       R0/R1
comment.create     R2
comment.delete-own R3
account.*          not delegated in v0
~~~

The site should have four ingress classes:

~~~text
human session       -> normal human authentication
delegated agent     -> Agent Admission v0
first-party service -> workload identity policy
unknown automation  -> existing anti-abuse / challenge fallback
~~~

The experiment is successful if a delegated agent can perform a bounded R2
effect without CAPTCHA while an anonymous bot cannot, and if an R4 test effect
provably pauses for effect-bound WebAuthn approval.

## 8. Deliberate gaps before public trial

Not implemented by this profile:

- OAuth Authorization Server / Resource Server integration;
- DPoP verifier;
- WebAuthn RP;
- SPIRE/SPIFFE deployment;
- grant revocation event propagation;
- persistent rate/budget accounting;
- public Agent Passport UI;
- website route middleware;
- GNAP laboratory endpoint.

Those should be adopted from mature implementations rather than recreated in
Security v2.
