-------------------- MODULE WorkspaceContinuationR1 --------------------
EXTENDS Naturals

\* Bounded abstract consumer continuity. This is not an authentication
\* protocol. "released" is a *caller assertion*, currently not an
\* independent proof that all external consumers have finished.
VARIABLES phase, job, pending, released, age, firstDone, closeReason

Vars == <<phase, job, pending, released, age, firstDone, closeReason>>

Init ==
    /\ phase = "open"
    /\ job = "none"
    /\ pending = FALSE
    /\ released = FALSE
    /\ age = "fresh"
    /\ firstDone = FALSE
    /\ closeReason = "none"

StartFirst ==
    /\ phase = "open"
    /\ job = "none"
    /\ ~firstDone
    /\ job' = "running"
    /\ UNCHANGED <<phase, pending, released, age, firstDone, closeReason>>

CompleteFirst ==
    /\ phase = "open"
    /\ job = "running"
    /\ ~firstDone
    /\ job' = "none"
    /\ firstDone' = TRUE
    /\ UNCHANGED <<phase, pending, released, age, closeReason>>

RequestNext ==
    /\ phase = "open"
    /\ job = "none"
    /\ firstDone
    /\ ~pending
    /\ ~released
    /\ pending' = TRUE
    /\ UNCHANGED <<phase, job, released, age, firstDone, closeReason>>

StartNext ==
    /\ phase = "open"
    /\ job = "none"
    /\ pending
    /\ job' = "running"
    /\ pending' = FALSE
    /\ UNCHANGED <<phase, released, age, firstDone, closeReason>>

CompleteNext ==
    /\ phase = "open"
    /\ job = "running"
    /\ firstDone
    /\ job' = "none"
    /\ UNCHANGED <<phase, pending, released, age, firstDone, closeReason>>

DeclareReleased ==
    /\ phase = "open"
    /\ job = "none"
    /\ ~released
    /\ released' = TRUE
    /\ pending' = FALSE
    /\ UNCHANGED <<phase, job, age, firstDone, closeReason>>

Expire ==
    /\ phase = "open"
    /\ age = "fresh"
    /\ age' = "expired"
    /\ UNCHANGED <<phase, job, pending, released, firstDone, closeReason>>

Close ==
    /\ phase = "open"
    /\ job = "none"
    /\ (released \/ age = "expired")
    /\ phase' = "closed"
    /\ closeReason' = IF released THEN "released" ELSE "expired"
    /\ UNCHANGED <<job, pending, released, age, firstDone>>

Next ==
    \/ StartFirst
    \/ CompleteFirst
    \/ RequestNext
    \/ StartNext
    \/ CompleteNext
    \/ DeclareReleased
    \/ Expire
    \/ Close

TypeOK ==
    /\ phase \in {"open", "closed"}
    /\ job \in {"none", "running"}
    /\ pending \in BOOLEAN
    /\ released \in BOOLEAN
    /\ age \in {"fresh", "expired"}
    /\ firstDone \in BOOLEAN
    /\ closeReason \in {"none", "released", "expired", "idle_only"}

NoUnreleasedFreshClose == phase = "open" \/ released \/ age = "expired"
NoRunningJobClosed == ~(phase = "closed" /\ job = "running")

Spec == Init /\ [][Next]_Vars

=============================================================================
