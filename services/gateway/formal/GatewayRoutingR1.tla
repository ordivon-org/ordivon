---------------- MODULE GatewayRoutingR1 ----------------
EXTENDS TLC

\* Gateway B01 is a NON-AUTHORITATIVE routing abstraction.
\* requested is the canonical lookup key; routeCapability is the record's
\* declared capability. routeOwner is only an operator-configured destination.
\* No admission, Job/Attempt, provider or credential truth is modeled.

CONSTANTS Capabilities, Owners
ASSUME /\ Capabilities # {}
       /\ Owners # {}
       /\ "none" \notin Capabilities
       /\ "none" \notin Owners

VARIABLES phase, requested, routeCapability, routeOwner, forwardedOwner
vars == <<phase, requested, routeCapability, routeOwner, forwardedOwner>>

Init ==
  /\ phase = "start"
  /\ requested = "none"
  /\ routeCapability = "none"
  /\ routeOwner = "none"
  /\ forwardedOwner = "none"

Lookup ==
  /\ phase = "start"
  /\ \E request \in Capabilities:
       \E recorded \in (Capabilities \cup {"none"}):
         \E destination \in (Owners \cup {"none"}):
           /\ requested' = request
           /\ routeCapability' = recorded
           /\ routeOwner' = destination
  /\ phase' = "observed"
  /\ UNCHANGED forwardedOwner

Validate ==
  /\ phase = "observed"
  /\ phase' = IF requested = routeCapability /\ routeOwner # "none"
               THEN "validated"
               ELSE "rejected"
  /\ UNCHANGED <<requested, routeCapability, routeOwner, forwardedOwner>>

Forward ==
  /\ phase = "validated"
  /\ phase' = "forwarded"
  /\ forwardedOwner' = routeOwner
  /\ UNCHANGED <<requested, routeCapability, routeOwner>>

Next == Lookup \/ Validate \/ Forward
Spec == Init /\ [][Next]_vars

TypeOK ==
  /\ phase \in {"start", "observed", "validated", "rejected", "forwarded"}
  /\ requested \in (Capabilities \cup {"none"})
  /\ routeCapability \in (Capabilities \cup {"none"})
  /\ routeOwner \in (Owners \cup {"none"})
  /\ forwardedOwner \in (Owners \cup {"none"})

ForwardedImpliesExactRoute ==
  phase = "forwarded" =>
    /\ requested = routeCapability
    /\ routeOwner \in Owners
    /\ forwardedOwner = routeOwner

RejectedNeverForwards ==
  phase = "rejected" => forwardedOwner = "none"

\* Expected counterexample: forward is reachable when a valid route exists.
NeverForward == phase # "forwarded"

\* Negative control: a programmer bypasses Validate and forwards a
\* mismatched record. This MUST violate ForwardedImpliesExactRoute.
UnsafeForward ==
  /\ phase = "observed"
  /\ routeCapability # requested
  /\ routeOwner \in Owners
  /\ phase' = "forwarded"
  /\ forwardedOwner' = routeOwner
  /\ UNCHANGED <<requested, routeCapability, routeOwner>>
UnsafeNext == Next \/ UnsafeForward
UnsafeSpec == Init /\ [][UnsafeNext]_vars
===============================================================
