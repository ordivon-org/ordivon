//! Rebind PG readback to the current or independently verified Attempt identity.
//! No historical MAX(attempt) guessing and no new native launch authority.

use super::*;

// Keep the exact recovery current-Attempt selectors shared with native PG
// falsification tests; current is an explicit Job pointer, not MAX(number).
pub(super) const RECOVERY_CURRENT_ATTEMPT_SQL: &str = "SELECT a.attempt_id,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.unit_name,a.created_at_ms,a.row_version,a.bundle_digest,j.execution_plan_json,j.operation_digest,a.attempt_number FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id WHERE j.job_id=$1";
pub(super) const RELEASE_CURRENT_ATTEMPT_STATE_SQL: &str = "SELECT a.state FROM jobs j JOIN attempts a ON a.attempt_id=j.current_attempt_id AND a.job_id=j.job_id WHERE j.job_id=$1";

// Observation is not an external effect. A terminal PG Job intentionally
// clears current_attempt_id after its terminal Attempt and events are committed.
// Bind read-only projection to the exact Attempt already qualified by
// observe_job_readonly(), never to an unverified newest historical Attempt.
pub(super) const READBACK_VERIFIED_ATTEMPT_SQL: &str = "SELECT a.attempt_id,a.state,a.termination_intent,a.launch_token_digest,a.bundle_path,a.unit_name,a.created_at_ms,a.row_version,a.bundle_digest,j.execution_plan_json,j.operation_digest,a.attempt_number FROM jobs j JOIN attempts a ON a.job_id=j.job_id AND a.attempt_id=$2 WHERE j.job_id=$1 AND j.row_version=$3 AND a.row_version=$4 AND j.resolution IS NOT DISTINCT FROM $5::TEXT AND (($5::TEXT IS NULL AND j.current_attempt_id=a.attempt_id) OR ($5::TEXT IS NOT NULL AND j.current_attempt_id IS NULL AND a.state=$5::TEXT))";
// Both native release control and normal native reconciliation use the
// existing one PG query to detect completed work. It never authorizes an
// external effect based on a historical Attempt.
pub(super) const RECONCILIATION_STAGE_SQL: &str = "SELECT (SELECT resolution FROM jobs WHERE job_id=$1), EXISTS(SELECT 1 FROM job_runtime_release_effects WHERE job_id=$1)";

/// An absent or foreign current Attempt is an inconsistent committed
/// lifecycle identity, not PostgreSQL transport unavailability. Never infer
/// native effects or Runner custody from the highest historical Attempt.
pub(super) fn require_recovery_current_attempt(
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

/// Negative evidence may be committed only after a *final* filesystem check.
/// Runner publishes result.json after completing its command; systemctl/cgroup
/// probes between an earlier file check and LOST commit can otherwise miss a
/// result that was durably written during the probes.
/// Match the PG Job-list recovery projection: a nonterminal issued Attempt
/// requiring a native startup, stop, or recovery witness must never be
/// advertised as recovery-free. A healthy running Job remains ordinary work.
pub(super) fn needs_recovery_observation(state: AttemptState, terminal: bool) -> bool {
    !terminal
        && matches!(
            state,
            AttemptState::Starting | AttemptState::Stopping | AttemptState::Recovering
        )
}

// Only active stdout/stderr are live previews. A terminal output must be
// projected from the *registered* Artifact path (old live-path registrations

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
