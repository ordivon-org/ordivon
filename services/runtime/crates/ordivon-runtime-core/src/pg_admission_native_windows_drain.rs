//! Durable, same-PG native Windows JobObject drain witness. This is NOT an
//! alternate Job Writer, a terminal decision, or another Registry.
//!
//! Called only after the Runtime service has independently connected to the
//! original Launcher OS pipe, compared kernel PID+birth and observed positive
//! ActiveProcesses==0 on the exact still-live JobObject. The original Launcher
//! retains the handle until this existing Job event transaction commits and
//! the Runtime sends its acknowledgement. Terminal CAS happens separately,
//! after the original Launcher is observed exited.
use super::{require_pg_writer_epoch, PgAdmissionError, PgAdmissionStore};
use postgres::IsolationLevel;
use serde_json::json;
use sha2::{Digest, Sha256};
use uuid::Uuid;

const NATIVE_DRAIN_EVENT: &str = "WINDOWS_NATIVE_JOB_DRAIN_OBSERVED";
const NATIVE_DRAIN_REASON: &str = "KERNEL_ORIGINAL_LAUNCHER_ACTIVE_ZERO";

#[derive(Clone, Debug)]
pub(crate) struct PgNativeWindowsDrainInput {
    pub job_id: String,
    pub attempt_id: String,
    pub expected_row_version: i64,
    pub expected_source_sha256: String,
    pub launch_token_digest: String,
    pub request_digest: String,
    pub result_digest: String,
    pub launcher_process_id: u32,
    pub launcher_creation_file_time: u64,
    pub observed_at_ms: i64,
}

#[derive(Debug, PartialEq, Eq)]
pub(crate) enum PgNativeWindowsDrainOutcome {
    Committed(String),
    Existing(String),
}

fn sha256_digest(bytes: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(bytes)))
}
fn valid_digest(v: &str) -> bool {
    v.len() == 71 && v.starts_with("sha256:") && v[7..].bytes().all(|b| b.is_ascii_hexdigit())
}
fn event_detail(i: &PgNativeWindowsDrainInput) -> String {
    // Stable key serialization plus exact real OS identity, not the target's
    // read/write receipt. Trust comes from the kernel observation at write
    // time and the qualified PG Writer, not from this serialized JSON.
    json!({
        "schemaVersion": 1,
        "jobId": i.job_id,
        "attemptId": i.attempt_id,
        "sourceSha256": i.expected_source_sha256,
        "launchTokenDigest": i.launch_token_digest,
        "requestDigest": i.request_digest,
        "resultDigest": i.result_digest,
        "jobObject": format!("Ordivon.{}", i.attempt_id),
        "launcherProcessId": i.launcher_process_id,
        "launcherCreationFileTime": i.launcher_creation_file_time,
        "kernelActiveProcesses": 0,
        "observedUnixMs": i.observed_at_ms,
    })
    .to_string()
}

