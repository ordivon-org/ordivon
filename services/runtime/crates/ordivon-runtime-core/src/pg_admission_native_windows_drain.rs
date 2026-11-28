//! Durable, same-PG native Windows JobObject drain witness. This is NOT an
//! alternate Job Writer, a terminal decision, or another Registry.
//!
//! Called only after the Runtime service has independently connected to the
//! original Launcher OS pipe, compared kernel PID+birth and observed positive
//! ActiveProcesses==0 on the exact still-live JobObject. The original Launcher
//! retains the handle until this existing Job event transaction commits and
//! the Runtime sends its acknowledgement. Terminal CAS happens separately,
//! after the original Launcher is observed exited.
use super::PgAdmissionError;
#[cfg(any(windows, test))]
use super::{require_pg_writer_epoch, PgAdmissionStore};
use crate::universal::sha256_bytes as sha256_digest;
#[cfg(any(windows, test))]
use postgres::IsolationLevel;
#[cfg(any(windows, test))]
use serde_json::json;
#[cfg(any(windows, test))]
use uuid::Uuid;

const NATIVE_DRAIN_EVENT: &str = "WINDOWS_NATIVE_JOB_DRAIN_OBSERVED";
const NATIVE_DRAIN_REASON: &str = "KERNEL_ORIGINAL_LAUNCHER_ACTIVE_ZERO";

#[cfg(any(windows, test))]
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

#[cfg(any(windows, test))]
#[derive(Debug, PartialEq, Eq)]
pub(crate) enum PgNativeWindowsDrainOutcome {
    Committed(String),
    Existing(String),
}

#[cfg(any(windows, test))]
fn valid_digest(v: &str) -> bool {
    v.len() == 71 && v.starts_with("sha256:") && v[7..].bytes().all(|b| b.is_ascii_hexdigit())
}
#[cfg(any(windows, test))]
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
        "expectedRowVersion": i.expected_row_version,
        "jobObject": format!("Ordivon.{}", i.attempt_id),
        "launcherProcessId": i.launcher_process_id,
        "launcherCreationFileTime": i.launcher_creation_file_time,
        "kernelActiveProcesses": 0,
        "observedUnixMs": i.observed_at_ms,
    })
    .to_string()
}

pub(super) struct PgWindowsDrainIdentity<'a> {
    pub(super) job_id: &'a str,
    pub(super) attempt_id: &'a str,
    pub(super) source_sha256: &'a str,
    pub(super) launch_token_digest: &'a str,
    pub(super) request_digest: &'a str,
    pub(super) result_digest: &'a str,
    pub(super) expected_row_version: i64,
}

#[cfg(any(windows, test))]
impl PgNativeWindowsDrainInput {
    fn drain_identity(&self) -> PgWindowsDrainIdentity<'_> {
        PgWindowsDrainIdentity {
            job_id: &self.job_id,
            attempt_id: &self.attempt_id,
            source_sha256: &self.expected_source_sha256,
            launch_token_digest: &self.launch_token_digest,
            request_digest: &self.request_digest,
            result_digest: &self.result_digest,
            expected_row_version: self.expected_row_version,
        }
    }
}

