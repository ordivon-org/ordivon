---- MODULE Lego21OwnerBoundary ----
EXTENDS Naturals

(***************************************************************************)
(* Tiny owner-composition model. The execution/network/domain owners are   *)
(* independent: an observation or Tool proposal is not effect authority.   *)
(* This is a bounded model, NOT an implementation-refinement proof.         *)
(***************************************************************************)

VARIABLES host, harness, network, runtime, dispatchCount, consumerEvidence

vars == <<host, harness, network, runtime, dispatchCount, consumerEvidence>>

HostStates == {"open", "accepted"}
HarnessStates == {"idle", "proposed"}
NetworkStates == {"unknown", "ready"}
RuntimeStates == {"idle", "admitted", "running", "ambiguous", "terminal"}

TypeOK ==
    /\ host \in HostStates
    /\ harness \in HarnessStates
    /\ network \in NetworkStates
    /\ runtime \in RuntimeStates
    /\ dispatchCount \in 0..2
    /\ consumerEvidence \in BOOLEAN

Init ==
    /\ host = "open"
    /\ harness = "idle"
    /\ network = "unknown"
    /\ runtime = "idle"
    /\ dispatchCount = 0
    /\ consumerEvidence = FALSE

NetworkObserve ==
    /\ network = "unknown"
    /\ network' = "ready"
    /\ UNCHANGED <<host, harness, runtime, dispatchCount, consumerEvidence>>

HarnessPropose ==
    /\ harness = "idle"
    /\ harness' = "proposed"
    /\ UNCHANGED <<host, network, runtime, dispatchCount, consumerEvidence>>

RuntimeAdmit ==
    /\ runtime = "idle"
    /\ harness = "proposed"
    /\ network = "ready"
    /\ runtime' = "admitted"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence>>

RuntimeDispatch ==
    /\ runtime = "admitted"
    /\ dispatchCount = 0
    /\ runtime' = "running"
    /\ dispatchCount' = dispatchCount + 1
    /\ UNCHANGED <<host, harness, network, consumerEvidence>>

RuntimeLoseKnowledge ==
    /\ runtime = "running"
    /\ runtime' = "ambiguous"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence>>

RuntimeObserveTerminal ==
    /\ runtime \in {"running", "ambiguous"}
    /\ runtime' = "terminal"
    /\ UNCHANGED <<host, harness, network, dispatchCount, consumerEvidence>>

ConsumerObserve ==
    /\ runtime = "terminal"
    /\ ~consumerEvidence
    /\ consumerEvidence' = TRUE
    /\ UNCHANGED <<host, harness, network, runtime, dispatchCount>>

HostAccept ==
    /\ host = "open"
    /\ runtime = "terminal"
    /\ consumerEvidence
    /\ host' = "accepted"
    /\ UNCHANGED <<harness, network, runtime, dispatchCount, consumerEvidence>>

Next ==
    \/ NetworkObserve
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
    host = "accepted" => (runtime = "terminal" /\ consumerEvidence)

NoDispatchFromNetworkOrModelDiscovery ==
    dispatchCount > 0 => (harness = "proposed" /\ network = "ready")

AmbiguityCannotBeTreatedAsCompletion ==
    runtime = "ambiguous" => (host = "open" /\ ~consumerEvidence /\ dispatchCount = 1)

NoHostAcceptanceWithoutConsumerEvidence ==
    ~consumerEvidence => host = "open"

=============================================================================
