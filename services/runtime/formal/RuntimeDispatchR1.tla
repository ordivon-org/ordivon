---- MODULE RuntimeDispatchR1 ----
EXTENDS Naturals

(***************************************************************************)
(* Standards-first formal model for the narrow Runtime dispatch boundary.   *)
(* It deliberately does not model workflow/business-process state.          *)
(***************************************************************************)

CONSTANTS Attempts, NoAttempt

AttemptStates == {"unused", "admitted", "running", "ambiguous", "lost", "terminal"}
JobStates == {"none", "admitted", "ambiguous", "terminal"}
ReconcileStates == {"none", "required", "absent", "committed"}

VARIABLES jobState, attemptState, currentAttempt, dispatchCount, reconcileState

vars == <<jobState, attemptState, currentAttempt, dispatchCount, reconcileState>>

TypeOK ==
    /\ Attempts # {}
    /\ NoAttempt \notin Attempts
    /\ jobState \in JobStates
    /\ attemptState \in [Attempts -> AttemptStates]
    /\ currentAttempt \in Attempts \cup {NoAttempt}
    /\ dispatchCount \in [Attempts -> 0..2]
    /\ reconcileState \in ReconcileStates

Init ==
    /\ jobState = "none"
    /\ attemptState = [a \in Attempts |-> "unused"]
    /\ currentAttempt = NoAttempt
    /\ dispatchCount = [a \in Attempts |-> 0]
    /\ reconcileState = "none"

Admit ==
    /\ jobState = "none"
    /\ currentAttempt = NoAttempt
    /\ \E a \in Attempts:
        /\ attemptState[a] = "unused"
        /\ attemptState' = [attemptState EXCEPT ![a] = "admitted"]
        /\ currentAttempt' = a
    /\ jobState' = "admitted"
    /\ reconcileState' = "none"
    /\ UNCHANGED dispatchCount

Dispatch ==
    /\ jobState = "admitted"
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] = "admitted"
    /\ dispatchCount[currentAttempt] = 0
    /\ attemptState' = [attemptState EXCEPT ![currentAttempt] = "running"]
    /\ dispatchCount' = [dispatchCount EXCEPT ![currentAttempt] = @ + 1]
    /\ UNCHANGED <<jobState, currentAttempt, reconcileState>>

LoseDispatchKnowledge ==
    /\ jobState = "admitted"
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] = "running"
    /\ attemptState' = [attemptState EXCEPT ![currentAttempt] = "ambiguous"]
    /\ jobState' = "ambiguous"
    /\ reconcileState' = "required"
    /\ UNCHANGED <<currentAttempt, dispatchCount>>

ObserveTerminalEvidence ==
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] \in {"running", "ambiguous"}
    /\ attemptState' = [attemptState EXCEPT ![currentAttempt] = "terminal"]
    /\ jobState' = "terminal"
    /\ reconcileState' = "committed"
    /\ UNCHANGED <<currentAttempt, dispatchCount>>

ReconcileProvenAbsent ==
    /\ jobState = "ambiguous"
    /\ currentAttempt # NoAttempt
    /\ attemptState[currentAttempt] = "ambiguous"
    /\ reconcileState = "required"
    /\ attemptState' = [attemptState EXCEPT ![currentAttempt] = "lost"]
    /\ jobState' = "admitted"
    /\ currentAttempt' = NoAttempt
    /\ reconcileState' = "absent"
    /\ UNCHANGED dispatchCount

AdmitExplicitRetry ==
    /\ jobState = "admitted"
    /\ currentAttempt = NoAttempt
    /\ reconcileState = "absent"
    /\ \E a \in Attempts:
        /\ attemptState[a] = "unused"
        /\ attemptState' = [attemptState EXCEPT ![a] = "admitted"]
        /\ currentAttempt' = a
    /\ reconcileState' = "none"
    /\ UNCHANGED <<jobState, dispatchCount>>

Next ==
    \/ Admit
    \/ Dispatch
    \/ LoseDispatchKnowledge
    \/ ObserveTerminalEvidence
    \/ ReconcileProvenAbsent
    \/ AdmitExplicitRetry

Spec == Init /\ [][Next]_vars

AtMostOnceDispatchPerAttempt ==
    \A a \in Attempts : dispatchCount[a] <= 1

AmbiguityRequiresReconciliation ==
    jobState = "ambiguous" =>
        /\ currentAttempt # NoAttempt
        /\ attemptState[currentAttempt] = "ambiguous"
        /\ reconcileState = "required"

NoUnusedAttemptWasDispatched ==
    \A a \in Attempts : attemptState[a] = "unused" => dispatchCount[a] = 0

TerminalAttemptWasDispatched ==
    \A a \in Attempts : attemptState[a] = "terminal" => dispatchCount[a] = 1

=============================================================================
