---- MODULE DoctorSnapshotR1 ----
EXTENDS Naturals

(* Bounded global Doctor history: one creation Event per Run, no other
   mutations. Existing-row locks do not prevent a fresh Run insertion.
   Stable represents one native PG transaction snapshot, not a new Store. *)
CONSTANT AllowWeakGlobal
VARIABLES stable, liveRuns, snapshotRuns, observedRuns, observedEvents, phase
vars == <<stable, liveRuns, snapshotRuns, observedRuns, observedEvents, phase>>

TypeOK == /\ stable \in BOOLEAN
          /\ liveRuns \in 1..2
          /\ snapshotRuns \in 1..2
          /\ observedRuns \in 0..2
          /\ observedEvents \in 0..2
          /\ phase \in {"start", "runs-read", "healthy", "not-qualified"}

Init == /\ stable \in BOOLEAN
        /\ liveRuns = 1
        /\ snapshotRuns = 1
        /\ observedRuns = 0
        /\ observedEvents = 0
        /\ phase = "start"

CreateRun == /\ liveRuns = 1
             /\ liveRuns' = 2
             /\ UNCHANGED <<stable, snapshotRuns, observedRuns, observedEvents, phase>>

ReadRuns == /\ phase = "start"
            /\ stable \/ AllowWeakGlobal
            /\ snapshotRuns' = liveRuns
            /\ observedRuns' = liveRuns
            /\ phase' = "runs-read"
            /\ UNCHANGED <<stable, liveRuns, observedEvents>>

RejectWeak == /\ phase = "start"
              /\ ~stable
              /\ ~AllowWeakGlobal
              /\ phase' = "not-qualified"
              /\ UNCHANGED <<stable, liveRuns, snapshotRuns, observedRuns, observedEvents>>

ReadEvents == /\ phase = "runs-read"
              /\ observedEvents' = IF stable THEN snapshotRuns ELSE liveRuns
              /\ phase' = "healthy"
              /\ UNCHANGED <<stable, liveRuns, snapshotRuns, observedRuns>>

Quiesce == /\ phase \in {"healthy", "not-qualified"}
           /\ UNCHANGED vars

Next == CreateRun \/ ReadRuns \/ RejectWeak \/ ReadEvents \/ Quiesce
Spec == Init /\ [][Next]_vars

(* In this fixture each Run has exactly its one creation Event. *)
CoherentReport == phase = "healthy" => observedRuns = observedEvents
QualifiedReport == phase = "healthy" => stable
HealthyIsUnreachable == phase # "healthy"
ConcurrentHealthyIsUnreachable ==
    ~(phase = "healthy" /\ liveRuns = 2 /\ observedRuns = 1 /\ observedEvents = 1)
====
