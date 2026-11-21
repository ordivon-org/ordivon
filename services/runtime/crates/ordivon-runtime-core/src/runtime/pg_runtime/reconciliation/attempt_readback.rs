//! Exact-current Attempt identity, frozen Plan decoding, and verified terminal readback.
use super::*;

impl PgRuntime {
    // One existing PG read, shared by regular reconciliation and cancellation.
    // An accepted STOP_REQUESTED Attempt needs qualified native identity but
    // no executable Plan: no OS dispatch may ever consume those Plan bytes.
    pub(super) fn current_attempt_row(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<postgres::Row> {
        require_recovery_current_attempt(
            db.client
                .query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&job])
                .map_err(pg_read_error)?,
            job,
        )
    }

    pub(in crate::runtime::pg_runtime) fn attempt(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let r = self.current_attempt_row(db, job)?;
        self.decode_attempt_record(&r, job)
    }

    /// Read-only identity may be historical only after the existing PG
    /// repeatable-read lifecycle, reservation and terminal-event verifier
    /// supplied its exact Attempt identifier. Re-bind the row to its owner,
    /// job/attempt versions, resolution, and current-or-terminal identity in
    /// one new read snapshot; a concurrent transition must be inconclusive.
    pub(in crate::runtime::pg_runtime) fn readback_attempt(
        &self,
        db: &mut PgAdmissionStore,
        snapshot: &PgJobSnapshot,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let row = db
            .client
            .query_opt(
                READBACK_VERIFIED_ATTEMPT_SQL,
                &[
                    &snapshot.job_id,
                    &snapshot.attempt_id,
                    &snapshot.job_row_version,
                    &snapshot.attempt_row_version,
                    &snapshot.resolution,
                ],
            )
            .map_err(pg_read_error)?;
        let row = row.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "verified PG lifecycle changed before Attempt readback",
                Some("jobId"),
                true,
            )
            .with_operation_id(&snapshot.job_id)
        })?;
        self.decode_attempt_record(&row, &snapshot.job_id)
    }

    /// A committed cancel is an OS control operation against the qualified
    /// current Attempt/Unit, not a new execution-plan dispatch. An invalid
    /// frozen Plan cannot block physical stop of an already running process.
    pub(in crate::runtime::pg_runtime) fn cancel_attempt_identity(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
    ) -> RuntimeResult<AttemptRecord> {
        let row = require_recovery_current_attempt(
            db.client
                .query_opt(RECOVERY_CURRENT_ATTEMPT_SQL, &[&job])
                .map_err(pg_read_error)?,
            job,
        )?;
        self.decode_attempt_identity(&row, job)
    }

    pub(super) fn decode_attempt_identity(
        &self,
        r: &postgres::Row,
        job: &str,
    ) -> RuntimeResult<AttemptRecord> {
        let a: AttemptRecord = serde_json::from_value(json!({"attemptId":r.get::<_,String>(0),"jobId":job,"attemptNumber":r.get::<_, i64>(11),"state":r.get::<_,String>(1),"terminationIntent":r.get::<_,String>(2),"launchTokenDigest":r.get::<_,String>(3),"bundlePath":r.get::<_,String>(4),"unitName":r.get::<_,String>(5),"createdAtMs":r.get::<_,i64>(6),"rowVersion":r.get::<_,i64>(7),"bundleDigest":r.get::<_,Option<String>>(8)})).map_err(io)?;
        let expected = self
            .config
            .executor
            .store_root
            .join("pg-attempts")
            .join(&a.attempt_id);
        if Path::new(&a.bundle_path) != expected {
            return Err(error("Attempt bundle outside PG store"));
        }
        Ok(a)
    }

    pub(super) fn decode_attempt_record(
        &self,
        r: &postgres::Row,
        job: &str,
    ) -> RuntimeResult<(AttemptRecord, RuntimeExecutionPlan, String)> {
        let a = self.decode_attempt_identity(r, job)?;
        // A malformed frozen execution plan is a damaged Job record, not
        // PostgreSQL server unavailability. This is the first real job.get /
        // observe readback boundary, before the optional Scheduler annotation.
        let plan: RuntimeExecutionPlan =
            serde_json::from_str(&r.get::<_, String>(9)).map_err(|e| {
                RuntimeError::invalid(
                    format!("committed executionPlan is invalid: {e}"),
                    "executionPlan",
                )
            })?;
        Ok((a, plan, r.get(10)))
    }
}
