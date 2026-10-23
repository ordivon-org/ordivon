# Ordivon Social Work Fabric R2 — Canonical Specification

Status: implementation contract for SWR2-01..08

## 0. Goal

R2 does not turn Host into Slack, Linear, an event bus, IAM, a scheduler, or a second Runtime. It hardens the existing Work / Social / Attention split into a small composable waist for multi-Agent collaboration and deterministic response-loss re-entry.

The canonical recovery circuit is:

`Work.get -> attention.reentry -> topic.resume -> owner-native reference readback -> reconcile uncertain effects -> WorkSnapshot commit -> cursor acknowledgement`.

Natural owner truth remains authoritative. Host stores semantic continuity, social organization, collaboration messages/relations, attention preferences and consumption cursors only.

## 1. LEGO property law

Every promoted Social Work LEGO must define Identity, Owner, Truth role, Mutability, Lifecycle, Ordering, Bounds, Replay and Authority non-claim.

Canonical R2 objects:

- `ActorRef`: stable Host reference; never authentication or authorization.
- `Work`: semantic continuity root; revisioned; never Runtime execution truth.
- `WorkSnapshot`: complete semantic state at one revision; CAS committed.
- `Space`: social scope; participation never implies IAM or assignment.
- `Topic`: named asynchronous conversation axis.
- `Message`: append-only collaboration record ordered by Host message sequence.
- `MessageRelation`: explicit collaboration edge; never inferred authority.
- `Subscription`: actor attention preference; never priority/assignment.
- `Attention`: rebuildable projection over owner rows; never durable inbox truth.
- `AttentionCursor`: monotone actor-global consumption horizon.
- `TopicConsumptionCursor`: monotone `(actor, topic)` message-sequence horizon.
- `Reference`: typed navigation/correlation shape only; foreign owner truth remains foreign.

## 2. SWR2-01 — Attention horizon advancement

If `(afterSequence, snapshotHighSequence]` contains no more relevant event, R1 must not leave the cursor at the old horizon.

For a delta evaluated at repeatable-read `snapshotHighSequence=H`:

- if additional relevant rows remain beyond the returned page, `nextAfterSequence = last_returned_change_sequence`;
- otherwise `nextAfterSequence = H`, including an empty page.

This is safe because the same snapshot proved that no unreturned relevant row exists at or below `H`.

Falsifiers: an empty page does not advance to `H`; a non-final page jumps over an omitted relevant row; or an event committed after the snapshot is skipped.

## 3. SWR2-02 — Dual bounded collection reads

All promoted R2 collection surfaces have both item-count and encoded-byte budgets. Canonical encoded size is RFC 8785 JSON via Host `canonical_bytes`.

Promoted bounded surfaces: `work.list`, `space.get`, `space.list`, `space.subject.list`, `space.participation.list`, `topic.list`, `topic.resume`, `message.search`, `message.relation.list`, `subscription.list`, `attention.get`, `attention.delta`, and `attention.reentry`.

Byte truncation is a page boundary: `hasMore=true`; the continuation cursor points to the last returned item. If one legal item cannot fit the declared budget, fail closed instead of returning a non-advancing empty page.

## 4. SWR2-03 — Durable TopicConsumptionCursor

Owner: Host PostgreSQL. Natural key: `(actor_ref, topic_ref)`. Value: Message `sequence`.

Mutation law: monotone; cannot acknowledge beyond the current maximum sequence in the topic; cannot move backwards; same acknowledgement is idempotent; cursor means navigation only, not semantic acceptance.

Tools: `topic.cursor.get(actorRef, topicRef)` and `topic.cursor.ack(actorRef, topicRef, cursor)`.

`attention.reentry` projects the saved topic cursor as `resumeAfterSequence` for topic items.

## 5. SWR2-04 — Message relation readback

Tool: `message.relation.list(messageRef, direction, relation?, afterChangeSequence, limit, maxBytes)`.

