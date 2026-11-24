---- MODULE EdgeArtifactEpochR1 ----
EXTENDS Naturals

(* Old request state can expire while an old Artifact remains.
   One representative immutable Artifact slot. Collision is nondeterministic;
   UUID randomness is not used as a safety proof. No external deletion,
   provider corruption or old Artifact expiration in this bounded trace. *)
CONSTANT CreateOnly
VARIABLES phase, slot, oldBytes, newBytes
vars == <<phase, slot, oldBytes, newBytes>>

Init ==
    /\ phase = "retained"
    /\ slot = "none"
    /\ oldBytes = "old"
    /\ newBytes = "absent"

ExpireState ==
    /\ phase = "retained"
    /\ phase' = "expired"
    /\ UNCHANGED <<slot, oldBytes, newBytes>>

Allocate ==
    /\ phase = "expired"
    /\ phase' = "allocated"
    /\ slot' \in {"old", "new"}
    /\ UNCHANGED <<oldBytes, newBytes>>

Write ==
    /\ phase = "allocated"
    /\ IF slot = "old" /\ CreateOnly
       THEN /\ phase' = "rejected"
            /\ UNCHANGED <<oldBytes, newBytes>>
       ELSE /\ phase' = "stored"
            /\ oldBytes' = IF slot = "old" THEN "new" ELSE oldBytes
            /\ newBytes' = IF slot = "new" THEN "new" ELSE newBytes
    /\ UNCHANGED slot

Commit ==
    /\ phase = "stored"
    /\ phase' = "committed"
    /\ UNCHANGED <<slot, oldBytes, newBytes>>

Next == ExpireState \/ Allocate \/ Write \/ Commit
Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ phase \in {"retained", "expired", "allocated", "rejected", "stored", "committed"}
    /\ slot \in {"none", "old", "new"}
    /\ oldBytes \in {"old", "new"}
    /\ newBytes \in {"absent", "new"}

RetainedEvidenceUnchanged == oldBytes = "old"
CommittedUsesIndependentSlot == phase = "committed" => slot = "new" /\ newBytes = "new"
CollisionDoesNotMutate == phase = "rejected" => oldBytes = "old" /\ newBytes = "absent"

NeverCollision == phase # "rejected"
NeverNewCommit == phase # "committed"

=============================================================================
