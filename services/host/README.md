# Ordivon Host v2

Clean-room, external-first reconstruction of Ordivon Host.

Host v1 is a behavioral/source oracle only. Host v2 does not import `ordivon_host` and does not copy its persistence implementation.

## Production-compatible Topic archive release

The currently installed direct Host Cloudflare Access connector and local
Gateway consume the pre-existing loopback Host HTTP transport without a Host
Owner bearer. A Schema14 function-only deployment may explicitly set
ORDIVON_HOST_V2_LEGACY_DIRECT_HTTP=true on the Host systemd service to retain
that existing ingress while upgrading the native Topic archival schema.
The listener still must bind loopback and requires the existing canonical
ORDIVON_HOST_V2_PUBLIC_ORIGIN HTTPS setting. Cloudflare Access must remain
active; this switch does not establish Principal or Host delegation.

Without that explicit compatibility flag, the new Host HTTP service still
requires ORDIVON_HOST_V2_OWNER_BEARER_TOKEN_FILE. Configuring both is an
error rather than allowing anonymous override. Remove the compatibility
mode only after all real direct MCP clients, Gateway/peer and Cloudflare
consumers migrate to Owner-credentialed access. This does not alter any
Tool semantics, PostgreSQL grants or the independent Gateway release gate.

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
property/regression test in `tests/test_canonical_json_property.py`. Run the local
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

## Work / Topic / Message lifecycle and archival boundary

Host owns semantic continuity, not the lifecycle of an external Runtime Job or
domain Goal. Do not terminalize records because they have been idle for N days.

- Work: open may be explicitly committed via the existing CAS to completed or
  abandoned, with a final current checkpoint. Terminal Work remains readable
  by work.get and may be excluded from an Agent's active inventory with the
  existing work.list(state="open") filter. Old Work revisions are optional
  retained history, not mandatory duplicate archives.
- Topic: open accepts messages; closed rejects new messages but may be
  reopened. A closed Topic may be changed via existing topic.state.set CAS to
  archived; archived rejects posts and is hidden from default topic.list.
  topic.list(includeArchived=true) exposes it, and topic.resume still reads
  its original messages. Explicit restoration: archived -> closed -> open,
  each transition rechecking the topic's message horizon and lifecycle occurrence.
  Epoch 9 / Host 0.11.0: read `topic.resume`'s `topic.changeSequence` and
  `topic.topicHighSequence` in the same snapshot, then supply
  `expectedChangeSequence`, `expectedHighSequence` and `expectedState`
  to `topic.state.set`. The positive change coordinate is an exact identity
  of the Topic row lifecycle, not an Attention ACK or a message cursor.
  Repeated close/reopen at an unchanged message horizon must use a fresh
  observed change coordinate; an exact old request is a historical receipt
  replay and cannot close the current Topic. An unversioned legacy request is
  rejected rather than silently replaying a different occurrence.
- Message: Messages are immutable. Their logical archive tier is inherited
  from the Topic; message.get(messageRef, expectedDigest) still retrieves the
  exact content after Topic archive. Existing direct search and historical
  references remain available. This is not physical deletion or off-host cold
  storage.

Physical retention is a separate operator decision. A candidate can be
inspected based on closed/archived Topic, terminal Work and record age, but no
time threshold alone proves that linked Work snapshots, message_relations
(including text target references), subscriptions, Topic/Attention cursors,
command receipts or external consumers are released. Physical purge requires
a verified restorable archive and exact consumer closure; current source does
not automatically purge Messages, Topics, Works, or references. Keep existing
pgBackRest backup separate from a selective retrievable archive; backup
verification is not consumer-safe deletion proof.

## Attention recovery model (one transaction cut)

From the repository root, run `mise run host:formal:attention-reentry` with the existing pinned TLA+ JAR.
The model covers interleaved relevant/unrelated change commits, monotone ACKs,
one-page re-entry and one captured MVCC cut. Both mixed-snapshot Topic cursor
and non-final page skipping are falsified with separate unsafe transitions.
This is a bounded abstract model, not a PostgreSQL SQL/source refinement or
installed Agent proof: retain the existing real PG18 single-snapshot and
pagination consumer tests. No new Host database, Tool or model executor.

## Host formal verification: Human and Agent entrypoints

**Human:** From services/host, run mise run formal:reply-source to check both
strict causal reply ordering and V1 JSON-safe Work revision increments
through the locked CrossHair symbolic executor. Run mise run verify for the
complete native Owner gate; a skipped PostgreSQL test is not a passing
database integration test. The selected invariant is revision r >= 1,
with r + 1 <= 2^53 - 1. A request at the JSON safe integer maximum is
invalid before PostgreSQL access because the next revision would exceed the wire domain.

**Agent:** The proof subjects are the actual called functions
social_message_commands._reply_target_precedes_source and
work_revision_logic.next_work_revision, not separate model copies. Preserve their
PEP 316 pre/postconditions, re-run the same native CrossHair entrypoint
after changing these source files, and then qualify the Work CAS transaction
and reply-edge SQL using existing Host PostgreSQL consumer tests.
Formally confirmed pure arithmetic never certifies psycopg connection,
commit, concurrency, installed release, or MCP effects. PostgreSQL
and V1 JSON numeric bounds are shared in postgres_bounds.py; do not recreate
per-module constants. The read-side Work.get accepts revisions up to the
JSON safe integer maximum, while Work.snapshot.commit requires a strictly lower
expectedRevision so an increment can be represented; both the native MCP
input and the WorkStore boundary enforce these domains.

