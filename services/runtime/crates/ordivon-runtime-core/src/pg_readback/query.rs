use super::artifact_inventory::read_artifact_inventory;
use super::inspection::read_inspection;
use super::terminal_event::terminal_events_coherent;
use super::types::{PgJobReadback, PgJobSnapshot, PgProjectionReadback};
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
        Ok(
            match self.read_job_snapshot(job_id, expected_source_sha256, false, None)? {
                Some(readback) => PgJobReadback::Observed(readback.snapshot),
                None => PgJobReadback::Inconclusive,
            },
        )
    }

    pub(crate) fn observe_job_projection_readonly(
        &mut self,
        job_id: &str,
        expected_source_sha256: &str,
    ) -> Result<Option<PgProjectionReadback>, PgAdmissionError> {
        self.read_job_snapshot(job_id, expected_source_sha256, true, None)
    }

    pub(crate) fn observe_job_inspection_readonly(
        &mut self,
        job_id: &str,
        expected_source_sha256: &str,
        event_limit: u32,
    ) -> Result<Option<PgProjectionReadback>, PgAdmissionError> {
        self.read_job_snapshot(job_id, expected_source_sha256, true, Some(event_limit))
    }

    fn read_job_snapshot(
        &mut self,
        job_id: &str,
        expected_source_sha256: &str,
        include_job_inventory: bool,
        event_limit: Option<u32>,
    ) -> Result<Option<PgProjectionReadback>, PgAdmissionError> {
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
            return Ok(None);
        };
        let Some(attempt) = tx.query_opt(
            "SELECT attempt_id, state, termination_intent, result_digest, finished_at_ms, row_version, started_at_ms, exit_code \
             FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
            &[&job_id],
        )? else {
            return Ok(None);
        };
        let attempt_id: String = attempt.get(0);
        // The selected Attempt cannot certify the whole Job while an older
        // Attempt still has an unresolved lifecycle or capacity reservation.
        // Scheduler allocations are separate from admission reservations:
        // a terminal writer releases both, while a never-dispatched Attempt
        // may have no allocation. Check the original PG history in one snapshot.
        let terminal_job = job.get::<_, Option<String>>(1).is_some();
        let unsettled_history: bool = tx
            .query_one(
                "SELECT EXISTS(SELECT 1 FROM attempts a \
                 LEFT JOIN concurrency_reservations c ON c.attempt_id=a.attempt_id \
                 LEFT JOIN job_allocations x ON x.attempt_id=a.attempt_id \
                 WHERE a.job_id=$1 AND (\
                   (a.attempt_id<>$2 AND (a.state NOT IN ('succeeded','failed','timed_out','cancelled','lost') \
                    OR c.state IS DISTINCT FROM 'released')) \
                   OR (x.state='active' AND (a.attempt_id<>$2 OR $3::boolean))))",
                &[&job_id, &attempt_id, &terminal_job],
            )?
            .get(0);
        if unsettled_history {
            return Ok(None);
        }
        let Some(reservation) = tx.query_opt(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&attempt_id],
        )?
        else {
            return Ok(None);
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
        if !snapshot.lifecycle_coherent() {
            return Ok(None);
        }
        let Some(artifacts) = read_artifact_inventory(&mut tx, &snapshot, include_job_inventory)?
        else {
            return Ok(None);
        };
        let selected = artifacts
            .iter()
            .filter(|a| a.attempt_id == snapshot.attempt_id)
            .map(|a| a.registration.clone())
            .collect::<Vec<_>>();
        if !terminal_events_coherent(&mut tx, &snapshot, &selected)? {
            return Ok(None);
        }
        let exit_code = attempt.get(7);
        let inspection = if let Some(limit) = event_limit {
            let Some(metadata) = read_inspection(&mut tx, &snapshot, limit)? else {
                return Ok(None);
            };
            Some(metadata)
        } else {
            None
        };
        tx.commit()?;
        Ok(Some(PgProjectionReadback {
            snapshot: Box::new(snapshot),
            artifacts,
            exit_code,
            inspection,
        }))
    }
}
