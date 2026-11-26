---- MODULE ToolUnknownRecoveryR1 ----
EXTENDS Naturals

(***************************************************************************)
(* Bounded logical LEGO for the original Harness PG ToolStep vs the       *)
(* independent installed Gateway/Runtime Owner.                            *)
(* Source consumers: loop.py, run_continuity.py and independent_result.py. *)
(* Real source qualification: test_gateway_cli_consumer.py and the         *)
(* opt-in test_live_gateway_unknown_recovery.py physical Owner test.       *)
(* This is NOT a SQL/Runtime implementation refinement or liveness proof.  *)
(***************************************************************************)

Phases == {"new", "intent", "sent", "unknown", "paused", "observed", "completed"}
Receipts == {"none", "unknown", "observed"}
PauseReasons == {"none", "effect-dispatch-pending"}
OwnerJobs == {"none", "original"}

VARIABLES phase, receipt, pauseReason, ownerJob, submissions,
          ownerReachable, reconciled, nextKey

vars == <<phase, receipt, pauseReason, ownerJob, submissions,
          ownerReachable, reconciled, nextKey>>

firstVars == <<phase, receipt, pauseReason, ownerJob, submissions, ownerReachable, reconciled>>

TypeOK ==
    /\ phase \in Phases
    /\ receipt \in Receipts
    /\ pauseReason \in PauseReasons
    /\ ownerJob \in OwnerJobs
    /\ submissions \in 0..2
    /\ ownerReachable \in BOOLEAN
    /\ reconciled \in BOOLEAN
    /\ nextKey \in {"none", "fresh", "reused"}

Init ==
    /\ phase = "new"
    /\ receipt = "none"
    /\ pauseReason = "none"
    /\ ownerJob = "none"
    /\ submissions = 0
    /\ ownerReachable = FALSE
    /\ reconciled = FALSE
    /\ nextKey = "none"

FreezeOriginalPgIntent ==
    /\ phase = "new"
    /\ phase' = "intent"
    /\ UNCHANGED <<receipt, pauseReason, ownerJob, submissions,
                  ownerReachable, reconciled>>

(* This abstracts one concrete Owner-admitted effect, not a generic retry. *)
SubmitOriginalOwner ==
    /\ phase = "intent"
    /\ submissions = 0
    /\ phase' = "sent"
    /\ ownerJob' = "original"
    /\ submissions' = 1
    /\ UNCHANGED <<receipt, pauseReason, ownerReachable, reconciled>>

(* Reply may disappear before any Owner Job is admitted. Unknown is NOT absent. *)
LoseBeforeOwnerAdmission ==
    /\ phase = "intent"
    /\ phase' = "unknown"
    /\ receipt' = "unknown"
    /\ UNCHANGED <<pauseReason, ownerJob, submissions,
                  ownerReachable, reconciled>>

LoseOwnerReply ==
    /\ phase = "sent"
    /\ phase' = "unknown"
    /\ receipt' = "unknown"
    /\ UNCHANGED <<pauseReason, ownerJob, submissions,
                  ownerReachable, reconciled>>

ReceiveOriginalOwnerReceipt ==
    /\ phase = "sent"
    /\ ownerJob = "original"
    /\ phase' = "observed"
    /\ receipt' = "observed"
    /\ UNCHANGED <<pauseReason, ownerJob, submissions,
                  ownerReachable, reconciled>>

CommitOriginalUnknownPause ==
    /\ phase = "unknown"
    /\ receipt = "unknown"
    /\ phase' = "paused"
    /\ pauseReason' = "effect-dispatch-pending"
    /\ UNCHANGED <<receipt, ownerJob, submissions,
                  ownerReachable, reconciled>>

(* The same original Owner may later become queryable. *)
RestoreOwnerReadability ==
    /\ phase = "paused"
    /\ ~ownerReachable
    /\ ownerReachable' = TRUE
    /\ UNCHANGED <<phase, receipt, pauseReason, ownerJob, submissions,
                  reconciled>>

(* Only original Owner evidence allows the existing Run to continue. *)
ResolveOriginalOwner ==
    /\ phase = "paused"
    /\ ownerReachable
    /\ ownerJob = "original"
    /\ submissions = 1
    /\ phase' = "observed"
    /\ receipt' = "observed"
    /\ pauseReason' = "none"
    /\ reconciled' = TRUE
    /\ UNCHANGED <<ownerJob, submissions, ownerReachable>>

