-------------------- MODULE HostTopicOccurrenceR1 --------------------
EXTENDS Integers, FiniteSets, TLC

\* One Topic and two actor identities. Atomic CAS+receipt linearization abstracts
\* the native row lock; no proof of SQL refinement or authorization here.
CONSTANT MaxGen, MaxHigh
States == {"open", "closed", "archived"}
Requests == [actor: 1..2, expected: States, gen: 1..MaxGen, high: 0..MaxHigh, target: States]
ReceiptType == [request: Requests, resultGen: 1..MaxGen]
NoEvent == [kind |-> "none", requested |-> 0, actual |-> 0]
Events == [kind: {"commit", "replay"}, requested: 1..MaxGen, actual: 1..MaxGen]
VARIABLES state, gen, high, receipts, last
vars == <<state, gen, high, receipts, last>>

Init ==
  /\ state = "open"
  /\ gen = 1
  /\ high = 0
  /\ receipts = {}
  /\ last = NoEvent

SameKey(a,b,versioned) ==
  /\ a.actor = b.actor
  /\ a.expected = b.expected
  /\ a.high = b.high
  /\ a.target = b.target
  /\ (~versioned \/ a.gen = b.gen)

Matches(q,versioned) ==
  {r \in receipts: SameKey(r.request,q,versioned)}

Legal(q) ==
  /\ q.expected = state
  /\ q.high = high
  /\ ~(state = "open" /\ q.target = "archived")
  /\ ~(state = "archived" /\ q.target = "open")
  /\ (q.target = state \/ gen < MaxGen)

Commit(q,versioned,checkGen) ==
  /\ Matches(q,versioned) = {}
  /\ Legal(q)
  /\ (~checkGen \/ q.gen = gen)
  /\ state' = q.target
  /\ gen' = IF q.target = state THEN gen ELSE gen+1
  /\ receipts' = receipts \cup {[request |-> q, resultGen |-> gen']}
  /\ last' = [kind |-> "commit", requested |-> q.gen, actual |-> gen]
  /\ UNCHANGED high

Replay(q,versioned) ==
  /\ \E r \in Matches(q,versioned):
       last' = [kind |-> "replay", requested |-> q.gen, actual |-> r.request.gen]
  /\ UNCHANGED <<state, gen, high, receipts>>

Post ==
  /\ state = "open"
  /\ high < MaxHigh
  /\ high' = high+1
  /\ UNCHANGED <<state, gen, receipts, last>>

Next == Post \/ \E q \in Requests: Commit(q,TRUE,TRUE) \/ Replay(q,TRUE)
\* Old key ignores the occurrence and aliases a fresh ABA command.
OldKeyNext == Post \/ \E q \in Requests:
  \/ Commit(q,FALSE,TRUE)
  \/ /\ q.gen = gen
     /\ q.expected = state
     /\ q.high = high
     /\ q.target # state
     /\ Replay(q,FALSE)
\* Distinct stale request incorrectly passes a state/high-only CAS.
OldCASNext == Post \/ \E q \in Requests:
  \/ /\ q.gen = gen
     /\ Commit(q,TRUE,FALSE)
  \/ /\ q.gen < gen
     /\ q.target # state
     /\ \E r \in receipts:
          /\ r.request.actor # q.actor
          /\ r.request.gen = q.gen
          /\ r.request.expected = q.expected
          /\ r.request.high = q.high
     /\ Commit(q,TRUE,FALSE)
  \/ Replay(q,TRUE)
Spec == Init /\ [][Next]_vars
OldKeySpec == Init /\ [][OldKeyNext]_vars
OldCASSpec == Init /\ [][OldCASNext]_vars

TypeOK ==
  /\ state \in States
  /\ gen \in 1..MaxGen
  /\ high \in 0..MaxHigh
  /\ receipts \subseteq ReceiptType
  /\ last \in Events \cup {NoEvent}
ReceiptGeneration ==
  \A r \in receipts:
    /\ r.resultGen = IF r.request.expected = r.request.target
                       THEN r.request.gen ELSE r.request.gen+1
    /\ r.resultGen <= gen
FreshCommit == last.kind = "commit" => last.requested = last.actual
ReplayExactOccurrence == last.kind = "replay" => last.requested = last.actual

\* Rejected commands, lost requests and exhausted coordinates stutter.
\* The model does not encode request digests, allocation rollback, byte
\* encoding, Postgres visibility, delivery, or client migration.
=============================================================================
