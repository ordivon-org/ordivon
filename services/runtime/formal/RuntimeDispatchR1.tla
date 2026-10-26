---- MODULE RuntimeDispatchR1 ----
EXTENDS Naturals

(***************************************************************************)
(* Standards-first formal model for the narrow Runtime dispatch boundary.   *)
(* It deliberately does not model workflow/business-process state.          *)
(***************************************************************************)

CONSTANTS Attempts, NoAttempt

AttemptStates == {"unused", "admitted", "running", "ambiguous", "orphanedHeld", "lost", "terminal"}
JobStates == {"none", "admitted", "ambiguous", "terminal"}
ReconcileStates == {"none", "required", "absent", "committed"}
ResultEvidenceStates == {"none", "foreign", "matching"}

VARIABLES jobState, attemptState, currentAttempt, dispatchCount, reconcileState, heldReservation, outputObserved, resultEvidence

vars == <<jobState, attemptState, currentAttempt, dispatchCount, reconcileState, heldReservation, outputObserved, resultEvidence>>

TypeOK ==
    /\ Attempts # {}
    /\ NoAttempt \notin Attempts
    /\ jobState \in JobStates
    /\ attemptState \in [Attempts -> AttemptStates]
    /\ currentAttempt \in Attempts \cup {NoAttempt}
    /\ dispatchCount \in [Attempts -> 0..2]
    /\ reconcileState \in ReconcileStates
    /\ heldReservation \in BOOLEAN
    /\ outputObserved \in [Attempts -> BOOLEAN]
    /\ resultEvidence \in [Attempts -> ResultEvidenceStates]

Init ==
    /\ jobState = "none"
    /\ attemptState = [a \in Attempts |-> "unused"]
    /\ currentAttempt = NoAttempt
    /\ dispatchCount = [a \in Attempts |-> 0]
    /\ reconcileState = "none"
    /\ heldReservation = FALSE
    /\ outputObserved = [a \in Attempts |-> FALSE]
    /\ resultEvidence = [a \in Attempts |-> "none"]

Admit ==
    /\ jobState = "none"
    /\ currentAttempt = NoAttempt
    /\ \E a \in Attempts:
        /\ attemptState[a] = "unused"
        /\ attemptState' = [attemptState EXCEPT ![a] = "admitted"]
        /\ currentAttempt' = a
    /\ jobState' = "admitted"
    /\ reconcileState' = "none"
    /\ UNCHANGED <<dispatchCount, heldReservation, outputObserved, resultEvidence>>

Dispatch ==
    /\ jobState = "admitted"
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] = "admitted"
    /\ dispatchCount[currentAttempt] = 0
    /\ attemptState' = [attemptState EXCEPT ![currentAttempt] = "running"]
    /\ dispatchCount' = [dispatchCount EXCEPT ![currentAttempt] = @ + 1]
    /\ UNCHANGED <<jobState, currentAttempt, reconcileState, heldReservation, outputObserved, resultEvidence>>

LoseDispatchKnowledge ==
    /\ jobState = "admitted"
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] = "running"
    /\ attemptState' = [attemptState EXCEPT ![currentAttempt] = "ambiguous"]
    /\ jobState' = "ambiguous"
    /\ reconcileState' = "required"
    /\ UNCHANGED <<currentAttempt, dispatchCount, heldReservation, outputObserved, resultEvidence>>

(* A physical orphan has no selected current Attempt, yet its durable *)
(* held reservation forbids blind admission/retry until proven absent.   *)
ObserveOrphanedHeld ==
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] \in {"admitted", "running", "ambiguous"}
    /\ attemptState' = [attemptState EXCEPT ![currentAttempt] = "orphanedHeld"]
    /\ currentAttempt' = NoAttempt
    /\ jobState' = "ambiguous"
    /\ reconcileState' = "required"
    /\ heldReservation' = TRUE
    /\ UNCHANGED <<dispatchCount, outputObserved, resultEvidence>>

