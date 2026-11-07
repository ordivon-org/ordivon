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
Both tasks invoke installed pytest directly, not a new harness. Use
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

## Current product surface

Host v2 runs Social Work Fabric schema 11. The release-owned
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
