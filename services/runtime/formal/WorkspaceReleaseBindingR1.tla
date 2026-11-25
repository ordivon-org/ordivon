-------------------- MODULE WorkspaceReleaseBindingR1 --------------------
EXTENDS TLC
\* Refines the collector's abstract release by a finite identity witness.
\* An authorized release is assumed truthful; this does not prove external
\* consumers are absent or that a concrete implementation supplies an
\* adequate root revision. A check followed by an effect is not atomic.
VARIABLES phase, generation, source, activity, release, rootRevision, checked
vars == <<phase, generation, source, activity, release, rootRevision, checked>>
Epoch == {0, 1}
NoRelease == [generation |-> 2, source |-> 2, activity |-> 2, rootRevision |-> 2]
Subject == [generation |-> generation, source |-> source, activity |-> activity, rootRevision |-> rootRevision]
Init ==
    /\ phase = "open"
    /\ generation = 0
    /\ source = 0
    /\ activity = 0
    /\ release = NoRelease
    /\ rootRevision = 0
    /\ checked = FALSE
ObserveRelease ==
    /\ phase = "open"
    /\ release' = Subject
    /\ UNCHANGED <<phase, generation, source, activity, rootRevision, checked>>
RevokeRelease ==
    /\ phase = "open"
    /\ release' = NoRelease
    /\ UNCHANGED <<phase, generation, source, activity, rootRevision, checked>>
ChangeGeneration ==
    /\ phase = "open"
    /\ generation = 0
    /\ generation' = 1
    /\ UNCHANGED <<phase, source, activity, release, rootRevision, checked>>
ChangeSource ==
    /\ phase = "open"
    /\ source = 0
    /\ source' = 1
    /\ UNCHANGED <<phase, generation, activity, release, rootRevision, checked>>
NewJobActivity ==
    /\ phase = "open"
    /\ activity = 0
    /\ activity' = 1
    /\ UNCHANGED <<phase, generation, source, release, rootRevision, checked>>
\* A settled historical root can change without moving max(activity).
ChangeRootAtSameActivity ==
    /\ phase = "open"
    /\ rootRevision = 0
    /\ rootRevision' = 1
    /\ UNCHANGED <<phase, generation, source, activity, release, checked>>
CloseEligible ==
    /\ phase = "open"
    /\ release.generation = generation
    /\ release.source = source
    /\ release.activity = activity
    /\ release.rootRevision = rootRevision
ObserveEligible ==
    /\ CloseEligible
    /\ checked' = TRUE
    /\ UNCHANGED <<phase, generation, source, activity, release, rootRevision>>
Close ==
    /\ checked
    /\ CloseEligible
    /\ phase' = "closed"
    /\ UNCHANGED <<generation, source, activity, release, rootRevision, checked>>
Next == ObserveRelease \/ RevokeRelease \/ ChangeGeneration
        \/ ChangeSource \/ NewJobActivity \/ ChangeRootAtSameActivity
        \/ ObserveEligible \/ Close
Spec == Init /\ [][Next]_vars /\ WF_vars(ObserveEligible) /\ WF_vars(Close)
TypeOK ==
    /\ phase \in {"open", "closed"}
    /\ generation \in Epoch
    /\ source \in Epoch
    /\ activity \in Epoch
    /\ rootRevision \in Epoch
    /\ checked \in BOOLEAN
    /\ release \in ({NoRelease} \cup [generation: Epoch, source: Epoch, activity: Epoch, rootRevision: Epoch])
ClosedHasCurrentRelease == phase = "closed" => release = Subject
StableEligibleEventuallyClosed == (<>[]CloseEligible) => <> (phase = "closed")
ClosedUnreachable == phase # "closed"
=============================================================================