impl PgAdmissionStore {
    /// Append a single idempotent immutable event to the real Job's journal.
    /// No terminal, Artifact, capacity release, process launch, or OS control
    /// is done here. The issuer/physical validation is performed by the native
    /// kernel gate BEFORE this method; never expose this as an MCP admission.
    pub(crate) fn record_native_windows_drain(
        &mut self,
        i: &PgNativeWindowsDrainInput,
    ) -> Result<PgNativeWindowsDrainOutcome, PgAdmissionError> {
        if i.job_id.is_empty()
            || i.attempt_id.is_empty()
            || i.expected_row_version < 0
            || i.observed_at_ms < 0
            || i.launcher_process_id == 0
            || i.launcher_creation_file_time == 0
            || i.expected_source_sha256.len() != 64
            || !i
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
            || !valid_digest(&i.launch_token_digest)
            || !valid_digest(&i.request_digest)
            || !valid_digest(&i.result_digest)
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        let detail = event_detail(i);
        let digest = sha256_digest(detail.as_bytes());
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::Serializable)
            .start()?;
        tx.query_one("SELECT pg_advisory_xact_lock($1)", &[&79245017_i64])?;
        let owner = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source' FOR UPDATE",
            &[],
        )?.ok_or(PgAdmissionError::Unqualified)?;
        if owner.get::<_, String>(0) != "QUALIFIED_WRITER"
            || owner.get::<_, String>(1) != i.expected_source_sha256
            || !owner.get::<_, bool>(2)
        {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, true)?;
        let Some(job) = tx.query_opt(
            "SELECT current_attempt_id,resolution FROM jobs WHERE job_id=$1 FOR UPDATE",
            &[&i.job_id],
        )?
        else {
            return Err(PgAdmissionError::InvalidInput);
        };
        let Some(attempt) = tx.query_opt(
            "SELECT state,row_version,launch_token_digest,bundle_digest FROM attempts WHERE attempt_id=$1 AND job_id=$2 FOR UPDATE",
            &[&i.attempt_id, &i.job_id],
        )? else { return Err(PgAdmissionError::InvalidInput); };
        // First qualify immutable source identity; a same-ID but different
        // frozen request/launch token is never valid even on idempotent replay.
        if attempt.get::<_, String>(2) != i.launch_token_digest
            || attempt.get::<_, Option<String>>(3).as_deref() != Some(&i.request_digest)
        {
            return Err(PgAdmissionError::Blocked);
        }
        let existing = tx.query_opt(
            "SELECT detail_json,detail_digest FROM job_events              WHERE job_id=$1 AND attempt_id=$2 AND event_type=$3",
            &[&i.job_id, &i.attempt_id, &NATIVE_DRAIN_EVENT],
        )?;
        if let Some(row) = existing {
            if row.get::<_, String>(0) != detail || row.get::<_, String>(1) != digest {
                return Err(PgAdmissionError::IdempotencyConflict);
            }
            tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
            return Ok(PgNativeWindowsDrainOutcome::Existing(i.job_id.clone()));
        }
        if job.get::<_, Option<String>>(0).as_deref() != Some(&i.attempt_id)
            || job.get::<_, Option<String>>(1).is_some()
            || attempt.get::<_, i64>(1) != i.expected_row_version
            || !matches!(
                attempt.get::<_, String>(0).as_str(),
                "starting" | "running" | "stopping" | "recovering"
            )
        {
            return Err(PgAdmissionError::Blocked);
        }
        let event_seq: i64 = tx
            .query_one(
                "SELECT COALESCE(MAX(event_sequence),0)+1 FROM job_events WHERE job_id=$1",
                &[&i.job_id],
            )?
            .get(0);
        tx.execute(
            "INSERT INTO job_events(event_id,job_id,attempt_id,event_sequence,event_type,origin,              previous_state,new_state,reason_code,detail_json,detail_digest,observed_at_ms)              VALUES($1,$2,$3,$4,$5,'SYSTEM_OBSERVED',$6,NULL,$7,$8,$9,$10)",
            &[
                &format!("event-{}",Uuid::now_v7()),
                &i.job_id,
                &i.attempt_id,
                &event_seq,
                &NATIVE_DRAIN_EVENT,
                &attempt.get::<_, String>(0),
                &NATIVE_DRAIN_REASON,
                &detail,
                &digest,
                &i.observed_at_ms,
            ],
        )?;
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(PgNativeWindowsDrainOutcome::Committed(i.job_id.clone()))
    }
}