### R2.1 declaration: Host Work snapshot compare-and-swap

This is **one independent formally DECLARED implementation-backed capability
LEGO**, not a declaration of all Host functions or an admission registry. The
effective contract is the existing `WorkStore.commit_snapshot` public behavior:

| Typed R2.1 coordinate | Host Work snapshot CAS interpretation |
| --- | --- |
| I | WorkRef, exact expectedRevision: int in [1, 2^53-2], WorkSnapshotInput, ActorRef, WorkState, ClientRequestId |
| O | Work readback with committed/existing admission, or a typed conflict/error; no claim of semantic Work completion |
| S | Actual Host PostgreSQL works, work_snapshots, actor_refs and command receipt rows in one transaction |
| pre | Exact bounded integer, valid typed payload/actor; a new commit requires current revision = expected and current state = open |
| post | On new commit revision increments by exactly one and current snapshot digest matches the canonical payload; exact replay or matching next revision yields existing, incompatible request conflicts |
| inv | At most one *different* snapshot can win the same expected revision; current Work pointer and immutable snapshot row agree; terminal Work cannot be reopened through a new commit |
| eff | Atomic PostgreSQL row-lock/CAS, snapshot insert and durable idempotency receipt; no Runtime Job or external domain effect |
| c | UNKNOWN(reason=unmeasured transaction latency under realistic contention, scope=Host PG18 Work CAS, obligation=record consumer-relevant cost if optimizing) |
| epsilon | UNKNOWN(reason=no general quantified external availability/failure bound, scope=database/deployment effects, obligation=qualify installed PG consumer); pure revision arithmetic is exact |
| prov | Actual code in `src/ordivon_host_v2/work_store.py` and `work_queries.py`; locked CrossHair 0.0.112 source contract, real PostgreSQL 18 Alembic/pytest via `mise run test:postgres:disposable`, exact SourceCut is the tested Git revision |
| unfold | `WorkStore.commit_snapshot` -> claim_command_receipt -> next_work_revision / canonical_digest -> PostgreSQL conditional UPDATE / INSERT -> read_work_in_tx -> record_command_receipt |

Evidence standing is **DECLARATION_COMPLETE** for this scoped contract; the
native CrossHair confirms the called revision arithmetic only, while the
disposable PostgreSQL 18 test suite covers **specific actual transaction and
consumer scenarios**. Neither provides a universal deductive proof of
PostgreSQL concurrency, a Rust/TLA-style refinement of all SQL operations,
an installed production SourceCut witness, or DOMAIN_ACCEPTED. Preserve these
distinct proof obligations; do not delete the real CAS/race/replay tests merely
because the revision increment has a source-level proof.

## First-principles Host logic and capability composition

[Host Logic Capability Architecture R1](docs/LOGIC_CAPABILITY_ARCHITECTURE_R1.md) derives the Work/Social/Attention continuity requirements from actual failure and recovery scenarios, maps Thought/Logic/Capability LEGO, and records the current directory/module boundaries. The first source extraction separates ActorRef semantics from Work and read-only Doctor from the Host service façade, without changing MCP contracts or granting permissions.

## Host Owner operation guide

See [Host Owner Guide](docs/HOST_OWNER_GUIDE.md) for directory retention decisions, reusable LEGO boundaries, and separate Human/Agent workflows. This guide is not a second authority for the MCP tool list or database schema.

Work Graph relation commands and cycle detection now live in src/ordivon_host_v2/work_relation_commands.py, composed by the existing WorkStore. This internal split does not introduce a second database or a public MCP tool.

## Current product surface

Host v2 runs Social Work Fabric schema 17 **when this source release is installed**; the running production schema must be read independently. The release-owned
[`mcp-surface.json`](mcp-surface.json) is the single declared inventory of
MCP tools; native tests compare that manifest with the actual server surface.
Do not maintain an independent count or partial list of current tools here.
The active tool families cover Host integrity, Work continuity, Space/Topic/Message
collaboration, Subscription and Attention navigation.

Legacy `task.*` and `board.*` tools and their active PostgreSQL storage are physically retired. Historical recovery evidence is retained separately and does not constrain the active model.

Work continuity is **current-snapshot-first**: the only mandatory revision is
the current Work snapshot. Earlier revisions may be retained or pruned according to
real consumer needs; missing historical revisions are not a Host health failure.
`work.get(revision=old)` may return a typed not-found/conflict when that revision
was pruned. The current snapshot's stored digest and payload must still agree,
and PostgreSQL CAS must still arbitrate concurrent updates. The `history` Doctor
verifies the integrity of any history that remains, but no longer requires
a gap-free archive. This is a contract change, not proof that production
has already compacted its older snapshots.

