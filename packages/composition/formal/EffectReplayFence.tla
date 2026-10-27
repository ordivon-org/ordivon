---- MODULE EffectReplayFence ----
EXTENDS Naturals

(***************************************************************************)
(* C06 task-local effect uncertainty, finite abstract transition model.     *)
(* R2.1 adopted semantics: state-machine safety with an explicit I/O seam. *)
(* This verifies ONLY this small mathematical model, not Python/Runtime,   *)
(* deployed facts or provider effects. No actor/owner approval is a proof. *)
(***************************************************************************)

VARIABLES phase, remoteState, terminal, recovery, delivery, indexed,
          recommendation, impacted, retryAllowed, effectEstablished

vars == <<phase, remoteState, terminal, recovery, delivery, indexed,
          recommendation, impacted, retryAllowed, effectEstablished>>

RemoteStates == {"started", "reconcile_required", "completed"}
DeliveryStates == {"unknown", "in_progress", "committed"}
Phases == {"new", "observed", "classified"}
Recommendations == {"none", "observe", "reconcile", "verify"}
Obligations == {"write", "client", "media"}

(***************************************************************************)
(* The output is intentionally monotone in uncertainty. "committed" here  *)
(* means only process delivery, never provider-effect completion.           *)
(***************************************************************************)
Decision(s, t, r, d) ==
    IF r \/ d = "unknown" \/ s = "reconcile_required" THEN "reconcile"
    ELSE IF ~t THEN "observe"
    ELSE "verify"

UnknownObligations(known) ==
    IF known THEN {"write", "client"} ELSE Obligations

TypeOK ==
    /\ phase \in Phases
    /\ remoteState \in RemoteStates
    /\ terminal \in BOOLEAN
    /\ recovery \in BOOLEAN
    /\ delivery \in DeliveryStates
    /\ indexed \in BOOLEAN
    /\ recommendation \in Recommendations
    /\ impacted \subseteq Obligations
    /\ retryAllowed \in BOOLEAN
    /\ effectEstablished \in BOOLEAN

Init ==
    /\ phase = "new"
    /\ remoteState = "started"
    /\ terminal = FALSE
    /\ recovery = FALSE
    /\ delivery = "in_progress"
    /\ indexed = FALSE
    /\ recommendation = "none"
    /\ impacted = {}
    /\ retryAllowed = FALSE
    /\ effectEstablished = FALSE

Observe(s, t, r, d, i) ==
    /\ phase = "new"
    /\ s \in RemoteStates
    /\ t \in BOOLEAN
    /\ r \in BOOLEAN
    /\ d \in DeliveryStates
    /\ i \in BOOLEAN
    /\ phase' = "observed"
    /\ remoteState' = s
    /\ terminal' = t
    /\ recovery' = r
    /\ delivery' = d
    /\ indexed' = i
    /\ UNCHANGED <<recommendation, impacted, retryAllowed, effectEstablished>>

Classify ==
    /\ phase = "observed"
    /\ phase' = "classified"
    /\ recommendation' = Decision(remoteState, terminal, recovery, delivery)
    /\ impacted' = UnknownObligations(indexed)
    (* Neither a Runtime exit receipt nor owner-shaped text is a proof. *)
    /\ retryAllowed' = FALSE
    /\ effectEstablished' = FALSE
    /\ UNCHANGED <<remoteState, terminal, recovery, delivery, indexed>>

Next ==
    \/ \E s \in RemoteStates :
         \E t \in BOOLEAN :
           \E r \in BOOLEAN :
             \E d \in DeliveryStates :
               \E i \in BOOLEAN : Observe(s, t, r, d, i)
    \/ Classify

Spec == Init /\ [][Next]_vars

NoBlindRetry ==
    phase = "classified" => ~retryAllowed

NoEffectEstablishedFromProcessExit ==
    phase = "classified" => ~effectEstablished

RecommendationMatchesObservedCase ==
    phase = "classified" =>
      recommendation = Decision(remoteState, terminal, recovery, delivery)

ExactKnownAndUnknownImpact ==
    phase = "classified" =>
      impacted = UnknownObligations(indexed)

NoFalseIsolationOnUnindexedEffect ==
    phase = "classified" /\ ~indexed => impacted = Obligations

IndependentMediaIsUnaffectedByIndexedEffect ==
    phase = "classified" /\ indexed => "media" \notin impacted

(* Nonvacuity probes: these are intentionally FALSE, and their TLC counter *)
(* examples demonstrate reconciliation, successful process exit with no    *)
(* effect confirmation, and unindexed spill are REACHABLE.                *)
ReconciliationIsUnreachable ==
    phase = "classified" => recommendation # "reconcile"

TerminalCommittedWithoutEffectIsUnreachable ==
    phase = "classified" =>
      ~(terminal /\ delivery = "committed" /\ ~effectEstablished)

UnindexedUncertaintyIsUnreachable ==
    phase = "classified" => indexed

=============================================================================
