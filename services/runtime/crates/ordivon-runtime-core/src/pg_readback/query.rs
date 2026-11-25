use super::terminal_event::terminal_events_coherent;
use super::types::{PgJobReadback, PgJobSnapshot};
use crate::pg_admission::{require_pg_writer_epoch, PgAdmissionError, PgAdmissionStore};
use postgres::IsolationLevel;

impl PgAdmissionStore {
    /// Read a single consistent Job/Attempt/Reservation snapshot without
    /// changing durable state. Only the qualified, source-bound PG writer
    /// namespace can be observed; a staged import is never current truth.
    /// An incoherent or absent row is INCONCLUSIVE, not a missing/terminal Job.
    pub fn observe_job_readonly(
        &mut self,
        job_id: &str,
        expected_source_sha256: &str,
    ) -> Result<PgJobReadback, PgAdmissionError> {
        if job_id.is_empty()
            || expected_source_sha256.len() != 64
            || !expected_source_sha256
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit())
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let owner = tx.query_opt(
            "SELECT state, source_sha256, promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = owner.get(0);
        let source: String = owner.get(1);
        let permitted: bool = owner.get(2);
        if state != "QUALIFIED_WRITER" || source != expected_source_sha256 || !permitted {
            return Err(PgAdmissionError::Unqualified);
        }
        // A source-qualified row can survive PITR on a new WAL timeline.
        // Current Job readback must not promote restored historical data to
        // installed/current authority without the operator-owned PG epoch.
        // This is a read-only check; forensic SQL can still inspect old rows.
        require_pg_writer_epoch(&mut tx, expected_source_sha256, false)?;
        let Some(job) = tx.query_opt(
            "SELECT desired_state, resolution, current_attempt_id, row_version FROM jobs WHERE job_id=$1",
            &[&job_id],
        )? else {
            return Ok(PgJobReadback::Inconclusive);
        };
        let Some(attempt) = tx.query_opt(
            "SELECT attempt_id, state, termination_intent, result_digest, finished_at_ms, row_version, started_at_ms \
             FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
            &[&job_id],
        )? else {
            return Ok(PgJobReadback::Inconclusive);
        };
        let attempt_id: String = attempt.get(0);
        let Some(reservation) = tx.query_opt(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&attempt_id],
        )?
        else {
            return Ok(PgJobReadback::Inconclusive);
        };
        let snapshot = PgJobSnapshot {
            job_id: job_id.to_owned(),
            desired_state: job.get(0),
            resolution: job.get(1),
            current_attempt_id: job.get(2),
            job_row_version: job.get(3),
            attempt_id,
            attempt_state: attempt.get(1),
            termination_intent: attempt.get(2),
            result_digest: attempt.get(3),
            started_at_ms: attempt.get(6),
            finished_at_ms: attempt.get(4),
            attempt_row_version: attempt.get(5),
            reservation_state: reservation.get(0),
        };
        if !snapshot.lifecycle_coherent() || !terminal_events_coherent(&mut tx, &snapshot)? {
            return Ok(PgJobReadback::Inconclusive);
        }
        // Read-only transaction commit is not an effectful admission.
        tx.commit()?;
        Ok(PgJobReadback::Observed(Box::new(snapshot)))
    }
}
