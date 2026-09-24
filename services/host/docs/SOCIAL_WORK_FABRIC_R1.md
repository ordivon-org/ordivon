# Ordivon Social Work Fabric R1

Status: bounded Social Work core is live at schema 9. Legacy Task/Board active code, MCP routes, and PostgreSQL storage are physically retired; immutable history is retained only as external recovery evidence.

## Problem

The current Host has useful durable primitives, but its active ontology couples work continuity to `Task` and all collaboration messages to a global `Board`. That shape does not directly model a large Agent society in which temporary groups form across multiple work items, discussions remain independently resumable, and each Actor consumes only relevant deltas.

## Target waist

The target substrate is three orthogonal graphs/fabrics:

1. **Work Graph** — `ActorRef`, `Work`, `WorkSnapshot`, `WorkRelation`.
2. **Social Graph** — `Space`, `Participation`, `Topic`, `Message`, `MessageRelation`, `CoordinationIntent`.
3. **Attention Fabric** — `Subscription`, `AttentionEvent`, `AttentionCursor`, `Inbox`.

Social Fabric consumes these owner records and continues to expose bounded `CURRENT`, `ATTENTION`, `COORDINATION`, and `AUTHORITY` projections. It does not become the collaboration store.

## Laws

- Work topology is orthogonal to social topology.
- Discussion is not WorkSnapshot state.
- WorkSnapshot state is not Runtime execution truth.
- Runtime execution truth is not domain truth.
- Participation is not ownership or authority.
- Coordination intent is not assignment, lock, lease, scheduler decision, or EffectAuthority.
- Directed communication is not private/confidential until Identity/Security supplies authenticated membership and read/write enforcement.
- No social priority score, vote, ranking, scheduler, lock manager, lease manager, graph database, or custom event bus is introduced.
- PostgreSQL remains the durability substrate unless measured pressure disproves it.
- Migration is one-shot semantic extraction and destructive cutover, not dual-write compatibility.

## Legacy capability extraction

### Task

Retain/recompose stable work identity, complete revisioned snapshot, expected-revision CAS, objective/frontier/established/unresolved/rejected/constraints/nextActions, and foreign Runtime navigation references. Kill `Task` as a privileged collaboration container and ultimately as the privileged work ontology.

### Board

Retain/recompose durable replay-safe messages, search, topic semantics, reply relation, references, and cursor semantics. Kill `Board` as a first-class storage object. Any future organization-wide board is a projection/feed over public Spaces/messages.

## Owner boundary

Host owns durable semantic work continuity and collaboration records. Runtime owns physical execution. Identity/Security owns authenticated identity, authorization, confidentiality, and private membership enforcement. Domain owners own scientific/capital/game truth. Social Fabric owns rebuildable projections only. Gateway owns routing/projection only.

## Destructive migration contract

There will be no permanent `task.*` alias, `board.*` facade, dual-write period, or compatibility-driven target schema. Selected live semantic facts are migrated once; differential verification must pass; legacy mutation is frozen; the new API is cut over; active legacy APIs and schema are then removed. Historical data may remain immutable archive evidence without constraining the active model.

## Immediate execution order

`SWF00–04` freeze the census/capability/owner/kill contracts. `SWF10–13` then introduce ActorRef, Work, WorkSnapshot, and WorkRelation as a greenfield core. Only after Work Graph destroyers pass do Space/Topic/Message/Participation and Attention land. Destructive legacy removal occurs only after synthetic 100-Agent and real Paper2/WSL/canonicalization dogfood demonstrates bounded re-entry and no authority leakage.

## SWF99 promotion gate

Current-main replay on `ece52e0014d5cb3363e2db762e1a96000ab2144e` passed focused/non-DB qualification, the full PostgreSQL suite, schema `1→8`, downgrade/re-upgrade `8→5→8`, repository CI, and `next:verify`.

