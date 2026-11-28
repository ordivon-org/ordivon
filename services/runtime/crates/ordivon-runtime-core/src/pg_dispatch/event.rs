use super::super::PgAdmissionError;
use postgres::Transaction;
use sha2::{Digest, Sha256};
use uuid::Uuid;

pub(super) struct PgDispatchEvent<'a> {
    pub(super) job_id: &'a str,
    pub(super) attempt_id: &'a str,
    pub(super) event_type: &'a str,
    pub(super) origin: &'a str,
    pub(super) old: &'a str,
    pub(super) new: &'a str,
    pub(super) reason: &'a str,
    pub(super) detail: serde_json::Value,
    pub(super) at: i64,
}

pub(super) fn append_dispatch_event(
    tx: &mut Transaction<'_>,
    event: PgDispatchEvent<'_>,
) -> Result<(), PgAdmissionError> {
    let PgDispatchEvent {
        job_id,
        attempt_id,
        event_type,
        origin,
        old,
        new,
        reason,
        detail,
        at,
    } = event;
    let number: i64 = tx
        .query_one(
            "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=$1",
            &[&job_id],
        )?
        .get(0);
    let encoded = detail.to_string();
    let digest = format!("sha256:{}", hex::encode(Sha256::digest(encoded.as_bytes())));
    tx.execute(
        "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence, \
            event_type,origin,previous_state,new_state,reason_code,detail_json, \
            detail_digest,observed_at_ms) \
         VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)",
        &[
            &format!("event-{}", Uuid::now_v7()),
            &job_id,
            &attempt_id,
            &number,
            &event_type,
            &origin,
            &old,
            &new,
            &reason,
            &encoded,
            &digest,
            &at,
        ],
    )?;
    Ok(())
}
