-------------------- MODULE WorkspaceReclaimReceiptR1 --------------------
EXTENDS TLC
CONSTANTS AllowOverwrite, DropObservedOnFailure
\* Two sweep observations compete for one receipt coordinate. The native
\* effect is outside this model; ObserveClose represents an observed result.
\* Trusted local filesystem, atomic no-clobber link and explicit sync assumed.
Writers == {"a", "b"}
None == "none"
VARIABLES phase, stored, first, reported
vars == <<phase, stored, first, reported>>
Init ==
    /\ phase = [w \in Writers |-> "initial"]
    /\ stored = None
    /\ first = None
    /\ reported = [w \in Writers |-> FALSE]
ObserveClose(w) ==
    /\ phase[w] = "initial"
    /\ phase' = [phase EXCEPT ![w] = "observed"]
    /\ UNCHANGED <<stored, first, reported>>
Publish(w) ==
    /\ phase[w] = "observed"
    /\ (stored = None \/ AllowOverwrite)
    /\ stored' = w
    /\ first' = IF first = None THEN w ELSE first
    /\ phase' = [phase EXCEPT ![w] = "linked"]
    /\ UNCHANGED reported
Sync(w) ==
    /\ phase[w] = "linked"
    /\ phase' = [phase EXCEPT ![w] = "durable"]
    /\ reported' = [reported EXCEPT ![w] = TRUE]
    /\ UNCHANGED <<stored, first>>
PublicationFailure(w) ==
    /\ phase[w] \in {"observed", "linked"}
    /\ phase' = [phase EXCEPT ![w] = "unknown"]
    /\ reported' = [reported EXCEPT ![w] = ~DropObservedOnFailure]
    /\ UNCHANGED <<stored, first>>
Next == \E w \in Writers: ObserveClose(w) \/ Publish(w) \/ Sync(w) \/ PublicationFailure(w)
Spec == Init /\ [][Next]_vars
TypeOK ==
    /\ phase \in [Writers -> {"initial", "observed", "linked", "durable", "unknown"}]
    /\ stored \in Writers \cup {None}
    /\ first \in Writers \cup {None}
    /\ reported \in [Writers -> BOOLEAN]
OriginalReceiptPreserved == stored = first
DurableMeansOriginal == \A w \in Writers: phase[w] = "durable" => stored = w
FailurePreservesObserved == \A w \in Writers: phase[w] = "unknown" => reported[w]
NoDurableReceipt == \A w \in Writers: phase[w] # "durable"
=============================================================================
