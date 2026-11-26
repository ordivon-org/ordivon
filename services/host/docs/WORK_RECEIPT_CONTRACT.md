# Work receipt contract

从 [Host Owner Guide](HOST_OWNER_GUIDE.md) 迁移的原契约。该文件承载相关职责的操作约束与历史资格证据；不另立运行时权威。

<a name="contract-1"></a>

### Work receipt retention — schema 0017 preparation

The existing Work receipt and snapshot tables own the retention relation.
A compact receipt binds its exact historical (workRef, revision) through a
nullable pair and a native MATCH FULL foreign key. Full legacy receipts and
unfinalized claims have no root pin. The CHECK binds the compact tag, operation
and typed identity; the replay codec still validates payload and response
digests. No separate retention registry or ordinary request-time graph scan.

0017 installs the validated legacy-only format fence. The service continues
to write full receipts; do not enable compact writers during this deployment.
Quiesce old serving readers, qualify the new installed generation and verify
the current schema, all consumers, backup and rollback first. The FK protects
existence, not content mutation or deliberate privileged deletion of receipts.

Before a future downgrade after compact writes, use the existing operator's
authorized maintenance transaction with bounded lock/statement timeouts and
call work_receipt_retention.expand_work_receipts_and_fence on its Psycopg
dict-row connection. It takes an exclusive lock, reconstructs the exact old
response and restores the legacy-only fence atomically. Any failure must
roll back the operation. A native savepoint prevents partial expansion even
if the caller catches a domain failure; the caller still owns final commit.
An already validated exact fence with zero roots returns zero newly expanded
rows, not the previous operation's count. Independently check the validated
fence and zero pins before
alembic downgrade; the migration rejects missing/weaker fences or surviving
compact roots. On ambiguous commit, inspect actual native state before retry.
Do not treat this source contract as production activation authority.

<a name="contract-2"></a>

### Receipt-root audit: native set association

Schema 0017 history audit streams the existing typed receipt-to-snapshot
association through one native LEFT JOIN (128 rows per cursor batch).
The read-only caller owns the repeatable-read cut. The shared codec still
validates the exact envelope, native coordinates, writer, snapshot digest
and reconstructed response digest. The ordinary request replay retains
its exact single lookup; the history audit must not hide a missing target,
a malformed Work receipt or a pin inconsistent with its operation.
Unpinned legacy full receipts remain self-contained. A history diagnostic
without typed schema roots is explicitly unavailable, not an absence proof.
No retirement or writer activation is implied by successful read-only audit.

<a name="contract-3"></a>

### Receipt maintenance: bounded native expansion

The maintenance operator reuses the native root projection and exact
hydration contract of the history audit; its candidate set is specifically
typed pins or the compact format tag. Unpinned legacy data is not rewritten.
Under the existing exclusive receipt lock and caller-owned savepoint, it
stages at most 128 responses or 4 MiB of canonical response bytes per update
batch, with a single larger response handled independently. This is a
transport batching target, not a new business payload limit or an absolute
memory/wire bound. The server cursor retains its bounded row fetch.

Native UPDATE FROM UNNEST consumes exact keys and JSON text converted back
to JSONB. The returned key set must equal the staged key set; counts alone
cannot qualify expansion. Any invalid coordinate, digest, missing target,
operation, or incomplete/relabelled update rolls back the whole maintenance
operation, even if its caller catches the error. Only after every batch is
qualified does the existing legacy-only fence become active. The caller
still controls the outer transaction and timeouts.

<a name="contract-4"></a>

### Dual-mode Work receipt writer (source candidate; default unchanged)

The existing MCP process composition accepts a strict
`ORDIVON_HOST_V2_COMPACT_WORK_RECEIPTS` option (0 by default, 1 requests
compact writes). This option does not authorize a migration or remove the
native legacy-only constraint. When the option is disabled the original
full-receipt write path incurs no extra database statements. When enabled,
the existing idempotency claim already holds ROW EXCLUSIVE until commit:
the writer observes the native fence inside that transaction, never caches
the mode, and writes full receipts when the validated fence is present.
An absent fence alone is insufficient: compact writes require the exact
validated and enforced schema-17 shape and root FK contracts, with the
PG18 deparsed definitions serving as independent qualification oracles.
A weak/unrecognized contract fails closed. Exact replay is validated before
atomically finalizing the tag and native pin in the same claim transaction.

Rollback takes the existing exclusive lock, expands all exact roots in a
savepoint and restores the validated legacy-only fence. Waiting opted-in
READ COMMITTED writers reobserve the fence after claim admission and fall
back to full receipts; no restart is required for that fallback.
The source option is not a production activation procedure. Before any
activation, qualify the installed schema, real consumer/rollback reader
fleet, recovery cut and release admission. No automatic DDL or historical
deletion is introduced.

Native root qualification also observes the four internal PostgreSQL FK
triggers (insert/update checks and target delete/update restrictions).
The ordinary origin session must see all four exact native signatures
enabled for origin or always. Catalog constraint definitions alone do
not prove active enforcement. This is a qualification of the observed
schema under the existing transaction, not a claim that a privileged
administrator cannot subsequently change database configuration.

<a name="contract-5"></a>

### Point replay observes the persisted root

The Work command path reuses the generic idempotency claim arbiter and
conflict validation, then observes the stored receipt row and schema
version in a single SQL statement. A legacy response must have no native
pin; a compact response must have the exact persisted native work/revision
identity, agreeing with the requested context and immutable envelope.
The shared codec verifies the exact indexed historical target. The
ordinary two-statement legacy replay and three-statement compact replay
(including the claim) are preserved, without an extra schema query.
A whole-row projection also preserves the explicitly tested schema-16
rollback compatibility; missing pin columns under schema >=17 are errors.
Bulk audit/maintenance retains its set-oriented root projection.

The batch expansion effect is qualified independently of UPDATE RETURNING.
For each bounded batch, a subsequent native set readback checks the exact
identity set, JSONB response, original operation and request digest, and
both cleared pin coordinates. Only identifiers and qualification booleans
are returned to the application; the expected encoded responses are sent
once for the update and again for the comparison. This catches ordinary
BEFORE and AFTER trigger rewrites of the batch's rows; it does not claim
protection against arbitrary later privileged DDL or unrelated trigger
side effects. The original exclusive lock and whole-operation savepoint
remain in force. No new payload admission limit or storage authority is
introduced.
