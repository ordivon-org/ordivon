------------------- MODULE RuntimeWorkspaceClaimBirthR2 -------------------
EXTENDS TLC, FiniteSets
\* R2.1 source candidate model, NOT an installed cross-owner refinement.
\* A/B are separate long-lived Harness Run consumers of one Git Workspace.
\* PostgreSQL advisory admission/close serialization is abstracted into
\* atomic transitions. It prevents simultaneous commits, NOT a Run created
\* after the Git Workspace was closed, or an unregistered future consumer.
\* Future pending intent is an upstream assumption, not a Runtime fact.
Consumers == {"runA", "runB"}
VARIABLES phase, registered, finished, released, pending
vars == <<phase, registered, finished, released, pending>>

Init ==
  /\ phase = "open"
  /\ registered = {"runA"}
  /\ finished = {}
  /\ released = {}
  /\ pending = {"runB"}

Finish(c) ==
  /\ phase = "open"
  /\ c \in registered
  /\ c \notin finished
  /\ finished' = finished \cup {c}
  /\ UNCHANGED <<phase, registered, released, pending>>

Relinquish(c) ==
  /\ phase = "open"
  /\ c \in finished
  /\ c \notin released
  /\ released' = released \cup {c}
  /\ UNCHANGED <<phase, registered, finished, pending>>

BirthB ==
  /\ phase = "open"
  /\ "runB" \in pending
  /\ registered' = registered \cup {"runB"}
  /\ pending' = pending \ {"runB"}
  /\ UNCHANGED <<phase, finished, released>>

AbandonFutureB ==
  /\ phase = "open"
  /\ "runB" \in pending
  /\ pending' = pending \ {"runB"}
  /\ UNCHANGED <<phase, registered, finished, released>>

\* Desired qualified close: all claims explicitly relinquished and no
\* unidentified pending consumer scopes. CURRENT SOURCE HAS NO PENDING INDEX.
QualifiedClose ==
  /\ phase = "open"
  /\ released = registered
  /\ pending = {}
  /\ phase' = "closed"
  /\ UNCHANGED <<registered, finished, released, pending>>

\* Actual source candidate's claim-only close lacks any proof of pending
\* future Run intent, despite holding the same admission lock.
ClaimOnlyClose ==
  /\ phase = "open"
  /\ released = registered
  /\ phase' = "closed"
  /\ UNCHANGED <<registered, finished, released, pending>>

\* Actual Run creation can commit in Harness PG AFTER Runtime closes
\* the physical Workspace, because no source/epoch existence is checked.
PostCloseBirthB ==
  /\ phase = "closed"
  /\ "runB" \in pending
  /\ registered' = registered \cup {"runB"}
  /\ pending' = pending \ {"runB"}
  /\ UNCHANGED <<phase, finished, released>>

Progress ==
  \/ \E c \in Consumers: Finish(c)
  \/ \E c \in Consumers: Relinquish(c)
  \/ BirthB
  \/ AbandonFutureB

SafeNext == Progress \/ QualifiedClose
SafeSpec == Init /\ [][SafeNext]_vars

UnsafeClaimNext == Progress \/ ClaimOnlyClose
UnsafeClaimSpec == Init /\ [][UnsafeClaimNext]_vars

UnsafeBirthNext == Progress \/ ClaimOnlyClose \/ PostCloseBirthB
UnsafeBirthSpec == Init /\ [][UnsafeBirthNext]_vars

TypeOK ==
  /\ phase \in {"open", "closed"}
  /\ registered \in SUBSET Consumers
  /\ finished \in SUBSET Consumers
  /\ released \in SUBSET Consumers
  /\ pending \in SUBSET Consumers
  /\ finished \subseteq registered
  /\ released \subseteq finished
  /\ registered \cap pending = {}

ClosedNoHeldClaim == phase = "closed" => registered = released
ClosedNoUnbornIntent == phase = "closed" => pending = {}

\* Nonvacuity counterexample must demonstrate a legitimate safe close.
NeverClosed == phase # "closed"
=============================================================================
