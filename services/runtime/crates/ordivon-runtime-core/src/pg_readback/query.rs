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
        // The latest Attempt, its reservation and all unsettled-history
        // exclusions are one row projection of the same qualified snapshot.
        // The job/attempt-number and attempt/reservation keys are unique in
        // the native schema. Missing evidence produces no row, not absence
        // authority. Keep the selected attempt distinct from the current
        // pointer: lifecycle_coherent checks that original relation below.
        let Some(row) = tx.query_opt(
            "SELECT j.desired_state, j.resolution, j.current_attempt_id, j.row_version, \
                    a.attempt_id, a.state, a.termination_intent, a.result_digest, \
                    a.finished_at_ms, a.row_version, a.started_at_ms, c.state \
             FROM jobs j \
             JOIN LATERAL (SELECT attempt_id, state, termination_intent, result_digest, \
                                  finished_at_ms, row_version, started_at_ms \
                           FROM attempts WHERE job_id=j.job_id \
                           ORDER BY attempt_number DESC LIMIT 1) a ON true \
             JOIN concurrency_reservations c ON c.attempt_id=a.attempt_id \
             WHERE j.job_id=$1 AND NOT EXISTS(SELECT 1 FROM attempts h \
                 LEFT JOIN concurrency_reservations hc ON hc.attempt_id=h.attempt_id \
                 LEFT JOIN job_allocations x ON x.attempt_id=h.attempt_id \
                 WHERE h.job_id=j.job_id AND (\
                   (h.attempt_id<>a.attempt_id AND (h.state NOT IN ('succeeded','failed','timed_out','cancelled','lost') \
                    OR hc.state IS DISTINCT FROM 'released')) \
                   OR (x.state='active' AND (h.attempt_id<>a.attempt_id OR j.resolution IS NOT NULL))))",
            &[&job_id],
        )? else {
            return Ok(PgJobReadback::Inconclusive);
        };
        let snapshot = PgJobSnapshot {
            job_id: job_id.to_owned(),
            desired_state: row.get(0),
            resolution: row.get(1),
            current_attempt_id: row.get(2),
            job_row_version: row.get(3),
            attempt_id: row.get(4),
            attempt_state: row.get(5),
            termination_intent: row.get(6),
            result_digest: row.get(7),
            finished_at_ms: row.get(8),
            attempt_row_version: row.get(9),
            started_at_ms: row.get(10),
            reservation_state: row.get(11),
        };
        if !snapshot.lifecycle_coherent() || !terminal_events_coherent(&mut tx, &snapshot)? {
            return Ok(PgJobReadback::Inconclusive);
        }
        // Read-only transaction commit is not an effectful admission.
        tx.commit()?;
        Ok(PgJobReadback::Observed(Box::new(snapshot)))
    }
}
