----------------------- MODULE ObservationGenerationR1 -----------------------
EXTENDS Naturals
CONSTANT Policy, MaxGeneration
VARIABLES latest, pending, phase, displayedGeneration, latestOutcome, active
vars == <<latest, pending, phase, displayedGeneration, latestOutcome, active>>
Outcomes == {"observed", "denied", "unavailable"}

Init ==
    /\ latest = 0
    /\ pending = {}
    /\ phase = "loading"
    /\ displayedGeneration = 0
    /\ latestOutcome = "loading"
    /\ active = TRUE

Begin ==
    /\ active
    /\ latest < MaxGeneration
    /\ latest' = latest + 1
    /\ pending' = pending \cup {latest'}
    /\ phase' = "loading"
    /\ displayedGeneration' = 0
    /\ latestOutcome' = "loading"
    /\ UNCHANGED active

Suspend ==
    /\ active
    /\ latest < MaxGeneration
    /\ latest' = latest + 1
    /\ active' = FALSE
    /\ phase' = "suspended"
    /\ latestOutcome' = "suspended"
    /\ displayedGeneration' = 0
    /\ UNCHANGED pending

Resume ==
    /\ ~active
    /\ latest < MaxGeneration
    /\ active' = TRUE
    /\ latest' = latest + 1
    /\ pending' = pending \cup {latest'}
    /\ phase' = "loading"
    /\ latestOutcome' = "loading"
    /\ displayedGeneration' = 0

Complete(g, outcome) ==
    /\ g \in pending
    /\ pending' = pending \ {g}
    /\ UNCHANGED <<latest, active>>
    /\ latestOutcome' = IF g = latest THEN outcome ELSE latestOutcome
    /\ IF Policy = "legacy" \/ (active /\ g = latest /\ phase = "loading")
       THEN /\ phase' = outcome
            /\ displayedGeneration' = IF outcome = "observed" THEN g ELSE 0
       ELSE UNCHANGED <<phase, displayedGeneration>>

Next == Begin \/ Suspend \/ Resume \/ \E g \in pending, o \in Outcomes : Complete(g,o)
Spec == Init /\ [][Next]_vars
TypeOK ==
    /\ latest \in 0..MaxGeneration
    /\ pending \subseteq 1..latest
    /\ phase \in Outcomes \cup {"loading", "suspended"}
    /\ latestOutcome \in Outcomes \cup {"loading", "suspended"}
    /\ displayedGeneration \in 0..latest
    /\ active \in BOOLEAN
ObservedMatchesLatest ==
    phase = "observed" => displayedGeneration = latest /\ latestOutcome = "observed"
NoPrivateRowsWhenNotObserved ==
    phase # "observed" => displayedGeneration = 0
DenialNotReplacedByStale ==
    latestOutcome = "denied" => phase = "denied" /\ displayedGeneration = 0
NoPrivateRowsWhenInactive ==
    ~active => phase = "suspended" /\ displayedGeneration = 0
NeverObserved == phase # "observed"
NeverDenied == phase # "denied"
NeverSuspended == phase # "suspended"
=============================================================================
