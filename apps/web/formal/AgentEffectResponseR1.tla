------------------------ MODULE AgentEffectResponseR1 ------------------------
EXTENDS TLC

\* One verified Agent, one exact effect, one pending asynchronous ALLOW or STEP_UP
\* decision and one other legal request. Authority changes abstract the
\* owner grant resolution and revision checks. No distributed DB claim.
CONSTANT Policy
VARIABLES phase, decision, authority, committed, response, staleApproval, missedReplay, ambiguousCommit
vars == <<phase, decision, authority, committed, response, staleApproval, missedReplay, ambiguousCommit>>

Init ==
    /\ phase = "idle"
    /\ decision = "none"
    /\ authority = "current"
    /\ committed = FALSE
    /\ response = "none"
    /\ staleApproval = FALSE
    /\ missedReplay = FALSE
    /\ ambiguousCommit = FALSE

Begin(d) ==
    /\ phase = "idle"
    /\ authority = "current"
    /\ ~committed
    /\ phase' = "awaiting"
    /\ decision' = d
    /\ UNCHANGED <<authority, committed, response, staleApproval, missedReplay, ambiguousCommit>>

Revoke ==
    /\ phase = "awaiting"
    /\ authority = "current"
    /\ authority' = "revoked"
    /\ UNCHANGED <<phase, decision, committed, response, staleApproval, missedReplay, ambiguousCommit>>

ChangeGrant ==
    /\ phase = "awaiting"
    /\ authority = "current"
    /\ authority' = "changed"
    /\ UNCHANGED <<phase, decision, committed, response, staleApproval, missedReplay, ambiguousCommit>>

BecomeAmbiguous ==
    /\ phase = "awaiting"
    /\ authority = "current"
    /\ authority' = "ambiguous"
    /\ UNCHANGED <<phase, decision, committed, response, staleApproval, missedReplay, ambiguousCommit>>

OtherExactCommit ==
    /\ phase = "awaiting"
    /\ authority = "current"
    /\ ~committed
    /\ committed' = TRUE
    /\ authority' = "changed"
    /\ UNCHANGED <<phase, decision, response, staleApproval, missedReplay, ambiguousCommit>>

Finish ==
    /\ phase = "awaiting"
    /\ phase' = "returned"
    /\ response' =
        IF Policy = "legacy" THEN
            IF decision = "step_up" THEN "step_up"
            ELSE IF committed THEN "replay"
            ELSE IF authority \in {"current", "ambiguous"} THEN "commit"
            ELSE "retry"
        ELSE IF committed THEN "replay"
        ELSE IF authority = "revoked" THEN "denied"
        ELSE IF authority # "current" THEN "retry"
        ELSE IF decision = "step_up" THEN "step_up"
        ELSE "commit"
    /\ staleApproval' = (response' = "step_up" /\ authority # "current")
    /\ missedReplay' = (committed /\ response' # "replay")
    /\ ambiguousCommit' = (response' = "commit" /\ authority = "ambiguous")
    /\ UNCHANGED <<decision, authority, committed>>

Next == Begin("step_up") \/ Begin("allow") \/ Revoke \/ ChangeGrant \/ BecomeAmbiguous \/ OtherExactCommit \/ Finish
Spec == Init /\ [][Next]_vars
TypeOK ==
    /\ phase \in {"idle", "awaiting", "returned"}
    /\ decision \in {"none", "step_up", "allow"}
    /\ authority \in {"current", "changed", "revoked", "ambiguous"}
    /\ committed \in BOOLEAN
    /\ response \in {"none", "step_up", "replay", "denied", "retry", "commit"}
    /\ staleApproval \in BOOLEAN
    /\ missedReplay \in BOOLEAN
    /\ ambiguousCommit \in BOOLEAN
NoStaleApproval == ~staleApproval
ExactCommitWins == ~missedReplay
NoAmbiguousCommit == ~ambiguousCommit
NeverStepUp == response # "step_up"
NeverReplay == response # "replay"
=============================================================================
