//! Explicitly opt-in PG dispatch-preparation persistence.
//! SOURCE/PG scratch only: these transactions do not create or launch a
//! physical runner and do not confer installed PostgreSQL writer authority.
use super::*;
use postgres::Transaction;

const ADMISSION_GLOBAL_LOCK: i64 = 79_245_017;

#[derive(Clone)]
pub struct PgBundleReady {
    pub attempt_id: String,
    pub expected_row_version: i64,
    pub bundle_digest: String,
    pub observed_at_ms: i64,
    pub expected_source_sha256: String,
}

#[derive(Clone)]
pub struct PgDispatchIssued {
    pub attempt_id: String,
    pub expected_row_version: i64,
    pub expected_bundle_digest: String,
    pub observed_at_ms: i64,
    pub expected_source_sha256: String,
}

fn sha256_id(s: &str) -> bool {
    s.len() == 71 && s.starts_with("sha256:") && s[7..].bytes().all(|b| b.is_ascii_hexdigit())
}

fn validate(
    attempt_id: &str,
    version: i64,
    digest: &str,
    at: i64,
    source: &str,
) -> Result<(), PgAdmissionError> {
    if attempt_id.is_empty()
        || version < 0
        || at < 0
        || !sha256_id(digest)
        || source.len() != 64
        || !source.bytes().all(|b| b.is_ascii_hexdigit())
    {
        return Err(PgAdmissionError::InvalidInput);
    }
    Ok(())
}

// The same serialization/authority fence as PgAdmissionStore::admit.
// This is an execution *precondition*, not authentication of the caller or a
// claim about already launched OS processes.
fn require_qualified_writer(
    tx: &mut Transaction<'_>,
    expected_source: &str,
) -> Result<(), PgAdmissionError> {
    tx.query_one(
        "SELECT pg_advisory_xact_lock($1)",
        &[&ADMISSION_GLOBAL_LOCK],
    )?;
    let row = tx
        .query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control \
         WHERE id='source' FOR UPDATE",
            &[],
        )?
        .ok_or(PgAdmissionError::Unqualified)?;
    if row.get::<_, String>(0) != "QUALIFIED_WRITER"
        || row.get::<_, String>(1) != expected_source
        || !row.get::<_, bool>(2)
    {
        return Err(PgAdmissionError::Unqualified);
    }
    require_pg_writer_epoch(tx, expected_source, true)?;
    Ok(())
}

fn eligible_attempt(
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

struct PgDispatchEvent<'a> {
    job_id: &'a str,
    attempt_id: &'a str,
    event_type: &'a str,
    origin: &'a str,
    old: &'a str,
    new: &'a str,
    reason: &'a str,
    detail: serde_json::Value,
    at: i64,
}

fn append_dispatch_event(
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

impl PgAdmissionStore {
    /// Persist a uniquely identified, immutable execution bundle before
    /// declaring that external dispatch might be attempted.
    pub fn commit_bundle_ready_pg(&mut self, i: &PgBundleReady) -> Result<i64, PgAdmissionError> {
        validate(
            &i.attempt_id,
            i.expected_row_version,
            &i.bundle_digest,
            i.observed_at_ms,
            &i.expected_source_sha256,
        )?;
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        require_qualified_writer(&mut tx, &i.expected_source_sha256)?;
        let (job_id, bundle) = eligible_attempt(&mut tx, &i.attempt_id, i.expected_row_version)?;
        if bundle.is_some() {
            return Err(PgAdmissionError::Blocked);
        }
        let affected = tx.execute(
            "UPDATE attempts SET bundle_digest=$1,row_version=row_version+1 \
             WHERE attempt_id=$2 AND state='accepted' AND row_version=$3 AND bundle_digest IS NULL",
            &[&i.bundle_digest, &i.attempt_id, &i.expected_row_version],
        )?;
        if affected != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        append_dispatch_event(
            &mut tx,
            PgDispatchEvent {
                job_id: &job_id,
                attempt_id: &i.attempt_id,
                event_type: "BUNDLE_READY",
                origin: "SYSTEM_OBSERVED",
                old: "accepted",
                new: "accepted",
                reason: "BUNDLE_COMMITTED",
                detail: serde_json::json!({"bundleDigest":i.bundle_digest}),
                at: i.observed_at_ms,
            },
        )?;
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(i.expected_row_version + 1)
    }

    /// Persist dispatch intent BEFORE a physical execution provider launches.
    /// "starting" does not imply that a process started or that cancellation
    /// can safely release the reservation.
    pub fn mark_dispatch_issued_pg(
        &mut self,
        i: &PgDispatchIssued,
    ) -> Result<i64, PgAdmissionError> {
        validate(
            &i.attempt_id,
            i.expected_row_version,
            &i.expected_bundle_digest,
            i.observed_at_ms,
            &i.expected_source_sha256,
        )?;
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        require_qualified_writer(&mut tx, &i.expected_source_sha256)?;
        let (job_id, bundle) = eligible_attempt(&mut tx, &i.attempt_id, i.expected_row_version)?;
        if bundle.as_deref() != Some(&i.expected_bundle_digest) {
            return Err(PgAdmissionError::Blocked);
        }
        let expected_detail =
            serde_json::json!({"bundleDigest":i.expected_bundle_digest}).to_string();
        let expected_digest = format!(
            "sha256:{}",
            hex::encode(Sha256::digest(expected_detail.as_bytes()))
        );
        let event_valid: bool = tx
            .query_one(
                "SELECT EXISTS(SELECT 1 FROM job_events WHERE job_id=$1 \
                AND attempt_id=$2 AND event_type='BUNDLE_READY' \
                AND origin='SYSTEM_OBSERVED' AND previous_state='accepted' \
                AND new_state='accepted' AND reason_code='BUNDLE_COMMITTED' \
                AND detail_json=$3 AND detail_digest=$4)",
                &[&job_id, &i.attempt_id, &expected_detail, &expected_digest],
            )?
            .get(0);
        if !event_valid {
            return Err(PgAdmissionError::Blocked);
        }
        let affected = tx.execute(
            "UPDATE attempts SET state='starting',row_version=row_version+1 \
             WHERE attempt_id=$1 AND state='accepted' AND row_version=$2 \
             AND bundle_digest=$3",
            &[
                &i.attempt_id,
                &i.expected_row_version,
                &i.expected_bundle_digest,
            ],
        )?;
        if affected != 1 {
            return Err(PgAdmissionError::Blocked);
        }
        append_dispatch_event(
            &mut tx,
            PgDispatchEvent {
                job_id: &job_id,
                attempt_id: &i.attempt_id,
                event_type: "DISPATCH_ISSUED",
                origin: "SYSTEM_DERIVED",
                old: "accepted",
                new: "starting",
                reason: "AT_MOST_ONCE_BOUNDARY_COMMITTED",
                detail: serde_json::json!({"bundleDigest":i.expected_bundle_digest}),
                at: i.observed_at_ms,
            },
        )?;
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(i.expected_row_version + 1)
    }
}
