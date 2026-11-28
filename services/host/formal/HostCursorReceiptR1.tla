-------------------- MODULE HostCursorReceiptR1 --------------------
EXTENDS Integers, FiniteSets, Sequences, TLC

\* One independent cursor key (Attention actor or Topic actor/topic).
\* Model the linearization of a native monotone UPSERT and durable receipt.
\* Two request IDs suffice to falsify the absent-row first-ACK race.
\* This is a bounded abstract transition system; PG source refinement,
\* actual receipt transaction and installed/authorized consumers are separate.
CONSTANT Horizon
ASSUME Horizon \in Nat \ {0}

Requests == 1..2
NoReceipt == [before |-> -1, after |-> -1]
NoReplay == [id |-> 0, before |-> -1, after |-> -1]
ReceiptType == [before: 0..Horizon, after: 0..Horizon]

VARIABLES cursor, pending, requested, sawAbsent, receipts, history, lastReplay
vars == <<cursor, pending, requested, sawAbsent, receipts, history, lastReplay>>

Init ==
  /\ cursor = 0
  /\ pending = {}
  /\ requested = [i \in Requests |-> 0]
  /\ sawAbsent = [i \in Requests |-> FALSE]
  /\ receipts = [i \in Requests |-> NoReceipt]
  /\ history = <<>>
  /\ lastReplay = NoReplay

Begin(i, n) ==
  /\ i \notin pending
  /\ receipts[i] = NoReceipt
  /\ pending' = pending \cup {i}
  /\ requested' = [requested EXCEPT ![i] = n]
  /\ sawAbsent' = [sawAbsent EXCEPT ![i] = (Len(history) = 0)]
  /\ UNCHANGED <<cursor, receipts, history, lastReplay>>

Admissible(i) ==
  /\ i \in pending
  /\ cursor <= requested[i]
  /\ requested[i] <= Horizon
  /\ receipts[i] = NoReceipt

CommitWithBefore(i, b) ==
  /\ Admissible(i)
  /\ cursor' = requested[i]
  /\ receipts' = [receipts EXCEPT
       ![i] = [before |-> b, after |-> requested[i]]]
  /\ history' = Append(history, i)
  /\ pending' = pending \ {i}
  /\ UNCHANGED <<requested, sawAbsent, lastReplay>>

\* The native SQL effect returns OLD/NEW at the actual write.
Commit(i) == CommitWithBefore(i, cursor)

\* Prior implementation: a missing row did not lock anything. A second
\* first writer could report zero after the first commit was already visible.
UnsafeCommit(i) ==
  CommitWithBefore(i, IF sawAbsent[i] THEN 0 ELSE cursor)

\* Reject an invalid monotone/horizon request or lose/abort a pending
\* transaction before commit. No cursor or durable receipt effect.
Reject(i) ==
  /\ i \in pending
  /\ ~Admissible(i)
  /\ pending' = pending \ {i}
  /\ UNCHANGED <<cursor, requested, sawAbsent, receipts, history, lastReplay>>

Abort(i) ==
  /\ i \in pending
  /\ pending' = pending \ {i}
  /\ UNCHANGED <<cursor, requested, sawAbsent, receipts, history, lastReplay>>

\* Same request ID and same coordinate: replay the historical transition.
Replay(i, n) ==
  /\ receipts[i] # NoReceipt
  /\ n = receipts[i].after
  /\ lastReplay' = [id |-> i, before |-> receipts[i].before,
                    after |-> receipts[i].after]
  /\ UNCHANGED <<cursor, pending, requested, sawAbsent, receipts, history>>

\* Same ID with changed coordinate is a conflict, not a new transition.
RejectReuse(i, n) ==
  /\ receipts[i] # NoReceipt
  /\ n # receipts[i].after
  /\ UNCHANGED vars

\* Falsifier: recompute a lost response from the current cursor instead of
\* replaying the historical transaction's durable receipt.
UnsafeReplay(i, n) ==
  /\ receipts[i] # NoReceipt
  /\ n = receipts[i].after
  /\ lastReplay' = [id |-> i, before |-> cursor, after |-> cursor]
  /\ UNCHANGED <<cursor, pending, requested, sawAbsent, receipts, history>>

Common ==
  \/ \E i \in Requests, n \in 0..(Horizon + 1): Begin(i, n)
  \/ \E i \in Requests: Reject(i) \/ Abort(i)
  \/ \E i \in Requests, n \in 0..(Horizon + 1): RejectReuse(i, n)

Next ==
  \/ Common
  \/ \E i \in Requests: Commit(i)
  \/ \E i \in Requests, n \in 0..(Horizon + 1): Replay(i, n)

UnsafeNext ==
  \/ Common
  \/ \E i \in Requests: UnsafeCommit(i)
  \/ \E i \in Requests, n \in 0..(Horizon + 1): Replay(i, n)

UnsafeReplayNext ==
  \/ Common
  \/ \E i \in Requests: Commit(i)
  \/ \E i \in Requests, n \in 0..(Horizon + 1): UnsafeReplay(i, n)

Spec == Init /\ [][Next]_vars
UnsafeSpec == Init /\ [][UnsafeNext]_vars
UnsafeReplaySpec == Init /\ [][UnsafeReplayNext]_vars

TypeOK ==
  /\ cursor \in 0..Horizon
  /\ pending \subseteq Requests
  /\ requested \in [Requests -> 0..(Horizon + 1)]
  /\ sawAbsent \in [Requests -> BOOLEAN]
  /\ receipts \in [Requests -> ReceiptType \cup {NoReceipt}]
  /\ history \in Seq(Requests)
  /\ Len(history) <= Cardinality(Requests)
  /\ lastReplay \in {NoReplay} \cup [id: Requests, before: 0..Horizon, after: 0..Horizon]

NoOrphanReceipt ==
  /\ Cardinality({history[j] : j \in 1..Len(history)}) = Len(history)
  /\ \A i \in Requests:
       (receipts[i] # NoReceipt) <=> i \in {history[j] : j \in 1..Len(history)}
  /\ \A i \in pending: receipts[i] = NoReceipt

ReceiptChain ==
  /\ \A j \in 1..Len(history):
       LET receipt == receipts[history[j]]
           predecessor == IF j = 1 THEN 0 ELSE receipts[history[j-1]].after
       IN /\ receipt.before = predecessor
          /\ predecessor <= receipt.after
          /\ receipt.after <= Horizon
  /\ cursor = IF Len(history) = 0 THEN 0 ELSE receipts[history[Len(history)]].after

ReplayExact ==
  lastReplay # NoReplay =>
    /\ receipts[lastReplay.id] # NoReceipt
    /\ lastReplay.before = receipts[lastReplay.id].before
    /\ lastReplay.after = receipts[lastReplay.id].after

=============================================================================
