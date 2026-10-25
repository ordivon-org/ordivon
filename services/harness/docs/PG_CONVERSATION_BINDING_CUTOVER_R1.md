# PostgreSQL conversation-binding cutover — R1

Natural consumer: Harness Browserless exact conversation affinity and adoption.
Issue: DB-PG-MIGRATE-CFT-01 / authority identity, transaction serialization, source freeze.
PG wins only after exact SQLite-to-PG identity import and sealed legacy writer authority.
Old SQLite remains a forensic snapshot; it must not be patched for new capabilities.

Obligations: (campaignRef, agentId) and requestId unique, canonical resource and
UUID7 session, stable bindingDigest, exact replay, verified pre-commit readback.
Migration needs captured source rows, PostgreSQL exact row parity, sealed old writer
and quiesced Browserless providers. PG readback cannot infer provider success.
Do not call a two-database handoff atomic without an admitted journal/cutover step.
Verification: native PostgreSQL tests + concurrent admissions and RED source drift.
New PG owner: scripts/postgres_conversation_binding.py, selected only by explicit
ORDIVON_CONVERSATION_POSTGRES_DSN. Browserless checks retired source identity
before ANY PG read/adoption; absent legacy source requires separately authorized
ORDIVON_CONVERSATION_PG_FRESH_BOOTSTRAP=1.

Migration procedure in a TEST DB: stop legacy workers; call
PostgresConversationBindingStore(dsn).retire_legacy_and_import(sqlite_path);
record returned sourceRows, postgresRows, identityDigest; verify
assert_legacy_sealed and reader matching; then deploy PG-configured worker.
The legacy table's only permitted new writes during migration are retirement
triggers that reject future INSERT/UPDATE/DELETE. No SQLite feature fixes.
If PG commits but the SQLite retirement commit fails, stop and requalify both
states; cross-database commit is NOT atomic. Do not enable production cutover
without a real operator-source freeze and independent deployment receipt.

Standing: source implementation candidate; actual active production cutover
remains UNKNOWN until disposable PG real tests and live deployment acceptance.
