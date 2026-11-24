-------------------- MODULE WorkspaceConsumerCloseR1 --------------------
EXTENDS TLC

\* Bounded abstraction for the first 4h of a Workspace's lifecycle.
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

\* Conditional liveness: under weak fairness for Close, a Workspace that
\* stays eligible forever cannot be retained forever solely by stuttering.
\* This does NOT witness actual physical consumers or scheduler fairness.
EligibleForClose ==
    /\ phase = "open"
    /\ ~liveJob
    /\ ~gitDependent
    /\ (released \/ age = "expired")

FairCloseSpec == Spec /\ WF_vars(Close)

StableEligibleEventuallyClosed ==
    (<>[]EligibleForClose) => <> (phase = "closed")

\* Deliberately unsatisfied in the current abstraction: expiry alone
\* is not proof that an otherwise active consumer has finished.
ExpiredActiveConsumerCannotBeClosed ==
    ~ (phase = "closed" /\ consumer = "active" /\ age = "expired")


\* Candidate refinement profile: the abstract consumer must finish before
\* physical Close is eligible. "finished" is a MODEL STATE, not a source-
\* authenticated fact: code/installed refinement remains an open obligation.
\* Preserve the historical R1 profile and its concrete age-only counterexample
\* so this profile cannot erase a known gap in the current implementation.
R2CandidateClose ==
    /\ Close
    /\ consumer = "finished"

NextR2Candidate ==
    \/ ConsumerFinishes
    \/ ConsumerReleases
    \/ AgeExpires
    \/ BeginJob
    \/ EndJob
    \/ AddGitDependent
    \/ RemoveGitDependent
    \/ R2CandidateClose

R2CandidateSpec == Init /\ [][NextR2Candidate]_vars

FairR2CandidateSpec == R2CandidateSpec /\ WF_vars(R2CandidateClose)

R2CandidateEligible ==
    /\ phase = "open"
    /\ consumer = "finished"
    /\ ~liveJob
    /\ ~gitDependent
    /\ (released \/ age = "expired")

StableR2CandidateEligibleEventuallyClosed ==
    (<>[]R2CandidateEligible) => <> (phase = "closed")

R2CandidateClosedConsumerFinished ==
    phase = "closed" => consumer = "finished"

\* Falsification-only: a normal R2 candidate must reach an early close
\* after a finished consumer explicitly releases (not just after age expires).
R2CandidateFreshReleasedCloseUnreachable ==
    ~ (phase = "closed" /\ age = "fresh" /\ released)

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
