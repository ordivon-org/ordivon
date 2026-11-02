------------------------ MODULE SemanticRefinementR1 ------------------------
EXTENDS TLC
VARIABLES modelClaim, ownerTrace, ownerGoal, traceClosed, accepted
vars == <<modelClaim, ownerTrace, ownerGoal, traceClosed, accepted>>
Init ==
    /\ modelClaim = FALSE
    /\ ownerTrace = "unknown"
    /\ ownerGoal = "unknown"
    /\ traceClosed = FALSE
    /\ accepted = FALSE
ClaimByModel ==
    /\ ~modelClaim
    /\ modelClaim' = TRUE
    /\ UNCHANGED <<ownerTrace, ownerGoal, traceClosed, accepted>>
ObserveTraceByOwner ==
    /\ ownerTrace = "unknown"
    /\ ownerTrace' \in {"pass", "fail"}
    /\ traceClosed' = TRUE
    /\ UNCHANGED <<modelClaim, ownerGoal, accepted>>
ObserveGoalByOwner ==
    /\ ownerGoal = "unknown"
    /\ ownerGoal' \in {"pass", "fail"}
    /\ UNCHANGED <<modelClaim, ownerTrace, traceClosed, accepted>>
PromoteFromOwnerEvidence ==
    /\ ~accepted
    /\ ownerTrace = "pass"
    /\ ownerGoal = "pass"
    /\ traceClosed
    /\ accepted' = TRUE
    /\ UNCHANGED <<modelClaim, ownerTrace, ownerGoal, traceClosed>>
Next ==
    \/ ClaimByModel
    \/ ObserveTraceByOwner
    \/ ObserveGoalByOwner
    \/ PromoteFromOwnerEvidence
Spec == Init /\ [][Next]_vars
TypeOK ==
    /\ modelClaim \in BOOLEAN
    /\ ownerTrace \in {"unknown", "pass", "fail"}
    /\ ownerGoal \in {"unknown", "pass", "fail"}
    /\ traceClosed \in BOOLEAN
    /\ accepted \in BOOLEAN
NoSelfClaimPromotion ==
    accepted => (traceClosed /\ ownerTrace = "pass" /\ ownerGoal = "pass")
NoClaimAloneAcceptance ==
    (modelClaim /\ ownerTrace = "unknown" /\ ownerGoal = "unknown") => ~accepted
\* Deliberately false: acceptance must be reachable.
NoAcceptedStateReachable == ~accepted
=============================================================================