The active ontology is intentionally orthogonal: `Work` owns revisioned semantic continuity, `Space`/`Topic`/`Message` own collaboration structure, and `Subscription`/`Attention` own rebuildable actor-scoped navigation. Work state is not chat history, social participation is not assignment or authorization, and Attention is not priority or scheduler truth.

Re-entry uses two different cursors: `attention.*` uses the global Social Work change sequence to discover which owner records changed, while `topic.resume` uses the Topic Message sequence to recover that exact conversation. Agents must not substitute one cursor domain for the other.

Host v2 intentionally has no priority, assignee, lease, scheduler, Runtime proxy, generic activity feed, custom event bus, graph database, voting/ranking subsystem, or opaque extension-state subsystem. Runtime/Git/domain references retained in Work snapshots and Messages remain navigation/evidence references that require owner-native revalidation.

External-news publication is not a Host responsibility. Its unconsumed `news_publications` table and historical data were retired with Alembic revision 0011, rather than kept as an inactive product surface.

The Host installer accepts an optional fifth argument --prepare-only
only when the fourth argument pins an independently reviewed Host Git tree
OID. Preparation verifies immutable Git source, MCP tool surface, exact
Python/uv versions and the locked release-local package, but leaves current
and the systemd process intact and prints activation=NOT_PERFORMED. A later
ordinary activation independently revalidates the same immutable candidate.
This mode does not authorize a deployment, reload secrets, provision Actor
Grants or prove migration of the main/peer Gateway and Cloudflare clients.
The separate Gateway Host/Security release check and live positive/negative
Agent consumers must still pass before cutting over the single Host Writer.

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

When a native pool checkout times out or its waiting queue rejects an
unadmitted request, MCP returns a bounded typed Host error:
DEADLINE_EXCEEDED for PoolTimeout, or RESOURCE_EXHAUSTED for
TooManyRequests, with retryable=true and retry-with-bounded-backoff.
These Psycopg errors occur before a connection checkout; the adapter
does not retry effects or expose DSN/internal exception messages. Other
operational failures such as a closed pool retain the normal generic
internal error boundary.

## Native PostgreSQL pool diagnostics (introduced with Host surface epoch 6)

The read-only host.pool.stats MCP tool uses Psycopg's official
ConnectionPool.get_stats() in the serving Host process. It does not
open a new database connection, run SQL, mutate counters, or introduce a
metrics database/collector. Direct (unpooled) test servers report
connectionMode=direct and stats=null, rather than pretending that
a PostgreSQL pool exists. A real Host server reports the fixed set of
15 upstream integer fields, filling omitted upstream zero-valued keys
with 0 and never returning credentials, DSN or private exception details.

Human: inspect host.pool.stats to read pool_size/pool_available,
requests_waiting, requests_queued, requests_errors, requests_wait_ms,
and connections_errors while diagnosing connection pressure. Stats are
per-process snapshots: after systemd restart, counters start fresh.
requests_wait_ms and usage_ms are cumulative milliseconds, not
p95/p99 latency histograms. For those quantiles, use a time-series
telemetry consumer with correct histogram instruments rather than
mislabelled derived averages.

Agent: treat this tool as process-local operational diagnostics, not Host
Work/Social/Attention domain truth and not PostgreSQL-cluster-wide state.
Do not call pop_stats() from a monitoring reader: it resets counters,
so repeated consumers would interfere with each other. Never derive
domain acceptance, scheduling priority, or a safe command retry from
a pool gauge alone; typed pre-checkout rejections have their own
MCP error contract.

## MCP input/output consumer contract release gate

The published MCP surface is not only a set of Tool names. Agents cache tool
input/output schemas and cannot use newly added arguments if their discovery is
stale. `mcp-surface.json` carries the native SDK `tools/list` contract digest;
`packaging/verify_tool_surface.py` requires a new surface epoch and package
version whenever Tool names or input/output contracts change. After the frozen
release-local `uv sync --locked`, `packaging/verify_release.py` asks the official
MCP SDK for the actual Host schemas and checks the digest **before** the service
symlink can move. This reuses the existing Gateway technique; it adds no second
registry, database or new public Tool. Client reconnect/recapture is still
required when a consuming platform serves an older cached Tool schema. A source
check alone is not an installed Agent consumer acceptance.

## Bounded consumer architecture

[Consumer Architecture R1](docs/CONSUMER_ARCHITECTURE_R1.md) records the
current Work/Social/Attention dependency direction, real consumers, rejected
second authorities and closure conditions. It does not replace the MCP surface,
PG migration chain or the installed Agent consumer observations.


### Numeric V1 interoperability (surface epoch 8)

Host numeric input coordinates (revision, cursor, expected Topic horizon and
message/intent timestamps) must be exact nonnegative JSON integers at most
2^53-1; a new Work CAS must leave room for its successor. The physical PG
BIGINT capacity is unchanged. Existing valid request IDs, JCS bytes, digest
and receipts are unchanged; no automatic string conversion or data migration.
The official native tools/list declares the input limits. Larger exact values
would require a versioned string-based wire contract and consumer migration.
Gateway ingress validation and imported/generated rows approaching this bound
are separate consumer/operational obligations, not certified by this input change.
