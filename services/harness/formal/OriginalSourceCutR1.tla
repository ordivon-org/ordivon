---- MODULE OriginalSourceCutR1 ----
EXTENDS Naturals, Sequences

(* Bounded source-read model, not a second Journal or physical release proof.
   integrity abstracts the existing original Store validator; it is an explicit
   premise, NOT a proof of CAS/SQL correctness. N represents committed revisions. *)
CONSTANTS N, UnsafeTailOnly
VARIABLES observed, integrity, accepted
vars == <<observed, integrity, accepted>>

Reads == UNION { [1..k -> 1..N] : k \in 0..N }
TypeOK == /\ observed \in Reads
          /\ integrity \in BOOLEAN
          /\ accepted \in BOOLEAN

Init == /\ observed = <<>>
        /\ integrity = FALSE
        /\ accepted = FALSE

Read == /\ ~accepted
        /\ observed' \in Reads
        /\ integrity' \in BOOLEAN
        /\ UNCHANGED accepted

TailMatches == IF Len(observed) = 0 THEN FALSE ELSE observed[Len(observed)] = N
ExactCut == /\ Len(observed) = N
            /\ \A slot \in 1..N : observed[slot] = slot

Accept == /\ ~accepted
          /\ IF UnsafeTailOnly THEN TailMatches ELSE (ExactCut /\ integrity)
          /\ accepted' = TRUE
          /\ UNCHANGED <<observed, integrity>>

Quiesce == /\ accepted
           /\ UNCHANGED vars

Next == Read \/ Accept \/ Quiesce
Spec == Init /\ [][Next]_vars

(* Independently formulated coverage: no original revision is omitted. *)
NoMissingOriginalRevision ==
    accepted => (\A rev \in 1..N :
                   \E slot \in 1..Len(observed) : observed[slot] = rev)
AcceptedIntegrity == accepted => integrity
AcceptanceIsUnreachable == ~accepted

====