/// Pure canonical native-issuer event identity, shared by current readback
/// and by the ORIGINAL terminal+Artifact transaction. This function does not
/// authenticate the OS: only native_terminal_gate may *produce* the event.
fn event_detail_matches(
    detail: &str,
    digest: &str,
    expected: &PgWindowsDrainIdentity<'_>,
) -> Option<serde_json::Value> {
    if sha256_digest(detail.as_bytes()) != digest {
        return None;
    }
    let v: serde_json::Value = serde_json::from_str(detail).ok()?;
    let matches = v.get("schemaVersion").and_then(|x| x.as_u64()) == Some(1)
        && v.get("jobId").and_then(|x| x.as_str()) == Some(expected.job_id)
        && v.get("attemptId").and_then(|x| x.as_str()) == Some(expected.attempt_id)
        && v.get("sourceSha256").and_then(|x| x.as_str()) == Some(expected.source_sha256)
        && v.get("launchTokenDigest").and_then(|x| x.as_str())
            == Some(expected.launch_token_digest)
        && v.get("requestDigest").and_then(|x| x.as_str()) == Some(expected.request_digest)
        && v.get("resultDigest").and_then(|x| x.as_str()) == Some(expected.result_digest)
        && v.get("expectedRowVersion").and_then(|x| x.as_i64())
            == Some(expected.expected_row_version)
        && v.get("jobObject").and_then(|x| x.as_str())
            == Some(format!("Ordivon.{}", expected.attempt_id).as_str())
        && v.get("launcherProcessId")
            .and_then(|x| x.as_u64())
            .is_some_and(|pid| pid > 0 && pid <= u32::MAX as u64)
        && v.get("launcherCreationFileTime")
            .and_then(|x| x.as_u64())
            .is_some_and(|birth| birth > 0)
        && v.get("kernelActiveProcesses").and_then(|x| x.as_u64()) == Some(0)
        && v.get("observedUnixMs")
            .and_then(|x| x.as_i64())
            .is_some_and(|time| time >= 0);
    matches.then_some(v)
}

/// The terminal transaction is the LAST defense against a caller bypassing
/// the OS-original witness consumer. This is only invoked for a Windows
/// native Attempt and never for the Linux systemd/cgroup runner.
///
/// This checks the existing Job Journal IN THE SAME serializable transaction
/// that updates Attempt/Job/Reservation and records original Artifacts.
pub(super) fn require_native_windows_drain_in_terminal_tx(
    tx: &mut postgres::Transaction<'_>,
    expected: &PgWindowsDrainIdentity<'_>,
) -> Result<(), PgAdmissionError> {
    let rows = tx.query(
        "SELECT origin,reason_code,detail_json,detail_digest FROM job_events \
         WHERE job_id=$1 AND attempt_id=$2 AND event_type=$3",
        &[&expected.job_id, &expected.attempt_id, &NATIVE_DRAIN_EVENT],
    )?;
    if rows.len() != 1 {
        return Err(PgAdmissionError::Blocked);
    }
    let row = &rows[0];
    let detail: String = row.get(2);
    let digest: String = row.get(3);
    if row.get::<_, String>(0) != "SYSTEM_OBSERVED"
        || row.get::<_, String>(1) != NATIVE_DRAIN_REASON
        || event_detail_matches(&detail, &digest, expected).is_none()
    {
        return Err(PgAdmissionError::Blocked);
    }
    Ok(())
}

#[cfg(any(windows, test))]
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
            let stored_detail: String = row.get(0);
            let stored_digest: String = row.get(1);
            // The original witness timestamp is immutable, but a fresh
            // observation after an ambiguous COMMIT may use a different time.
            // Replay is qualified by full source/Attempt/OS identity, never
            // by a caller's claim that no prior mutation happened.
            let exact = event_detail_matches(&stored_detail, &stored_digest, &i.drain_identity())
                .is_some_and(|v| {
                    v.get("launcherProcessId").and_then(|x| x.as_u64())
                        == Some(i.launcher_process_id as u64)
                        && v.get("launcherCreationFileTime").and_then(|x| x.as_u64())
                            == Some(i.launcher_creation_file_time)
                });
            if !exact {
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

#[cfg(any(windows, test))]
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
        let match_v = event_detail_matches(&detail, &digest, &i.drain_identity());
        if !match_v.is_some_and(|v| {
            v.get("launcherProcessId").and_then(|x| x.as_u64())
                == Some(i.launcher_process_id as u64)
                && v.get("launcherCreationFileTime").and_then(|x| x.as_u64())
                    == Some(i.launcher_creation_file_time)
        }) {
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