impl PgAdmissionStore {
    /// Read the same existing PG Journal event after the original Launcher has
    /// exited and its named JobObject may have been destroyed. This is not a
    /// claim that a missing event means the process never drained. It only
    /// qualifies a previously durable original-issuer kernel observation.
    pub(crate) fn qualified_native_windows_drain(
        &mut self,
        i: &PgNativeWindowsDrainInput,
    ) -> Result<bool, PgAdmissionError> {
        let mut tx = self
            .client
            .build_transaction()
            .isolation_level(IsolationLevel::RepeatableRead)
            .read_only(true)
            .start()?;
        let Some(owner) = tx.query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )?
        else {
            return Err(PgAdmissionError::Unqualified);
        };
        if owner.get::<_, String>(0) != "QUALIFIED_WRITER"
            || owner.get::<_, String>(1) != i.expected_source_sha256
            || !owner.get::<_, bool>(2)
        {
            return Err(PgAdmissionError::Unqualified);
        }
        require_pg_writer_epoch(&mut tx, &i.expected_source_sha256, false)?;
        let rows = tx.query(
            "SELECT e.origin,e.reason_code,e.detail_json,e.detail_digest,              a.launch_token_digest,a.bundle_digest,a.row_version,              j.current_attempt_id,j.resolution              FROM job_events e              JOIN attempts a ON a.attempt_id=e.attempt_id AND a.job_id=e.job_id              JOIN jobs j ON j.job_id=e.job_id              WHERE e.job_id=$1 AND e.attempt_id=$2 AND e.event_type=$3",
            &[&i.job_id, &i.attempt_id, &NATIVE_DRAIN_EVENT],
        )?;
        if rows.len() != 1 {
            return Ok(false);
        }
        let r = &rows[0];
        let detail: String = r.get(2);
        let digest: String = r.get(3);
        if r.get::<_, String>(0) != "SYSTEM_OBSERVED"
            || r.get::<_, String>(1) != NATIVE_DRAIN_REASON
            || digest != sha256_digest(detail.as_bytes())
            || r.get::<_, String>(4) != i.launch_token_digest
            || r.get::<_, Option<String>>(5).as_deref() != Some(&i.request_digest)
            || r.get::<_, i64>(6) != i.expected_row_version
            || r.get::<_, Option<String>>(7).as_deref() != Some(&i.attempt_id)
            || r.get::<_, Option<String>>(8).is_some()
        {
            return Ok(false);
        }
        let v: serde_json::Value =
            serde_json::from_str(&detail).map_err(|_| PgAdmissionError::InvalidInput)?;
        if v.get("schemaVersion").and_then(|v| v.as_u64()) != Some(1)
            || v.get("jobId").and_then(|v| v.as_str()) != Some(i.job_id.as_str())
            || v.get("attemptId").and_then(|v| v.as_str()) != Some(i.attempt_id.as_str())
            || v.get("sourceSha256").and_then(|v| v.as_str())
                != Some(i.expected_source_sha256.as_str())
            || v.get("launchTokenDigest").and_then(|v| v.as_str())
                != Some(i.launch_token_digest.as_str())
            || v.get("requestDigest").and_then(|v| v.as_str()) != Some(i.request_digest.as_str())
            || v.get("resultDigest").and_then(|v| v.as_str()) != Some(i.result_digest.as_str())
            || v.get("jobObject").and_then(|v| v.as_str())
                != Some(format!("Ordivon.{}", i.attempt_id).as_str())
            || v.get("launcherProcessId").and_then(|v| v.as_u64())
                != Some(i.launcher_process_id as u64)
            || v.get("launcherCreationFileTime").and_then(|v| v.as_u64())
                != Some(i.launcher_creation_file_time)
            || v.get("kernelActiveProcesses").and_then(|v| v.as_u64()) != Some(0)
            || !v
                .get("observedUnixMs")
                .and_then(|v| v.as_i64())
                .is_some_and(|t| t >= 0)
        {
            return Ok(false);
        }
        tx.commit().map_err(|_| PgAdmissionError::UnknownCommit)?;
        Ok(true)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn fixture() -> PgNativeWindowsDrainInput {
        PgNativeWindowsDrainInput {
            job_id: "job-p".into(),
            attempt_id: "attempt-p".into(),
            expected_row_version: 1,
            expected_source_sha256: "a".repeat(64),
            launch_token_digest: format!("sha256:{}", "b".repeat(64)),
            request_digest: format!("sha256:{}", "c".repeat(64)),
            result_digest: format!("sha256:{}", "d".repeat(64)),
            launcher_process_id: 1234,
            launcher_creation_file_time: 999999,
            observed_at_ms: 10,
        }
    }
    #[test]
    fn native_drain_journal_detail_is_immutable_identity_bound() {
        let one = fixture();
        let d = event_detail(&one);
        let value: serde_json::Value = serde_json::from_str(&d).unwrap();
        assert_eq!(value["kernelActiveProcesses"], 0);
        assert_eq!(value["launcherProcessId"], 1234);
        assert_eq!(value["jobObject"], "Ordivon.attempt-p");
        assert_eq!(d, event_detail(&one));
        let mut other = one.clone();
        other.launcher_creation_file_time += 1;
        assert_ne!(
            sha256_digest(d.as_bytes()),
            sha256_digest(event_detail(&other).as_bytes())
        );
        assert!(valid_digest(&one.result_digest));
        assert!(!valid_digest("sha256:bad"));
    }
}
