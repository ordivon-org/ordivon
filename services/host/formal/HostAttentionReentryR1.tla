-------------------- MODULE HostAttentionReentryR1 --------------------
EXTENDS Naturals, FiniteSets, TLC

\* Abstract Host re-entry contract at one transaction-local MVCC cut.
\* A ChangeSeq is NOT a Topic MessageSeq. Relevant commits add one
\* message and one change; unrelated commits advance only ChangeSeq.
\* One-item pages are sufficient to falsify a non-final cursor skip.
\* This model ASSUMES committed change ordering; PG SQL, isolation,
\* byte pagination and installed MCP are separate refinement duties.

CONSTANT MaxChanges
ASSUME MaxChanges \in Nat \ {0}

VARIABLES changeHigh, relevant, topicHigh, topicCursor,
          attentionCursor, stage, snapshotHigh, snapshotAfter,
          snapshotTopicCursor, firstRelevant, hasMore,
          resultAfter, resultTopicCursor

vars == <<changeHigh, relevant, topicHigh, topicCursor,
          attentionCursor, stage, snapshotHigh, snapshotAfter,
          snapshotTopicCursor, firstRelevant, hasMore,
          resultAfter, resultTopicCursor>>

Eligible(refs, after, high) ==
  {i \in refs : i > after /\ i <= high}

FirstEligible(refs, after, high) ==
  LET candidates == Eligible(refs, after, high)
  IN IF candidates = {} THEN 0
     ELSE CHOOSE n \in candidates :
       \A k \in candidates : n <= k

Init ==
  /\ changeHigh = 0
  /\ relevant = {}
  /\ topicHigh = 0
  /\ topicCursor = 0
  /\ attentionCursor = 0
  /\ stage = "idle"
  /\ snapshotHigh = 0
  /\ snapshotAfter = 0
  /\ snapshotTopicCursor = 0
  /\ firstRelevant = 0
  /\ hasMore = FALSE
  /\ resultAfter = 0
  /\ resultTopicCursor = 0

CommitRelevant ==
  /\ changeHigh < MaxChanges
  /\ changeHigh' = changeHigh + 1
  /\ relevant' = relevant \cup {changeHigh + 1}
  /\ topicHigh' = topicHigh + 1
  /\ UNCHANGED <<topicCursor, attentionCursor, stage, snapshotHigh,
                 snapshotAfter, snapshotTopicCursor, firstRelevant,
                 hasMore, resultAfter, resultTopicCursor>>

CommitUnrelated ==
  /\ changeHigh < MaxChanges
  /\ changeHigh' = changeHigh + 1
  /\ UNCHANGED <<relevant, topicHigh, topicCursor, attentionCursor,
                 stage, snapshotHigh, snapshotAfter, snapshotTopicCursor,
                 firstRelevant, hasMore, resultAfter, resultTopicCursor>>

AckTopic ==
  /\ topicCursor < topicHigh
  /\ topicCursor' \in (topicCursor + 1)..topicHigh
  /\ UNCHANGED <<changeHigh, relevant, topicHigh, attentionCursor,
                 stage, snapshotHigh, snapshotAfter, snapshotTopicCursor,
                 firstRelevant, hasMore, resultAfter, resultTopicCursor>>

AckAttention ==
  /\ attentionCursor < changeHigh
  /\ attentionCursor' \in (attentionCursor + 1)..changeHigh
  /\ UNCHANGED <<changeHigh, relevant, topicHigh, topicCursor, stage,
                 snapshotHigh, snapshotAfter, snapshotTopicCursor,
                 firstRelevant, hasMore, resultAfter, resultTopicCursor>>

BeginReentry ==
  /\ stage = "idle"
  /\ stage' = "captured"
  /\ snapshotHigh' = changeHigh
  /\ snapshotAfter' = attentionCursor
  /\ snapshotTopicCursor' = topicCursor
  /\ firstRelevant' = FirstEligible(relevant, attentionCursor, changeHigh)
  /\ hasMore' =
      IF firstRelevant' = 0 THEN FALSE
      ELSE \E k \in relevant : k > firstRelevant' /\ k <= changeHigh
  /\ UNCHANGED <<changeHigh, relevant, topicHigh, topicCursor,
                 attentionCursor, resultAfter, resultTopicCursor>>

