---- MODULE Lego21OwnerBoundary ----
EXTENDS Naturals

(***************************************************************************)
(* Tiny owner-composition model. The execution/network/domain owners are   *)
(* independent: an observation or Tool proposal is not effect authority.   *)
(* This is a bounded model, NOT an implementation-refinement proof.         *)
(***************************************************************************)

CONSTANTS RequiresHarness, RequiresNetwork

VARIABLES host, harness, network, runtime, dispatchCount, consumerEvidence,
          sourceEvidenceBinding, admissionInputsWitness, terminalReceipt,
          receiptAttemptBinding

vars == <<host, harness, network, runtime, dispatchCount, consumerEvidence,
          sourceEvidenceBinding, admissionInputsWitness, terminalReceipt,
          receiptAttemptBinding>>

HostStates == {"open", "accepted"}
HarnessStates == {"idle", "proposed"}
NetworkStates == {"unknown", "ready"}
RuntimeStates == {"idle", "admitted", "running", "ambiguous", "terminal"}
EvidenceStates == {"none", "matching", "foreign"}
SourceBindingStates == {"none", "admission-bound", "different-source"}
ReceiptStates == {"none", "pending", "committed"}
ReceiptAttemptBindings == {"none", "foreign", "attempt-bound"}

TypeOK ==
    /\ RequiresHarness \in BOOLEAN
    /\ RequiresNetwork \in BOOLEAN
    /\ host \in HostStates
    /\ harness \in HarnessStates
    /\ network \in NetworkStates
    /\ runtime \in RuntimeStates
    /\ dispatchCount \in 0..2
    /\ consumerEvidence \in EvidenceStates
    /\ sourceEvidenceBinding \in SourceBindingStates
    /\ admissionInputsWitness \in BOOLEAN
    /\ terminalReceipt \in ReceiptStates
    /\ receiptAttemptBinding \in ReceiptAttemptBindings

Init ==
    /\ host = "open"
    /\ harness = "idle"
    /\ network = "unknown"
    /\ runtime = "idle"
    /\ dispatchCount = 0
    /\ consumerEvidence = "none"
    /\ sourceEvidenceBinding = "none"
    /\ admissionInputsWitness = FALSE
    /\ terminalReceipt = "none"
    /\ receiptAttemptBinding = "none"

NetworkObserve ==
    /\ network = "unknown"
    /\ network' = "ready"
    /\ UNCHANGED <<host, harness, runtime, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness, terminalReceipt, receiptAttemptBinding>>

NetworkDegrade ==
    /\ network = "ready"
    /\ network' = "unknown"
    /\ UNCHANGED <<host, harness, runtime, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness, terminalReceipt, receiptAttemptBinding>>

HarnessPropose ==
    /\ harness = "idle"
    /\ harness' = "proposed"
    /\ UNCHANGED <<host, network, runtime, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness, terminalReceipt, receiptAttemptBinding>>

RuntimeAdmit ==
    /\ runtime = "idle"
    /\ (~RequiresHarness \/ harness = "proposed")
    /\ (~RequiresNetwork \/ network = "ready")
    /\ runtime' = "admitted"
    /\ admissionInputsWitness' =
        /\ (~RequiresHarness \/ harness = "proposed")
        /\ (~RequiresNetwork \/ network = "ready")
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence, sourceEvidenceBinding, terminalReceipt, receiptAttemptBinding>>

RuntimeDispatch ==
    /\ runtime = "admitted"
    /\ dispatchCount = 0
    /\ runtime' = "running"
    /\ dispatchCount' = dispatchCount + 1
    /\ UNCHANGED <<host, harness, network, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness, terminalReceipt, receiptAttemptBinding>>

RuntimeLoseKnowledge ==
    /\ runtime = "running"
    /\ runtime' = "ambiguous"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness, terminalReceipt, receiptAttemptBinding>>

RuntimeObserveTerminal ==
    /\ runtime \in {"running", "ambiguous"}
    /\ runtime' = "terminal"
    /\ terminalReceipt' = "pending"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness, receiptAttemptBinding>>

(* A durable terminal result is not identical to observing terminal state. *)
RuntimeCommitTerminal ==
    /\ runtime = "terminal"
    /\ terminalReceipt = "pending"
    /\ terminalReceipt' = "committed"
    /\ UNCHANGED <<host, harness, network, runtime, dispatchCount,
                  consumerEvidence, sourceEvidenceBinding, admissionInputsWitness, receiptAttemptBinding>>

(* Counterexample input: an externally presented receipt for another Attempt.
   This is NOT a Runtime-authorized CommitTerminal transition. A boolean
   "receipt present" abstraction would wrongly allow Host acceptance. *)
RuntimeObserveForeignReceipt ==
    /\ host = "open"
    /\ runtime = "terminal"
    /\ terminalReceipt \in {"pending", "committed"}
    /\ receiptAttemptBinding \in {"none", "attempt-bound"}
    /\ receiptAttemptBinding' = "foreign"
    /\ UNCHANGED <<host, harness, network, runtime, dispatchCount,
                  consumerEvidence, sourceEvidenceBinding, admissionInputsWitness,
                  terminalReceipt>>

(* Separate authoritative Runtime commit from an adversarial presentation.
   The actual owner must bind the exact committed Attempt and SourceCut; this
   abstract transition does not itself prove that implementation bridge. *)
