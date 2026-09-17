# Host v2 R7 Read Projection Contraction

## Goal

R7 reduces Agent read cost without expanding Host authority. The design follows the same local pattern already used by Runtime and Skill services: discovery returns a compact projection; exact semantic content is hydrated only when requested.

## Task inventory

`task.list` now returns `schemaVersion=4`, `itemView=basic`, and one compact current-task summary per item: task/goal identity, revision, Host lifecycle state, checkpoint digest, and writer provenance. It does not hydrate or return WorkingCheckpoint payloads. The PostgreSQL path is one bounded join query instead of an inventory query followed by per-task resume/event/checkpoint reads.

Exact WorkingCheckpoint content remains available through `task.resume`. `task.resume`, `task.adopt`, and `task.checkpoint` now return a compact `task` identity/revision capsule plus exactly one top-level `checkpoint` copy; `writerLabel` remains top-level for compatibility. Their response schema version advances to 4.

`expectedRevision` remains the mutation concurrency fence. This change does not weaken stale-write rejection or move Runtime/Git/domain authority into Host.

## Board search snapshot

`board.search` now executes its source search in a repeatable-read read-only transaction and explicitly fences result rows with `sequence <= sourceSnapshotHighWater`. `liveHighWater` is sampled after the source snapshot transaction, so concurrent Board growth can be represented without letting newer rows leak into an older reported source snapshot.

## Compatibility

Tool names are unchanged. Host interface `surfaceVersion` advances from 7 to 8. `task.resume` remains the exact checkpoint read operation in this cut; a later compatibility-reviewed cut may introduce `task.get` as the clearer pure-read name.
