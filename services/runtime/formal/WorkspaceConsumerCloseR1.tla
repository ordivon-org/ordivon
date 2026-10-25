-------------------- MODULE WorkspaceConsumerCloseR1 --------------------
EXTENDS TLC

\* Bounded abstraction for the first 24h of a Workspace's lifecycle.
\* The Release transition ASSUMES a trustworthy consumer; no native Runtime
\* authority currently proves that assumption for consumerReleased=true.

VARIABLES phase, age, consumer, released, liveJob, gitDependent

vars == <<phase, age, consumer, released, liveJob, gitDependent>>

Init ==
    /\ phase = "open"
    /\ age = "fresh"
    /\ consumer = "active"
    /\ released = FALSE
    /\ liveJob = FALSE
    /\ gitDependent = FALSE

ConsumerFinishes ==
    /\ phase = "open"
    /\ consumer = "active"
    /\ consumer' = "finished"
    /\ UNCHANGED <<phase, age, released, liveJob, gitDependent>>

ConsumerReleases ==
    /\ phase = "open"
    /\ consumer = "finished"
    /\ ~released
    /\ released' = TRUE
    /\ UNCHANGED <<phase, age, consumer, liveJob, gitDependent>>

AgeExpires ==
    /\ phase = "open"
    /\ age = "fresh"
    /\ age' = "expired"
    /\ UNCHANGED <<phase, consumer, released, liveJob, gitDependent>>

BeginJob ==
    /\ phase = "open"
    /\ ~liveJob
    /\ liveJob' = TRUE
    /\ UNCHANGED <<phase, age, consumer, released, gitDependent>>

EndJob ==
    /\ phase = "open"
    /\ liveJob
    /\ liveJob' = FALSE
    /\ UNCHANGED <<phase, age, consumer, released, gitDependent>>

AddGitDependent ==
    /\ phase = "open"
    /\ ~gitDependent
    /\ gitDependent' = TRUE
    /\ UNCHANGED <<phase, age, consumer, released, liveJob>>

RemoveGitDependent ==
    /\ phase = "open"
    /\ gitDependent
    /\ gitDependent' = FALSE
    /\ UNCHANGED <<phase, age, consumer, released, liveJob>>

Close ==
    /\ phase = "open"
    /\ ~liveJob
    /\ ~gitDependent
    /\ (released \/ age = "expired")
    /\ phase' = "closed"
    /\ UNCHANGED <<age, consumer, released, liveJob, gitDependent>>

Next ==
    \/ ConsumerFinishes
    \/ ConsumerReleases
    \/ AgeExpires
    \/ BeginJob
    \/ EndJob
    \/ AddGitDependent
    \/ RemoveGitDependent
    \/ Close

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ phase \in {"open", "closed"}
    /\ age \in {"fresh", "expired"}
    /\ consumer \in {"active", "finished"}
    /\ released \in BOOLEAN
    /\ liveJob \in BOOLEAN
    /\ gitDependent \in BOOLEAN

FreshActiveConsumerCannotBeClosed ==
    (phase = "closed" /\ age = "fresh") =>
        (consumer = "finished" /\ released)

ClosedHasNoLiveJob == phase = "closed" => ~liveJob
ClosedHasNoGitDependent == phase = "closed" => ~gitDependent
ReleasedAssumesConsumerFinished == released => consumer = "finished"

\* A reachable safe closure must be shown, not inferred from vacuous invariants.
ClosedUnreachable == phase # "closed"
=============================================================================
