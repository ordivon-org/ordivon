---- MODULE Lego21OwnerBoundary ----
EXTENDS Naturals

(***************************************************************************)
(* Tiny owner-composition model. The execution/network/domain owners are   *)
(* independent: an observation or Tool proposal is not effect authority.   *)
(* This is a bounded model, NOT an implementation-refinement proof.         *)
(***************************************************************************)

CONSTANTS RequiresHarness, RequiresNetwork

VARIABLES host, harness, network, runtime, dispatchCount, consumerEvidence,
          admissionInputsWitness

vars == <<host, harness, network, runtime, dispatchCount, consumerEvidence,
          admissionInputsWitness>>

HostStates == {"open", "accepted"}
HarnessStates == {"idle", "proposed"}
NetworkStates == {"unknown", "ready"}
RuntimeStates == {"idle", "admitted", "running", "ambiguous", "terminal"}
EvidenceStates == {"none", "matching", "foreign"}

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

Init ==
    /\ host = "open"
    /\ harness = "idle"
    /\ network = "unknown"
    /\ runtime = "idle"
    /\ dispatchCount = 0
    /\ consumerEvidence = "none"
    /\ admissionInputsWitness = FALSE

NetworkObserve ==
    /\ network = "unknown"
    /\ network' = "ready"
    /\ UNCHANGED <<host, harness, runtime, dispatchCount, consumerEvidence,
                  admissionInputsWitness>>

NetworkDegrade ==
    /\ network = "ready"
    /\ network' = "unknown"
    /\ UNCHANGED <<host, harness, runtime, dispatchCount, consumerEvidence,
                  admissionInputsWitness>>

HarnessPropose ==
    /\ harness = "idle"
    /\ harness' = "proposed"
    /\ UNCHANGED <<host, network, runtime, dispatchCount, consumerEvidence,
                  admissionInputsWitness>>

RuntimeAdmit ==
    /\ runtime = "idle"
    /\ (~RequiresHarness \/ harness = "proposed")
    /\ (~RequiresNetwork \/ network = "ready")
    /\ runtime' = "admitted"
    /\ admissionInputsWitness' =
        /\ (~RequiresHarness \/ harness = "proposed")
        /\ (~RequiresNetwork \/ network = "ready")
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence>>

RuntimeDispatch ==
    /\ runtime = "admitted"
    /\ dispatchCount = 0
    /\ runtime' = "running"
    /\ dispatchCount' = dispatchCount + 1
    /\ UNCHANGED <<host, harness, network, consumerEvidence,
                  admissionInputsWitness>>

RuntimeLoseKnowledge ==
    /\ runtime = "running"
    /\ runtime' = "ambiguous"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence,
                  admissionInputsWitness>>

RuntimeObserveTerminal ==
    /\ runtime \in {"running", "ambiguous"}
    /\ runtime' = "terminal"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence,
                  admissionInputsWitness>>

ConsumerObserve ==
    /\ runtime = "terminal"
    /\ consumerEvidence = "none"
    (* Evidence can belong to this Work or a different consumer. *)
    /\ consumerEvidence' \in {"matching", "foreign"}
    /\ UNCHANGED <<host, harness, network, runtime, dispatchCount,
                  admissionInputsWitness>>

HostAccept ==
    /\ host = "open"
    /\ runtime = "terminal"
    (* A foreign Work's valid result is NOT evidence for this Work. *)
    /\ consumerEvidence = "matching"
    /\ host' = "accepted"
    /\ UNCHANGED <<harness, network, runtime, dispatchCount, consumerEvidence,
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

=============================================================================
