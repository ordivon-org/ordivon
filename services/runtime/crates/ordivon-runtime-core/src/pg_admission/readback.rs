//! PostgreSQL admission owner: readback.
use super::*;

/// Read-only witness for a potentially committed admission whose response was lost.
///
/// Inconclusive is deliberately NOT equivalent to "the write did not commit".
/// The witness binds the exact submitted identity, its initial Attempt and
/// capacity reservation, and all three admission events. It does not assert
/// dispatch, runner activity, terminal completion, or installed PG authority.
#[derive(Debug, PartialEq, Eq)]
pub enum PgAdmissionObservation {
    Confirmed(String),
    Inconclusive,
}

impl PgAdmissionStore {
    pub fn observe_admission(
        &mut self,
        i: &PgAdmissionInput,
    ) -> Result<PgAdmissionObservation, PgAdmissionError> {
        i.validate()?;
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

        // A key by itself is insufficient: require the original immutable Job,
        // first Attempt and capacity reservation to be mutually consistent.
        // Mutable lifecycle/desired-state columns must NOT be pinned to their
        // initial values: the original admission stays true after progression.
        let row = tx.query_opt(
            "SELECT j.job_id,j.request_digest,j.operation_digest,j.workspace_id, \
                    j.workspace_snapshot_json,j.execution_plan_json,j.execution_plan_digest, \
                    j.created_at_ms,a.attempt_id,a.attempt_number,a.launch_token_digest, \
                    a.bundle_path,a.unit_name,a.created_at_ms, \
                    r.reservation_id,r.global_limit,r.acquired_at_ms \
             FROM idempotency_keys k \
             JOIN jobs j ON j.job_id=k.job_id AND j.principal=k.principal \
                AND j.client_request_id=k.client_request_id \
             JOIN attempts a ON a.job_id=j.job_id AND a.attempt_number=1 \
             JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id \
             WHERE k.principal=$1 AND k.client_request_id=$2 \
                AND k.operation_digest=j.operation_digest",
            &[&i.principal, &i.client_request_id],
        )?;
        let Some(row) = row else {
            return Ok(PgAdmissionObservation::Inconclusive);
        };
        let matches = row.get::<_, String>(0) == i.job_id
            && row.get::<_, String>(1) == i.request_digest
            && row.get::<_, String>(2) == i.operation_digest
            && row.get::<_, String>(3) == i.workspace_id
            && row.get::<_, String>(4) == i.workspace_snapshot_json
            && row.get::<_, String>(5) == i.execution_plan_json
            && row.get::<_, String>(6) == i.execution_plan_digest
            && row.get::<_, i64>(7) == i.created_at_ms
            && row.get::<_, String>(8) == i.attempt_id
            && row.get::<_, i64>(9) == 1
            && row.get::<_, String>(10) == i.launch_token_digest
            && row.get::<_, String>(11) == i.bundle_path
            && row.get::<_, String>(12) == i.unit_name
            && row.get::<_, i64>(13) == i.created_at_ms
            && row.get::<_, String>(14) == i.reservation_id
            && row.get::<_, i64>(15) == i64::from(i.global_limit)
            && row.get::<_, i64>(16) == i.created_at_ms;
        if !matches {
            return Ok(PgAdmissionObservation::Inconclusive);
        }

        let rows = tx.query(
            "SELECT event_sequence,event_type,origin,previous_state,new_state, \
                    reason_code,detail_json,detail_digest,observed_at_ms,attempt_id \
             FROM job_events WHERE job_id=$1 AND event_sequence BETWEEN 1 AND 3 \
             ORDER BY event_sequence",
            &[&i.job_id],
        )?;
        if rows.len() != 3 {
            return Ok(PgAdmissionObservation::Inconclusive);
        }
        let expected = [
            (
                "REQUEST_RECEIVED",
                "REQUEST_ACCEPTED",
                None,
                serde_json::json!({"requestDigest":i.request_digest}),
            ),
            (
                "JOB_RECORD_CREATED",
                "JOB_CREATED",
                None,
                serde_json::json!({"operationDigest":i.operation_digest}),
            ),
            (
                "ATTEMPT_CREATED",
                "ATTEMPT_ACCEPTED",
                Some("accepted"),
                serde_json::json!({"attemptNumber":1}),
            ),
        ];
        for (index, (row, (event_type, reason, new_state, detail))) in
            rows.iter().zip(expected.iter()).enumerate()
        {
            let encoded = detail.to_string();
            let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
            if row.get::<_, i64>(0) != (index + 1) as i64
                || row.get::<_, String>(1) != *event_type
                || row.get::<_, String>(2) != "SYSTEM_DERIVED"
                || row.get::<_, Option<String>>(3).is_some()
                || row.get::<_, Option<String>>(4).as_deref() != *new_state
                || row.get::<_, String>(5) != *reason
                || row.get::<_, String>(6) != encoded
                || row.get::<_, String>(7) != digest
                || row.get::<_, i64>(8) != i.created_at_ms
                || row.get::<_, Option<String>>(9).as_deref() != Some(i.attempt_id.as_str())
            {
                return Ok(PgAdmissionObservation::Inconclusive);
            }
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgAdmissionObservation::Confirmed(i.job_id.clone()))
    }
}
