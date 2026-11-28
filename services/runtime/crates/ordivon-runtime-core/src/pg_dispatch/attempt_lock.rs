use super::super::PgAdmissionError;
use postgres::Transaction;

pub(super) fn eligible_attempt(
    tx: &mut Transaction<'_>,
    attempt_id: &str,
    expected_version: i64,
) -> Result<(String, Option<String>), PgAdmissionError> {
    let row = tx
        .query_opt(
            "SELECT a.job_id,a.state,a.row_version,a.bundle_digest, \
                j.current_attempt_id,j.desired_state,j.resolution,r.state \
         FROM attempts a \
         JOIN jobs j ON j.job_id=a.job_id \
         JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id \
         WHERE a.attempt_id=$1 FOR UPDATE OF a,j,r",
            &[&attempt_id],
        )?
        .ok_or(PgAdmissionError::Blocked)?;
    let job_id: String = row.get(0);
    let state: String = row.get(1);
    let version: i64 = row.get(2);
    let bundle_digest: Option<String> = row.get(3);
    let current: Option<String> = row.get(4);
    let desired: String = row.get(5);
    let resolution: Option<String> = row.get(6);
    let reservation: String = row.get(7);
    if state != "accepted"
        || version != expected_version
        || current.as_deref() != Some(attempt_id)
        || desired != "run"
        || resolution.is_some()
        || reservation != "active"
    {
        return Err(PgAdmissionError::Blocked);
    }
    let allocated: bool = tx
        .query_one(
            "SELECT EXISTS(SELECT 1 FROM job_allocations WHERE attempt_id=$1 AND state='active')",
            &[&attempt_id],
        )?
        .get(0);
    if !allocated {
        return Err(PgAdmissionError::Blocked);
    }
    // An unresolved Runtime release effect is an additional dispatch fence.
    let pending: bool = tx
        .query_one(
            "SELECT EXISTS(SELECT 1 FROM job_runtime_release_effects \
         WHERE job_id=$1)",
            &[&job_id],
        )?
        .get(0);
    if pending {
        return Err(PgAdmissionError::Blocked);
    }
    Ok((job_id, bundle_digest))
}
