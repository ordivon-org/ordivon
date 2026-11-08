# Ordivon Host v2

Clean-room, external-first reconstruction of Ordivon Host.

Host v1 is a behavioral/source oracle only. Host v2 does not import `ordivon_host` and does not copy its persistence implementation.

## Substrate

- PostgreSQL is the authority store.
- Psycopg owns database access and transaction primitives.
- Pydantic owns request/result validation.
- RFC 8785 owns canonical JSON bytes used for semantic digests.
- the official MCP Python SDK v2 owns MCP protocol/transport behavior.
- Alembic exclusively owns schema creation and migration; the running Host only verifies schema readiness.
- CrossHair checks pure Host source contracts symbolically; pytest/Hypothesis retain the database and real-consumer verification boundaries.

## Tests with mature upstream tools

The public canonical-JSON boundary has a real [Hypothesis](https://github.com/HypothesisWorks/hypothesis)
property/regression test in `tests/test_canonical_property.py`. Run the local
Owner's native `mise run test:focused`; select any existing pytest node with
`HOST_PYTEST_NODE=tests/test_contract_policy.py mise run test:focused`.
Both tasks invoke installed pytest directly, not a new harness.
For a physical, locally repeatable PostgreSQL 18 qualification, run
`mise run test:postgres:disposable` in `services/host`. This explicit
Owner-native entrypoint reuses the existing Host queue script and its
existing Docker `postgres:18` image, creates a random container name and password
bound to a loopback-only ephemeral port, executes Alembic migrations and all
existing real Host tests, and removes the test container on exit. It rejects
an inherited `ORDIVON_HOST_V2_TEST_DSN` rather than risk running local
disposable acceptance against a shared or production database. The default
`mise run queue` retains its original GitHub-hosted auto-provision boundary;
outside that runner it requires an explicit independent TEST_DSN.

Use
`mise run verify` for the full Host Owner test gate; it can legitimately
report database cases as SKIP without a database DSN, so focused/unit PASS
never claims PostgreSQL integration qualification.

## Host formal verification: Human and Agent entrypoints

**Human:** From services/host, run mise run formal:reply-source to check both
strict causal reply ordering and PostgreSQL-bounded Work revision increments
through the locked CrossHair symbolic executor. Run mise run verify for the
complete native Owner gate; a skipped PostgreSQL test is not a passing
database integration test. The selected invariant is revision r >= 1,
with r + 1 <= 2^63 - 1. A request at the signed BIGINT maximum is
invalid before PostgreSQL access because the next revision would overflow.

**Agent:** The proof subjects are the actual called functions
social_message_commands._reply_target_precedes_source and
work_store._next_work_revision, not separate model copies. Preserve their
PEP 316 pre/postconditions, re-run the same native CrossHair entrypoint
after changing these source files, and then qualify the Work CAS transaction
and reply-edge SQL using existing Host PostgreSQL consumer tests.
Formally confirmed pure arithmetic never certifies psycopg connection,
commit, concurrency, installed release, or MCP effects. PostgreSQL
numeric bounds are shared in postgres_bounds.py; do not recreate
per-module constants. The read-side Work.get accepts revisions up to the
signed BIGINT maximum, while Work.snapshot.commit requires a strictly lower
expectedRevision so an increment can be represented; both the native MCP
input and the WorkStore boundary enforce these domains.

### R2.1 declaration: Host Work snapshot compare-and-swap

This is **one independent formally DECLARED implementation-backed capability
LEGO**, not a declaration of all Host functions or an admission registry. The
effective contract is the existing `WorkStore.commit_snapshot` public behavior:

| Typed R2.1 coordinate | Host Work snapshot CAS interpretation |
| --- | --- |
| I | WorkRef, exact expectedRevision: int in [1, 2^63-2], WorkSnapshotInput, ActorRef, WorkState, ClientRequestId |
| O | Work readback with committed/existing admission, or a typed conflict/error; no claim of semantic Work completion |
| S | Actual Host PostgreSQL works, work_snapshots, actor_refs and command receipt rows in one transaction |
| pre | Exact bounded integer, valid typed payload/actor; a new commit requires current revision = expected and current state = open |
| post | On new commit revision increments by exactly one and current snapshot digest matches the canonical payload; exact replay or matching next revision yields existing, incompatible request conflicts |
| inv | At most one *different* snapshot can win the same expected revision; current Work pointer and immutable snapshot row agree; terminal Work cannot be reopened through a new commit |
| eff | Atomic PostgreSQL row-lock/CAS, snapshot insert and durable idempotency receipt; no Runtime Job or external domain effect |
| c | UNKNOWN(reason=unmeasured transaction latency under realistic contention, scope=Host PG18 Work CAS, obligation=record consumer-relevant cost if optimizing) |
| epsilon | UNKNOWN(reason=no general quantified external availability/failure bound, scope=database/deployment effects, obligation=qualify installed PG consumer); pure revision arithmetic is exact |
| prov | Actual code in `src/ordivon_host_v2/work_store.py` and `work_queries.py`; locked CrossHair 0.0.112 source contract, real PostgreSQL 18 Alembic/pytest via `mise run test:postgres:disposable`, exact SourceCut is the tested Git revision |
| unfold | `WorkStore.commit_snapshot` -> claim_command_receipt -> _next_work_revision / canonical_digest -> PostgreSQL conditional UPDATE / INSERT -> _get_work_in_tx -> record_command_receipt |

Evidence standing is **DECLARATION_COMPLETE** for this scoped contract; the
native CrossHair confirms the called revision arithmetic only, while the
disposable PostgreSQL 18 test suite covers **specific actual transaction and
consumer scenarios**. Neither provides a universal deductive proof of
PostgreSQL concurrency, a Rust/TLA-style refinement of all SQL operations,
an installed production SourceCut witness, or DOMAIN_ACCEPTED. Preserve these
distinct proof obligations; do not delete the real CAS/race/replay tests merely
because the revision increment has a source-level proof.

## Host Owner operation guide

See [Host Owner Guide](docs/HOST_OWNER_GUIDE.md) for directory retention decisions, reusable LEGO boundaries, and separate Human/Agent workflows. This guide is not a second authority for the MCP tool list or database schema.

Work Graph relation commands and cycle detection now live in src/ordivon_host_v2/work_relation_commands.py, composed by the existing WorkStore. This internal split does not introduce a second database or a public MCP tool.

## Current product surface

Host v2 runs Social Work Fabric schema 13. The release-owned
[`mcp-surface.json`](mcp-surface.json) is the single declared inventory of
MCP tools; native tests compare that manifest with the actual server surface.
Do not maintain an independent count or partial list of current tools here.
The active tool families cover Host integrity, Work continuity, Space/Topic/Message
collaboration, Subscription and Attention navigation.

Legacy `task.*` and `board.*` tools and their active PostgreSQL storage are physically retired. Historical recovery evidence is retained separately and does not constrain the active model.

The active ontology is intentionally orthogonal: `Work` owns revisioned semantic continuity, `Space`/`Topic`/`Message` own collaboration structure, and `Subscription`/`Attention` own rebuildable actor-scoped navigation. Work state is not chat history, social participation is not assignment or authorization, and Attention is not priority or scheduler truth.

Re-entry uses two different cursors: `attention.*` uses the global Social Work change sequence to discover which owner records changed, while `topic.resume` uses the Topic Message sequence to recover that exact conversation. Agents must not substitute one cursor domain for the other.

Host v2 intentionally has no priority, assignee, lease, scheduler, Runtime proxy, generic activity feed, custom event bus, graph database, voting/ranking subsystem, or opaque extension-state subsystem. Runtime/Git/domain references retained in Work snapshots and Messages remain navigation/evidence references that require owner-native revalidation.

External-news publication is not a Host responsibility. Its unconsumed \`news_publications\` table and historical data were retired with Alembic revision 0011, rather than kept as an inactive product surface.

Production releases are immutable Git-SHA directories with a release-local `.venv`; systemd executes only `/opt/ordivon/host-v2/current/.venv/...`. This prevents a shared Python environment from retaining stale code when the package version is unchanged.

Host v2 intentionally does not restore v1's SQLite Journal/WAL/file-lock machinery, filesystem CAS for normal JSON payloads, separate SQLite Board FTS sidecar, Runtime/Harness/provider proxying, historical cognition execution stack, or a separate ContinuityLens subsystem.

See `docs/SOCIAL_WORK_FABRIC_R2_SPEC.md` for the active Social Work Fabric contracts and `docs/SOCIAL_WORK_FABRIC_R2_IMPLEMENTATION.md` for source-bound implementation receipts. `docs/SOCIAL_WORK_FABRIC_R1.md` is historical evidence, not current schema or API authority.


### PostgreSQL connection lifecycle

The MCP process owns one native Psycopg ConnectionPool, created in main()
and closed on stdio/HTTP server exit. Work, Social, Attention and Host status
all borrow from that same bounded pool; each operation retains its existing
Psycopg transaction and isolation level. build_server(dsn) and direct Store
constructors still use single-use native Psycopg connections for callers that
own no process pool (e.g. schema preflight and isolated tests).

ORDIVON_HOST_V2_PG_POOL_MAX_SIZE defaults to 8 (accepted 1..64).
The queue is limited to 64 waiters and checkout timeout is 5 seconds.
This is backpressure, not a claim about domain completion or automatic retry.
Use mise run test:postgres:disposable to run actual PostgreSQL 18 / Alembic
and native-pool rollback, bound and full MCP consumer tests. Ordinary pytest
runs without the disposable DSN skip PostgreSQL tests and do not constitute
an installed-Host qualification.
