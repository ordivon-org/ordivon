use ordivon_kernel::sha256_digest;
use serde_json::json;
use sqlx::{PgPool, Row};

use super::db_err;
use crate::LedgerError;

pub(super) struct Migration {
    version: i64,
    statements: &'static [&'static str],
}

impl Migration {
    fn checksum(&self) -> Result<String, LedgerError> {
        sha256_digest(&json!({
            "version": self.version,
            "statements": self.statements,
        }))
        .map_err(LedgerError::Kernel)
    }
}

pub(super) const KERNEL_SCHEMA_VERSION: i64 = 3;

const KERNEL_TABLES_V1: &[&str] = &[
    "CREATE TABLE IF NOT EXISTS kernel_ledger_events (
        event_seq BIGINT PRIMARY KEY,
        event_id TEXT NOT NULL UNIQUE,
        event_type TEXT NOT NULL,
        origin TEXT NOT NULL,
        created_at TEXT NOT NULL,
        object_type TEXT NOT NULL,
        object_id TEXT NOT NULL,
        payload JSONB NOT NULL,
        payload_hash TEXT NOT NULL,
        prev_hash TEXT NOT NULL,
        event_hash TEXT NOT NULL
    )",
    "CREATE TABLE IF NOT EXISTS kernel_seal_segments (
        segment_id TEXT PRIMARY KEY,
        first_event_seq BIGINT NOT NULL,
        last_event_seq BIGINT NOT NULL,
        event_count BIGINT NOT NULL,
        root_digest TEXT NOT NULL,
        previous_seal_ref TEXT,
        sealed_at TEXT NOT NULL
    )",
    "CREATE TABLE IF NOT EXISTS kernel_projection_heads (
        projection_id TEXT PRIMARY KEY,
        source_first_seq BIGINT NOT NULL,
        source_last_seq BIGINT NOT NULL,
        event_count BIGINT NOT NULL,
        head_hash TEXT NOT NULL,
        rebuilt_at TEXT NOT NULL
    )",
    "CREATE TABLE IF NOT EXISTS kernel_authority_uses (
        jti TEXT PRIMARY KEY,
        intent_id TEXT NOT NULL,
        obligation_id TEXT NOT NULL,
        action_class TEXT NOT NULL,
        target_ref TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        used_at TEXT NOT NULL
    )",
    "CREATE TABLE IF NOT EXISTS kernel_authority_revocations (
        jti TEXT PRIMARY KEY,
        revoked_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )",
    "CREATE TABLE IF NOT EXISTS kernel_policy_decisions (
        decision_id TEXT PRIMARY KEY,
        policy_hash TEXT NOT NULL,
        decision TEXT NOT NULL,
        created_at TEXT NOT NULL
    )",
    "CREATE TABLE IF NOT EXISTS kernel_mock_records (
        record_ref TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        deleted BOOLEAN NOT NULL DEFAULT false,
        last_action_class TEXT NOT NULL,
        last_idempotency_key TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )",
    "CREATE TABLE IF NOT EXISTS kernel_adapter_dispatches (
        dispatch_id TEXT PRIMARY KEY,
        obligation_id TEXT NOT NULL,
        action_class TEXT NOT NULL,
        target_ref TEXT NOT NULL,
        idempotency_key TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL,
        dispatched_at TEXT NOT NULL
    )",
    "CREATE TABLE IF NOT EXISTS kernel_observed_events (
        event_id TEXT PRIMARY KEY,
        dispatch_id TEXT NOT NULL REFERENCES kernel_adapter_dispatches(dispatch_id),
        trace_id TEXT NOT NULL,
        action_class TEXT NOT NULL,
        target_ref TEXT NOT NULL,
        status TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        authority_ref TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        observed_at TEXT NOT NULL
    )",
    "CREATE TABLE IF NOT EXISTS kernel_debts (
        debt_id TEXT PRIMARY KEY,
        debt_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        owner TEXT NOT NULL,
        due_at TEXT NOT NULL,
        blocking_scope TEXT NOT NULL,
        introduced_by_receipt TEXT NOT NULL,
        root_cause_code TEXT NOT NULL,
        verification_receipt TEXT,
        state TEXT NOT NULL
    )",
];

