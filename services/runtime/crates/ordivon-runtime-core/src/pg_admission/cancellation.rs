//! PostgreSQL admission owner: cancellation.
use super::*;

impl PgAdmissionStore {
    /// Persist only a cancel/stop intent. Do not infer that a runner has
    /// stopped, release capacity, or resolve an accepted Job without an
    /// independently observed dispatch fence and terminal receipt.
    pub fn request_cancel_intent(
        &mut self,
        i: &PgCancelIntent,
    ) -> Result<PgCancelOutcome, PgAdmissionError> {
        if i.job_id.is_empty()
            || i.observed_at_ms < 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
        {
            return Err(PgAdmissionError::InvalidInput);
        }

        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        // Same serialization boundary as admission and terminal CAS.
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, true)?;

        let job = tx.query_opt(
            "SELECT resolution,desired_state,current_attempt_id FROM jobs WHERE job_id=$1 FOR UPDATE",
            &[&i.job_id],
        )?.ok_or(PgAdmissionError::InvalidInput)?;
        let resolution: Option<String> = job.get(0);
        let desired: String = job.get(1);
        let current_attempt: Option<String> = job.get(2);

        if resolution.is_some() && resolution.as_deref() != Some("orphaned") {
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(PgCancelOutcome::Existing(i.job_id.clone()));
        }
        let attempt_id = if resolution.as_deref() == Some("orphaned") {
            // A resolved orphan has no current_attempt_id; use the latest
            // durable Attempt and prove the reservation is still held.
            tx.query_opt(
                "SELECT attempt_id FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
                &[&i.job_id],
            )?.ok_or(PgAdmissionError::Blocked)?.get::<_, String>(0)
        } else {
            current_attempt.ok_or(PgAdmissionError::Blocked)?
        };
        let attempt = tx.query_opt(
            "SELECT state,termination_intent FROM attempts WHERE attempt_id=$1 AND job_id=$2 FOR UPDATE",
            &[&attempt_id,&i.job_id],
        )?.ok_or(PgAdmissionError::Blocked)?;
        let previous: String = attempt.get(0);
        let stop_intent: String = attempt.get(1);

        // Never treat a lifecycle projection alone as evidence that a
        // stopped/terminal attempt released its real capacity.
        let reservation = tx
            .query_opt(
                "SELECT state FROM concurrency_reservations WHERE attempt_id=$1 FOR UPDATE",
                &[&attempt_id],
            )?
            .ok_or(PgAdmissionError::Blocked)?;
        let reservation_state: String = reservation.get(0);
        let is_orphan = resolution.as_deref() == Some("orphaned");
        if is_orphan {
            if previous != "orphaned" || reservation_state != "held_orphaned" {
                return Err(PgAdmissionError::Blocked);
            }
        } else if !matches!(
            previous.as_str(),
            "accepted" | "starting" | "running" | "recovering" | "stopping"
        ) || reservation_state != "active"
        {
            return Err(PgAdmissionError::Blocked);
        }

        if desired == "cancelled"
            && stop_intent == "stop_requested"
            && (is_orphan || matches!(previous.as_str(), "accepted" | "stopping"))
        {
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(PgCancelOutcome::Existing(i.job_id.clone()));
        }
        if !matches!(desired.as_str(), "run" | "cancelled")
            || !matches!(stop_intent.as_str(), "natural" | "stop_requested")
        {
            return Err(PgAdmissionError::Blocked);
        }

        // First record the Job intent, even when its Attempt has not yet
        // started. An accepted Attempt stays accepted until dispatch fencing
        // and terminal ownership prove that early cancellation completed.
        if desired != "cancelled" {
            let changed = tx.execute(
                "UPDATE jobs SET desired_state='cancelled',row_version=row_version+1 WHERE job_id=$1 AND desired_state='run'",
                &[&i.job_id],
            )?;
            if changed != 1 {
                return Err(PgAdmissionError::Blocked);
            }
        }
        let next_state = if matches!(previous.as_str(), "starting" | "running" | "recovering") {
            "stopping"
        } else {
            previous.as_str()
        };
        let changed = tx.execute(
            "UPDATE attempts SET state=$1,termination_intent='stop_requested',row_version=row_version+1 WHERE attempt_id=$2 AND state=$3 AND termination_intent=$4",
            &[&next_state,&attempt_id,&previous,&stop_intent],
        )?;
        if changed != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        let next_sequence: i64 = tx
            .query_one(
                "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=$1",
                &[&i.job_id],
            )?
            .get(0);
        let reason = if is_orphan {
            "ORPHAN_CANCEL_INTENT_COMMITTED"
        } else if previous == "accepted" {
            "CANCEL_INTENT_AWAITING_DISPATCH_FENCE"
        } else {
            "CANCEL_INTENT_COMMITTED"
        };
        let detail = cancel_detail(i);
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(detail.as_bytes())));
        tx.execute(
            "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms) VALUES($1,$2,$3,$4,'STOP_REQUESTED','SYSTEM_DERIVED',$5,$6,$7,$8,$9,$10)",
            &[&format!("event-{}", Uuid::now_v7()),&i.job_id,&attempt_id,&next_sequence,
                &previous,&next_state,&reason,&detail,&digest,&i.observed_at_ms],
        )?;
        // No capacity release, no resolved Job, no runner side effects.
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgCancelOutcome::IntentRecorded(i.job_id.clone()))
    }
}

