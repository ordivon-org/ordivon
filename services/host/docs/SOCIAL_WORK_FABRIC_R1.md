# Ordivon Social Work Fabric R1

Status: destructive recomposition candidate. Legacy Task and Board shapes have no inheritance right.

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
