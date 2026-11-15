---------------- MODULE WorkspaceMultiAgentReleaseR1 ----------------
EXTENDS TLC, FiniteSets

\* A distinct cross-Agent scope refinement of WorkspaceConsumerCloseR1,
\* NOT a replacement for its implemented four-hour/native guard.
\* Two logical Harness Runs may use the same physical Runtime Workspace,
\* even after one Run has already received its terminal Tool/Run receipt.
\* Each abstract Release is ASSUMED accurate; real principal identity,
\* PG claim persistence, durable delivery and installed refinement remain
\* UNKNOWN until a source-owned owner/consumer binding exists.
\*
\* The current native consumerReleased=true is a single CALLER ASSERTION.
\* The UnsafeSingle/UnsafeAge models must exhibit the missing consumer B
\* being displaced by early closing, rather than assuming one Run owns all.

Consumers == {"runA", "runB"}

VARIABLES phase, finished, released, liveJob, gitDependent, age

vars == <<phase, finished, released, liveJob, gitDependent, age>>

Init ==
    /\ phase = "open"
    /\ finished = {}
    /\ released = {}
    /\ liveJob = FALSE
    /\ gitDependent = FALSE
    /\ age = "fresh"

Finish(c) ==
    /\ phase = "open"
    /\ c \in Consumers
    /\ c \notin finished
    /\ finished' = finished \cup {c}
    /\ UNCHANGED <<phase, released, liveJob, gitDependent, age>>

Release(c) ==
    /\ phase = "open"
    /\ c \in finished
    /\ c \notin released
    /\ released' = released \cup {c}
    /\ UNCHANGED <<phase, finished, liveJob, gitDependent, age>>

BeginJob ==
    /\ phase = "open"
    /\ ~liveJob
    /\ liveJob' = TRUE
    /\ UNCHANGED <<phase, finished, released, gitDependent, age>>

EndJob ==
    /\ phase = "open"
    /\ liveJob
    /\ liveJob' = FALSE
    /\ UNCHANGED <<phase, finished, released, gitDependent, age>>

AddGitDependency ==
    /\ phase = "open"
    /\ ~gitDependent
    /\ gitDependent' = TRUE
    /\ UNCHANGED <<phase, finished, released, liveJob, age>>

RemoveGitDependency ==
    /\ phase = "open"
    /\ gitDependent
    /\ gitDependent' = FALSE
    /\ UNCHANGED <<phase, finished, released, liveJob, age>>

AgeExpires ==
    /\ phase = "open"
    /\ age = "fresh"
    /\ age' = "expired"
    /\ UNCHANGED <<phase, finished, released, liveJob, gitDependent>>

Close ==
    /\ phase = "open"
    /\ released = Consumers
    /\ ~liveJob
    /\ ~gitDependent
    /\ phase' = "closed"
    /\ UNCHANGED <<finished, released, liveJob, gitDependent, age>>

Progress ==
    \/ \E c \in Consumers: Finish(c)
    \/ \E c \in Consumers: Release(c)
    \/ BeginJob
    \/ EndJob
    \/ AddGitDependency
    \/ RemoveGitDependency
    \/ AgeExpires

SafeNext == Progress \/ Close
SafeSpec == Init /\ [][SafeNext]_vars
FairSafeSpec == SafeSpec /\ WF_vars(Close)

Eligible ==
    /\ phase = "open"
    /\ released = Consumers
    /\ ~liveJob
    /\ ~gitDependent

StableEligibleEventuallyClosed ==
    (<>[]Eligible) => <> (phase = "closed")

TypeOK ==
    /\ phase \in {"open", "closed"}
    /\ finished \in SUBSET Consumers
    /\ released \in SUBSET Consumers
    /\ released \subseteq finished
    /\ liveJob \in BOOLEAN
    /\ gitDependent \in BOOLEAN
    /\ age \in {"fresh", "expired"}

ClosedImpliesEveryConsumerReleased ==
    phase = "closed" => released = Consumers

ClosedHasNoPhysicalDependencies ==
    phase = "closed" => ~liveJob /\ ~gitDependent

\* We must demonstrate legitimate closure, not prove safety vacuously.
ClosedUnreachable == phase # "closed"

\* Existing source's single consumerReleased=true, presented here as an
\* unsafe abstract early close after run A releases, regardless of run B.
UnsafeSingleReleaseClose ==
    /\ phase = "open"
    /\ released = {"runA"}
    /\ ~liveJob
    /\ ~gitDependent
    /\ phase' = "closed"
    /\ UNCHANGED <<finished, released, liveJob, gitDependent, age>>

UnsafeSingleNext == Progress \/ UnsafeSingleReleaseClose
UnsafeSingleSpec == Init /\ [][UnsafeSingleNext]_vars

\* Existing age-only fallback may close while a Run is paused between Jobs;
\* this counterexample is a requirement discovery, NOT an installed defect
\* attribution for an individual Workspace removed by existing GC policy.
UnsafeAgeOnlyClose ==
    /\ phase = "open"
    /\ age = "expired"
    /\ released # Consumers
    /\ ~liveJob
    /\ ~gitDependent
    /\ phase' = "closed"
    /\ UNCHANGED <<finished, released, liveJob, gitDependent, age>>

UnsafeAgeNext == Progress \/ UnsafeAgeOnlyClose
UnsafeAgeSpec == Init /\ [][UnsafeAgeNext]_vars
=============================================================================
