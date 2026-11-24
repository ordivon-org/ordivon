---- MODULE EdgeCommitEvidenceR1 ----
EXTENDS Naturals

(* One intent, one generation-1 commit with a lost reply, one possible
   same-intent takeover, and a repeated conditional write after commit.
   Generation-specific keys and monotonic conditional
   state writes are environment assumptions; retention expiry is excluded.
   Observations and physical commit are deliberately separate. *)
CONSTANTS UnsafeCleanup, UnsafeRepeatRejection
VARIABLES remote, observation, phase, artifact, decision, attempt
vars == <<remote, observation, phase, artifact, decision, attempt>>

Init ==
    /\ remote = "pending1"
    /\ observation = "none"
    /\ phase = "waiting"
    /\ artifact = TRUE
    /\ decision = "none"
    /\ attempt = "unknown"

(* The outstanding request may finish even after a negative observation. *)
LateCommit ==
    /\ remote = "pending1"
    /\ remote' = "committed1"
    /\ UNCHANGED <<observation, phase, artifact, decision, attempt>>

Takeover ==
    /\ remote = "pending1"
    /\ remote' = "pending2"
    /\ UNCHANGED <<observation, phase, artifact, decision, attempt>>

(* A second write with the old ETag is definitively rejected. That says
   nothing about the first write: the Receipt already exists. *)
RepeatRejected ==
    /\ remote = "committed1"
    /\ phase = "waiting"
    /\ attempt = "unknown"
    /\ attempt' = "rejected"
    /\ UNCHANGED <<remote, observation, phase, artifact, decision>>

Observe ==
    /\ phase = "waiting"
    /\ observation' \in {"unknown",
          CASE remote = "pending1" -> "pending"
            [] remote = "committed1" -> "same"
            [] OTHER -> "newer"}
    /\ phase' = "observed"
    /\ UNCHANGED <<remote, artifact, decision, attempt>>

Choose ==
    /\ phase = "observed"
    /\ phase' = "done"
    /\ decision' = IF UnsafeRepeatRejection /\ attempt = "rejected" THEN "cleanup"
                    ELSE IF observation = "same" THEN "recover"
                    ELSE IF observation = "newer" \/ UnsafeCleanup THEN "cleanup"
                    ELSE "retain"
    /\ artifact' = IF decision' = "cleanup" THEN FALSE ELSE artifact
    /\ UNCHANGED <<remote, observation, attempt>>

Next == LateCommit \/ Takeover \/ RepeatRejected \/ Observe \/ Choose
Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ remote \in {"pending1", "committed1", "pending2"}
    /\ observation \in {"none", "unknown", "pending", "same", "newer"}
    /\ phase \in {"waiting", "observed", "done"}
    /\ artifact \in BOOLEAN
    /\ decision \in {"none", "recover", "retain", "cleanup"}
    /\ attempt \in {"unknown", "rejected"}

CommittedEvidenceExists == remote = "committed1" => artifact
CleanupRequiresFence == decision = "cleanup" => remote = "pending2"
UnknownPreservesEvidence ==
    phase = "done" /\ observation \in {"unknown", "pending"} => artifact
RecoveredIsCommitted == decision = "recover" => remote = "committed1"

(* Intentionally false probes: require witnesses of the important paths. *)
NeverLateAfterPendingObservation ==
    ~(phase = "done" /\ observation = "pending" /\ remote = "committed1")
NeverCleanup == decision # "cleanup"
NeverRecover == decision # "recover"
NeverRepeatedRecovery == ~(attempt = "rejected" /\ decision = "recover")
NeverRepeatedUnknownRetain ==
    ~(attempt = "rejected" /\ observation = "unknown" /\ decision = "retain")

=============================================================================