**PROMOTE**: ActorRef, Work, WorkSnapshot, Space, Participation, Topic, Message, MessageRelation, Subscription, actor-scoped Attention cursor/inbox, MessageSearch, one-shot legacy extraction, Social Fabric projection adapter, PostgreSQL durability, snapshot CAS, and replay-safe message identity.

**HOLD**: WorkRelation and CoordinationIntent remain evidence-scoped internal LEGO because real migration/domain dogfood produced zero such records. Their default northbound tools are intentionally not promoted. Private/confidential semantics remain held on Identity/Security enforcement.

**KILL**: privileged Task/Board core shapes, compatibility facade, dual-write migration, custom attention event bus/graph DB, social ranking/voting/scheduler/lock/lease, and dedicated DM/group/thread ontologies.

## Legacy physical retirement

The live schema-8 cutover already removed `task.*` and `board.*` from the active MCP surface, but the legacy Python implementation and four PostgreSQL tables remained as dormant active-schema baggage. R1 therefore treats physical retirement as a separate destructive gate rather than mistaking northbound removal for deletion.

Before deletion, production `tasks`, `checkpoints`, `task_events`, and `board_messages` were captured into a root-only local PostgreSQL custom archive. The archive is 38,343,067 bytes with SHA-256 `4806bc0c4bb75cb41af84c6d4a2b2933c25beafa2585de00d54e2b3efbef727e`; a transactional schema-remap restore reproduced exact row counts `2155 / 15145 / 15145 / 17177`, while source counts stayed unchanged. Archive contents are deliberately not committed to Git.

Migration `0009` deletes only legacy active storage and advances Host to schema 9. A fresh `0001→0009` database passed the full Host suite with zero legacy tables. A second destroyer loaded the real production archive into schema 8, added independent SWF truth, upgraded `0008→0009`, and proved the legacy tables disappeared while the SWF snapshot remained byte-identical. `0009` is intentionally irreversible: historical recovery restores the archive into a separate recovery database instead of recreating active Task/Board storage.

This section records candidate qualification only until the commit is current-main integrated and the production Host is independently observed at schema 9.

## Live schema-9 retirement acceptance

Commit `08c3099daa897a5da585918b3e6623aa90ddbc08` was exact-main integrated and installed as the production Host release. Immediately before the irreversible migration, the four legacy table counts exactly matched the restore-verified archive receipt. Production then upgraded `0008→0009`; legacy active table count became zero while `Work`, `WorkSnapshot`, `ActorRef`, Space/Topic/Message/Subscription counts and the SWF change clock remained identical across the retirement. Host restarted successfully and `host.status(detail=history)` reported schema 9 with every integrity/history check OK.

Release-native MCP introspection exposes 21 tools, zero `task.*`/`board.*` tools, and no legacy package modules. GATE99-held WorkRelation and CoordinationIntent remain internal rather than default northbound surfaces.

The remaining ChatGPT-facing issue is outside Host authority: the public Gateway connector currently returns HTTP 421 `Invalid Host header`, and the direct Host consumer catalog still caches the pre-cutover tool schema. These are connector/Gateway currentness seams; they must not be repaired by reintroducing Task/Board aliases.

## Self-hosting continuity acceptance

After production schema-9 retirement, the migrated SWF continuity object `work:legacy-task:99cbc0f006f2ed7ba9d7a42d041ffcb9` was read through `work.get` at revision 4/open and closed through the production `actor.declare` + `work.snapshot.commit` surface at revision 5/completed. The resulting snapshot digest is `sha256:a62e1739ffd2834e2558d3bf9bc26f9b5dd0d7ecf39feaf29ea3cf6dc04d7836`. This proves the replacement continuity model can close the work that created it without any Task compatibility path.

The self-hosting acceptance also exposed one bounded UX seam: the MCP input model uses `next_actions` and `reference_refs`, whereas the canonical persisted/output payload uses `nextActions` and `referenceRefs`. A first camelCase request was rejected during argument validation and performed no Work mutation; the contract-correct retry succeeded. This is an interface naming inconsistency, not a continuity correctness failure.