const KERNEL_CONSTRAINTS_V2: &[&str] = &[
    "ALTER TABLE kernel_observed_events
     ADD COLUMN IF NOT EXISTS source_identity TEXT NOT NULL DEFAULT 'system:mock-action-adapter'",
    "DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'kernel_ledger_events_hashes_nonempty'
        ) THEN
            ALTER TABLE kernel_ledger_events
            ADD CONSTRAINT kernel_ledger_events_hashes_nonempty
            CHECK (
                length(trim(payload_hash)) > 0
                AND length(trim(prev_hash)) > 0
                AND length(trim(event_hash)) > 0
            );
        END IF;
    END $$",
    "DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'kernel_authority_uses_nonempty'
        ) THEN
            ALTER TABLE kernel_authority_uses
            ADD CONSTRAINT kernel_authority_uses_nonempty
            CHECK (
                length(trim(jti)) > 0
                AND length(trim(intent_id)) > 0
                AND length(trim(obligation_id)) > 0
                AND length(trim(target_ref)) > 0
                AND length(trim(idempotency_key)) > 0
            );
        END IF;
    END $$",
    "DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'kernel_policy_decisions_decision_allowed'
        ) THEN
            ALTER TABLE kernel_policy_decisions
            ADD CONSTRAINT kernel_policy_decisions_decision_allowed
            CHECK (decision IN ('Allow', 'Deny', 'Error'));
        END IF;
    END $$",
    "DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'kernel_dispatches_nonempty'
        ) THEN
            ALTER TABLE kernel_adapter_dispatches
            ADD CONSTRAINT kernel_dispatches_nonempty
            CHECK (
                length(trim(dispatch_id)) > 0
                AND length(trim(obligation_id)) > 0
                AND length(trim(action_class)) > 0
                AND length(trim(target_ref)) > 0
                AND length(trim(idempotency_key)) > 0
            );
        END IF;
    END $$",
    "DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'kernel_observed_events_status_allowed'
        ) THEN
            ALTER TABLE kernel_observed_events
            ADD CONSTRAINT kernel_observed_events_status_allowed
            CHECK (status IN ('Acked', 'Observed', 'Applied', 'Succeeded', 'Partial', 'Unknown', 'Failed'));
        END IF;
    END $$",
];

