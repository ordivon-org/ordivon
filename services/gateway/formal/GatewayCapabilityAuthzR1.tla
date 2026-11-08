---------------- MODULE GatewayCapabilityAuthzR1 ----------------
EXTENDS TLC

\* Finite abstraction of the protected artifact.read Gateway PEP.
\* Trust boundary: "ingress" means already verified by Access middleware;
\* "binding" means the Security decision echoes the exact server-derived
\* principal, issuer, capability and resource (not Tool-supplied claims).
\* V2 authority/effect booleans denote non-None admitted evidence.
\* V3 authzen denotes the conjunction of standard, decision=TRUE and
\* exact request-ID echo. A separate obligation flag denotes an outstanding
\* mandatory PDP action; this PEP never executes such obligations.
\* V3 also requires authority/effect BOTH absent.
\* Upstream PDP and real provider effects are outside the model.

VARIABLES phase, target, ingress, version, binding, qualified,
          outcome, authority, effect, authzen, obligations

vars == <<phase, target, ingress, version, binding, qualified,
          outcome, authority, effect, authzen, obligations>>

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
  /\ obligations = FALSE

ResolveTarget ==
  /\ phase = "start"
  /\ \E t \in BOOLEAN:
       /\ target' = t
       /\ phase' = IF t THEN "target" ELSE "rejected"
  /\ UNCHANGED <<ingress, version, binding, qualified, outcome,
                 authority, effect, authzen, obligations>>

ReadVerifiedIngress ==
  /\ phase = "target"
  /\ \E i \in BOOLEAN:
       /\ ingress' = i
       /\ phase' = IF i THEN "identity" ELSE "rejected"
  /\ UNCHANGED <<target, version, binding, qualified, outcome,
                 authority, effect, authzen, obligations>>

ReadSecurityDecision ==
  /\ phase = "identity"
  /\ \E v \in {"v2", "v3", "invalid"}:
     \E o \in {"allow", "deny", "stepup", "unknown"}:
     \E b \in BOOLEAN:
     \E q \in BOOLEAN:
     \E a \in BOOLEAN:
     \E e \in BOOLEAN:
     \E z \in BOOLEAN:
     \E u \in BOOLEAN:
       /\ version' = v
       /\ outcome' = o
       /\ binding' = b
       /\ qualified' = q
       /\ authority' = a
       /\ effect' = e
       /\ authzen' = z
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
         /\ ~obligations
         /\ ~authority
         /\ ~effect)

Forward ==
  /\ phase = "decision"
  /\ AllowDecision
  /\ phase' = "forwarded"
  /\ UNCHANGED <<target, ingress, version, binding, qualified,
                 outcome, authority, effect, authzen, obligations>>

RejectDecision ==
  /\ phase = "decision"
  /\ ~AllowDecision
  /\ phase' = "rejected"
  /\ UNCHANGED <<target, ingress, version, binding, qualified,
                 outcome, authority, effect, authzen, obligations>>

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
    (authzen /\ ~authority /\ ~effect /\ ~obligations)

NoOtherVersionForwards ==
  phase = "forwarded" => version \in {"v2", "v3"}

NoUnfulfilledV3Obligations ==
  (phase = "forwarded" /\ version = "v3") => ~obligations

\* Falsification-only action, excluded from Spec. This models an accidental
\* bypass of the exact Principal/resource decision binding check.
UnsafeForwardWithUnboundDecision ==
  /\ phase = "decision"
  /\ outcome = "allow"
  /\ ~binding
  /\ phase' = "forwarded"
  /\ UNCHANGED <<target, ingress, version, binding, qualified,
                 outcome, authority, effect, authzen, obligations>>

\* Counterexample-only action for accidentally dropping a mandatory PDP
\* obligation while preserving all other AuthZEN evidence.
UnsafeForwardWithUnfulfilledObligation ==
  /\ phase = "decision"
  /\ target
  /\ ingress
  /\ version = "v3"
  /\ binding
  /\ qualified
  /\ outcome = "allow"
  /\ authzen
  /\ obligations
  /\ ~authority
  /\ ~effect
  /\ phase' = "forwarded"
  /\ UNCHANGED <<target, ingress, version, binding, qualified,
                 outcome, authority, effect, authzen, obligations>>

UnsafeNext == Next \/ UnsafeForwardWithUnboundDecision
UnsafeObligationNext == Next \/ UnsafeForwardWithUnfulfilledObligation
UnsafeObligationSpec == Init /\ [][UnsafeObligationNext]_vars
UnsafeSpec == Init /\ [][UnsafeNext]_vars

\* Expected counterexample under the safe Spec, proving forward is reachable.
ForwardUnreachable == phase # "forwarded"
===============================================================
