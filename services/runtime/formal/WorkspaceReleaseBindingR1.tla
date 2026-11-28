-------------------- MODULE WorkspaceReleaseBindingR1 --------------------
EXTENDS TLC
\* Refines the collector's abstract release by a finite identity witness.
\* An authorized release is assumed truthful; this does not prove external
\* consumers are absent, clock uniqueness, or an atomic policy-to-close fence.
VARIABLES phase, generation, source, activity, release
vars == <<phase, generation, source, activity, release>>
Epoch == {0, 1}
NoRelease == [generation |-> 2, source |-> 2, activity |-> 2]
Subject == [generation |-> generation, source |-> source, activity |-> activity]
Init ==
    /\ phase = "open"
    /\ generation = 0
    /\ source = 0
    /\ activity = 0
    /\ release = NoRelease
ObserveRelease ==
    /\ phase = "open"
    /\ release' = Subject
    /\ UNCHANGED <<phase, generation, source, activity>>
RevokeRelease ==
    /\ phase = "open"
    /\ release' = NoRelease
    /\ UNCHANGED <<phase, generation, source, activity>>
ChangeGeneration ==
    /\ phase = "open"
    /\ generation = 0
    /\ generation' = 1
    /\ UNCHANGED <<phase, source, activity, release>>
ChangeSource ==
    /\ phase = "open"
    /\ source = 0
    /\ source' = 1
    /\ UNCHANGED <<phase, generation, activity, release>>
NewJobActivity ==
    /\ phase = "open"
    /\ activity = 0
    /\ activity' = 1
    /\ UNCHANGED <<phase, generation, source, release>>
CloseEligible ==
    /\ phase = "open"
    /\ release.generation = generation
    /\ release.source = source
    /\ release.activity = activity
Close ==
    /\ CloseEligible
    /\ phase' = "closed"
    /\ UNCHANGED <<generation, source, activity, release>>
Next == ObserveRelease \/ RevokeRelease \/ ChangeGeneration
        \/ ChangeSource \/ NewJobActivity \/ Close
Spec == Init /\ [][Next]_vars /\ WF_vars(Close)
TypeOK ==
    /\ phase \in {"open", "closed"}
    /\ generation \in Epoch
    /\ source \in Epoch
    /\ activity \in Epoch
    /\ release \in ({NoRelease} \cup [generation: Epoch, source: Epoch, activity: Epoch])
ClosedHasCurrentRelease == phase = "closed" => release = Subject
StableEligibleEventuallyClosed == (<>[]CloseEligible) => <> (phase = "closed")
ClosedUnreachable == phase # "closed"
=============================================================================
