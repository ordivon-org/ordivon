---- MODULE OriginalSourceCutR1 ----
EXTENDS Naturals, Sequences

(* Bounded source-read model, not a second Journal or physical release proof.
   integrity abstracts the existing original Store validator; it is an explicit
   premise, NOT a proof of CAS/SQL correctness. N represents committed revisions. *)
CONSTANTS N, UnsafeTailOnly
VARIABLES observed, integrity, accepted, pendingRevision, terminal
vars == <<observed, integrity, accepted, pendingRevision, terminal>>

Reads == UNION { [1..k -> 1..N] : k \in 0..N }
TypeOK == /\ observed \in Reads
          /\ integrity \in BOOLEAN
          /\ accepted \in BOOLEAN
          /\ pendingRevision \in 0..N
          /\ terminal \in BOOLEAN

Init == /\ observed = <<>>
        /\ integrity = FALSE
        /\ accepted = FALSE
        /\ pendingRevision \in 0..N
        /\ terminal = FALSE

Read == /\ ~accepted
        /\ observed' \in Reads
        /\ integrity' \in BOOLEAN
        /\ UNCHANGED <<accepted, pendingRevision, terminal>>

TailMatches == IF Len(observed) = 0 THEN FALSE ELSE observed[Len(observed)] = N
ExactCut == /\ Len(observed) = N
            /\ \A slot \in 1..N : observed[slot] = slot

Accept == /\ ~accepted
          /\ IF UnsafeTailOnly THEN TailMatches ELSE (ExactCut /\ integrity)
          /\ accepted' = TRUE
          /\ UNCHANGED <<observed, integrity, pendingRevision, terminal>>

(* Zero denotes no outstanding effect. An incomplete source may hide the
   original pending revision. This models the normal terminal transaction,
   not the separately qualified UNKNOWN quarantine or OS/Domain release. *)
PendingVisible == \E slot \in 1..Len(observed) : observed[slot] = pendingRevision
CommitNormalTerminal ==
    /\ accepted
    /\ ~terminal
    /\ ~PendingVisible
    /\ terminal' = TRUE
    /\ UNCHANGED <<observed, integrity, accepted, pendingRevision>>

Quiesce == /\ accepted
           /\ UNCHANGED vars

Next == Read \/ Accept \/ CommitNormalTerminal \/ Quiesce
Spec == Init /\ [][Next]_vars

(* Independently formulated coverage: no original revision is omitted. *)
NoMissingOriginalRevision ==
    accepted => (\A rev \in 1..N :
                   \E slot \in 1..Len(observed) : observed[slot] = rev)
AcceptedIntegrity == accepted => integrity
AcceptanceIsUnreachable == ~accepted
TerminalHasNoPending == terminal => pendingRevision = 0
TerminalIsUnreachable == ~terminal

====
