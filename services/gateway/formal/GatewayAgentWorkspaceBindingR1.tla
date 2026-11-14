---------------- MODULE GatewayAgentWorkspaceBindingR1 ----------------
EXTENDS TLC

\* Finite assume/guarantee interface for one terminal Runtime Job.
\* Runtime job.list's exact request->Job->Workspace is authoritative in this model.
\* Neither terminality nor matching Workspace proves Agent Run completion,
\* Artifact preservation, or consumerReleased authorization.
\* UNKNOWN must never be promoted to a matching Workspace identity.

VARIABLES stage, physicalWorkspace, projectedWorkspace, decision

vars == <<stage, physicalWorkspace, projectedWorkspace, decision>>

Init ==
    /\ stage = "admitted"
    /\ physicalWorkspace \in {"granted", "other"}
    /\ projectedWorkspace = "none"
    /\ decision = "none"

OwnerObservation ==
    /\ stage = "admitted"
    /\ \E observed \in {"unknown", physicalWorkspace}:
           /\ projectedWorkspace' = observed
           /\ stage' = "observed"
    /\ UNCHANGED <<physicalWorkspace, decision>>

ConsumerDecision ==
    /\ stage = "observed"
    /\ decision' =
           IF projectedWorkspace = "unknown"
           THEN "reconcile"
           ELSE IF projectedWorkspace = "granted"
           THEN "accepted"
           ELSE "rejected"
    /\ stage' = "done"
    /\ UNCHANGED <<physicalWorkspace, projectedWorkspace>>

Next == OwnerObservation \/ ConsumerDecision
Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ stage \in {"admitted", "observed", "done"}
    /\ physicalWorkspace \in {"granted", "other"}
    /\ projectedWorkspace \in {"none", "unknown", "granted", "other"}
    /\ decision \in {"none", "reconcile", "accepted", "rejected"}

AcceptedRequiresExactOwnerWorkspace ==
    decision = "accepted" =>
        (physicalWorkspace = "granted" /\ projectedWorkspace = physicalWorkspace)

MissingOwnerWorkspaceNeedsReconciliation ==
    (stage = "done" /\ projectedWorkspace = "unknown") =>
        decision = "reconcile"

OtherWorkspaceMustBeRejected ==
    (stage = "done" /\ physicalWorkspace = "other"
       /\ projectedWorkspace = "other") =>
        decision = "rejected"

\* Reachability witness: correct matching observation can be accepted.
NeverAccepted == decision # "accepted"

\* Negative control: trusting only Job terminality admits a wrong/unknown
\* Workspace binding. TLC must provide the named invariant counterexample.
UnsafeConsumerDecision ==
    /\ stage = "observed"
    /\ decision' = "accepted"
    /\ stage' = "done"
    /\ UNCHANGED <<physicalWorkspace, projectedWorkspace>>

UnsafeNext == OwnerObservation \/ UnsafeConsumerDecision
UnsafeSpec == Init /\ [][UnsafeNext]_vars
=============================================================================