ReconcileHeldOrphanProvenAbsent ==
    /\ jobState = "ambiguous"
    /\ currentAttempt = NoAttempt
    /\ reconcileState = "required"
    /\ \E a \in Attempts:
        /\ attemptState[a] = "orphanedHeld"
        /\ attemptState' = [attemptState EXCEPT ![a] = "lost"]
    /\ jobState' = "admitted"
    /\ reconcileState' = "absent"
    /\ heldReservation' = FALSE
    /\ UNCHANGED <<currentAttempt, dispatchCount, outputObserved, resultEvidence>>


(* Output bytes exist independently of exact terminal result provenance. *)
PublishPartialOutput ==
    /\ jobState = "admitted"
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] = "running"
    /\ ~outputObserved[currentAttempt]
    /\ outputObserved' = [outputObserved EXCEPT ![currentAttempt] = TRUE]
    /\ UNCHANGED <<jobState, attemptState, currentAttempt, dispatchCount, reconcileState, heldReservation, resultEvidence>>

(* CEGAR: foreign evidence is possible, but cannot authorize this Attempt. *)
ObserveResultEvidence ==
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] \in {"running", "ambiguous"}
    /\ resultEvidence[currentAttempt] = "none"
    /\ \E standing \in {"foreign", "matching"}:
         resultEvidence' = [resultEvidence EXCEPT ![currentAttempt] = standing]
    /\ UNCHANGED <<jobState, attemptState, currentAttempt, dispatchCount, reconcileState, heldReservation, outputObserved>>

(* Rejected evidence is an external observation, not a durable
   incompatibility of the selected Attempt. A later exact matching result
   may correct it; this is a possible bounded transition, not fairness. *)
CorrectForeignResultEvidence ==
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] \in {"running", "ambiguous"}
    /\ resultEvidence[currentAttempt] = "foreign"
    /\ resultEvidence' = [resultEvidence EXCEPT ![currentAttempt] = "matching"]
    /\ UNCHANGED <<jobState, attemptState, currentAttempt, dispatchCount,
                  reconcileState, heldReservation, outputObserved>>

ObserveTerminalEvidence ==
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] \in {"running", "ambiguous"}
    /\ resultEvidence[currentAttempt] = "matching"
    /\ attemptState' = [attemptState EXCEPT ![currentAttempt] = "terminal"]
    /\ jobState' = "terminal"
    /\ reconcileState' = "committed"
    (* SQL commit_terminal clears jobs.current_attempt_id in the same CAS. *)
    /\ currentAttempt' = NoAttempt
    /\ UNCHANGED <<dispatchCount, heldReservation, outputObserved, resultEvidence>>

ReconcileProvenAbsent ==
    /\ jobState = "ambiguous"
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] = "ambiguous"
    /\ reconcileState = "required"
    /\ attemptState' = [attemptState EXCEPT ![currentAttempt] = "lost"]
    /\ jobState' = "admitted"
    /\ currentAttempt' = NoAttempt
    /\ reconcileState' = "absent"
    /\ UNCHANGED <<dispatchCount, heldReservation, outputObserved, resultEvidence>>

AdmitExplicitRetry ==
    /\ jobState = "admitted"
    /\ currentAttempt = NoAttempt
    /\ reconcileState = "absent"
    /\ \E a \in Attempts:
        /\ attemptState[a] = "unused"
        /\ attemptState' = [attemptState EXCEPT ![a] = "admitted"]
        /\ currentAttempt' = a
    /\ reconcileState' = "none"
    /\ UNCHANGED <<jobState, dispatchCount, heldReservation, outputObserved, resultEvidence>>

Next ==
    \/ Admit
    \/ Dispatch
    \/ LoseDispatchKnowledge
    \/ PublishPartialOutput
    \/ ObserveResultEvidence
    \/ CorrectForeignResultEvidence
    \/ ObserveOrphanedHeld
    \/ ReconcileHeldOrphanProvenAbsent
    \/ ObserveTerminalEvidence
    \/ ReconcileProvenAbsent
    \/ AdmitExplicitRetry

