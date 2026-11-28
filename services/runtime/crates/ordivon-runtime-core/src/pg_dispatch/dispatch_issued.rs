use super::super::{PgAdmissionError, PgAdmissionStore};
use super::attempt_lock::eligible_attempt;
use super::event::{append_dispatch_event, PgDispatchEvent};
use super::qualification::require_qualified_writer;
use super::types::{validate, PgDispatchIssued};
use postgres::IsolationLevel;
use sha2::{Digest, Sha256};

impl PgAdmissionStore {
    /// Persist dispatch intent BEFORE a physical execution provider launches.
    /// "starting" does not imply that a process started or that cancellation
    /// can safely release the reservation.
    pub fn mark_dispatch_issued_pg(
        &mut self,
        i: &PgDispatchIssued,
        issuer_schema: Option<&str>,
        issuer_principal: Option<&str>,
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
        // Admission-current is not dispatch-current. Recheck the original
        // immutable Harness Run cut before committing any new launch intent.
        if issuer_principal.is_some() && issuer_schema.is_none() {
            return Err(PgAdmissionError::Unqualified);
        }
        if let Some(schema) = issuer_schema {
            let job = tx.query_one(
                "SELECT principal,client_request_id,execution_plan_json FROM jobs WHERE job_id=$1",
                &[&job_id],
            )?;
            let principal: String = job.get(0);
            if issuer_principal.is_none_or(|expected| principal == expected) {
                let request_id: String = job.get(1);
                let immutable_plan: String = job.get(2);
                crate::pg_admission::issuer::require_current_harness_issuer_for_plan(
                    &mut tx,
                    &immutable_plan,
                    &request_id,
                    schema,
                )?;
            }
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
