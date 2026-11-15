//! Fresh PostgreSQL execution vertical. No SQLite Registry is opened.
//! One durable dispatch generation; ambiguous launch is never automatically retried.
use super::job_attempt_state::{JobIdentityContract, OperationIdentityBindings};
use super::*;
use crate::pg_admission::*;
use crate::universal::{self, RunnerRequest, RunnerStartEvidence};
use crate::{
    CompactWorkspaceOpenResult, GitWorkspaceCreateRequest, PgJobReadback, UniversalExecutorConfig,
    WorkspaceCloseRequest, WorkspaceCloseResult, WorkspaceMutateRequest, WorkspaceMutateResult,
};
use serde_json::json;
use std::{
    fs,
    path::{Path, PathBuf},
    sync::{Arc, Mutex},
    thread,
    time::{Duration, Instant},
};
use uuid::Uuid;

#[derive(Clone)]
pub struct PgRuntimeConfig {
    pub dsn: String,
    pub schema: String,
    pub source_sha256: String,
    /// Optional SAME-PG issuer currentness guard, not foreignRef authentication.
    pub harness_issuer_schema: Option<String>,
    pub executor: UniversalExecutorConfig,
    /// Existing physical carrier guards shared with Runtime::workspace.open.
    pub workspace_headroom: Vec<WorkspaceHeadroomConfig>,
}

/// Per-process progress cursors for bounded background reconciliation scans.
/// They are hints, never durable execution authority: after a restart the scan
/// restarts at the beginning, and ordinary Job state stays in PostgreSQL.
#[derive(Clone, Default)]
struct ReconciliationCursor {
    key: Option<(i64, String)>,
    upper_fence: Option<(i64, String)>,
    generation: u64,
}

#[derive(Default)]
struct ReconciliationCursors {
    issued: ReconciliationCursor,
    cancelled: ReconciliationCursor,
}

#[derive(Clone)]
pub struct PgRuntime {
    config: PgRuntimeConfig,
    reconciliation_cursors: Arc<Mutex<ReconciliationCursors>>,
}

/// Northbound delivery describes availability of an execution result, not
/// whether PostgreSQL committed a terminal control record. A native-stop-only
/// LOST result is mechanically converged but has no Runner result or proof of
/// a domain effect. Keep job.list and job.observe on the same projection law.
fn pg_delivery_disposition(
    resolution: Option<&str>,
    runner_result_available: bool,
) -> &'static str {
    match resolution {
        None => "in_progress",
        Some("lost") => "unknown",
        Some("orphaned") => "reconciliation_required",
        Some("succeeded" | "failed" | "timed_out" | "cancelled") if runner_result_available => {
            "committed"
        }
        Some(_) => "reconciliation_required",
    }
}

#[cfg(test)]
mod pg_delivery_semantics_tests {
    use super::pg_delivery_disposition;

    #[test]
    fn control_commit_is_not_runner_result_delivery() {
        for (resolution, available, expected) in [
            (None, false, "in_progress"),
            (None, true, "in_progress"),
            (Some("succeeded"), true, "committed"),
            (Some("failed"), true, "committed"),
            (Some("timed_out"), true, "committed"),
            (Some("cancelled"), true, "committed"),
            (Some("cancelled"), false, "reconciliation_required"),
            (Some("succeeded"), false, "reconciliation_required"),
            (Some("lost"), false, "unknown"),
            (Some("lost"), true, "unknown"),
            (Some("orphaned"), false, "reconciliation_required"),
            (Some("orphaned"), true, "reconciliation_required"),
            (Some("alien"), true, "reconciliation_required"),
            (Some("alien"), false, "reconciliation_required"),
        ] {
            assert_eq!(pg_delivery_disposition(resolution, available), expected);
        }
    }
}

fn error(message: impl Into<String>) -> RuntimeError {
    RuntimeError::new(RuntimeErrorCode::RegistryUnavailable, message, None, false)
}
// A PostgreSQL serialization/deadlock abort has a definite failed transaction,
// not a permanently unavailable Registry. Distinguish it at the shared
// PgAdmissionError boundary. Never replay an already admitted Job: MCP retains
// its committed operationId and the reconcile_first retry contract.
fn transient_pg_transaction_abort(code: Option<&postgres::error::SqlState>) -> bool {
    code.is_some_and(|code| {
        code == &postgres::error::SqlState::T_R_SERIALIZATION_FAILURE
            || code == &postgres::error::SqlState::T_R_DEADLOCK_DETECTED
    })
}

