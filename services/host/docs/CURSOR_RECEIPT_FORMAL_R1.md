# Cursor receipt transition contract R1

One independent cursor key (actor for Attention, actor/topic for Topic) and a
durable request receipt share the same PostgreSQL transaction. The cursor
is navigation acknowledgement, not a semantic-consumption or authorization
claim. Two cursor domains still have distinct horizons and storage.

## Abstract refinement obligation

For a new admitted request at a linearization point, let old be the actual
committed cursor (zero for an absent row) and n the requested coordinate.
Require old <= n <= horizon. The atomic committed effect is cursor := n and
receipt[request] := (old,n). A replay of the exact request returns that
historical receipt; a changed request under the same key is a conflict.
An aborted or rejected transition has no committed cursor/receipt effect.

HostCursorReceiptR1 models two request IDs, a fixed horizon, both first
observations of absence, rejected/out-of-horizon operations, pre-commit abort,
new commits and response replay. NoOrphanReceipt, ReceiptChain and ReplayExact
are safety properties checked over this bounded transition system. It does not
model full digest payloads, response admission labels, database crash mechanics,
multi-key lock ordering, changing horizons, arbitrary-size concurrency, or
authorization. RejectReuse represents a no-state-change conflict; the model
does not prove error projection.

Run from the repo root using the existing pinned Runtime-owned TLC JAR:
`mise run host:formal:attention-reentry`. The shared task checks the existing
reentry model and this receipt model, with four deliberate negative cases.
For this receipt model at Horizon=2, unsafe-predecessor reproduces both first
writers observing absence and the second reporting previousCursor=0 despite
an earlier committed nonzero cursor. unsafe-replay reproduces recomputing a
lost response from the current cursor instead of replaying the durable receipt.

Implementation target: Host PR #2613 uses PostgreSQL 18 OLD/NEW from the
conditional UPSERT and the existing caller-owned command receipt transaction.
The original actual PG concurrent ACK test was RED for both domains and the
candidate GREEN. This model alone is not a source-to-model refinement proof,
not the native PG test, not evidence that #2613 is merged/installed, and not
proof of an independent Agent's actual consumption. Retain those obligations.
