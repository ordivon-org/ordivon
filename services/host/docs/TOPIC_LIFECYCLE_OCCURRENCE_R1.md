# Topic lifecycle occurrence refinement R1

## Real consumer defect and smallest repair

Actual SDK + PostgreSQL 18 on main 0d9e2cf190620be71fd21b6316df93f885287077:
job-01a20d46-61fb-7214-b0f5-00806a89322a. Open, close, reopen,
close with unchanged high=0 and identical parameters. Last MCP result:
admission=existing, state=closed; native stored state=open. The previous
receipt identity represents the parameter tuple, not the occurrence.
A random per-request ID would destroy exact historical retry and still fail
to distinguish a newly submitted stale ABA observation.

## Contract

For one Topic, let (s,g,h) be its state, existing row change_sequence
(positive exact integer), and committed message high. Read all three from
one REPEATABLE READ cut via topic.resume's typed TopicResumeCoordinate. A new state command names
(s,g,h,target,actor,topic) in the request digest. A previously committed
exact request returns its own historical receipt; it is not a current-state
read. A new request checks (s,g,h) under the existing Topic FOR NO KEY UPDATE
posting fence. No state/receipt effect if any precondition is false.
If target differs, allocate the existing swf_next_change_sequence within
the same transaction and return the new coordinate. A no-op retains g.
The operation and receipt commit together.

Invariant: two distinct committed lifecycle changes of the same Topic
have strictly increasing g. After an open→closed→open cycle, state and
message high can equal the initial observation but g cannot. Therefore
the original request identity cannot collide with a fresh occurrence
(except an assumed cryptographic digest collision), and a distinct stale
request cannot pass the CAS. No new counter, table, lock domain or
authorization boundary. Coordinate exhaustion remains Schema 15 fail-closed.

PostgreSQL 18 row locks and transaction isolation:
https://www.postgresql.org/docs/18/explicit-locking.html
https://www.postgresql.org/docs/18/transaction-iso.html

## Consumer and release

Host epoch 9, package 0.11.0, same 31 tool names. Required exact positive
expectedChangeSequence is deliberately incompatible with unversioned
topic.state.set callers. Do not weaken it to optional; the old observation
cannot resolve an ABA occurrence. TopicResponse.changeSequence is optional
for exact legacy topic.create receipt replays; topic.resume is the current
same-cut source. Old receipts stay unmodified. New state receipts explicitly
label historical replay. Gateway must carry the field with the same exact
numeric domain, and consumers must refresh the installed tool contract.
No production activation without matched Host/Gateway and actual route/
policy evidence; #2349 remains independent. Verify actual SDK+PG empty and
nonempty cycle, old replay/no mutation, distinct stale rejection,
strict invalid inputs, and existing concurrent close/post and archive tests.
