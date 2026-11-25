//! Read-only bounded Job timeline and metadata, with original event provenance.
use super::types::{PgInspectionEvent, PgInspectionMetadata, PgJobSnapshot};
use crate::pg_admission::PgAdmissionError;
use postgres::Transaction;

pub(super) fn read_inspection(
    tx: &mut Transaction<'_>,
    snapshot: &PgJobSnapshot,
    event_limit: u32,
) -> Result<Option<PgInspectionMetadata>, PgAdmissionError> {
    let job = tx.query_one(
        "SELECT client_request_id,created_at_ms,EXISTS(SELECT 1 FROM attempts a WHERE a.job_id=j.job_id AND a.attempt_id<>$2) FROM jobs j WHERE j.job_id=$1",
        &[&snapshot.job_id,&snapshot.attempt_id],
    )?;
    let Ok(created_at_ms) = u64::try_from(job.get::<_, i64>(1)) else {
        return Ok(None);
    };
    let rows = tx.query(
        "SELECT e.event_sequence,e.attempt_id,e.event_type,e.origin,e.previous_state,e.new_state,e.reason_code,e.observed_at_ms,a.job_id
         FROM job_events e LEFT JOIN attempts a ON a.attempt_id=e.attempt_id
         WHERE e.job_id=$1 ORDER BY e.event_sequence LIMIT $2",
        &[&snapshot.job_id,&(i64::from(event_limit)+1)],
    )?;
    let mut events = Vec::with_capacity(rows.len());
    for row in rows {
        let attempt_id: Option<String> = row.get(1);
        if attempt_id.is_some()
            && row.get::<_, Option<String>>(8).as_deref() != Some(snapshot.job_id.as_str())
        {
            return Ok(None);
        }
        let (Ok(sequence), Ok(observed_at_ms)) = (
            u64::try_from(row.get::<_, i64>(0)),
            u64::try_from(row.get::<_, i64>(7)),
        ) else {
            return Ok(None);
        };
        events.push(PgInspectionEvent {
            sequence,
            attempt_id,
            event_type: row.get(2),
            origin: row.get(3),
            previous_state: row.get(4),
            new_state: row.get(5),
            reason_code: row.get(6),
            observed_at_ms,
        });
    }
    Ok(Some(PgInspectionMetadata {
        client_request_id: job.get(0),
        created_at_ms,
        has_other_attempts: job.get(2),
        events,
    }))
}
