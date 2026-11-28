use super::super::{PgAdmissionError, PgAdmissionStore};
use super::attempt_lock::eligible_attempt;
use super::event::{append_dispatch_event, PgDispatchEvent};
use super::qualification::require_qualified_writer;
use super::types::{validate, PgBundleReady};
use postgres::IsolationLevel;

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
}
