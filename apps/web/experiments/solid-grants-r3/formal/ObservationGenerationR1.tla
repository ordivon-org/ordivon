----------------------- MODULE ObservationGenerationR1 -----------------------
EXTENDS Naturals
CONSTANT Policy, MaxGeneration
VARIABLES latest, pending, phase, displayedGeneration, latestOutcome
vars == <<latest, pending, phase, displayedGeneration, latestOutcome>>
Outcomes == {"observed", "denied", "unavailable"}

Init ==
    /\ latest = 0
    /\ pending = {}
    /\ phase = "loading"
    /\ displayedGeneration = 0
    /\ latestOutcome = "loading"

Begin ==
    /\ latest < MaxGeneration
    /\ latest' = latest + 1
    /\ pending' = pending \cup {latest'}
    /\ phase' = "loading"
    /\ displayedGeneration' = 0
    /\ latestOutcome' = "loading"

Complete(g, outcome) ==
    /\ g \in pending
    /\ pending' = pending \ {g}
    /\ latest' = latest
    /\ latestOutcome' = IF g = latest THEN outcome ELSE latestOutcome
    /\ IF Policy = "legacy" \/ (g = latest /\ phase = "loading")
       THEN /\ phase' = outcome
            /\ displayedGeneration' = IF outcome = "observed" THEN g ELSE 0
       ELSE UNCHANGED <<phase, displayedGeneration>>

Next == Begin \/ \E g \in pending, o \in Outcomes : Complete(g,o)
Spec == Init /\ [][Next]_vars
TypeOK ==
    /\ latest \in 0..MaxGeneration
    /\ pending \subseteq 1..latest
    /\ phase \in Outcomes \cup {"loading"}
    /\ latestOutcome \in Outcomes \cup {"loading"}
    /\ displayedGeneration \in 0..latest
ObservedMatchesLatest ==
    phase = "observed" => displayedGeneration = latest /\ latestOutcome = "observed"
NoPrivateRowsWhenNotObserved ==
    phase # "observed" => displayedGeneration = 0
DenialNotReplacedByStale ==
    latestOutcome = "denied" => phase = "denied" /\ displayedGeneration = 0
NeverObserved == phase # "observed"
NeverDenied == phase # "denied"
=============================================================================
