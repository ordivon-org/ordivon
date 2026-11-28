use super::super::{PgAdmissionError, PgAdmissionStore};
use super::event::{append_dispatch_event, PgDispatchEvent};
use super::qualification::require_qualified_writer;
use super::types::{validate, PgDispatchIssued};
use postgres::IsolationLevel;
use sha2::{Digest, Sha256};

impl PgAdmissionStore {
    /// Used ONLY by the unique in-memory issuer between committing its
    /// DISPATCH_ISSUED fence and invoking systemd-run. A post-crash observer
    /// must NEVER call this: PG state alone cannot prove whether the original
    /// caller already submitted an asynchronous systemd Manager Job.
    ///
    /// Returns false to continue physical handoff; true only if cancellation
    /// was committed before *this issuer* called the OS, and the original
    /// Job/Attempt/reservation is now atomically cancelled. No PROCESS_EXITED
    /// event or fictitious Runner Artifact is manufactured.
    pub(crate) fn settle_cancel_before_native_handoff(
        &mut self,
        issued: &PgDispatchIssued,
    ) -> Result<bool, PgAdmissionError> {
        validate(
            &issued.attempt_id,
            issued.expected_row_version,
            &issued.expected_bundle_digest,
            issued.observed_at_ms,
            &issued.expected_source_sha256,
        )?;
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        require_qualified_writer(&mut tx, &issued.expected_source_sha256)?;
        let row = tx.query_opt(
            "SELECT a.job_id,a.state,a.termination_intent,a.row_version,a.bundle_digest,                     j.current_attempt_id,j.desired_state,j.resolution,r.state              FROM attempts a JOIN jobs j ON j.job_id=a.job_id              JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id              WHERE a.attempt_id=$1 FOR UPDATE OF a,j,r",
            &[&issued.attempt_id],
        )?.ok_or(PgAdmissionError::Blocked)?;
        let job: String = row.get(0);
        let state: String = row.get(1);
        let intent: String = row.get(2);
        let version: i64 = row.get(3);
        let bundle: Option<String> = row.get(4);
        let current: Option<String> = row.get(5);
        let desired: String = row.get(6);
        let resolution: Option<String> = row.get(7);
        let reservation: String = row.get(8);
        if current.as_deref() != Some(issued.attempt_id.as_str())
            || bundle.as_deref() != Some(issued.expected_bundle_digest.as_str())
            || resolution.is_some()
            || reservation != "active"
            || version < issued.expected_row_version
        {
            return Err(PgAdmissionError::Blocked);
        }
        // This check is NOT a promise that cancellation cannot race after it.
        // The issuer must also recheck after the physical handoff and stop the
        // exact OS Unit when a newly committed stop intent wins that race.
        if state == "starting"
            && intent == "natural"
            && desired == "run"
            && version == issued.expected_row_version
        {
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(false);
        }
        if state != "stopping"
            || intent != "stop_requested"
            || desired != "cancelled"
            || version <= issued.expected_row_version
        {
            return Err(PgAdmissionError::Blocked);
        }
        let dispatch_count: i64 = tx.query_one(
            "SELECT COUNT(*) FROM job_events WHERE job_id=$1 AND attempt_id=$2              AND event_type='DISPATCH_ISSUED' AND origin='SYSTEM_DERIVED'              AND reason_code='AT_MOST_ONCE_BOUNDARY_COMMITTED'",
            &[&job, &issued.attempt_id],
        )?.get(0);
        let stop_count: i64 = tx.query_one(
            "SELECT COUNT(*) FROM job_events WHERE job_id=$1 AND attempt_id=$2              AND event_type='STOP_REQUESTED'",
            &[&job, &issued.attempt_id],
        )?.get(0);
        let runner_count: i64 = tx.query_one(
            "SELECT COUNT(*) FROM job_events WHERE job_id=$1 AND attempt_id=$2              AND event_type='RUNNER_BOUND'",
            &[&job, &issued.attempt_id],
        )?.get(0);
        if dispatch_count != 1 || stop_count != 1 || runner_count != 0 {
            return Err(PgAdmissionError::Blocked);
        }
        // Unlike a cancelled running Attempt, no process existed to exit:
        // record the issuer's own positive pre-handoff fact, not OS quiescence.
        let detail = serde_json::json!({
            "attemptId":issued.attempt_id,
            "bundleDigest":issued.expected_bundle_digest,
            "dispatchIssued":true,
            "nativeCallIssued":false
        });
        let result_digest = format!(
            "sha256:{}",
            hex::encode(Sha256::digest(detail.to_string().as_bytes()))
        );
        let now: i64 = tx
            .query_one(
                "SELECT floor(extract(epoch from clock_timestamp())*1000)::bigint",
                &[],
            )?
            .get(0);
        if tx.execute(
            "UPDATE attempts SET state='cancelled',result_digest=$1,              finished_at_ms=$2,row_version=row_version+1              WHERE attempt_id=$3 AND state='stopping' AND row_version=$4",
            &[&result_digest, &now, &issued.attempt_id, &version],
        )? != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        if tx.execute(
            "UPDATE concurrency_reservations SET state='released',released_at_ms=$1,              release_reason='CANCELLED_BEFORE_NATIVE_HANDOFF',state_observed_at_ms=$1              WHERE attempt_id=$2 AND state='active'",
            &[&now, &issued.attempt_id],
        )? != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        tx.execute(
            "UPDATE job_allocations SET state='released',released_at_ms=$1              WHERE attempt_id=$2 AND state='active'",
            &[&now, &issued.attempt_id],
        )?;
        if tx.execute(
            "UPDATE jobs SET resolution='cancelled',current_attempt_id=NULL,              row_version=row_version+1 WHERE job_id=$1 AND resolution IS NULL              AND current_attempt_id=$2 AND desired_state='cancelled'",
            &[&job, &issued.attempt_id],
        )? != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        append_dispatch_event(
            &mut tx,
            PgDispatchEvent {
                job_id: &job,
                attempt_id: &issued.attempt_id,
                event_type: "NATIVE_HANDOFF_PREVENTED",
                origin: "SYSTEM_DERIVED",
                old: "stopping",
                new: "cancelled",
                reason: "CANCELLED_BEFORE_NATIVE_HANDOFF",
                detail: serde_json::json!({
                    "resultDigest":result_digest,
                    "dispatchIssued":true,
                    "nativeCallIssued":false,
                }),
                at: now,
            },
        )?;
        append_dispatch_event(
            &mut tx,
            PgDispatchEvent {
                job_id: &job,
                attempt_id: &issued.attempt_id,
                event_type: "JOB_TERMINAL",
                origin: "SYSTEM_DERIVED",
                old: "stopping",
                new: "cancelled",
                reason: "CANCELLED_BEFORE_NATIVE_HANDOFF",
                detail: serde_json::json!({"resolution":"cancelled"}),
                at: now,
            },
        )?;
        tx.query_one(
            "SELECT pg_notify('ordivon_runtime_schedule',current_schema())",
            &[],
        )?;
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(true)
    }
}
