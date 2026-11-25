------------------ MODULE RuntimePgMaintenanceAdmissionR1 ------------------
EXTENDS Naturals, FiniteSets

(*
  Finite refinement target for the permanent PG maintenance row.
  A snapshot captures one observed gate state/version; the existing
  short admission transaction serializes row check + new Job commit.
  A close is a durable native row update, not a long-lived shared lock.
  No reopening transition is specified here: external recovery and the
  installed all-writer qualification remain independent obligations.
*)
CONSTANTS OmitVersion, OmitGate, LoseOnRestart, BlockSettlement, BlockReplay
VARIABLE s
Gate == {"OPEN", "CLOSED", "MISSING", "MALFORMED"}
Init ==
    s = [gate |-> "OPEN", gen |-> 0, everClosed |-> FALSE,
         snap |-> "NONE", snapGen |-> 0, jobs |-> 1, pending |-> 1,
         late |-> FALSE, replayed |-> FALSE]
Snapshot ==
    /\ s.snap = "NONE" /\ s.jobs < 2
    /\ s' = [s EXCEPT !.snap = s.gate, !.snapGen = s.gen]
Close ==
    /\ s.gate = "OPEN" /\ s.gen < 2
    /\ s' = [s EXCEPT !.gate = "CLOSED", !.gen = @ + 1, !.everClosed = TRUE]
Damage(g) ==
    /\ s.gate \in {"OPEN","CLOSED"} /\ s.gen < 2
    /\ g \in {"MISSING","MALFORMED"}
    /\ s' = [s EXCEPT !.gate = g, !.gen = @ + 1]
TryNew ==
    /\ s.snap # "NONE" /\ s.jobs < 2
    /\ IF (OmitGate \/ s.snap = "OPEN")
          /\ (OmitVersion \/ s.snapGen = s.gen)
       THEN s' = [s EXCEPT !.jobs = @ + 1, !.pending = @ + 1,
                     !.late = @ \/ s.gate # "OPEN" \/ s.everClosed,
                     !.snap = "NONE"]
       ELSE s' = [s EXCEPT !.snap = "NONE"]
Settle ==
    /\ s.pending > 0
    /\ ~(BlockSettlement /\ s.gate # "OPEN")
    /\ s' = [s EXCEPT !.pending = @ - 1]
Replay ==
    /\ s.jobs > 0 /\ ~s.replayed
    /\ ~(BlockReplay /\ s.gate # "OPEN")
    /\ s' = [s EXCEPT !.replayed = TRUE]
Restart ==
    s' = [s EXCEPT !.snap = "NONE",
          !.gate = IF LoseOnRestart /\ s.everClosed THEN "OPEN" ELSE @]
Next == Snapshot \/ Close \/ (\E g \in Gate: Damage(g)) \/
        TryNew \/ Settle \/ Replay \/ Restart
Spec == Init /\ [][Next]_s
TypeOK ==
    /\ s.gate \in Gate /\ s.gen \in 0..2 /\ s.snapGen \in 0..2
    /\ s.snap \in Gate \cup {"NONE"}
    /\ s.jobs \in 1..2 /\ s.pending \in 0..2 /\ s.pending <= s.jobs
    /\ s.late \in BOOLEAN /\ s.replayed \in BOOLEAN /\ s.everClosed \in BOOLEAN
NoNewAfterClosureOrUnknown == ~s.late
NoImplicitReopen == s.everClosed => s.gate # "OPEN"
DrainProgress == s.pending > 0 => ENABLED Settle
ExactReplayProgress == s.jobs > 0 /\ ~s.replayed => ENABLED Replay
NeverClosedDrainedReplay == ~(s.gate = "CLOSED" /\ s.pending = 0 /\ s.replayed)
=============================================================================