impl PgAdmissionStore {
    /// Reconcile a lost COMMIT acknowledgement using a NEW qualified PG
    /// connection. Only an exact durable STOP_REQUESTED event plus coherent
    /// Job/Attempt/Reservation state proves this particular cancel intent.
    /// Absence is INCONCLUSIVE, never proof that a mutation did not commit.
    pub fn observe_cancel_intent(
        &mut self,
        i: &PgCancelIntent,
    ) -> Result<PgCancelObservation, PgAdmissionError> {
        if i.job_id.is_empty()
            || i.observed_at_ms < 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let authority = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        let state: String = authority.get(0);
        let source: String = authority.get(1);
        let permitted: bool = authority.get(2);
        if state != "QUALIFIED_WRITER" || !permitted || source != i.expected_source_sha256 {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, false)?;
        let Some(job) = tx.query_opt(
            "SELECT desired_state,resolution,current_attempt_id FROM jobs WHERE job_id=$1",
            &[&i.job_id],
        )?
        else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let desired: String = job.get(0);
        let resolution: Option<String> = job.get(1);
        let current_attempt: Option<String> = job.get(2);
        if desired != "cancelled" {
            return Ok(PgCancelObservation::Inconclusive);
        }
        let attempt_id = if resolution.is_some() {
            tx.query_opt(
                "SELECT attempt_id FROM attempts WHERE job_id=$1 ORDER BY attempt_number DESC LIMIT 1",
                &[&i.job_id],
            )?.map(|row| row.get::<_, String>(0))
        } else {
            current_attempt
        };
        let Some(attempt_id) = attempt_id else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let Some(attempt) = tx.query_opt(
            "SELECT state,termination_intent FROM attempts WHERE attempt_id=$1 AND job_id=$2",
            &[&attempt_id, &i.job_id],
        )?
        else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let attempt_state: String = attempt.get(0);
        let intent: String = attempt.get(1);
        if intent != "stop_requested" {
            return Ok(PgCancelObservation::Inconclusive);
        }
        let Some(reservation) = tx.query_opt(
            "SELECT state FROM concurrency_reservations WHERE attempt_id=$1",
            &[&attempt_id],
        )?
        else {
            return Ok(PgCancelObservation::Inconclusive);
        };
        let reservation_state: String = reservation.get(0);
        let coherent = if resolution.as_deref() == Some("orphaned") {
            attempt_state == "orphaned" && reservation_state == "held_orphaned"
        } else if resolution.is_some() {
            matches!(
                attempt_state.as_str(),
                "succeeded" | "failed" | "timed_out" | "cancelled" | "lost"
            ) && reservation_state == "released"
        } else {
            matches!(attempt_state.as_str(), "accepted" | "stopping")
                && reservation_state == "active"
        };
        if !coherent {
            return Ok(PgCancelObservation::Inconclusive);
        }
        let detail = cancel_detail(i);
        let event_digest = format!("sha256:{}", hex::encode(Sha256::digest(detail.as_bytes())));
        let event_exists: bool = tx.query_one(
            "SELECT EXISTS(SELECT 1 FROM job_events WHERE job_id=$1 AND attempt_id=$2 AND event_type='STOP_REQUESTED' AND origin='SYSTEM_DERIVED' AND detail_digest=$3 AND detail_json=$4 AND observed_at_ms=$5 AND reason_code IN ('CANCEL_INTENT_AWAITING_DISPATCH_FENCE','CANCEL_INTENT_COMMITTED','ORPHAN_CANCEL_INTENT_COMMITTED'))",
            &[&i.job_id,&attempt_id,&event_digest,&detail,&i.observed_at_ms],
        )?.get(0);
        if !event_exists {
            return Ok(PgCancelObservation::Inconclusive);
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgCancelObservation::Confirmed(i.job_id.clone()))
    }
}
