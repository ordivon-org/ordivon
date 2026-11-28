use super::super::{PgAdmissionError, PgAdmissionStore};
use super::qualification::require_qualified_writer;
use super::types::{sha256_id, validate};
use postgres::IsolationLevel;

/// Immutable identity of the single issued native payload, borrowed for
/// the duration of the receiver transaction. No authority is granted by
/// constructing this value; all fields are checked at the effect boundary.
pub(crate) struct PgIssuedHarnessSpawn<'a> {
    pub job_id: &'a str,
    pub attempt_id: &'a str,
    pub principal: &'a str,
    pub bundle_digest: &'a str,
    pub launch_token_digest: &'a str,
    pub source_sha256: &'a str,
    pub issuer_schema: &'a str,
}

impl PgAdmissionStore {
    /// The native receiver owns the original issuer row lock until the
    /// physical spawn call returns. This is not a retryable transaction and
    /// not a whole-Run NoFutureSpawn certificate (connection loss and
    /// already-issued Manager work require independent settlement).
    pub(crate) fn with_current_issued_harness_spawn<T>(
        &mut self,
        identity: PgIssuedHarnessSpawn<'_>,
        spawn: impl FnOnce() -> T,
    ) -> Result<T, PgAdmissionError> {
        let PgIssuedHarnessSpawn {
            job_id,
            attempt_id,
            principal,
            bundle_digest,
            launch_token_digest,
            source_sha256,
            issuer_schema,
        } = identity;
        validate(attempt_id, 0, bundle_digest, 0, source_sha256)?;
        if !sha256_id(launch_token_digest) || job_id.is_empty() || principal.is_empty() {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        // No unbounded SQL wait while the native process owns the effect.
        tx.batch_execute("SET LOCAL lock_timeout='3s'; SET LOCAL statement_timeout='5s'")?;
        require_qualified_writer(&mut tx, source_sha256)?;
        let row = tx
            .query_opt(
                "SELECT j.principal,j.client_request_id,j.execution_plan_json
               FROM attempts a JOIN jobs j ON j.job_id=a.job_id
               JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id
              WHERE j.job_id=$1 AND a.attempt_id=$2
                AND j.current_attempt_id=a.attempt_id AND j.desired_state='run'
                AND j.resolution IS NULL AND a.state IN ('starting','running')
                AND a.termination_intent='natural' AND r.state='active'
                AND a.bundle_digest=$3 AND a.launch_token_digest=$4
              FOR UPDATE OF j,a,r",
                &[&job_id, &attempt_id, &bundle_digest, &launch_token_digest],
            )?
            .ok_or(PgAdmissionError::Blocked)?;
        if row.get::<_, String>(0) != principal {
            return Err(PgAdmissionError::Blocked);
        }
        let issued: i64 = tx
            .query_one(
                "SELECT count(*) FROM job_events WHERE job_id=$1 AND attempt_id=$2
             AND event_type='DISPATCH_ISSUED'",
                &[&job_id, &attempt_id],
            )?
            .get(0);
        if issued != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        super::super::issuer::require_current_harness_issuer_for_plan(
            &mut tx,
            &row.get::<_, String>(2),
            &row.get::<_, String>(1),
            issuer_schema,
        )?;
        // Keep the *same transaction* alive across the native call, not a
        // standalone currentness SELECT. The caller must never retry spawn
        // on a lost transaction acknowledgement.
        let result = spawn();
        drop(tx);
        Ok(result)
    }
}
