# Generated coordinate closure (schema 15 candidate)

## Problem and evidence

The exact JSON integer input contract is insufficient if a valid command can
produce a coordinate outside the same range. On Host #2624, two fresh PG18
databases reproduced this using disposable-only boundary seeding: a legal
message.post committed sequence or change_sequence 9007199254740992, while
topic.resume or attention.reentry then failed canonical JSON encoding.
Runtime job: job-01a20c0b-02c4-73cb-8fdc-baa189a31b16.

## Logic and ownership

Message identity and the transactionally serialized global change clock remain
separate coordinate domains. Their representability bound is 2^53-1, not
their physical bigint storage limit. The existing PostgreSQL allocator, not
MCP or a new counter service, owns allocation. No reset, cycle, rewrite,
renumbering or attempt to force gapless message identity is introduced.

Alembic 0015 bounds the message identity sequence and validates its stored
rows, the clock and all current change_sequence columns. A rejected clock
increment rolls back its whole caller-owned transaction; native identity
sequence gaps on a failed transaction remain permissible. At the bound a
new command returns non-retryable RESOURCE_EXHAUSTED; existing receipts
replay, and existing rows remain readable. Unrelated check violations are
not translated into capacity errors. This is the generated-coordinate slice,
not a claim that arbitrary privileged imports of every Host integer are safe.

Migration validates existing data instead of silently repairing it. Apply
only under the normal independently reviewed release gate; validate the
actual installed source and real data, lock impact, allocator position,
backup/rollback plan, compatible clients and owner authorization. Downgrade
removes the fences without resetting coordinates; it restores the old risk.
A future wider wire contract requires versioned exact representation (not
an automatic fallback to imprecise numbers or an in-place counter reset).

## Reproducible validation

Host queue automatically creates two *additional fresh capacity databases* only when
it owns a new disposable PostgreSQL container. The tests refuse nonempty
fixture databases before seeding. With caller-supplied test DSN, these cases
are skipped unless separate fresh schema-15
ORDIVON_HOST_V2_BOUNDARY_MESSAGE_DSN and
ORDIVON_HOST_V2_BOUNDARY_CHANGE_DSN are explicitly supplied.

The native MCP test commits the last representable coordinate, reads Topic
and Attention through their normal tools, rejects the next write without
adding a row or receipt, and replays the original exact message. No production
counter may ever be seeded to test this.

Source candidate depends on #2624 exact integer wire admission. Its schema
15 is not deployed; the old production schema remains 14. A merged source
or a passing scratch test is not independent release authorization.

The same owned disposable queue creates three more schema-14 fixtures for
migration rejection: out-of-range global clock, out-of-range historical
change_sequence with an otherwise valid clock, and message identity allocator
already beyond the new maximum. Each must reject the upgrade and preserve
exact old Alembic/schema versions, clock, row, sequence bound/position and
the full native constraint catalog. The negative fixtures require separate
ORDIVON_HOST_V2_MIGRATION_CLOCK_DSN, ORDIVON_HOST_V2_MIGRATION_HISTORY_DSN,
ORDIVON_HOST_V2_MIGRATION_ALLOCATOR_DSN when run manually. Tests refuse
nonempty or non-schema-14 fixture databases before seeding. This evidence
proves transactional rejection on these cases, not actual production data
standing or migration lock duration.

For the fourth dedicated schema-14 fixture (ORDIVON_HOST_V2_MIGRATION_LOCK_DSN),
a real reader holds ACCESS SHARE on the last constrained table. A migration
client with session-local PGOPTIONS lock_timeout=500ms and
statement_timeout=10000ms must fail, roll back all earlier DDL, and succeed
after natural lock release. For an authorized deployment choose the actual
lock and statement timeouts explicitly for that session; quiesce affected
consumers, do not kill unrelated writers or globally change PostgreSQL
settings. The bounded test is not evidence of production lock duration.


## Native serving-process readiness

The production main unit historically called HostV2.initialize() in its
ExecStartPre; the standalone STDIO entrypoint and protected HTTP unit did not.
The shared serving entrypoint now checks the existing owner schema using the
same native pool before either transport serves. build_server() deliberately
remains an offline SDK composition/discovery entrypoint, not serving admission.
No automatic migration, credential change or extra authority is introduced.
A dedicated schema-14 fixture (ORDIVON_HOST_V2_MIGRATION_STARTUP_DSN) proves
both native processes reject the mismatch before serving; the normal
schema-15 test DB proves actual STDIO and authenticated loopback HTTP calls.
A schema check at startup does not guarantee compatibility across an online
migration: quiesce all affected serving consumers before changing schema.