fn pg(e: PgAdmissionError) -> RuntimeError {
    let issuer_not_current = matches!(&e, PgAdmissionError::IssuerNotCurrent);
    let aborted = matches!(
        &e,
        PgAdmissionError::Database(err) if transient_pg_transaction_abort(err.code())
    );
    let code = if aborted {
        RuntimeErrorCode::RegistryBusy
    } else {
        match &e {
            PgAdmissionError::IdempotencyConflict => RuntimeErrorCode::IdempotencyConflict,
            PgAdmissionError::Capacity => RuntimeErrorCode::ConcurrencyLimit,
            PgAdmissionError::UnknownCommit => RuntimeErrorCode::DispatchOutcomeUnknown,
            PgAdmissionError::WorkspaceStale => RuntimeErrorCode::WorkspaceStateMismatch,
            PgAdmissionError::IssuerNotCurrent => RuntimeErrorCode::AuthorizationDenied,
            _ => RuntimeErrorCode::RegistryUnavailable,
        }
    };
    let mut error = RuntimeError::new(
        code,
        format!("PostgreSQL Runtime: {e:?}"),
        issuer_not_current.then_some("execution.foreignReferences"),
        aborted,
    );
    if aborted {
        error.retry_after_ms = Some(250);
    }
    error
}

#[cfg(test)]
mod pg_transaction_error_contract_tests {
    use super::*;

    #[test]
    fn only_true_postgres_transaction_aborts_are_transient() {
        use postgres::error::SqlState;
        for code in [
            &SqlState::T_R_SERIALIZATION_FAILURE,
            &SqlState::T_R_DEADLOCK_DETECTED,
        ] {
            assert!(transient_pg_transaction_abort(Some(code)));
        }
        assert!(!transient_pg_transaction_abort(Some(
            &SqlState::UNIQUE_VIOLATION
        )));
        assert!(!transient_pg_transaction_abort(Some(
            &SqlState::UNDEFINED_TABLE
        )));
        assert!(!transient_pg_transaction_abort(None));
    }

    #[test]
    #[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN"]
    fn native_pg_abort_is_registry_busy_not_permanent_unavailable() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("explicit disposable PostgreSQL connection required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        for (state, busy) in [
            ("40001", true),  // actual server serialization abort
            ("40P01", true),  // actual server deadlock abort
            ("23505", false), // unrelated integrity violation
        ] {
            let actual = db
                .batch_execute(&format!(
                    "DO $$ BEGIN RAISE EXCEPTION SQLSTATE '{state}'; END $$;"
                ))
                .unwrap_err();
            let mapped = pg(PgAdmissionError::Database(actual));
            if busy {
                assert_eq!(mapped.code, RuntimeErrorCode::RegistryBusy);
                assert!(mapped.retryable);
                assert_eq!(mapped.retry_after_ms, Some(250));
            } else {
                assert_eq!(mapped.code, RuntimeErrorCode::RegistryUnavailable);
                assert!(!mapped.retryable);
                assert_eq!(mapped.retry_after_ms, None);
            }
        }
    }
}
fn io(e: impl std::fmt::Display) -> RuntimeError {
    error(e.to_string())
}

// Shared by existing Workspace effect paths; the filesystem effect has
// already happened when this PostgreSQL COMMIT acknowledgment is inspected.
fn workspace_effect_commit<E: std::fmt::Display>(
    receipt: Result<(), E>,
    operation: &str,
) -> RuntimeResult<()> {
    receipt.map_err(|e| {
        RuntimeError::new(
            RuntimeErrorCode::DispatchOutcomeUnknown,
            format!(
                "{operation} filesystem effect may have completed; PostgreSQL COMMIT outcome is unknown ({e}); inspect Workspace state before retry"
            ),
            None,
            false,
        )
    })
}
fn now() -> RuntimeResult<i64> {
    Ok(universal::now_unix_ms().map_err(io)? as i64)
}
fn encode<T: serde::Serialize>(v: &T) -> RuntimeResult<String> {
    serde_json::to_string(v).map_err(io)
}
fn decode<T: serde::de::DeserializeOwned>(s: &str) -> RuntimeResult<T> {
    serde_json::from_str(s).map_err(io)
}

