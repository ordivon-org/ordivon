---
schema_version: 1
id: game.storage-externalization-boundary-r1-20260911
title: Ordivon Game — Storage Externalization Boundary R1
profile: engineering
lifecycle: candidate
source_role: migration-decision
visibility: internal
owners:
  - ordivon-game
updated: 2026-09-11
base_candidate: 067e13198ef601ed3863cedfee204f7ce4c2bdcf
---
# Storage Externalization Boundary R1

## Verdict

```text
NO_ADDITIONAL_PHYSICAL_SUBTRACTION_ADMITTED
```

The provider layers admitted large physical deletion because Game had reimplemented generic execution, credential and retry infrastructure. Storage does not have the same shape. The mature mechanical substrate is already **SQLite + Node `node:sqlite`**. The remaining local persistence code predominantly defines Game truth rather than a competing database framework.

Creating a new Game-local ORM, repository layer, generic event store, or storage adapter would therefore add another abstraction without replacing an immature external substrate. **Do not add an ORM, repository layer, generic event store, or local storage adapter merely to hide SQLite.**

## What is external already

SQLite / `node:sqlite` own the generic mechanics:

- file-backed or in-memory database access;
- ACID transactions;
- WAL;
- locking and busy behavior;
- foreign-key and uniqueness enforcement;
- statement execution and query materialization.

The visible local setup around directory creation, `DatabaseSync`, PRAGMAs and SQLite error normalization is small relative to the domain contracts it surrounds. Extracting those lines into a new internal wrapper would be code motion, not meaningful external substitution.

## What must remain Game authority

### Station Zero v2 / GameStore

The following are semantic contracts:

- Run identity bound to Scenario, Ruleset, Genesis and evaluated inputs;
- canonical Command identity and idempotency;
- canonical Event identity;
- separate Command and Event hash chains;
- exact before/after World digests;
- contiguous sequence and cross-stream alignment;
- one accepted World transition + Command row + Event row + mission status in one transaction;
- sparse Snapshot semantics as disposable caches;
- Snapshot anchoring to authoritative Command evidence;
- recovery from the newest valid Snapshot plus authoritative tail;
- full verification from retained authoritative history;
- point-in-time World reconstruction through the actual Game Ruleset;
- fail-closed behavior when retained history, replayed Event or digest diverges.

Moving these to a generic external event-store abstraction would move Game authority, not implementation mechanics.

### Station Zero v3

One committed Turn currently binds in the same SQLite transaction:

```text
committed Planning
+ current World Head
+ deterministic Turn application
+ World Event chain
+ Turn Record chain
+ new World Head
+ resolved Planning Head
+ Run status
→ COMMIT
```

That is an atomic Game invariant. Splitting it across a generic remote owner would introduce a dual-write window unless a replacement proves an equivalent transaction or an explicitly different topology with preserved judgments.

### Team / local evidence

Several Team and local-evidence tables intentionally share the Game database because recovery and evidence relationships currently rely on short local transactions. Their table layout is implementation, but their atomic relation to Game facts cannot be deleted by naming another owner.

## Why the earlier R2 decomposition language is narrowed

R2 correctly classified SQLite setup, WAL/busy plumbing and Snapshot mechanics as generic-looking. Physical inspection now shows the separable residue is too small to justify another Ordivon abstraction, while Snapshot *meaning* is tightly bound to replay and tamper detection.

Therefore E5 resolves as:

```text
SQLite mechanical substrate        → ALREADY EXTERNAL / CONSUMED
Game transaction + evidence rules  → KEEP
Snapshot semantic contract         → KEEP
New local persistence wrapper      → REJECT
Remote store replacement           → NOT_ADMITTED
```

## Cross-owner future path

If Game evidence must later cross into Host/Operations/Research, the mature migration shape remains a **transactional outbox**:

```text
Game authoritative local transaction
  → Game truth
  → durable outbox identity
COMMIT
  ↓
idempotent relay / external consumer
```

That can externalize *delivery* without creating a synchronous dual-write dependency or transferring Game World authority. It is not needed merely to clean up the current local store.

A future replacement is admitted only if it preserves or deliberately supersedes, with falsification evidence, exact idempotency, ordering, atomic Game/evidence relation, response-loss recovery, restart replay, historical Run readability and corruption detection.

## Replay and deployment consequence

No additional physical subtraction is admitted for `src/replay/*` or `src/deployment/*` in this round. Their current retained surfaces answer Game questions and encode evaluation conditions. Generic build/release/deployment and observability remain outside Game, but those are not implemented here as competing frameworks.

## Engineering rule

The next useful work is **not another persistence refactor**. Reopen this boundary only when one of these pressures exists:

1. a real cross-owner consumer requires durable event delivery;
2. SQLite becomes a measured product/runtime bottleneck;
3. a second Game proves a reusable persistence contract rather than Station Zero-specific semantics;
4. an external owner exposes a proven transaction/outbox interface satisfying the retained invariants.

Until then, keep the direct SQLite substrate and spend engineering effort on Game/product work rather than wrapper creation.

## Verification

Focused storage/replay/v3 persistence boundary suite: `63 / 63 PASS`. Full repository verification after freezing the boundary: `419 / 419 PASS`, `0 FAIL`. No production storage source was changed in this round; the added regression guard protects the existing external-substrate/direct-domain-semantics split.
