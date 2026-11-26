//! Qualified PG Job event writer for scheduler issues, separate from selection policy.
//! Uses the existing writer, lock, current-Attempt fence, and Job event ledger.
use super::{
    encode, io, json, now, PgAdmissionStore, PgRuntime, RuntimeError, RuntimeErrorCode,
    RuntimeResult,
};
use crate::universal;

/// One durable diagnostic per Attempt and issue class, using the existing PG
/// Job event ledger. No new table, worker, admission outcome or terminal state.
/// A qualified writer and the same allocation/close fence serialize with
/// admission, terminal commits and other event_sequence appenders.
pub(super) fn record_scheduler_issue(
    runtime: &PgRuntime,
    db: &mut PgAdmissionStore,
    job: &str,
    attempt_id: &str,
    reason: &str,
    error: &RuntimeError,
) -> RuntimeResult<()> {
    let mut tx = db
        .client
        .build_transaction()
        .isolation_level(postgres::IsolationLevel::ReadCommitted)
        .start()
        .map_err(io)?;
    tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])
        .map_err(io)?;
    runtime.require_qualified_writer_tx(&mut tx)?;
    // A stale pending snapshot cannot append an issue to a newer/terminal
    // Attempt or claim that a separately cancelled Job still needs dispatch.
    let current = tx
        .query_opt(
            "SELECT a.attempt_id FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id              WHERE j.job_id=$1 AND a.attempt_id=$2 AND a.state='accepted' AND j.desired_state='run' AND j.resolution IS NULL              FOR UPDATE OF j,a",
            &[&job, &attempt_id],
        )
        .map_err(io)?;
    if current.is_none() {
        return Ok(());
    }
    let recorded = tx
        .query_opt(
            "SELECT 1 FROM job_events WHERE job_id=$1 AND attempt_id=$2              AND event_type='SCHEDULER_ISSUE' AND reason_code=$3 LIMIT 1",
            &[&job, &attempt_id, &reason],
        )
        .map_err(io)?;
    if recorded.is_some() {
        return Ok(());
    }
    let detail = encode(&json!({
        "schemaVersion": 1,
        "errorCode": error.code.as_str(),
        "field": error.field,
    }))?;
    let digest = universal::sha256_bytes(detail.as_bytes());
    let seq: i64 = tx
        .query_one(
            "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=$1",
            &[&job],
        )
        .map_err(io)?
        .get(0);
    tx.execute(
        "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms)          VALUES($1,$2,$3,$4,'SCHEDULER_ISSUE','SYSTEM_DERIVED','accepted','accepted',$5,$6,$7,$8)",
        &[
            &format!("event-{}", uuid::Uuid::now_v7()),
            &job,
            &attempt_id,
            &seq,
            &reason,
            &detail,
            &digest,
            &now()?,
        ],
    )
    .map_err(io)?;
    tx.commit().map_err(|_| {
        RuntimeError::new(
            RuntimeErrorCode::DispatchOutcomeUnknown,
            "scheduler diagnostic COMMIT outcome unknown; read back the Job event before retrying",
            Some("jobId"),
            false,
        )
        .with_operation_id(job)
    })?;
    Ok(())
}