CompleteReentry ==
  /\ stage = "captured"
  /\ stage' = "complete"
  /\ resultAfter' =
       IF firstRelevant = 0 \/ ~hasMore THEN snapshotHigh
       ELSE firstRelevant
  /\ resultTopicCursor' = snapshotTopicCursor
  /\ UNCHANGED <<changeHigh, relevant, topicHigh, topicCursor,
                 attentionCursor, snapshotHigh, snapshotAfter,
                 snapshotTopicCursor, firstRelevant, hasMore>>

ResetReentry ==
  /\ stage = "complete"
  /\ stage' = "idle"
  /\ UNCHANGED <<changeHigh, relevant, topicHigh, topicCursor,
                 attentionCursor, snapshotHigh, snapshotAfter,
                 snapshotTopicCursor, firstRelevant, hasMore,
                 resultAfter, resultTopicCursor>>

Next ==
  \/ CommitRelevant
  \/ CommitUnrelated
  \/ AckTopic
  \/ AckAttention
  \/ BeginReentry
  \/ CompleteReentry
  \/ ResetReentry

Spec == Init /\ [][Next]_vars

TypeOK ==
  /\ changeHigh \in 0..MaxChanges
  /\ relevant \subseteq 1..changeHigh
  /\ topicHigh \in 0..MaxChanges
  /\ topicCursor \in 0..topicHigh
  /\ attentionCursor \in 0..changeHigh
  /\ stage \in {"idle", "captured", "complete"}
  /\ snapshotHigh \in 0..MaxChanges
  /\ snapshotAfter \in 0..MaxChanges
  /\ snapshotTopicCursor \in 0..MaxChanges
  /\ firstRelevant \in 0..MaxChanges
  /\ hasMore \in BOOLEAN
  /\ resultAfter \in 0..MaxChanges
  /\ resultTopicCursor \in 0..MaxChanges

SnapshotCutBounds ==
  stage \in {"captured", "complete"} =>
    /\ snapshotAfter <= snapshotHigh
    /\ snapshotHigh <= changeHigh
    /\ snapshotTopicCursor <= topicCursor

ReturnedCutBounds ==
  stage = "complete" =>
    /\ snapshotAfter <= resultAfter
    /\ resultAfter <= snapshotHigh

\* Topic cursor must be read from the SAME MVCC cut as the delta horizon.
\* A later committed topic ACK cannot appear in an earlier reentry page.
ReturnedCursorFromSameCut ==
  stage = "complete" => resultTopicCursor = snapshotTopicCursor

\* The API itself never skips a relevant event. AckAttention is a
\* CALLER-controlled navigation action, NOT proof of semantic consumption.
NoSkippedEligiblePageEvent ==
  stage = "complete" =>
    \A i \in relevant :
      (snapshotAfter < i /\ i <= resultAfter) =>
        (firstRelevant # 0 /\ i = firstRelevant)

\* Falsifier: consume Topic ACK from a newer PG checkout after delta.
UnsafeMixedSnapshotComplete ==
  /\ stage = "captured"
  /\ stage' = "complete"
  /\ resultAfter' =
       IF firstRelevant = 0 \/ ~hasMore THEN snapshotHigh
       ELSE firstRelevant
  /\ resultTopicCursor' = topicCursor
  /\ UNCHANGED <<changeHigh, relevant, topicHigh, topicCursor,
                 attentionCursor, snapshotHigh, snapshotAfter,
                 snapshotTopicCursor, firstRelevant, hasMore>>

\* Falsifier: a non-final page cannot jump directly to the snapshot horizon.
UnsafeSkipNonFinalPage ==
  /\ stage = "captured"
  /\ hasMore
  /\ stage' = "complete"
  /\ resultAfter' = snapshotHigh
  /\ resultTopicCursor' = snapshotTopicCursor
  /\ UNCHANGED <<changeHigh, relevant, topicHigh, topicCursor,
                 attentionCursor, snapshotHigh, snapshotAfter,
                 snapshotTopicCursor, firstRelevant, hasMore>>

UnsafeNext == Next \/ UnsafeMixedSnapshotComplete
UnsafeSpec == Init /\ [][UnsafeNext]_vars
UnsafePageNext == Next \/ UnsafeSkipNonFinalPage
UnsafePageSpec == Init /\ [][UnsafePageNext]_vars

=============================================================================