mod artifact;
mod job;
mod native_stop;
mod node_query;
mod reconciliation;
mod release;
mod scheduling;
mod workspace;

impl PgRuntime {
    pub fn new(config: PgRuntimeConfig) -> RuntimeResult<Self> {
        // Pure preflight first: an unqualified or unreachable PG writer must
        // never create Workspace/cache directories before source admission.
        config.executor.validate().map_err(io)?;
        super::engine::validate_workspace_headroom(&config.workspace_headroom)?;
        if config.source_sha256.len() != 64
            || !config.source_sha256.bytes().all(|b| b.is_ascii_hexdigit())
        {
            return Err(RuntimeError::invalid(
                "source SHA-256 required",
                "sourceSha256",
            ));
        }
        let runtime = Self {
            config,
            reconciliation_cursors: Arc::new(Mutex::new(ReconciliationCursors::default())),
        };
        // Fail closed before advertising a live MCP endpoint. Schema existence is
        // NOT permission to admit new Jobs. Qualification is an external,
        // operator-owned PG record and must match the exact configured source.
        // Never bootstrap, promote, or silently authorize this process.
        let mut db = runtime.store()?;
        let row=db.client.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[]
        ).map_err(io)?;
        let qualified = match row {
            Some(row) => {
                row.get::<_, String>(0) == "QUALIFIED_WRITER"
                    && row.get::<_, String>(1) == runtime.config.source_sha256
                    && row.get::<_, bool>(2)
            }
            None => false,
        };
        if !qualified {
            return Err(error(
                "PG Runtime source writer not qualified; refusing startup",
            ));
        }
        crate::pg_admission::require_pg_writer_epoch(
            &mut db.client,
            &runtime.config.source_sha256,
            false,
        )
        .map_err(pg)?;
        // Authorization includes the independently controlled app-role
        // privilege check in store(); only now may native paths be created.
        runtime.config.executor.ensure_store().map_err(io)?;
        Ok(runtime)
    }
    fn store(&self) -> RuntimeResult<PgAdmissionStore> {
        let mut db =
            PgAdmissionStore::connect(&self.config.dsn, &self.config.schema).map_err(pg)?;
        // Qualification is not independently controlled if the app owns the
        // stage table, inherits its owner's role, or can rewrite protected
        // fields. The authenticated session_user can SET ROLE NONE to regain
        // its privileges, so the current effective role alone is insufficient.
        // This does NOT attest pg_hba or service authentication.
        let app_can_promote: Option<bool> = db
            .client
            .query_opt(
                "SELECT pg_has_role(current_user,c.relowner,'MEMBER') \
                    OR pg_has_role(current_user,n.nspowner,'MEMBER') \
                    OR has_schema_privilege(current_user,n.oid,'CREATE') \
                    OR (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname=current_user) \
                    OR has_table_privilege(current_user,c.oid,'INSERT') \
                    OR has_table_privilege(current_user,c.oid,'DELETE') \
                    OR has_table_privilege(current_user,c.oid,'TRUNCATE') \
                    OR has_column_privilege(current_user,c.oid,'state','UPDATE') \
                    OR has_column_privilege(current_user,c.oid,'source_sha256','UPDATE') \
                    OR has_column_privilege(current_user,c.oid,'promotion_allowed','UPDATE') \
                    OR pg_has_role(session_user,c.relowner,'MEMBER') \
                    OR pg_has_role(session_user,n.nspowner,'MEMBER') \
                    OR has_schema_privilege(session_user,n.oid,'CREATE') \
                    OR (SELECT rolsuper FROM pg_catalog.pg_roles WHERE rolname=session_user) \
                    OR has_table_privilege(session_user,c.oid,'INSERT') \
                    OR has_table_privilege(session_user,c.oid,'DELETE') \
                    OR has_table_privilege(session_user,c.oid,'TRUNCATE') \
                    OR has_column_privilege(session_user,c.oid,'state','UPDATE') \
                    OR has_column_privilege(session_user,c.oid,'source_sha256','UPDATE') \
                    OR has_column_privilege(session_user,c.oid,'promotion_allowed','UPDATE') \
             FROM pg_catalog.pg_class c
             JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
             WHERE n.nspname=$1 AND c.relname='_stage_control' AND c.relkind='r'",
                &[&self.config.schema],
            )
            .map_err(io)?
            .map(|row| row.get(0));
        if app_can_promote != Some(false) {
            return Err(error(
                "PG Runtime control table not independently qualified; refusing startup",
            ));
        }
        Ok(db)
    }

    // A startup-qualified process may outlive operator revocation. Gate each
    // new filesystem-changing Workspace effect on the existing PG writer
    // source, while holding a row lock against concurrent qualification edits.
    fn require_qualified_writer_tx(&self, tx: &mut postgres::Transaction<'_>) -> RuntimeResult<()> {
        let row = tx
            .query_opt(
                "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR SHARE",
                &[],
            )
            .map_err(io)?;
        let qualified = row.is_some_and(|row| {
            row.get::<_, String>(0) == "QUALIFIED_WRITER"
                && row.get::<_, String>(1) == self.config.source_sha256
                && row.get::<_, bool>(2)
        });
        if !qualified {
            return Err(error(
                "PG Runtime source writer revoked; refusing Workspace effect",
            ));
        }
        crate::pg_admission::require_pg_writer_epoch(tx, &self.config.source_sha256, true)
            .map_err(pg)?;
        Ok(())
    }
    fn authorize(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
        principal: &str,
    ) -> RuntimeResult<()> {
        match db
            .client
            .query_opt("SELECT principal FROM jobs WHERE job_id=$1", &[&job])
            .map_err(io)?
        {
            Some(r) if r.get::<_, String>(0) == principal => Ok(()),
            _ => Err(RuntimeError::new(
                RuntimeErrorCode::JobNotFound,
                "Job not found for principal",
                Some("jobId"),
                false,
            )),
        }
    }
}

