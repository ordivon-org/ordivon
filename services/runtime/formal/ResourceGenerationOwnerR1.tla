----------------------- MODULE ResourceGenerationOwnerR1 ---------------------
EXTENDS Naturals, TLC

\* Bounded, single target design model: content identity is not revision.
\* A native issue may complete after issuer death. Settle represents positive
\* native completion/no-handoff and an exact receipt; those are refinement
\* obligations, not facts inferred from a database row or an absent process.
\* No claim of production storage, full NoFutureSpawn, or receiver authority.

CONSTANTS Policy, MaxRevision
Contents == {"A", "B"}
Phases == {"idle", "reserved", "issued", "completed", "aborted"}
Faults == {"stale", "supersede", "foreign", "early", "receipt"}

VARIABLES revision, activeContent, nativeContent, pendingEffect,
          pendingContent, phase, issuerAlive, visitedB, recoveredAfterCrash, bad

vars == <<revision, activeContent, nativeContent, pendingEffect,
          pendingContent, phase, issuerAlive, visitedB, recoveredAfterCrash, bad>>

Init ==
    /\ revision = 0
    /\ activeContent = "A"
    /\ nativeContent = "A"
    /\ pendingEffect = 0
    /\ pendingContent = "none"
    /\ phase = "idle"
    /\ issuerAlive = TRUE
    /\ visitedB = FALSE
    /\ recoveredAfterCrash = FALSE
    /\ bad = {}

Reserve(expectedRevision, expectedContent, wanted) ==
    /\ revision < MaxRevision
    /\ expectedContent = activeContent
    /\ wanted \in Contents \ {activeContent}
    /\ (expectedRevision = revision \/ Policy = "ignoreRevision")
    /\ (pendingEffect = 0 \/ Policy = "supersede")
    /\ revision' = revision + 1
    /\ pendingEffect' = revision + 1
    /\ pendingContent' = wanted
    /\ phase' = "reserved"
    /\ issuerAlive' = TRUE
    /\ bad' = bad
        \cup (IF expectedRevision # revision THEN {"stale"} ELSE {})
        \cup (IF pendingEffect # 0 THEN {"supersede"} ELSE {})
    /\ UNCHANGED <<activeContent, nativeContent, visitedB, recoveredAfterCrash>>

FreshReserve == \E wanted \in Contents :
    Reserve(revision, activeContent, wanted)

\* A previously captured revision-0 proposal, specifically after B was
\* physically selected and A became active again. Pointer equality is ABA.
StaleInitialReserve ==
    /\ revision >= 2
    /\ visitedB
    /\ Reserve(0, "A", "B")

Issue ==
    /\ pendingEffect # 0
    /\ phase = "reserved"
    /\ issuerAlive
    /\ phase' = "issued"
    /\ UNCHANGED <<revision, activeContent, nativeContent, pendingEffect,
                   pendingContent, issuerAlive, visitedB, recoveredAfterCrash, bad>>

NativeComplete ==
    /\ phase = "issued"
    /\ phase' = "completed"
    /\ nativeContent' = pendingContent
    /\ visitedB' = (visitedB \/ pendingContent = "B")
    /\ UNCHANGED <<revision, activeContent, pendingEffect, pendingContent,
                   issuerAlive, recoveredAfterCrash, bad>>

PositiveAbortBeforeIssue ==
    /\ phase = "reserved"
    /\ phase' = "aborted"
    /\ UNCHANGED <<revision, activeContent, nativeContent, pendingEffect,
                   pendingContent, issuerAlive, visitedB, recoveredAfterCrash, bad>>

CrashIssuer ==
    /\ pendingEffect # 0
    /\ issuerAlive
    /\ issuerAlive' = FALSE
    /\ UNCHANGED <<revision, activeContent, nativeContent, pendingEffect,
                   pendingContent, phase, visitedB, recoveredAfterCrash, bad>>

Settle(effect, exactReceipt) ==
    /\ pendingEffect # 0
    /\ (effect = pendingEffect \/ Policy = "wrongEffect")
    /\ (phase \in {"completed", "aborted"}
        \/ (Policy = "earlySettlement" /\ phase = "issued"))
    /\ (exactReceipt \/ Policy = "forgedReceipt")
    /\ activeContent' = nativeContent
    /\ pendingEffect' = 0
    /\ pendingContent' = "none"
    /\ phase' = "idle"
    /\ recoveredAfterCrash' = (recoveredAfterCrash
        \/ (~issuerAlive /\ phase = "completed"))
    /\ bad' = bad
        \cup (IF effect # pendingEffect THEN {"foreign"} ELSE {})
        \cup (IF phase \notin {"completed", "aborted"} THEN {"early"} ELSE {})
        \cup (IF ~exactReceipt THEN {"receipt"} ELSE {})
    /\ UNCHANGED <<revision, nativeContent, issuerAlive, visitedB>>

Next ==
    \/ FreshReserve
    \/ StaleInitialReserve
    \/ Issue
    \/ NativeComplete
    \/ PositiveAbortBeforeIssue
    \/ CrashIssuer
    \/ \E effect \in 0..MaxRevision, exactReceipt \in BOOLEAN :
        Settle(effect, exactReceipt)

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ revision \in 0..MaxRevision
    /\ activeContent \in Contents
    /\ nativeContent \in Contents
    /\ pendingEffect \in 0..MaxRevision
    /\ pendingContent \in Contents \cup {"none"}
    /\ phase \in Phases
    /\ issuerAlive \in BOOLEAN
    /\ visitedB \in BOOLEAN
    /\ recoveredAfterCrash \in BOOLEAN
    /\ bad \subseteq Faults

PhaseCoherent ==
    /\ ((pendingEffect = 0) <=> (phase = "idle"))
    /\ IF pendingEffect = 0 THEN pendingContent = "none"
       ELSE pendingEffect = revision /\ pendingContent \in Contents
StablePhysical ==
    phase \in {"idle", "reserved", "issued", "aborted"} =>
        nativeContent = activeContent
NoStaleAdmission == "stale" \notin bad
NoPendingSupersession == "supersede" \notin bad
NoForeignSettlement == "foreign" \notin bad
NoEarlySettlement == "early" \notin bad
NoForgedReceipt == "receipt" \notin bad

\* Deliberately false positive-control invariants. TLC must produce traces.
NeverReturnedToA == ~(revision >= 2 /\ visitedB /\ pendingEffect = 0
                      /\ activeContent = "A" /\ nativeContent = "A")
NeverRecoveredAfterCrash == ~recoveredAfterCrash
=============================================================================