`direction` is `outgoing | incoming | both`. Ordering is `(change_sequence, source_message_ref, relation, target_ref)` ascending. The continuation is `nextAfterChangeSequence`. The anchor `messageRef` must exist. Opaque `references/about` targets remain opaque references, not existence proof.

`topic.resume` does not implicitly expand an unbounded relation graph.

## 6. SWR2-05 — Attention causal reasons

Every Attention event exposes sorted/deduplicated `reasons[]` derived from the same repeatable-read snapshot.

Vocabulary: `followed_work`, `followed_space`, `followed_topic`, `mentioned`, `replied_to_me`, `own_participation`, `own_coordination_intent`.

Every event also exposes deterministic `navigationKind` (`work | space | topic | subject`) and `navigationRef`. Reasons explain routing only; they are not importance, ranking, assignment, acceptance or authorization.

## 7. SWR2-06 — Re-entry projection

`attention.reentry` is a rebuildable UX projection, never a truth table.

Input: `actorRef`, optional `afterSequence` (omission uses durable Attention cursor), `limit`, `maxBytes`.

Output groups raw Attention events by `(navigationKind,navigationRef)`, retaining unioned `reasons[]`, represented event kinds, latest included change sequence, `resumeAfterSequence` for Topic items, snapshot high-water, `hasMore` and continuation horizon. No score/rank/priority field is permitted.

## 8. SWR2-07 — Query-oriented indexes

PostgreSQL stays canonical. R2 adds only dominant-query indexes:

- `work_snapshots(work_ref, change_sequence)`
- source/target Work relation + change sequence
- `participations(actor_ref, change_sequence)`
- `topics(space_ref, change_sequence)`
- `messages(topic_ref, change_sequence)`
- `messages(space_ref, change_sequence)`
- `messages(author_actor_ref, message_ref)` for reply-to-me reverse navigation
- `message_relations(target_ref, relation, change_sequence)`

The transactional singleton `swf_change_clock` stays unchanged. Replacing it with a non-transactional sequence could permit a late commit behind an already acknowledged high-water.

## 9. SWR2-08 — Cross-owner Reference convergence

Runtime already owns `ForeignReference { namespace, type, id, generation?, digest? }`; Harness consumes that owner-native wire shape rather than duplicating it.

R2 freezes the same semantic target shape but does not migrate existing `WorkSnapshot.referenceRefs: list[str]`. A Reference is navigation/correlation, never foreign fact proof or authority transfer. `generation`/`digest` are optional owner-native commitments, not Host attestations.

A future physical migration requires at least two Host northbound consumers that need structured decomposition and cannot safely recover it from owner-native surfaces.

## 10. Schema 0010

Add only `topic_consumption_cursors` and the SWR2-07 indexes. No inbox/event/cache table. Host schema version becomes 10.

## 11. Northbound surface

New tools: `space.subject.list`, `space.participation.list`, `topic.list`, `topic.cursor.get`, `topic.cursor.ack`, `message.relation.list`, `attention.reentry`.

Existing collection tools gain `maxBytes`; `space.get` gains bounded embedded collection limits. Gateway mirrors Host arguments without becoming owner.

## 12. Verification

Correctness: horizon advancement, no skipped page row, topic-cursor monotonicity/high-water rejection, bidirectional relation recovery, causal reasons, unranked re-entry grouping, canonical byte-budget enforcement.

Recovery: topic cursor survives new Store/process instances; re-entry uses cursor without copying Message state; cursor acknowledgement replay recovers committed result.

Authority: Participation never grants access; Subscription never assigns Work; Attention never becomes inbox truth; Reference never transfers authority.

Performance: migration 0010 proves query indexes; unrelated-only intervals are crossed once per completed horizon; no new queue/cache/event-store write amplification.

## 13. Explicit non-goals

No DM/GroupChat ontology, ranking, voting, scheduler, Redis, Kafka/NATS, graph DB, CRDT, Scylla/Cassandra, inline blob storage, authorization from Participation, or automatic domain truth extraction from Message bodies.