#[cfg(test)]
mod workspace_effect_commit_tests {
    use super::*;

    #[test]
    fn failed_post_effect_commit_is_unknown_to_existing_mcp_consumer() {
        let effect = std::env::temp_dir().join(format!("ordivon-pg-effect-{}", Uuid::now_v7()));
        fs::write(&effect, b"file changed before SQL COMMIT").unwrap();
        assert_eq!(
            fs::read(&effect).unwrap(),
            b"file changed before SQL COMMIT"
        );
        let receipt = workspace_effect_commit(
            Err(std::io::Error::new(
                std::io::ErrorKind::ConnectionReset,
                "lost COMMIT reply",
            )),
            "workspace.mutate",
        );
        let err = receipt.expect_err("a missing COMMIT receipt cannot prove success");
        assert_eq!(err.code, RuntimeErrorCode::DispatchOutcomeUnknown);
        assert!(!err.retryable, "reconciliation before retry");
        assert!(
            effect.exists(),
            "an error cannot imply the filesystem was rolled back"
        );
        fs::remove_file(effect).unwrap();
    }

    #[test]
    fn real_postgres_connection_loss_after_effect_is_unknown() {
        // Optional native physical test: same disposable PG socket setup as
        // pg_admission live fixtures, never a production database.
        let Ok(dsn) = std::env::var("ORDIVON_PG_TEST_DSN") else {
            return;
        };
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        let mut tx = db.transaction().unwrap();
        let effect = std::env::temp_dir().join(format!("ordivon-pg-effect-{}", Uuid::now_v7()));
        fs::write(&effect, b"physical effect before database disconnection").unwrap();
        assert!(effect.is_file());
        // Kill only this disposable test session; genuine PostgreSQL protocol
        // connection loss makes the subsequent COMMIT acknowledgement fail.
        let _ = tx.query_one("SELECT pg_terminate_backend(pg_backend_pid())", &[]);
        let receipt = workspace_effect_commit(tx.commit(), "workspace.mutate");
        let err = receipt.expect_err("lost real PG COMMIT acknowledgement");
        assert_eq!(err.code, RuntimeErrorCode::DispatchOutcomeUnknown);
        assert!(!err.retryable);
        assert!(
            effect.exists(),
            "physical change does not roll back with PG"
        );
        fs::remove_file(effect).unwrap();
    }
}
