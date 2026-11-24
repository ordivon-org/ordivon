----------------------- MODULE EffectApprovalRecordR1 -----------------------
EXTENDS TLC
\* One exact R4 Effect, one previously registered pending row, two possible
\* binding identities, native atomic approval write and commit. Retained
\* pending storage is distinct from an available pending observation.
CONSTANT Policy
VARIABLES state, binding, firstBinding, committed, renewed, exposedAfterCommit
vars == <<state, binding, firstBinding, committed, renewed, exposedAfterCommit>>

Init ==
    /\ state = "absent"
    /\ binding = "none"
    /\ firstBinding = "none"
    /\ committed = FALSE
    /\ renewed = FALSE
    /\ exposedAfterCommit = FALSE

WriteApproval(b) ==
    /\ (Policy = "legacy" \/
         (~committed /\ state \in {"absent", "live"} /\ binding \in {"none", b}))
    /\ state' = "live"
    /\ binding' = b
    /\ firstBinding' = IF firstBinding = "none" THEN b ELSE firstBinding
    /\ renewed' = (renewed \/ (state = "live" /\ binding = b))
    /\ UNCHANGED <<committed, exposedAfterCommit>>

Commit ==
    /\ ~committed
    /\ state = "live"
    /\ state' = "consumed"
    /\ committed' = TRUE
    /\ UNCHANGED <<binding, firstBinding, renewed, exposedAfterCommit>>

LookupPending ==
    /\ committed
    /\ exposedAfterCommit' = (Policy = "legacy")
    /\ UNCHANGED <<state, binding, firstBinding, committed, renewed>>

Next == (\E b \in {"A", "B"} : WriteApproval(b)) \/ Commit \/ LookupPending
Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ state \in {"absent", "live", "consumed"}
    /\ binding \in {"none", "A", "B"}
    /\ firstBinding \in {"none", "A", "B"}
    /\ committed \in BOOLEAN
    /\ renewed \in BOOLEAN
    /\ exposedAfterCommit \in BOOLEAN
TerminalConsumed == committed => state = "consumed"
BindingImmutable == firstBinding # "none" => binding = firstBinding
NoPendingAfterCommit == ~exposedAfterCommit
NeverCommitted == ~committed
NeverRenewed == ~renewed
=============================================================================
