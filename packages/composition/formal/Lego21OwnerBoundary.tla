---- MODULE Lego21OwnerBoundary ----
EXTENDS Naturals

(***************************************************************************)
(* Tiny owner-composition model. The execution/network/domain owners are   *)
(* independent: an observation or Tool proposal is not effect authority.   *)
(* This is a bounded model, NOT an implementation-refinement proof.         *)
(***************************************************************************)

CONSTANTS RequiresHarness, RequiresNetwork

VARIABLES host, harness, network, runtime, dispatchCount, consumerEvidence,
          admissionInputsWitness, terminalReceipt

vars == <<host, harness, network, runtime, dispatchCount, consumerEvidence,
          admissionInputsWitness, terminalReceipt>>

HostStates == {"open", "accepted"}
HarnessStates == {"idle", "proposed"}
NetworkStates == {"unknown", "ready"}
RuntimeStates == {"idle", "admitted", "running", "ambiguous", "terminal"}
EvidenceStates == {"none", "matching", "foreign"}
(* Runtime's observed terminal state is not its durable terminal receipt. *)
ReceiptStates == {"none", "pending", "committed"}

TypeOK ==
    /\ RequiresHarness \in BOOLEAN
    /\ RequiresNetwork \in BOOLEAN
    /\ host \in HostStates
    /\ harness \in HarnessStates
    /\ network \in NetworkStates
    /\ runtime \in RuntimeStates
    /\ dispatchCount \in 0..2
    /\ consumerEvidence \in EvidenceStates
    /\ admissionInputsWitness \in BOOLEAN
    /\ terminalReceipt \in ReceiptStates

Init ==
    /\ host = "open"
    /\ harness = "idle"
    /\ network = "unknown"
    /\ runtime = "idle"
    /\ dispatchCount = 0
    /\ consumerEvidence = "none"
    /\ admissionInputsWitness = FALSE
    /\ terminalReceipt = "none"

NetworkObserve ==
    /\ network = "unknown"
    /\ network' = "ready"
    /\ UNCHANGED <<host, harness, runtime, dispatchCount, consumerEvidence,
                  admissionInputsWitness, terminalReceipt>>

NetworkDegrade ==
    /\ network = "ready"
    /\ network' = "unknown"
    /\ UNCHANGED <<host, harness, runtime, dispatchCount, consumerEvidence,
                  admissionInputsWitness, terminalReceipt>>

HarnessPropose ==
    /\ harness = "idle"
    /\ harness' = "proposed"
    /\ UNCHANGED <<host, network, runtime, dispatchCount, consumerEvidence,
                  admissionInputsWitness, terminalReceipt>>

RuntimeAdmit ==
    /\ runtime = "idle"
    /\ (~RequiresHarness \/ harness = "proposed")
    /\ (~RequiresNetwork \/ network = "ready")
    /\ runtime' = "admitted"
    /\ admissionInputsWitness' =
        /\ (~RequiresHarness \/ harness = "proposed")
        /\ (~RequiresNetwork \/ network = "ready")
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence,
                  terminalReceipt>>

RuntimeDispatch ==
    /\ runtime = "admitted"
    /\ dispatchCount = 0
    /\ runtime' = "running"
    /\ dispatchCount' = dispatchCount + 1
    /\ UNCHANGED <<host, harness, network, consumerEvidence,
                  admissionInputsWitness, terminalReceipt>>

RuntimeLoseKnowledge ==
    /\ runtime = "running"
    /\ runtime' = "ambiguous"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence,
                  admissionInputsWitness, terminalReceipt>>

RuntimeObserveTerminal ==
    /\ runtime \in {"running", "ambiguous"}
    /\ runtime' = "terminal"
    /\ terminalReceipt' = "pending"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence,
                  admissionInputsWitness>>

(* A source/Attempt-bound durable finish is separate from observing terminal. *)
RuntimeCommitTerminal ==
    /\ runtime = "terminal"
    /\ terminalReceipt = "pending"
    /\ terminalReceipt' = "committed"
    /\ UNCHANGED <<host, harness, network, runtime, dispatchCount,
                  consumerEvidence, admissionInputsWitness>>

ConsumerObserve ==
    /\ runtime = "terminal"
    /\ consumerEvidence = "none"
    (* Evidence can belong to this Work or a different consumer. *)
    /\ consumerEvidence' \in {"matching", "foreign"}
    /\ UNCHANGED <<host, harness, network, runtime, dispatchCount,
                  admissionInputsWitness, terminalReceipt>>

HostAccept ==
    /\ host = "open"
    /\ runtime = "terminal"
    (* A foreign Work's valid result is NOT evidence for this Work. *)
    /\ consumerEvidence = "matching"
    /\ terminalReceipt = "committed"
    /\ host' = "accepted"
    /\ UNCHANGED <<harness, network, runtime, dispatchCount, consumerEvidence,
                  admissionInputsWitness, terminalReceipt>>

Next ==
    \/ NetworkObserve
    \/ NetworkDegrade
    \/ HarnessPropose
    \/ RuntimeAdmit
    \/ RuntimeDispatch
    \/ RuntimeLoseKnowledge
    \/ RuntimeObserveTerminal
    \/ RuntimeCommitTerminal
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

(* A matching domain response alone cannot promote an uncommitted Runtime
   terminal observation into accepted Host Work. *)
NoHostAcceptanceWithoutCommittedTerminalReceipt ==
    host = "accepted" => terminalReceipt = "committed"

(* Intentionally false non-vacuity probe: the mismatch must be reachable
   before the durable finish is committed, or the new guard is vacuous. *)
PendingMatchedTerminalReceiptIsUnreachable ==
    ~(runtime = "terminal" /\ terminalReceipt = "pending"
      /\ consumerEvidence = "matching" /\ host = "open")

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

=============================================================================
