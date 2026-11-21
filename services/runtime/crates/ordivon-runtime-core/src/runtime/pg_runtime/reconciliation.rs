//! PostgreSQL Attempt readback, native reconciliation, and Job result projection.
use super::*;

mod attempt_readback;
mod dispatch_accepted;
mod native_stop_evidence;
mod native_terminal;
mod native_witness;
mod output;
mod pre_dispatch_cancel;
mod projection;
mod scan;
mod sweep;

use native_witness::{
    native_running_witness, observed_namespace_pid, runner_result_still_absent, NativePidReadback,
};
use output::{active_log_window, output_projection_relative_path};
use scan::{
    advance_reconciliation_cursor, latest_reconciliation_key, next_reconciliation_cursor,
    scan_reconciliation_page,
};

/// Retain PostgreSQL's SQLSTATE across direct Client reads. The shared
/// PgAdmissionError adapter owns transaction-abort vs unavailable taxonomy;
/// generic io(Display) would erase SQLSTATE 40001/40P01 first.
fn pg_read_error(error: postgres::Error) -> RuntimeError {
    pg(PgAdmissionError::Database(error))
}
use crate::PgJobSnapshot;

// Keep the exact recovery current-Attempt selectors shared with native PG
// falsification tests; current is an explicit Job pointer, not MAX(number).
const RECOVERY_CURRENT_ATTEMPT_SQL: &str = "SELECT a.attempt_id,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.unit_name,a.created_at_ms,a.row_version,a.bundle_digest,j.execution_plan_json,j.operation_digest,a.attempt_number FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id WHERE j.job_id=$1";
const RELEASE_CURRENT_ATTEMPT_STATE_SQL: &str = "SELECT a.state FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id WHERE j.job_id=$1";

// Observation is not an external effect. A terminal PG Job intentionally
// clears current_attempt_id after its terminal Attempt and events are committed.
// Bind read-only projection to the exact Attempt already qualified by
// observe_job_readonly(), never to an unverified newest historical Attempt.
const READBACK_VERIFIED_ATTEMPT_SQL: &str = "SELECT a.attempt_id,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.unit_name,a.created_at_ms,a.row_version,a.bundle_digest,j.execution_plan_json,j.operation_digest,a.attempt_number FROM jobs j JOIN attempts a ON a.job_id=j.job_id AND a.attempt_id=$2 WHERE j.job_id=$1 AND j.row_version=$3 AND a.row_version=$4 AND j.resolution IS NOT DISTINCT FROM $5::TEXT AND (($5::TEXT IS NULL AND j.current_attempt_id=a.attempt_id) OR ($5::TEXT IS NOT NULL AND j.current_attempt_id IS NULL AND a.state=$5::TEXT))";
// Both native release control and normal native reconciliation use the
// existing one PG query to detect completed work. It never authorizes an
// external effect based on a historical Attempt.
const RECONCILIATION_STAGE_SQL: &str = "SELECT (SELECT resolution FROM jobs WHERE job_id=$1), EXISTS(SELECT 1 FROM job_runtime_release_effects WHERE job_id=$1)";

/// An absent or foreign current Attempt is an inconsistent committed
/// lifecycle identity, not PostgreSQL transport unavailability. Never infer
/// native effects or Runner custody from the highest historical Attempt.
fn require_recovery_current_attempt(
    row: Option<postgres::Row>,
    job: &str,
) -> RuntimeResult<postgres::Row> {
    row.ok_or_else(|| {
        RuntimeError::new(
            RuntimeErrorCode::ReconciliationRequired,
            "committed PG Job has no coherent current Attempt identity",
            Some("currentAttemptId"),
            false,
        )
        .with_operation_id(job)
    })
}

#[cfg(test)]
mod pg_reconciliation_direct_error_tests {
    use super::*;

    /// Exercise actual PostgreSQL, not a fabricated SQLSTATE.
    #[test]
    #[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN and #2123 typed mapper"]
    fn native_postgres_recovery_keeps_server_transaction_abort_sqlstate() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
            .expect("dedicated disposable PostgreSQL cluster is required");
        let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
        for (state, busy) in [("40001", true), ("40P01", true), ("23505", false)] {
            let source_error = db
                .batch_execute(&format!(
                    "DO $$ BEGIN RAISE EXCEPTION SQLSTATE '{state}'; END $$;"
                ))
                .unwrap_err();
            let projected = pg_read_error(source_error);
            assert_eq!(
                projected.code,
                if busy {
                    RuntimeErrorCode::RegistryBusy
                } else {
                    RuntimeErrorCode::RegistryUnavailable
                },
                "SQLSTATE {state} must retain typed classification"
            );
            assert_eq!(projected.retryable, busy);
            if busy {
                assert_eq!(projected.retry_after_ms, Some(250));
            }
        }
    }
}

#[cfg(test)]
mod native_stop_lock_portability_tests {
    #[test]
    fn native_stop_receipt_lock_excludes_an_independent_writer_until_drop() {
        let temporary = tempfile::tempdir().expect("isolated native stop lock fixture");
        let path = temporary.path().join("native-stop-evidence.lock");
        let first = std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&path)
            .unwrap();
        let second = std::fs::OpenOptions::new().write(true).open(&path).unwrap();
        first.lock().expect("first exclusive lock");
        assert!(
            matches!(second.try_lock(), Err(std::fs::TryLockError::WouldBlock)),
            "a second handle cannot publish a conflicting native stop receipt"
        );
        drop(first);
        second
            .try_lock()
            .expect("dropping the first File must release its lock");
    }
}
