---- MODULE Lego21OwnerBoundary ----
EXTENDS Naturals

(***************************************************************************)
(* Tiny owner-composition model. The execution/network/domain owners are   *)
(* independent: an observation or Tool proposal is not effect authority.   *)
(* This is a bounded model, NOT an implementation-refinement proof.         *)
(***************************************************************************)

CONSTANTS RequiresHarness, RequiresNetwork

VARIABLES host, harness, network, runtime, dispatchCount, consumerEvidence,
          sourceEvidenceBinding, admissionInputsWitness

vars == <<host, harness, network, runtime, dispatchCount, consumerEvidence,
          sourceEvidenceBinding, admissionInputsWitness>>

HostStates == {"open", "accepted"}
HarnessStates == {"idle", "proposed"}
NetworkStates == {"unknown", "ready"}
RuntimeStates == {"idle", "admitted", "running", "ambiguous", "terminal"}
EvidenceStates == {"none", "matching", "foreign"}
SourceBindingStates == {"none", "admission-bound", "different-source"}

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

Init ==
    /\ host = "open"
    /\ harness = "idle"
    /\ network = "unknown"
    /\ runtime = "idle"
    /\ dispatchCount = 0
    /\ consumerEvidence = "none"
    /\ sourceEvidenceBinding = "none"
    /\ admissionInputsWitness = FALSE

NetworkObserve ==
    /\ network = "unknown"
    /\ network' = "ready"
    /\ UNCHANGED <<host, harness, runtime, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness>>

NetworkDegrade ==
    /\ network = "ready"
    /\ network' = "unknown"
    /\ UNCHANGED <<host, harness, runtime, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness>>

HarnessPropose ==
    /\ harness = "idle"
    /\ harness' = "proposed"
    /\ UNCHANGED <<host, network, runtime, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness>>

RuntimeAdmit ==
    /\ runtime = "idle"
    /\ (~RequiresHarness \/ harness = "proposed")
    /\ (~RequiresNetwork \/ network = "ready")
    /\ runtime' = "admitted"
    /\ admissionInputsWitness' =
        /\ (~RequiresHarness \/ harness = "proposed")
        /\ (~RequiresNetwork \/ network = "ready")
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence, sourceEvidenceBinding>>

RuntimeDispatch ==
    /\ runtime = "admitted"
    /\ dispatchCount = 0
    /\ runtime' = "running"
    /\ dispatchCount' = dispatchCount + 1
    /\ UNCHANGED <<host, harness, network, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness>>

RuntimeLoseKnowledge ==
    /\ runtime = "running"
    /\ runtime' = "ambiguous"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness>>

RuntimeObserveTerminal ==
    /\ runtime \in {"running", "ambiguous"}
    /\ runtime' = "terminal"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness>>

ConsumerObserve ==
    /\ runtime = "terminal"
    /\ consumerEvidence = "none"
    /\ sourceEvidenceBinding = "none"
    (* Evidence can belong to this Work or a different consumer. *)
    /\ consumerEvidence' \in {"matching", "foreign"}
    (* Abstract admission SourceCut binding; not a live digest check. *)
    /\ sourceEvidenceBinding' \in {"admission-bound", "different-source"}
    /\ UNCHANGED <<host, harness, network, runtime, dispatchCount,
                  admissionInputsWitness>>

HostAccept ==
    /\ host = "open"
    /\ runtime = "terminal"
    (* A foreign Work's valid result is NOT evidence for this Work. *)
    /\ consumerEvidence = "matching"
    /\ sourceEvidenceBinding = "admission-bound"
    /\ host' = "accepted"
    /\ UNCHANGED <<harness, network, runtime, dispatchCount, consumerEvidence, sourceEvidenceBinding,
                  admissionInputsWitness>>

Next ==
    \/ NetworkObserve
    \/ NetworkDegrade
    \/ HarnessPropose
    \/ RuntimeAdmit
    \/ RuntimeDispatch
    \/ RuntimeLoseKnowledge
    \/ RuntimeObserveTerminal
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

(* Intentionally false negative oracle: a matching Work can have wrong source. *)
WrongSourceEvidenceIsUnreachable ==
    ~(consumerEvidence = "matching" /\ sourceEvidenceBinding = "different-source")

=============================================================================
