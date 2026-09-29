# Social Work Fabric R2 — Implementation Receipt

Date: 2026-09-28

## Source fence

- implementation opening HEAD: `9c448f4a0a8e831d4ff4ed61fbf66570bb0e170b`
- final pre-commit canonical main observed: `b965f3add762342a2992d7c01f77515917edf07d`
- relevant movement between them under `services/host`, `services/gateway`, and `.agents/skills/social-work-collaboration`: none

The implementation therefore did not silently overwrite concurrent Social Work changes.

## Realized SWR2 LEGO

### SWR2-01 Attention horizon advancement

`attention.delta` now advances `nextAfterSequence` to the repeatable-read `snapshotHighSequence` when the returned page is final, including an empty relevant page. Non-final pages advance only to the last returned relevant event. `afterSequence == snapshotHighSequence` has a no-fan-out fast path; `afterSequence > snapshotHighSequence` fails closed.

### SWR2-02 Dual bounded collection reads

Host collection reads now combine item limits with canonical JSON byte budgets. `social_bounds.bounded_prefix` is the shared primitive. Large Message-bearing surfaces use a larger legal minimum so one maximum current Message can still progress a page. Space aggregation is bounded and exposes collection counts/`hasMore`; dedicated list surfaces provide continuation.

### SWR2-03 Durable TopicConsumptionCursor

Migration 0010 adds `topic_consumption_cursors(actor_ref,topic_ref,cursor)`. `topic.cursor.get` and receipt-backed `topic.cursor.ack` enforce monotonicity and topic high-water bounds. `attention.reentry` projects `resumeAfterSequence` from this durable Host state.

### SWR2-04 MessageRelation readback

`message.relation.list` supports `outgoing|incoming|both`, optional relation filtering, change-sequence continuation, item bounds and byte bounds. Opaque `references/about` targets remain navigation references rather than foreign truth claims.

### SWR2-05 Attention reasons

Attention events now expose sorted/deduplicated causal `reasons[]` plus `navigationKind/navigationRef`. The reason vocabulary is routing-only: follow Work/Space/Topic, mention, reply-to-me, own participation and own coordination intent.

### SWR2-06 Re-entry projection

`attention.reentry` groups raw owner-row deltas by navigation target, unions reason/event-kind evidence, carries latest change sequence, and attaches durable Topic resume cursors. It has no rank, score, assignment or scheduler semantics.

### SWR2-07 Query-oriented performance

Migration 0010 adds composite indexes for actor/target-scoped range access, including Topic/Space Message range indexes and an author/message index for reply-to-me reverse navigation. The Message Attention branch was rewritten target-first: subscription-driven paths start from the actor's subscribed Topic/Space, while mention/reply paths start from explicit relation edges. The transactional singleton Social Work change clock is retained because its commit-safe total ordering is part of cursor correctness.

Synthetic falsifier with 20,000 unrelated Messages:

| Measurement | pre target-first | R2 final |
| --- | ---: | ---: |
| first empty Attention call | ~32.3 ms | ~13.3 ms |
| repeated empty poll after horizon advancement | ~12.7 ms | ~4.8 ms |
| `EXPLAIN ANALYZE` core SQL | ~20.1 ms | ~0.48 ms |
| unrelated global Message index rows visited in the dominant Message branch | 20,000 | 0 |

The final plan uses actor subscriptions plus `message_topic_change_idx` / `message_space_change_idx` and relation indexes rather than scanning the global Message change range.

### SWR2-08 Reference convergence

The spec freezes the target typed reference value shape already owned by Runtime (`namespace,type,id,generation?,digest?`) and used directly by Harness. R2 intentionally does not migrate `WorkSnapshot.referenceRefs: list[str]`: no current Host consumer justifies a cross-owner breaking migration. Reference remains correlation/navigation, not foreign proof or authority transfer.

## Schema and release surface

- Host database schema: 9 -> 10
- Host package: 0.4.0 -> 0.5.0
- Host MCP surface epoch: 2 -> 3
- Gateway package: 0.6.0 -> 0.7.0
- Gateway MCP surface epoch: 3 -> 4

New northbound tools:

- `space.subject.list`
- `space.participation.list`
- `topic.list`
- `topic.cursor.get`
- `topic.cursor.ack`
- `message.relation.list`
- `attention.reentry`

Existing collection surfaces gained explicit byte budgets where payload size can grow independently of item count.

## Verification

A disposable PostgreSQL cluster owned by the local non-root `postgres` account was initialized from empty storage for integration verification. Alembic successfully migrated `0001 -> ... -> 0010`; no production Host database was used for tests.

Final verification:

- Host `uv lock --check`: PASS
- Host `uv sync --locked`: PASS
- Host Alembic fresh `upgrade head`: PASS
- Host `ruff check .`: PASS
- Host complete pytest suite with PostgreSQL integration tests enabled: PASS
- Gateway `uv lock --check`: PASS
- Gateway `uv sync --locked`: PASS
- Gateway `ruff check .`: PASS
- Gateway complete pytest suite: PASS (one upstream Starlette/AnyIO deprecation warning only)
- `git diff --check`: PASS
- 100-Agent dynamic regrouping regression: PASS
- Attention empty-horizon falsifier: PASS
- non-final Attention page no-skip falsifier: PASS
- Topic cursor persistence/backward/high-water falsifiers: PASS
- Message relation outgoing/incoming readback: PASS
- follow/mention/reply causal reason projection: PASS
- canonical byte-budget Message page falsifier: PASS
- migration 0010 index/table proof: PASS

## Explicit non-realizations

No durable Attention inbox/event table, Redis, Kafka/NATS, graph database, CRDT, Scylla/Cassandra, social ranking, voting, scheduler, DM ontology, inline artifact/blob storage, or Participation-derived authorization was introduced.