CompleteBoundedRun ==
    /\ phase = "observed"
    /\ receipt = "observed"
    /\ phase' = "completed"
    /\ UNCHANGED <<receipt, pauseReason, ownerJob, submissions,
                  ownerReachable, reconciled>>

(* Terminal bounded Run and unresolved no-Owner read remain quiescent.
   This is not an invented progress/liveness transition. *)
QuiesceWithoutNewOwnerEffect ==
    /\ (phase = "completed"
        \/ (phase = "paused" /\ ownerReachable /\ ownerJob = "none"))
    /\ UNCHANGED firstVars

FirstNext ==
    \/ FreezeOriginalPgIntent
    \/ SubmitOriginalOwner
    \/ LoseBeforeOwnerAdmission
    \/ LoseOwnerReply
    \/ ReceiveOriginalOwnerReceipt
    \/ CommitOriginalUnknownPause
    \/ RestoreOwnerReadability
    \/ ResolveOriginalOwner
    \/ CompleteBoundedRun
    \/ QuiesceWithoutNewOwnerEffect

(* R39: first observed Tool remains a source identity after settlement.
   Model stops at a second prepared Intent; no claim of its physical effect. *)
PrepareFreshNext ==
    /\ phase = "observed"
    /\ nextKey = "none"
    /\ nextKey' = "fresh"
    /\ UNCHANGED firstVars

QuiesceAtNextAdmission ==
    /\ nextKey # "none"
    /\ UNCHANGED vars

Next ==
    \/ /\ nextKey = "none"
       /\ FirstNext
       /\ UNCHANGED nextKey
    \/ PrepareFreshNext
    \/ QuiesceAtNextAdmission

Spec == Init /\ [][Next]_vars

NoReusedRequestIdentity == nextKey # "reused"
FreshNextIsUnreachable == nextKey # "fresh"

UnsafePrepareReusedNext ==
    /\ phase = "observed"
    /\ nextKey = "none"
    /\ nextKey' = "reused"
    /\ UNCHANGED firstVars

BadKeyNext == Next \/ UnsafePrepareReusedNext
BadKeySpec == Init /\ [][BadKeyNext]_vars

AtMostOneOriginalOwnerSubmit == submissions <= 1
NoObservationWithoutOriginalOwner ==
    phase \in {"observed", "completed"} =>
      /\ receipt = "observed"
      /\ ownerJob = "original"
      /\ submissions = 1
NoPausedResultWithoutUnknown ==
    phase = "paused" =>
      /\ receipt = "unknown"
      /\ pauseReason = "effect-dispatch-pending"
NoUnknownEquivalentToCompleted ==
    receipt = "unknown" => phase \notin {"observed", "completed"}
ReconciliationRequiresOriginalOwner ==
    reconciled => /\ ownerJob = "original"
                  /\ submissions = 1
                  /\ phase \in {"observed", "completed"}

(***************************************************************************)
(* Unsafe, deliberately excluded action: a second native effect after     *)
(* ambiguous delivery. BadSpec must falsify AtMostOneOriginalOwnerSubmit.  *)
(* This guards against vacuous "no effects ever happen" safety tests.      *)
(***************************************************************************)
UnsafeRetryAfterUnknown ==
    /\ phase = "paused"
    /\ ownerJob = "original"
    /\ submissions = 1
    /\ submissions' = 2
    /\ phase' = "sent"
    /\ receipt' = "none"
    /\ pauseReason' = "none"
    /\ UNCHANGED <<ownerJob, ownerReachable, reconciled>>

BadNext == Next \/ (/\ nextKey = "none" /\ UnsafeRetryAfterUnknown /\ UNCHANGED nextKey)
BadSpec == Init /\ [][BadNext]_vars

(* Deliberately FALSE reachability predicates for independent controls. *)
RecoveredOriginalOwnerIsUnreachable ==
    ~(phase = "completed" /\ reconciled /\ submissions = 1)
LostBeforeAdmissionIsUnreachable ==
    ~(phase = "paused" /\ ownerJob = "none" /\ submissions = 0)
PhysicalCallIsUnreachable == ~(submissions = 1)

=============================================================================
