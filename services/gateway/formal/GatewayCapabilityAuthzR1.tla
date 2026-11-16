---------------- MODULE GatewayCapabilityAuthzR1 ----------------
EXTENDS TLC

\* Finite abstraction of the protected artifact.read Gateway PEP.
\* Trust boundary: "ingress" means already verified by Access middleware;
\* "binding" means the Security decision echoes the exact server-derived
\* principal, issuer, capability and resource (not Tool-supplied claims).
\* V2 authority/effect booleans denote non-None admitted evidence.
\* V3 evidence covers the designated AuthZEN standard, a Boolean permit,
\* and equality of the request and response identifiers.
\* The separate nonce qualification flag requires a nonblank ID value.
\* Equality of two absent/blank IDs is insufficient authorization evidence.
\* V3 also requires authority/effect BOTH absent.
\* Upstream PDP and real provider effects are outside the model.

VARIABLES phase, target, ingress, version, binding, qualified,
          outcome, authority, effect, authzen, authzenNonce, obligations

vars == <<phase, target, ingress, version, binding, qualified,
          outcome, authority, effect, authzen, authzenNonce, obligations>>

Init ==
  /\ phase = "start"
  /\ target = FALSE
  /\ ingress = FALSE
  /\ version = "none"
  /\ binding = FALSE
  /\ qualified = FALSE
  /\ outcome = "none"
  /\ authority = FALSE
  /\ effect = FALSE
  /\ authzen = FALSE
  /\ authzenNonce = FALSE
  /\ obligations = FALSE

ResolveTarget ==
  /\ phase = "start"
  /\ \E t \in BOOLEAN:
       /\ target' = t
       /\ phase' = IF t THEN "target" ELSE "rejected"
  /\ UNCHANGED <<ingress, version, binding, qualified, outcome,
                 authority, effect, authzen, authzenNonce, obligations>>

ReadVerifiedIngress ==
  /\ phase = "target"
  /\ \E i \in BOOLEAN:
       /\ ingress' = i
       /\ phase' = IF i THEN "identity" ELSE "rejected"
  /\ UNCHANGED <<target, version, binding, qualified, outcome,
                 authority, effect, authzen, authzenNonce, obligations>>

ReadSecurityDecision ==
  /\ phase = "identity"
  /\ \E v \in {"v2", "v3", "invalid"}:
     \E o \in {"allow", "deny", "stepup", "unknown"}:
     \E b \in BOOLEAN:
     \E q \in BOOLEAN:
     \E a \in BOOLEAN:
     \E e \in BOOLEAN:
     \E z \in BOOLEAN:
     \E n \in BOOLEAN:
     \E u \in BOOLEAN:
       /\ version' = v
       /\ outcome' = o
       /\ binding' = b
       /\ qualified' = q
       /\ authority' = a
       /\ effect' = e
       /\ authzen' = z
       /\ authzenNonce' = n
       /\ obligations' = u
       /\ phase' = "decision"
  /\ UNCHANGED <<target, ingress>>

AllowDecision ==
  /\ target
  /\ ingress
  /\ binding
  /\ qualified
  /\ outcome = "allow"
  /\ (\/ /\ version = "v2"
         /\ authority
         /\ effect
      \/ /\ version = "v3"
         /\ authzen
         /\ authzenNonce
         /\ ~obligations
         /\ ~authority
         /\ ~effect)

Forward ==
  /\ phase = "decision"
  /\ AllowDecision
  /\ phase' = "forwarded"
  /\ UNCHANGED <<target, ingress, version, binding, qualified,
                 outcome, authority, effect, authzen, authzenNonce, obligations>>

RejectDecision ==
  /\ phase = "decision"
  /\ ~AllowDecision
  /\ phase' = "rejected"
  /\ UNCHANGED <<target, ingress, version, binding, qualified,
                 outcome, authority, effect, authzen, authzenNonce, obligations>>

Next ==
  \/ ResolveTarget
  \/ ReadVerifiedIngress
  \/ ReadSecurityDecision
  \/ Forward
  \/ RejectDecision

Spec == Init /\ [][Next]_vars

TypeOK ==
  /\ phase \in {"start", "target", "identity", "decision", "forwarded", "rejected"}
  /\ target \in BOOLEAN
  /\ ingress \in BOOLEAN
  /\ version \in {"none", "v2", "v3", "invalid"}
  /\ binding \in BOOLEAN
  /\ qualified \in BOOLEAN
  /\ outcome \in {"none", "allow", "deny", "stepup", "unknown"}
  /\ authority \in BOOLEAN
  /\ effect \in BOOLEAN
  /\ authzen \in BOOLEAN
  /\ authzenNonce \in BOOLEAN
  /\ obligations \in BOOLEAN

ForwardImpliesBinding ==
  phase = "forwarded" =>
    /\ target
    /\ ingress
    /\ binding
    /\ qualified
    /\ outcome = "allow"

V2NeedsDelegatedEvidence ==
  (phase = "forwarded" /\ version = "v2") =>
    (authority /\ effect)

V3NeedsInteractiveEvidence ==
  (phase = "forwarded" /\ version = "v3") =>
    (authzen /\ authzenNonce /\ ~authority /\ ~effect /\ ~obligations)

NoUnfulfilledV3Obligations ==
  (phase = "forwarded" /\ version = "v3") => ~obligations

NoOtherVersionForwards ==
  phase = "forwarded" => version \in {"v2", "v3"}

\* Falsification-only action, excluded from Spec. This models an accidental
\* bypass of the exact Principal/resource decision binding check.
UnsafeForwardWithUnboundDecision ==
  /\ phase = "decision"
  /\ outcome = "allow"
  /\ ~binding
  /\ phase' = "forwarded"
  /\ UNCHANGED <<target, ingress, version, binding, qualified,
                 outcome, authority, effect, authzen, authzenNonce, obligations>>

\* Counterexample-only action: a v3 PERMIT with an unfulfilled mandatory
\* obligation reaches the Owner even though this PEP cannot perform it.
UnsafeForwardWithUnfulfilledObligation ==
  /\ phase = "decision"
  /\ target
  /\ ingress
  /\ version = "v3"
  /\ binding
  /\ qualified
  /\ outcome = "allow"
  /\ authzen
  /\ authzenNonce
  /\ obligations
  /\ ~authority
  /\ ~effect
  /\ phase' = "forwarded"
  /\ UNCHANGED <<target, ingress, version, binding, qualified,
                 outcome, authority, effect, authzen, authzenNonce, obligations>>

UnsafeObligationNext == Next \/ UnsafeForwardWithUnfulfilledObligation
UnsafeObligationSpec == Init /\ [][UnsafeObligationNext]_vars

UnsafeNext == Next \/ UnsafeForwardWithUnboundDecision
UnsafeSpec == Init /\ [][UnsafeNext]_vars

\* Expected counterexample under the safe Spec, proving forward is reachable.
ForwardUnreachable == phase # "forwarded"
===============================================================