const KERNEL_SECURITY_V3: &[&str] = &[
    "ALTER TABLE kernel_policy_decisions
     ADD COLUMN IF NOT EXISTS input_digest TEXT NOT NULL DEFAULT 'sha256:legacy'",
    "ALTER TABLE kernel_policy_decisions
     ADD COLUMN IF NOT EXISTS evaluator TEXT NOT NULL DEFAULT 'legacy'",
    "ALTER TABLE kernel_policy_decisions
     ADD COLUMN IF NOT EXISTS reason_code TEXT NOT NULL DEFAULT 'LEGACY'",
    "ALTER TABLE kernel_adapter_dispatches
     ADD COLUMN IF NOT EXISTS policy_decision_id TEXT",
    "CREATE TABLE IF NOT EXISTS kernel_adapter_sources (
        source_identity TEXT PRIMARY KEY,
        adapter_name TEXT NOT NULL,
        supported_action_classes TEXT NOT NULL,
        dangerous_actions_sandboxed BOOLEAN NOT NULL DEFAULT true,
        registered_at TEXT NOT NULL
    )",
    "INSERT INTO kernel_adapter_sources
        (source_identity, adapter_name, supported_action_classes, dangerous_actions_sandboxed, registered_at)
     VALUES
        ('system:mock-action-adapter', 'mock-action', 'ALL', true, '2026-05-17T00:00:00Z')
     ON CONFLICT (source_identity) DO NOTHING",
    "DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'kernel_dispatch_policy_decision_fk'
        ) THEN
            ALTER TABLE kernel_adapter_dispatches
            ADD CONSTRAINT kernel_dispatch_policy_decision_fk
            FOREIGN KEY (policy_decision_id) REFERENCES kernel_policy_decisions(decision_id);
        END IF;
    END $$",
    "DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'kernel_observed_events_source_fk'
        ) THEN
            ALTER TABLE kernel_observed_events
            ADD CONSTRAINT kernel_observed_events_source_fk
            FOREIGN KEY (source_identity) REFERENCES kernel_adapter_sources(source_identity);
        END IF;
    END $$",
    "CREATE OR REPLACE FUNCTION kernel_append_ledger_event(
        p_event_seq BIGINT,
        p_event_id TEXT,
        p_event_type TEXT,
        p_origin TEXT,
        p_created_at TEXT,
        p_object_type TEXT,
        p_object_id TEXT,
        p_payload JSONB,
        p_payload_hash TEXT,
        p_prev_hash TEXT,
        p_event_hash TEXT
     ) RETURNS VOID
     LANGUAGE plpgsql
     SECURITY DEFINER
     SET search_path = public
     AS $$
     DECLARE
        latest_seq BIGINT;
        latest_hash TEXT;
        expected_seq BIGINT;
        expected_prev TEXT;
     BEGIN
        LOCK TABLE kernel_ledger_events IN EXCLUSIVE MODE;
        SELECT event_seq, event_hash
          INTO latest_seq, latest_hash
          FROM kernel_ledger_events
         ORDER BY event_seq DESC
         LIMIT 1;
        IF latest_seq IS NULL THEN
            expected_seq := 1;
            expected_prev := 'sha256:GENESIS';
        ELSE
            expected_seq := latest_seq + 1;
            expected_prev := latest_hash;
        END IF;
        IF p_event_seq <> expected_seq THEN
            RAISE EXCEPTION 'kernel ledger non-append sequence: expected %, got %', expected_seq, p_event_seq;
        END IF;
        IF p_prev_hash <> expected_prev THEN
            RAISE EXCEPTION 'kernel ledger prev_hash mismatch: expected %, got %', expected_prev, p_prev_hash;
        END IF;
        INSERT INTO kernel_ledger_events
             (event_seq, event_id, event_type, origin, created_at, object_type, object_id,
              payload, payload_hash, prev_hash, event_hash)
        VALUES
             (p_event_seq, p_event_id, p_event_type, p_origin, p_created_at, p_object_type, p_object_id,
              p_payload, p_payload_hash, p_prev_hash, p_event_hash);
     END;
     $$",
    "REVOKE UPDATE, DELETE ON kernel_ledger_events FROM PUBLIC",
    OPTIONAL_ROLE_GRANTS,
];

const OPTIONAL_ROLE_GRANTS: &str = "DO $$ BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ordivon_kernel_app') THEN
        GRANT USAGE ON SCHEMA public TO ordivon_kernel_app;
        GRANT SELECT ON kernel_ledger_events TO ordivon_kernel_app;
        GRANT SELECT, INSERT ON kernel_authority_uses TO ordivon_kernel_app;
        GRANT SELECT ON kernel_authority_revocations TO ordivon_kernel_app;
        GRANT SELECT, INSERT ON kernel_policy_decisions TO ordivon_kernel_app;
        GRANT SELECT, INSERT ON kernel_adapter_dispatches TO ordivon_kernel_app;
        GRANT SELECT, INSERT ON kernel_observed_events TO ordivon_kernel_app;
        GRANT SELECT, INSERT, UPDATE ON kernel_mock_records TO ordivon_kernel_app;
        GRANT SELECT, INSERT ON kernel_debts TO ordivon_kernel_app;
        GRANT SELECT ON kernel_adapter_sources TO ordivon_kernel_app;
        GRANT EXECUTE ON FUNCTION kernel_append_ledger_event(
            BIGINT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, JSONB, TEXT, TEXT, TEXT
        ) TO ordivon_kernel_app;
    END IF;
END $$";

