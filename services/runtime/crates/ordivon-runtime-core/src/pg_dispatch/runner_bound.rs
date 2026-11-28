use super::super::{PgAdmissionError, PgAdmissionStore};
use super::event::{append_dispatch_event, PgDispatchEvent};
use super::qualification::require_qualified_writer;
use super::types::{sha256_id, validate, PgRunnerBound};
use postgres::IsolationLevel;
use sha2::{Digest, Sha256};

impl PgAdmissionStore {
    /// Positive native Runner binding, not dispatch intent or domain completion.
    /// Only the Runtime native reconciler calls this after matching systemd's
    /// InvocationID, MainPID and cgroup to the Runner-start receipt.
    pub(crate) fn mark_runner_bound_pg(
        &mut self,
        i: &PgRunnerBound,
    ) -> Result<i64, PgAdmissionError> {
        validate(
            &i.attempt_id,
            i.expected_row_version,
            &i.expected_bundle_digest,
            i.observed_at_ms,
            &i.expected_source_sha256,
        )?;
        if !sha256_id(&i.runner_start_digest) || i.native_invocation_id.is_empty() {
            return Err(PgAdmissionError::InvalidInput);
        }
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        require_qualified_writer(&mut tx, &i.expected_source_sha256)?;
        let row = tx
            .query_opt(
                "SELECT a.job_id,a.state,a.row_version,a.bundle_digest,j.current_attempt_id,\
                j.desired_state,j.resolution,r.state \
             FROM attempts a JOIN jobs j ON j.job_id=a.job_id \
             JOIN concurrency_reservations r ON r.attempt_id=a.attempt_id \
             WHERE a.attempt_id=$1 FOR UPDATE OF a,j,r",
                &[&i.attempt_id],
            )?
            .ok_or(PgAdmissionError::Blocked)?;
        let job_id: String = row.get(0);
        let previous: String = row.get(1);
        let version: i64 = row.get(2);
        let bundle: Option<String> = row.get(3);
        let current: Option<String> = row.get(4);
        let desired: String = row.get(5);
        let resolution: Option<String> = row.get(6);
        let reservation: String = row.get(7);
        if previous != "starting"
            || version != i.expected_row_version
            || bundle.as_deref() != Some(i.expected_bundle_digest.as_str())
            || current.as_deref() != Some(i.attempt_id.as_str())
            || desired != "run"
            || resolution.is_some()
            || reservation != "active"
        {
            return Err(PgAdmissionError::Blocked);
        }
        let allocated: bool = tx.query_one(
            "SELECT EXISTS(SELECT 1 FROM job_allocations WHERE attempt_id=$1 AND state='active')",
            &[&i.attempt_id],
        )?.get(0);
        if !allocated {
            return Err(PgAdmissionError::Blocked);
        }
        let original_detail =
            serde_json::json!({"bundleDigest":i.expected_bundle_digest}).to_string();
        let original_digest = format!(
            "sha256:{}",
            hex::encode(Sha256::digest(original_detail.as_bytes()))
        );
        let issued: bool = tx
            .query_one(
                "SELECT EXISTS(SELECT 1 FROM job_events WHERE job_id=$1 AND attempt_id=$2 \
                AND event_type='DISPATCH_ISSUED' AND origin='SYSTEM_DERIVED' \
                AND previous_state='accepted' AND new_state='starting' \
                AND reason_code='AT_MOST_ONCE_BOUNDARY_COMMITTED' \
                AND detail_json=$3 AND detail_digest=$4)",
                &[&job_id, &i.attempt_id, &original_detail, &original_digest],
            )?
            .get(0);
        if !issued {
            return Err(PgAdmissionError::Blocked);
        }
        if tx.execute(
            "UPDATE attempts SET state='running',started_at_ms=$1,row_version=row_version+1 \
                WHERE attempt_id=$2 AND state='starting' AND row_version=$3",
            &[&i.observed_at_ms, &i.attempt_id, &i.expected_row_version],
        )? != 1
        {
            return Err(PgAdmissionError::Blocked);
        }
        append_dispatch_event(
            &mut tx,
            PgDispatchEvent {
                job_id: &job_id,
                attempt_id: &i.attempt_id,
                event_type: "RUNNER_BOUND",
                origin: "SYSTEM_OBSERVED",
                old: "starting",
                new: "running",
                reason: "SUPERVISOR_OWNER_MATCHED",
                detail: serde_json::json!({
                    "runnerStartDigest": i.runner_start_digest,
                    "invocationId": i.native_invocation_id,
                }),
                at: i.observed_at_ms,
            },
        )?;
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(i.expected_row_version + 1)
    }
}