Spec == Init /\ [][Next]_vars


\* Liveness is separate from at-most-once safety. Fair admission, dispatch
\* and observable first outcome give a first decision, not domain completion.
FairSpec ==
    Spec
    /\ WF_vars(Admit)
    /\ WF_vars(Dispatch)
    /\ WF_vars(ObserveTerminalEvidence \/ LoseDispatchKnowledge)

ProgressToFirstDecision ==
    <> (jobState = "terminal" \/ jobState = "ambiguous")

AtMostOnceDispatchPerAttempt ==
    \A a \in Attempts : dispatchCount[a] <= 1

(* Safety across distinct Attempt identities: no second unresolved live Attempt. *)
LiveAttemptStates == {"admitted", "running", "ambiguous"}

NoCompetingLiveAttempts ==
    \A a \in Attempts:
        \A b \in Attempts:
            a # b =>
                ~(attemptState[a] \in LiveAttemptStates
                  /\ attemptState[b] \in LiveAttemptStates)

(* One detached unresolved Attempt is a defect before any retry occurs. *)
NoDetachedLiveAttempt ==
    \A a \in Attempts:
        attemptState[a] \in LiveAttemptStates => currentAttempt = a

(* An orphaned-held record is unresolved even if no Attempt pointer *)
(* remains; it must not become dispatch-eligible or appear accepted.     *)
(* The one-Job abstraction needs only one extra bit for the physical *)
(* held-orphan capacity fence; selection and reservation are not equal. *)
HeldOrphanIsFenced ==
    /\ (heldReservation <=> (\E a \in Attempts: attemptState[a] = "orphanedHeld"))
    /\ (heldReservation =>
           /\ currentAttempt = NoAttempt
           /\ jobState = "ambiguous"
           /\ reconcileState = "required")

AmbiguityRequiresReconciliation ==
    jobState = "ambiguous" =>
        /\ reconcileState = "required"
        /\ (\/ /\ currentAttempt # NoAttempt
               /\ attemptState[currentAttempt] = "ambiguous"
            \/ /\ currentAttempt = NoAttempt
               /\ \E a \in Attempts: attemptState[a] = "orphanedHeld")

NoUnusedAttemptWasDispatched ==
    \A a \in Attempts : attemptState[a] = "unused" => dispatchCount[a] = 0

TerminalAttemptWasDispatched ==
    \A a \in Attempts : attemptState[a] = "terminal" => dispatchCount[a] = 1

MatchingResultRequiredForTerminal ==
    jobState = "terminal" =>
        /\ currentAttempt = NoAttempt
        /\ \E a \in Attempts:
            /\ attemptState[a] = "terminal"
            /\ resultEvidence[a] = "matching"

NoForeignResultIsTerminal ==
    \A a \in Attempts: attemptState[a] = "terminal" => resultEvidence[a] = "matching"

(* A rejected foreign result is not a proof that no matching result can
   later be qualified for the same live Attempt. ENABLED is NOT eventuality. *)
ForeignResultDoesNotDisableMatchingRecovery ==
    (currentAttempt # NoAttempt
     /\ attemptState[currentAttempt] \in {"running", "ambiguous"}
     /\ resultEvidence[currentAttempt] = "foreign")
    => ENABLED CorrectForeignResultEvidence

(* Intentionally false reachability probe; not admitted as a safety law. *)
ForeignResultIsUnreachable ==
    \A a \in Attempts: resultEvidence[a] # "foreign"

TerminalEvidenceIsCommitted ==
    jobState = "terminal" =>
        /\ currentAttempt = NoAttempt
        /\ reconcileState = "committed"
        /\ \E a \in Attempts: attemptState[a] = "terminal"

=============================================================================