const MIGRATIONS: &[Migration] = &[
    Migration {
        version: 1,
        statements: KERNEL_TABLES_V1,
    },
    Migration {
        version: 2,
        statements: KERNEL_CONSTRAINTS_V2,
    },
    Migration {
        version: KERNEL_SCHEMA_VERSION,
        statements: KERNEL_SECURITY_V3,
    },
];

const REQUIRED_COLUMNS: &[(&str, &[&str])] = &[
    (
        "kernel_ledger_events",
        &[
            "event_seq",
            "event_id",
            "payload",
            "payload_hash",
            "prev_hash",
            "event_hash",
        ],
    ),
    (
        "kernel_authority_uses",
        &[
            "jti",
            "intent_id",
            "obligation_id",
            "target_ref",
            "idempotency_key",
        ],
    ),
    (
        "kernel_policy_decisions",
        &[
            "decision_id",
            "policy_hash",
            "input_digest",
            "evaluator",
            "decision",
            "reason_code",
            "created_at",
        ],
    ),
    (
        "kernel_adapter_dispatches",
        &[
            "dispatch_id",
            "obligation_id",
            "action_class",
            "target_ref",
            "idempotency_key",
            "policy_decision_id",
            "status",
        ],
    ),
    (
        "kernel_observed_events",
        &["event_id", "dispatch_id", "source_identity", "status"],
    ),
    (
        "kernel_adapter_sources",
        &[
            "source_identity",
            "adapter_name",
            "supported_action_classes",
            "dangerous_actions_sandboxed",
        ],
    ),
];

pub(super) async fn ensure_schema(pool: &PgPool) -> Result<(), LedgerError> {
    let mut tx = pool.begin().await.map_err(db_err)?;
    sqlx::query("SELECT pg_advisory_xact_lock(hashtext('ordivon_kernel_schema')::bigint)")
        .execute(&mut *tx)
        .await
        .map_err(db_err)?;
    sqlx::query(
        "CREATE TABLE IF NOT EXISTS kernel_schema_migrations (
            version BIGINT PRIMARY KEY,
            checksum TEXT NOT NULL,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )",
    )
    .execute(&mut *tx)
    .await
    .map_err(db_err)?;

    for migration in MIGRATIONS {
        let checksum = migration.checksum()?;
        let applied =
            sqlx::query("SELECT checksum FROM kernel_schema_migrations WHERE version = $1")
                .bind(migration.version)
                .fetch_optional(&mut *tx)
                .await
                .map_err(db_err)?;
        if let Some(row) = applied {
            let existing: String = row.get("checksum");
            if existing != checksum {
                return Err(LedgerError::Database(format!(
                    "kernel schema migration {} checksum mismatch",
                    migration.version
                )));
            }
            continue;
        }

        for statement in migration.statements {
            sqlx::query(statement)
                .execute(&mut *tx)
                .await
                .map_err(db_err)?;
        }
        sqlx::query("INSERT INTO kernel_schema_migrations (version, checksum) VALUES ($1, $2)")
            .bind(migration.version)
            .bind(checksum)
            .execute(&mut *tx)
            .await
            .map_err(db_err)?;
    }
    sqlx::query(OPTIONAL_ROLE_GRANTS)
        .execute(&mut *tx)
        .await
        .map_err(db_err)?;

    tx.commit().await.map_err(db_err)?;
    verify_schema(pool).await?;
    Ok(())
}

async fn verify_schema(pool: &PgPool) -> Result<(), LedgerError> {
    for (table, columns) in REQUIRED_COLUMNS {
        for column in *columns {
            let row = sqlx::query(
                "SELECT 1
                 FROM information_schema.columns
                 WHERE table_schema = current_schema()
                   AND table_name = $1
                   AND column_name = $2",
            )
            .bind(table)
            .bind(column)
            .fetch_optional(pool)
            .await
            .map_err(db_err)?;
            if row.is_none() {
                return Err(LedgerError::Database(format!(
                    "kernel schema drift: missing {table}.{column}"
                )));
            }
        }
    }
    Ok(())
}
