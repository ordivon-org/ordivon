-------------------- MODULE WorkspaceConsumerCloseR1 --------------------
EXTENDS TLC

\* Bounded abstraction for the first 24h of a Workspace's lifecycle.
\* The Release transition ASSUMES a trustworthy consumer; no native Runtime
\* authority currently proves that assumption for consumerReleased=true.

VARIABLES phase, age, consumer, released, liveJob, gitDependent, installedUnitBound

vars == <<phase, age, consumer, released, liveJob, gitDependent, installedUnitBound>>

Init ==
    /\ phase = "open"
    /\ age = "fresh"
    /\ consumer = "active"
    /\ released = FALSE
    /\ liveJob = FALSE
    /\ gitDependent = FALSE
    /\ installedUnitBound = FALSE

ConsumerFinishes ==
    /\ phase = "open"
    /\ consumer = "active"
    /\ consumer' = "finished"
    /\ UNCHANGED <<phase, age, released, liveJob, gitDependent, installedUnitBound>>

ConsumerReleases ==
    /\ phase = "open"
    /\ consumer = "finished"
    /\ ~released
    /\ released' = TRUE
    /\ UNCHANGED <<phase, age, consumer, liveJob, gitDependent, installedUnitBound>>

AgeExpires ==
    /\ phase = "open"
    /\ age = "fresh"
    /\ age' = "expired"
    /\ UNCHANGED <<phase, consumer, released, liveJob, gitDependent, installedUnitBound>>

BeginJob ==
    /\ phase = "open"
    /\ ~liveJob
    /\ liveJob' = TRUE
    /\ UNCHANGED <<phase, age, consumer, released, gitDependent, installedUnitBound>>

EndJob ==
    /\ phase = "open"
    /\ liveJob
    /\ liveJob' = FALSE
    /\ UNCHANGED <<phase, age, consumer, released, gitDependent, installedUnitBound>>

AddGitDependent ==
    /\ phase = "open"
    /\ ~gitDependent
    /\ gitDependent' = TRUE
    /\ UNCHANGED <<phase, age, consumer, released, liveJob, installedUnitBound>>

RemoveGitDependent ==
    /\ phase = "open"
    /\ gitDependent
    /\ gitDependent' = FALSE
    /\ UNCHANGED <<phase, age, consumer, released, liveJob, installedUnitBound>>

BindInstalledUnit ==
    /\ phase = "open"
    /\ ~installedUnitBound
    /\ installedUnitBound' = TRUE
    /\ UNCHANGED <<phase, age, consumer, released, liveJob, gitDependent>>

UnbindInstalledUnit ==
    /\ phase = "open"
    /\ installedUnitBound
    /\ installedUnitBound' = FALSE
    /\ UNCHANGED <<phase, age, consumer, released, liveJob, gitDependent>>

Close ==
    /\ phase = "open"
    /\ ~liveJob
    /\ ~gitDependent
    /\ ~installedUnitBound
    /\ (released \/ age = "expired")
    /\ phase' = "closed"
    /\ UNCHANGED <<age, consumer, released, liveJob, gitDependent, installedUnitBound>>

Next ==
    \/ ConsumerFinishes
    \/ ConsumerReleases
    \/ AgeExpires
    \/ BeginJob
    \/ EndJob
    \/ AddGitDependent
    \/ RemoveGitDependent
    \/ BindInstalledUnit
    \/ UnbindInstalledUnit
    \/ Close

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ phase \in {"open", "closed"}
    /\ age \in {"fresh", "expired"}
    /\ consumer \in {"active", "finished"}
    /\ released \in BOOLEAN
    /\ liveJob \in BOOLEAN
    /\ gitDependent \in BOOLEAN
    /\ installedUnitBound \in BOOLEAN

FreshActiveConsumerCannotBeClosed ==
    (phase = "closed" /\ age = "fresh") =>
        (consumer = "finished" /\ released)

ClosedHasNoLiveJob == phase = "closed" => ~liveJob
ClosedHasNoGitDependent == phase = "closed" => ~gitDependent
ClosedHasNoInstalledUnitConsumer == phase = "closed" => ~installedUnitBound
ReleasedAssumesConsumerFinished == released => consumer = "finished"

\* A reachable safe closure must be shown, not inferred from vacuous invariants.
ClosedUnreachable == phase # "closed"
=============================================================================