RuntimeBindCommittedReceipt ==
    /\ runtime = "terminal"
    /\ terminalReceipt = "committed"
    /\ receiptAttemptBinding \in {"none", "foreign"}
    /\ receiptAttemptBinding' = "attempt-bound"
    /\ UNCHANGED <<host, harness, network, runtime, dispatchCount,
                  consumerEvidence, sourceEvidenceBinding, admissionInputsWitness,
                  terminalReceipt>>

ConsumerObserve ==
    /\ runtime = "terminal"
    /\ consumerEvidence = "none"
    /\ sourceEvidenceBinding = "none"
    (* Evidence can belong to this Work or a different consumer. *)
    /\ consumerEvidence' \in {"matching", "foreign"}
    (* Abstract admission SourceCut binding; not a live digest check. *)
    /\ sourceEvidenceBinding' \in {"admission-bound", "different-source"}
    /\ UNCHANGED <<host, harness, network, runtime, dispatchCount,
                  admissionInputsWitness, terminalReceipt, receiptAttemptBinding>>

HostAccept ==
    /\ host = "open"
    /\ runtime = "terminal"
    (* A foreign Work's valid result is NOT evidence for this Work. *)
    /\ consumerEvidence = "matching"
    /\ sourceEvidenceBinding = "admission-bound"
    /\ terminalReceipt = "committed"
    /\ receiptAttemptBinding = "attempt-bound"
    /\ host' = "accepted"
    /\ UNCHANGED <<harness, network, runtime, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness, terminalReceipt, receiptAttemptBinding>>

Next ==
    \/ NetworkObserve
    \/ NetworkDegrade
    \/ HarnessPropose
    \/ RuntimeAdmit
    \/ RuntimeDispatch
    \/ RuntimeLoseKnowledge
    \/ RuntimeObserveTerminal
    \/ RuntimeCommitTerminal
    \/ RuntimeObserveForeignReceipt
    \/ RuntimeBindCommittedReceipt
    \/ ConsumerObserve
    \/ HostAccept

Spec == Init /\ [][Next]_vars

AtMostOnePhysicalDispatch == dispatchCount <= 1

NoHostAcceptanceFromRuntimeAlone ==
    host = "accepted" => (runtime = "terminal" /\ consumerEvidence = "matching")

(***************************************************************************)
(* Physical dispatch requires the admission-time witness. Route readiness  *)
(* can later disappear; a current network reading cannot rewrite history.  *)
(* This boolean models the existence of admitted evidence, not live TLS or *)
(* actual effect authorization.                                             *)
(***************************************************************************)
NoDispatchWithoutRequiredInputs ==
    dispatchCount > 0 => admissionInputsWitness

AmbiguityCannotBeTreatedAsCompletion ==
    runtime = "ambiguous" => (host = "open" /\ consumerEvidence = "none" /\ dispatchCount = 1)

NoHostAcceptanceWithoutConsumerEvidence ==
    consumerEvidence # "matching" => host = "open"

NoHostAcceptanceWithWrongSource ==
    sourceEvidenceBinding # "admission-bound" => host = "open"

(* Correct Work/SourceCut evidence does not establish a durable Runtime finish. *)
NoHostAcceptanceWithoutCommittedTerminalReceipt ==
    host = "accepted" => terminalReceipt = "committed"

NoHostAcceptanceWithoutAttemptBoundReceipt ==
    host = "accepted" => receiptAttemptBinding = "attempt-bound"

(* A foreign presented receipt is untrusted evidence, not an authoritative
   Runtime commit mutation. Even when an attacker has presented one, the
   exact source/Attempt-qualified recovery step remains ENABLED. This is a
   local option invariant, not fairness or eventual recovery. *)
NoForeignReceiptBlocksLocalRecovery ==
    (runtime = "terminal" /\ terminalReceipt = "committed"
      /\ receiptAttemptBinding = "foreign" /\ host = "open")
    => ENABLED RuntimeBindCommittedReceipt

(* False reachability assertion: matching source and Work may predate commit. *)
PendingMatchedTerminalReceiptIsUnreachable ==
    ~(runtime = "terminal" /\ terminalReceipt = "pending"
      /\ consumerEvidence = "matching"
      /\ sourceEvidenceBinding = "admission-bound" /\ host = "open")

(***************************************************************************)
(* Intentionally FALSE non-vacuity probe, not an admitted safety invariant. *)
(* The standalone probe cfg must find a post-admission NetworkDegrade path. *)
(***************************************************************************)
NetworkNeverDegradesAfterAdmission ==
    ~(
        network = "unknown"
        /\ runtime \in {"admitted", "running", "ambiguous", "terminal"}
        /\ admissionInputsWitness
    )

(***************************************************************************)
(* Intentionally FALSE reachability probe, not an admitted safety law.    *)
(* TLC must find an actual foreign consumer witness or the model is empty. *)
(***************************************************************************)
ForeignEvidenceIsUnreachable ==
    consumerEvidence # "foreign"

(* Deliberately false reachability probe: a foreign Attempt receipt must
   be representable, even while domain evidence matches this Work+SourceCut. *)
ForeignTerminalReceiptIsUnreachable ==
    ~(terminalReceipt = "committed"
      /\ receiptAttemptBinding = "foreign"
      /\ consumerEvidence = "matching"
      /\ sourceEvidenceBinding = "admission-bound"
      /\ host = "open")


(* Intentionally false negative oracle: a matching Work can have wrong source. *)
WrongSourceEvidenceIsUnreachable ==
    ~(consumerEvidence = "matching" /\ sourceEvidenceBinding = "different-source")

=============================================================================
