//! Read-only Windows-native evidence check for the PostgreSQL Runtime.
//! Phase is an observation, not a terminal or proof that a Job Object is dead.
//! The authoritative effect transition remains PG CAS + OS process ownership.
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    fs,
    path::{Path, PathBuf},
};

const MAX_EVIDENCE_BYTES: u64 = 2 * 1024 * 1024;
const MAX_OUTPUT_BYTES: u64 = 4 * 1024 * 1024;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PgWindowsWitnessIdentity {
    pub job_id: String,
    pub attempt_id: String,
    pub launch_token_digest: String,
    /// Digest of the exact immutable launcher request, not the PG execution plan.
    pub request_digest: String,
    /// Must identify the exact binary admitted as the Windows launcher.
    pub launcher_image_digest: String,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PgWindowsWitnessPhase {
    NoLauncherWitness,
    LauncherWitness,
    TargetWitness,
    ResultWitnessPendingOsReconciliation,
}

/// A syntax-bound receipt, NOT a trusted OS observation: the carrier can be
/// written by the native target. This must never authorize terminal PG CAS.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PgWindowsDrainCandidate {
    pub receipt_digest: String,
    pub launcher_process_id: u64,
    pub launcher_creation_file_time: u64,
    pub target_process_id: u64,
    pub target_creation_file_time: u64,
    pub total_processes: u64,
    pub observed_unix_ms: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PgWindowsWitnessObservation {
    pub phase: PgWindowsWitnessPhase,
    /// Derived only from a qualified PG Attempt identity, not target-authored JSON.
    /// Lookup is diagnostic: a named kernel object becoming absent is UNKNOWN.
    pub admitted_job_object_name: String,
    pub launcher_process_id: Option<u64>,
    pub launcher_creation_file_time: Option<u64>,
    pub target_process_id: Option<u64>,
    pub target_creation_file_time: Option<u64>,
    pub result_digest: Option<String>,
    /// Result files reside in a target-mutable carrier. They never prove that
    /// the owned process tree exited or that PostgreSQL committed a terminal.
    pub terminal_proven: bool,
}

fn read_value(path: &Path) -> Result<Option<(Value, Vec<u8>)>, String> {
    if !path.exists() {
        return Ok(None);
    }
    let meta = fs::symlink_metadata(path).map_err(|e| format!("metadata: {e}"))?;
    if !meta.file_type().is_file() || meta.len() > MAX_EVIDENCE_BYTES {
        return Err("evidence must be a bounded regular non-symlink file".into());
    }
    let bytes = fs::read(path).map_err(|e| format!("evidence read: {e}"))?;
    if bytes.len() as u64 != meta.len() {
        return Err("evidence mutated during read".into());
    }
    let value =
        serde_json::from_slice::<Value>(&bytes).map_err(|e| format!("evidence JSON: {e}"))?;
    if !value.is_object() {
        return Err("evidence must be a JSON object".into());
    }
    Ok(Some((value, bytes)))
}
fn exact_text(value: &Value, key: &str, expected: &str) -> Result<(), String> {
    if value.get(key).and_then(Value::as_str) != Some(expected) {
        return Err(format!("{key}: identity mismatch"));
    }
    Ok(())
}
fn positive_u64(value: &Value, key: &str) -> Result<u64, String> {
    let v = value.get(key).and_then(Value::as_u64).unwrap_or(0);
    (v > 0)
        .then_some(v)
        .ok_or_else(|| format!("{key}: missing or nonpositive"))
}
fn identity(value: &Value, expected: &PgWindowsWitnessIdentity) -> Result<(), String> {
    if value.get("schemaVersion").and_then(Value::as_u64) != Some(1) {
        return Err("schemaVersion: invalid".into());
    }
    exact_text(value, "jobId", &expected.job_id)?;
    exact_text(value, "attemptId", &expected.attempt_id)?;
    exact_text(value, "launchTokenDigest", &expected.launch_token_digest)
}
fn sha256(bytes: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(bytes)))
}

/// No OS calls. A mere result.json is always a candidate, never a terminal.
/// Uses exact attempt and process creation identity to reject stale/PID-reused
/// witnesses and does not infer negative effects from missing evidence.
pub fn inspect_windows_pg_bundle(
    dir: &Path,
    expected: &PgWindowsWitnessIdentity,
) -> Result<PgWindowsWitnessObservation, String> {
    inspect_windows_pg_bundle_with_start(dir, expected).map(|(witness, _)| witness)
}

// Return the digest of the SAME validated start bytes, never re-read the
// mutable carrier to manufacture a different RUNNER_BOUND commitment.
fn inspect_windows_pg_bundle_with_start(
    dir: &Path,
    expected: &PgWindowsWitnessIdentity,
) -> Result<(PgWindowsWitnessObservation, Option<String>), String> {
    if expected.job_id.is_empty()
        || expected.attempt_id.is_empty()
        || !expected.launch_token_digest.starts_with("sha256:")
        || !expected.request_digest.starts_with("sha256:")
        || !expected.launcher_image_digest.starts_with("sha256:")
    {
        return Err("unqualified expected identity".into());
    }
    let launcher = read_value(&dir.join("windows-launcher-start.json"))?;
    let target = read_value(&dir.join("windows-start.json"))?;
    let result = read_value(&dir.join("result.json"))?;
    let mut output = PgWindowsWitnessObservation {
        phase: PgWindowsWitnessPhase::NoLauncherWitness,
        admitted_job_object_name: format!("Ordivon.{}", expected.attempt_id),
        launcher_process_id: None,
        launcher_creation_file_time: None,
        target_process_id: None,
        target_creation_file_time: None,
        result_digest: None,
        terminal_proven: false,
    };
    let Some((launch, _)) = launcher else {
        if target.is_some() || result.is_some() {
            return Err("target/result without independently bound launcher identity".into());
        }
        return Ok((output, None));
    };
    identity(&launch, expected)?;
    exact_text(&launch, "requestDigest", &expected.request_digest)?;
    exact_text(
        &launch,
        "launcherImageDigest",
        &expected.launcher_image_digest,
    )?;
    exact_text(
        &launch,
        "jobName",
        &format!("Ordivon.{}", expected.attempt_id),
    )?;
    let pid = positive_u64(&launch, "launcherProcessId")?;
    let birth = positive_u64(&launch, "launcherProcessCreationTimeFileTime")?;
    positive_u64(&launch, "observedUnixMs")?;
    output.phase = PgWindowsWitnessPhase::LauncherWitness;
    output.launcher_process_id = Some(pid);
    output.launcher_creation_file_time = Some(birth);
    let Some((start, start_bytes)) = target else {
        if result.is_some() {
            return Err("result without bound target-start identity".into());
        }
        return Ok((output, None));
    };
    identity(&start, expected)?;
    exact_text(&start, "requestDigest", &expected.request_digest)?;
    exact_text(
        &start,
        "launcherImageDigest",
        &expected.launcher_image_digest,
    )?;
    exact_text(
        &start,
        "jobName",
        &format!("Ordivon.{}", expected.attempt_id),
    )?;
    if positive_u64(&start, "launcherProcessId")? != pid
        || positive_u64(&start, "launcherProcessCreationTimeFileTime")? != birth
    {
        return Err("target launcher owner is not the admitted launcher".into());
    }
    output.target_process_id = Some(positive_u64(&start, "processId")?);
    output.target_creation_file_time = Some(positive_u64(&start, "processCreationTimeFileTime")?);
    positive_u64(&start, "observedUnixMs")?;
    output.phase = PgWindowsWitnessPhase::TargetWitness;
    let Some((complete, bytes)) = result else {
        return Ok((output, Some(sha256(&start_bytes))));
    };
    identity(&complete, expected)?;
    exact_text(&complete, "taskId", &expected.attempt_id)?;
    if !matches!(
        complete.get("status").and_then(Value::as_str),
        Some("COMPLETED" | "FAILED" | "CANCELLED")
    ) {
        return Err("invalid runner result status".into());
    }
    let status = complete
        .get("status")
        .and_then(Value::as_str)
        .unwrap_or_default();
    let exit = complete.get("exitCode").and_then(Value::as_i64);
    let timeout = complete.get("timedOut").and_then(Value::as_bool);
    if timeout.is_none()
        || (status == "COMPLETED" && (exit != Some(0) || timeout != Some(false)))
        || (status == "CANCELLED" && timeout != Some(false))
    {
        return Err("result terminal status contradicts process exit evidence".into());
    }
    let begin = positive_u64(&complete, "startedUnixMs")?;
    if positive_u64(&complete, "finishedUnixMs")? < begin {
        return Err("result finished before start".into());
    }
    for (name, filename) in [("stdout", "stdout.log"), ("stderr", "stderr.log")] {
        let item = complete
            .get(name)
            .ok_or_else(|| format!("{name}: absent"))?;
        exact_text(item, "fileName", filename)?;
        let artifact = read_raw_bounded(&dir.join(filename))?;
        if item.get("retainedBytes").and_then(Value::as_u64) != Some(artifact.len() as u64)
            || item.get("digest").and_then(Value::as_str) != Some(sha256(&artifact).as_str())
        {
            return Err(format!("{name}: retained artifact identity mismatch"));
        }
    }
    output.phase = PgWindowsWitnessPhase::ResultWitnessPendingOsReconciliation;
    output.result_digest = Some(sha256(&bytes));
    Ok((output, Some(sha256(&start_bytes))))
}
/// Missing receipt is UNKNOWN. A matching carrier receipt is NOT a trusted
/// native drain and never substitutes for independent owner/provenance checks.
pub fn inspect_windows_pg_drain_candidate(
    dir: &Path,
    expected: &PgWindowsWitnessIdentity,
    observed: &PgWindowsWitnessObservation,
) -> Result<Option<PgWindowsDrainCandidate>, String> {
    let Some((drain, bytes)) = read_value(&dir.join("windows-job-drain.json"))? else {
        return Ok(None);
    };
    if observed.phase != PgWindowsWitnessPhase::ResultWitnessPendingOsReconciliation
        || observed.result_digest.is_none()
        || observed.admitted_job_object_name != format!("Ordivon.{}", expected.attempt_id)
    {
        return Err("native drain without exact admitted Result/Attempt witness".into());
    }
    identity(&drain, expected)?;
    exact_text(&drain, "requestDigest", &expected.request_digest)?;
    exact_text(&drain, "jobName", &observed.admitted_job_object_name)?;
    let launcher_process_id = positive_u64(&drain, "launcherProcessId")?;
    let launcher_creation_file_time = positive_u64(&drain, "launcherProcessCreationTimeFileTime")?;
    let target_process_id = positive_u64(&drain, "targetProcessId")?;
    let target_creation_file_time = positive_u64(&drain, "targetProcessCreationTimeFileTime")?;
    if observed.launcher_process_id != Some(launcher_process_id)
        || observed.launcher_creation_file_time != Some(launcher_creation_file_time)
        || observed.target_process_id != Some(target_process_id)
        || observed.target_creation_file_time != Some(target_creation_file_time)
    {
        return Err("native drain process birth does not match admitted owner/target".into());
    }
    let total_processes = positive_u64(&drain, "totalProcesses")?;
    if drain.get("activeProcesses").and_then(Value::as_u64) != Some(0) {
        return Err("native drain does not positively report zero active processes".into());
    }
    let observed_unix_ms = positive_u64(&drain, "observedUnixMs")?;
    Ok(Some(PgWindowsDrainCandidate {
        receipt_digest: sha256(&bytes),
        launcher_process_id,
        launcher_creation_file_time,
        target_process_id,
        target_creation_file_time,
        total_processes,
        observed_unix_ms,
    }))
}

fn read_raw_bounded(path: &Path) -> Result<Vec<u8>, String> {
    let meta = fs::symlink_metadata(path).map_err(|e| format!("output metadata: {e}"))?;
    if !meta.file_type().is_file() || meta.len() > MAX_OUTPUT_BYTES {
        return Err("output must be a bounded regular file".into());
    }
    let bytes = fs::read(path).map_err(|e| format!("output read: {e}"))?;
    if bytes.len() as u64 != meta.len() {
        return Err("output changed during read".into());
    }
    Ok(bytes)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use tempfile::TempDir;

    fn fixtures() -> (TempDir, PgWindowsWitnessIdentity) {
        let dir = TempDir::new().unwrap();
        let id = PgWindowsWitnessIdentity {
            job_id: "job-1".into(),
            attempt_id: "attempt-1".into(),
            launch_token_digest: "sha256:".to_string() + &"a".repeat(64),
            request_digest: "sha256:".to_string() + &"b".repeat(64),
            launcher_image_digest: "sha256:".to_string() + &"c".repeat(64),
        };
        (dir, id)
    }
    fn write(dir: &Path, name: &str, value: Value) {
        fs::write(dir.join(name), serde_json::to_vec(&value).unwrap()).unwrap();
    }
    fn launcher(id: &PgWindowsWitnessIdentity) -> Value {
        json!({"schemaVersion":1,"jobId":id.job_id,"attemptId":id.attempt_id,
            "launchTokenDigest":id.launch_token_digest,"requestDigest":id.request_digest,
            "launcherImageDigest":id.launcher_image_digest,"jobName":"Ordivon.attempt-1",
            "launcherProcessId":120,"launcherProcessCreationTimeFileTime":130,"observedUnixMs":1})
    }
    fn target(id: &PgWindowsWitnessIdentity) -> Value {
        let mut x = launcher(id);
        x["processId"] = json!(140);
        x["processCreationTimeFileTime"] = json!(150);
        x
    }
    fn result(id: &PgWindowsWitnessIdentity) -> Value {
        let empty = sha256(&[]);
        json!({"schemaVersion":1,"jobId":id.job_id,"attemptId":id.attempt_id,
            "taskId":id.attempt_id,"launchTokenDigest":id.launch_token_digest,
            "status":"COMPLETED","exitCode":0,"timedOut":false,"startedUnixMs":2,"finishedUnixMs":3,
            "stdout":{"fileName":"stdout.log","retainedBytes":0,"digest":empty},
            "stderr":{"fileName":"stderr.log","retainedBytes":0,"digest":empty}})
    }
    fn with_result(dir: &Path, id: &PgWindowsWitnessIdentity) -> PgWindowsWitnessObservation {
        write(dir, "windows-launcher-start.json", launcher(id));
        write(dir, "windows-start.json", target(id));
        fs::write(dir.join("stdout.log"), []).unwrap();
        fs::write(dir.join("stderr.log"), []).unwrap();
        write(dir, "result.json", result(id));
        inspect_windows_pg_bundle(dir, id).unwrap()
    }

    #[test]
    fn validated_start_digest_is_exact_and_missing_or_foreign_is_not_a_binding() {
        let (d, i) = fixtures();
        let (empty, digest) = inspect_windows_pg_bundle_with_start(d.path(), &i).unwrap();
        assert_eq!(empty.phase, PgWindowsWitnessPhase::NoLauncherWitness);
        assert_eq!(digest, None);
        write(d.path(), "windows-launcher-start.json", launcher(&i));
        let (only_launcher, digest) = inspect_windows_pg_bundle_with_start(d.path(), &i).unwrap();
        assert_eq!(only_launcher.phase, PgWindowsWitnessPhase::LauncherWitness);
        assert_eq!(digest, None);
        let bytes = serde_json::to_vec_pretty(&target(&i)).unwrap();
        fs::write(d.path().join("windows-start.json"), &bytes).unwrap();
        let (start, digest) = inspect_windows_pg_bundle_with_start(d.path(), &i).unwrap();
        assert_eq!(start.phase, PgWindowsWitnessPhase::TargetWitness);
        assert_eq!(digest, Some(sha256(&bytes)));
        assert!(!start.terminal_proven);
        let mut foreign = target(&i);
        foreign["launcherProcessId"] = json!(999);
        write(d.path(), "windows-start.json", foreign);
        assert!(inspect_windows_pg_bundle_with_start(d.path(), &i).is_err());
    }

    fn native_drain(id: &PgWindowsWitnessIdentity) -> Value {
        json!({"schemaVersion":1,"jobId":id.job_id,"attemptId":id.attempt_id,
            "launchTokenDigest":id.launch_token_digest,"requestDigest":id.request_digest,
            "jobName":format!("Ordivon.{}",id.attempt_id),
            "launcherProcessId":120,"launcherProcessCreationTimeFileTime":130,
            "targetProcessId":140,"targetProcessCreationTimeFileTime":150,
            "totalProcesses":2,"activeProcesses":0,"observedUnixMs":4})
    }

    #[test]
    fn no_native_drain_receipt_remains_unknown() {
        let (d, i) = fixtures();
        let observed = with_result(d.path(), &i);
        assert_eq!(
            inspect_windows_pg_drain_candidate(d.path(), &i, &observed).unwrap(),
            None
        );
        assert!(!observed.terminal_proven);
    }

    #[test]
    fn exact_drain_receipt_still_cannot_prove_os_terminal() {
        let (d, i) = fixtures();
        let observed = with_result(d.path(), &i);
        write(d.path(), "windows-job-drain.json", native_drain(&i));
        let candidate = inspect_windows_pg_drain_candidate(d.path(), &i, &observed)
            .unwrap()
            .expect("syntax only");
        assert_eq!(candidate.total_processes, 2);
        assert_eq!(candidate.launcher_process_id, 120);
        assert!(candidate.receipt_digest.starts_with("sha256:"));
        assert!(!observed.terminal_proven);
    }

    #[test]
    fn drain_rejects_cross_attempt_and_stale_request() {
        let (d, i) = fixtures();
        let observed = with_result(d.path(), &i);
        let mut wrong = native_drain(&i);
        wrong["attemptId"] = json!("older-attempt");
        write(d.path(), "windows-job-drain.json", wrong);
        assert!(inspect_windows_pg_drain_candidate(d.path(), &i, &observed).is_err());
        let mut wrong = native_drain(&i);
        wrong["requestDigest"] = json!("sha256:stale");
        write(d.path(), "windows-job-drain.json", wrong);
        assert!(inspect_windows_pg_drain_candidate(d.path(), &i, &observed).is_err());
    }

    #[test]
    fn drain_rejects_launcher_and_target_pid_reuse() {
        let (d, i) = fixtures();
        let observed = with_result(d.path(), &i);
        let mut wrong = native_drain(&i);
        wrong["launcherProcessCreationTimeFileTime"] = json!(131);
        write(d.path(), "windows-job-drain.json", wrong);
        assert!(inspect_windows_pg_drain_candidate(d.path(), &i, &observed).is_err());
        let mut wrong = native_drain(&i);
        wrong["targetProcessCreationTimeFileTime"] = json!(151);
        write(d.path(), "windows-job-drain.json", wrong);
        assert!(inspect_windows_pg_drain_candidate(d.path(), &i, &observed).is_err());
    }

    #[test]
    fn drain_rejects_populated_and_never_assigned_job() {
        let (d, i) = fixtures();
        let observed = with_result(d.path(), &i);
        let mut wrong = native_drain(&i);
        wrong["activeProcesses"] = json!(1);
        write(d.path(), "windows-job-drain.json", wrong);
        assert!(inspect_windows_pg_drain_candidate(d.path(), &i, &observed).is_err());
        let mut wrong = native_drain(&i);
        wrong["totalProcesses"] = json!(0);
        write(d.path(), "windows-job-drain.json", wrong);
        assert!(inspect_windows_pg_drain_candidate(d.path(), &i, &observed).is_err());
    }

    #[test]
    fn drain_alone_cannot_invent_result() {
        let (d, i) = fixtures();
        write(d.path(), "windows-launcher-start.json", launcher(&i));
        write(d.path(), "windows-start.json", target(&i));
        let observed = inspect_windows_pg_bundle(d.path(), &i).unwrap();
        write(d.path(), "windows-job-drain.json", native_drain(&i));
        assert!(inspect_windows_pg_drain_candidate(d.path(), &i, &observed).is_err());
        assert!(!observed.terminal_proven);
    }

    #[test]
    #[cfg(unix)]
    fn drain_symlink_is_rejected() {
        let (d, i) = fixtures();
        let observed = with_result(d.path(), &i);
        std::os::unix::fs::symlink("result.json", d.path().join("windows-job-drain.json")).unwrap();
        assert!(inspect_windows_pg_drain_candidate(d.path(), &i, &observed).is_err());
    }

    #[test]
    fn missing_is_unknown_not_a_negative() {
        let (d, i) = fixtures();
        assert_eq!(
            inspect_windows_pg_bundle(d.path(), &i).unwrap().phase,
            PgWindowsWitnessPhase::NoLauncherWitness
        );
    }
    #[test]
    fn launcher_only_is_not_target_started() {
        let (d, i) = fixtures();
        write(d.path(), "windows-launcher-start.json", launcher(&i));
        assert_eq!(
            inspect_windows_pg_bundle(d.path(), &i).unwrap().phase,
            PgWindowsWitnessPhase::LauncherWitness
        );
    }
    #[test]
    fn refuses_spoofed_pid_or_birth() {
        let (d, i) = fixtures();
        write(d.path(), "windows-launcher-start.json", launcher(&i));
        let mut x = target(&i);
        x["launcherProcessCreationTimeFileTime"] = json!(999);
        write(d.path(), "windows-start.json", x);
        assert!(inspect_windows_pg_bundle(d.path(), &i)
            .unwrap_err()
            .contains("owner"));
    }
    #[test]
    fn result_without_start_never_terminal() {
        let (d, i) = fixtures();
        write(d.path(), "windows-launcher-start.json", launcher(&i));
        write(d.path(), "result.json", result(&i));
        assert!(inspect_windows_pg_bundle(d.path(), &i).is_err());
    }
    #[test]
    fn result_is_not_os_death_proof() {
        let (d, i) = fixtures();
        write(d.path(), "windows-launcher-start.json", launcher(&i));
        write(d.path(), "windows-start.json", target(&i));
        fs::write(d.path().join("stdout.log"), []).unwrap();
        fs::write(d.path().join("stderr.log"), []).unwrap();
        write(d.path(), "result.json", result(&i));
        let x = inspect_windows_pg_bundle(d.path(), &i).unwrap();
        assert_eq!(
            x.phase,
            PgWindowsWitnessPhase::ResultWitnessPendingOsReconciliation
        );
        assert!(!x.terminal_proven);
        assert!(x.result_digest.is_some());
        fs::write(d.path().join("stdout.log"), b"mutated").unwrap();
        assert!(inspect_windows_pg_bundle(d.path(), &i)
            .unwrap_err()
            .contains("stdout"));
    }
    #[test]
    fn unadmitted_launcher_image_rejected() {
        let (d, i) = fixtures();
        let mut x = launcher(&i);
        x["launcherImageDigest"] = json!("sha256:bad");
        write(d.path(), "windows-launcher-start.json", x);
        assert!(inspect_windows_pg_bundle(d.path(), &i).is_err());
    }
    #[test]
    fn contradicted_terminal_state_rejected() {
        let (d, i) = fixtures();
        write(d.path(), "windows-launcher-start.json", launcher(&i));
        write(d.path(), "windows-start.json", target(&i));
        fs::write(d.path().join("stdout.log"), []).unwrap();
        fs::write(d.path().join("stderr.log"), []).unwrap();
        let mut x = result(&i);
        x["exitCode"] = json!(2);
        write(d.path(), "result.json", x);
        assert!(inspect_windows_pg_bundle(d.path(), &i)
            .unwrap_err()
            .contains("contradicts"));
    }
    #[test]
    fn absent_target_with_stale_result_is_contradiction() {
        let (d, i) = fixtures();
        write(d.path(), "result.json", result(&i));
        assert!(inspect_windows_pg_bundle(d.path(), &i).is_err());
    }
    #[test]
    fn unexpected_symlink_rejected() {
        let (d, i) = fixtures();
        write(d.path(), "windows-launcher-start.json", launcher(&i));
        #[cfg(unix)]
        std::os::unix::fs::symlink(
            "windows-launcher-start.json",
            d.path().join("windows-start.json"),
        )
        .unwrap();
        #[cfg(unix)]
        assert!(inspect_windows_pg_bundle(d.path(), &i).is_err());
    }
}

#[path = "pg_windows_evidence/terminal.rs"]
pub(crate) mod terminal;

/// Bind a Windows evidence read to an exact, admitted PostgreSQL Job snapshot.
/// PostgreSQL qualification and ownership are checked in one read-only snapshot.
/// This must NOT be used to declare terminal before independent OS owner death
/// (PID + creation FILETIME / Job Object) and the final PG CAS are established.
pub fn inspect_admitted_windows_pg_bundle(
    dsn: &str,
    schema: &str,
    source_sha256: &str,
    principal: &str,
    job_id: &str,
    store_root: &Path,
) -> Result<PgWindowsWitnessObservation, String> {
    let mut store = crate::pg_admission::PgAdmissionStore::connect(dsn, schema)
        .map_err(|_| "PG schema unavailable or invalid".to_string())?;
    let bound =
        bind_admitted_windows_pg_bundle(&mut store, source_sha256, principal, job_id, store_root)?;
    inspect_windows_pg_bundle(&bound.root, &bound.identity)
}

struct BoundWindowsPgBundle {
    root: PathBuf,
    identity: PgWindowsWitnessIdentity,
    #[cfg(windows)]
    attempt_row_version: i64,
    #[cfg(windows)]
    resolved: bool,
    #[cfg(windows)]
    starting_natural: bool,
    #[cfg(windows)]
    runner_bound_start_digest: Option<String>,
}

/// Shared trusted binding for readback and effectful reconciliation.
/// Never accepts caller-provided Attempt, bundle, launcher or row-version identity.
fn bind_admitted_windows_pg_bundle(
    store: &mut crate::pg_admission::PgAdmissionStore,
    source_sha256: &str,
    principal: &str,
    job_id: &str,
    store_root: &Path,
) -> Result<BoundWindowsPgBundle, String> {
    use crate::pg_readback::PgJobReadback;
    use postgres::IsolationLevel;

    if source_sha256.len() != 64
        || !source_sha256.bytes().all(|v| v.is_ascii_hexdigit())
        || principal.is_empty()
        || job_id.is_empty()
    {
        return Err("invalid PG readback query identity".into());
    }
    // The one qualified PG readback owns Writer Epoch, lifecycle, terminal
    // events and Reservation coherence. Do not reimplement those checks here.
    let qualified = match store
        .observe_job_readonly(job_id, source_sha256)
        .map_err(|_| "PG writer/currentness readback unavailable".to_string())?
    {
        PgJobReadback::Observed(snapshot) => snapshot,
        PgJobReadback::Inconclusive => {
            return Err("PG lifecycle inconclusive: current Attempt, resolved PG Job retains a pointer, or terminal evidence disagrees".into());
        }
    };

    // A second read-only snapshot is only for the Windows provider's immutable
    // bundle fields, absent from the shared lifecycle projection. Fence both
    // versions and the exact Attempt: a changing Job is UNKNOWN, never a
    // fallback to its highest historical attempt.
    let mut tx = store
        .client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .map_err(|_| "PG provider snapshot unavailable".to_string())?;
    let row = tx
        .query_opt(
            "SELECT j.principal,j.workspace_snapshot_json,a.launch_token_digest, \
             a.bundle_path,a.unit_name,a.bundle_digest \
             FROM jobs j JOIN attempts a ON a.job_id=j.job_id AND a.attempt_id=$2 \
             WHERE j.job_id=$1 AND j.row_version=$3 AND a.row_version=$4 \
               AND j.resolution IS NOT DISTINCT FROM $5::TEXT AND a.state=$6::TEXT \
               AND (($5::TEXT IS NULL AND j.current_attempt_id=a.attempt_id) \
                 OR ($5::TEXT IS NOT NULL AND j.current_attempt_id IS NULL))",
            &[
                &job_id,
                &qualified.attempt_id,
                &qualified.job_row_version,
                &qualified.attempt_row_version,
                &qualified.resolution,
                &qualified.attempt_state,
            ],
        )
        .map_err(|_| "PG provider snapshot lookup failed".to_string())?
        .ok_or_else(|| "PG provider/Attempt identity changed during readback".to_string())?;
    if row.get::<_, String>(0) != principal {
        return Err("PG principal ownership conflict".into());
    }
    let snapshot: Value = serde_json::from_str(&row.get::<_, String>(1))
        .map_err(|_| "PG provider snapshot invalid".to_string())?;
    let provider = &snapshot["executionProvider"];
    if provider["contract"].as_str() != Some("windows_native_launcher_v1") {
        return Err("PG Job is not bound to the Windows native launcher".into());
    }
    let launcher_digest = provider["executableDigest"]
        .as_str()
        .filter(|d| d.len() == 71 && d.starts_with("sha256:"))
        .ok_or_else(|| "PG launcher provider digest invalid".to_string())?;
    let attempt_id = qualified.attempt_id.clone();
    let token: String = row.get(2);
    let bundle: String = row.get(3);
    let name: String = row.get(4);
    let request_digest: String = row
        .get::<_, Option<String>>(5)
        .ok_or_else(|| "PG dispatch has not committed immutable bundle".to_string())?;
    if name != format!("Ordivon.{attempt_id}") {
        return Err("PG attempt does not bind the Windows native Job Object".into());
    }
    let launcher_digest = launcher_digest.to_owned();
    // A previously observed supervisor binding is part of terminal evidence.
    // Fast Jobs may finish before RUNNER_BOUND; do not require a fabricated
    // start. If it exists, preserve its exact original carrier bytes.
    #[cfg(windows)]
    let runner_bound_start_digest = {
        let event = tx
            .query_opt(
                "SELECT origin,reason_code,detail_json,detail_digest FROM job_events \
             WHERE job_id=$1 AND attempt_id=$2 AND event_type='RUNNER_BOUND'",
                &[&job_id, &attempt_id],
            )
            .map_err(|_| "PG native supervisor event unavailable or ambiguous".to_string())?;
        match (qualified.started_at_ms, event) {
            (None, None) => None,
            (Some(_), Some(row)) => {
                let origin: String = row.get(0);
                let reason: String = row.get(1);
                let detail: String = row.get(2);
                let digest: String = row.get(3);
                let value: Value = serde_json::from_str(&detail)
                    .map_err(|_| "PG native supervisor event invalid".to_string())?;
                let start = value["runnerStartDigest"]
                    .as_str()
                    .filter(|v| {
                        v.len() == 71
                            && v.starts_with("sha256:")
                            && v[7..].bytes().all(|b| b.is_ascii_hexdigit())
                    })
                    .ok_or("PG native supervisor start digest invalid")?;
                if origin != "SYSTEM_OBSERVED"
                    || reason != "SUPERVISOR_OWNER_MATCHED"
                    || digest != sha256(detail.as_bytes())
                    || !value["invocationId"]
                        .as_str()
                        .is_some_and(|v| v.starts_with("windows-launcher:"))
                {
                    return Err("PG native supervisor event identity mismatch".into());
                }
                Some(start.to_owned())
            }
            _ => return Err("PG native supervisor timestamp/event mismatch".into()),
        }
    };
    tx.commit()
        .map_err(|_| "PG read-only snapshot commit failed".to_string())?;

    let expected = store_root.join("pg-attempts").join(&attempt_id);
    let root = fs::canonicalize(&expected).map_err(|_| "PG bundle root unavailable".to_string())?;
    if root != fs::canonicalize(&bundle).map_err(|_| "PG bundle unavailable".to_string())? {
        return Err("PG Attempt bundle escapes configured store root".into());
    }
    let bytes = read_raw_bounded(&root.join("request.json"))?;
    if sha256(&bytes) != request_digest {
        return Err("PG immutable request digest mismatch".into());
    }
    let identity = PgWindowsWitnessIdentity {
        job_id: job_id.to_owned(),
        attempt_id,
        launch_token_digest: token,
        request_digest,
        launcher_image_digest: launcher_digest,
    };
    Ok(BoundWindowsPgBundle {
        root,
        identity,
        #[cfg(windows)]
        attempt_row_version: qualified.attempt_row_version,
        #[cfg(windows)]
        resolved: qualified.resolution.is_some(),
        #[cfg(windows)]
        starting_natural: qualified.resolution.is_none()
            && qualified.attempt_state == "starting"
            && qualified.termination_intent == "natural"
            && qualified.desired_state == "run",
        #[cfg(windows)]
        runner_bound_start_digest,
    })
}

#[cfg(windows)]
#[path = "pg_windows_evidence/running.rs"]
mod running;

/// Positive native supervisor binding. The existing RUNNER_BOUND event means
/// observed custody, NOT proof of resumed user instructions or domain success.
#[cfg(windows)]
pub(crate) fn reconcile_admitted_windows_pg_running(
    store: &mut crate::pg_admission::PgAdmissionStore,
    source_sha256: &str,
    principal: &str,
    job_id: &str,
    store_root: &Path,
) -> Result<bool, String> {
    let bound =
        bind_admitted_windows_pg_bundle(store, source_sha256, principal, job_id, store_root)?;
    if !bound.starting_natural {
        return Ok(false);
    }
    let (witness, start_digest) =
        inspect_windows_pg_bundle_with_start(&bound.root, &bound.identity)?;
    let Some(start_digest) = start_digest else {
        return Ok(false);
    };
    let observed_at_ms = crate::universal::now_unix_ms().map_err(|e| e.to_string())? as i64;
    let Some(invocation) = running::observe_owned_target(&bound.identity, &witness) else {
        return Ok(false);
    };
    // The existing CAS arbitrates concurrent cancel/terminal/other observer.
    // Neither a conflict nor an unknown commit permits a new launch.
    let input = crate::pg_admission::PgRunnerBound {
        attempt_id: bound.identity.attempt_id,
        expected_row_version: bound.attempt_row_version,
        expected_bundle_digest: bound.identity.request_digest,
        runner_start_digest: start_digest,
        native_invocation_id: invocation,
        observed_at_ms,
        expected_source_sha256: source_sha256.to_owned(),
    };
    match store.mark_runner_bound_pg(&input) {
        Ok(_) => Ok(true),
        Err(crate::pg_admission::PgAdmissionError::Blocked) => Ok(false),
        Err(e) => Err(format!("Windows native supervisor binding: {e:?}")),
    }
}

/// Native PG service reconciliation entry: authenticated principal and Job only.
/// The original PG writer/epoch and exact current Attempt supply the CAS key.
/// Does not admit, dispatch, respawn, or select a historical Attempt for writing.
/// Repeated observation of an already resolved Job is read-only.
#[cfg(windows)]
pub fn reconcile_admitted_windows_pg_terminal(
    store: &mut crate::pg_admission::PgAdmissionStore,
    source_sha256: &str,
    principal: &str,
    job_id: &str,
    store_root: &Path,
) -> Result<bool, String> {
    let bound =
        bind_admitted_windows_pg_bundle(store, source_sha256, principal, job_id, store_root)?;
    if bound.resolved {
        return Ok(false);
    }
    terminal::reconcile_windows_native_terminal(
        store,
        &bound.root,
        &bound.identity,
        source_sha256,
        bound.attempt_row_version,
        bound.runner_bound_start_digest.as_deref(),
    )
}

/// Read-only native Windows Job Object population, independent of target-writable
/// result.json and the launcher's PID. This is a physical *observation*, not
/// proof of stable terminality: the owning launcher may still spawn children,
/// and a vanished named object is not evidence that the exact Attempt ended.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PgWindowsJobObjectState {
    Populated,
    Empty,
    NotFound,
    Unknown,
}

/// Missing launcher identity never authorizes an OS-level conclusion.
#[cfg(any(windows, test))]
fn eligible_job_object_name(witness: &PgWindowsWitnessObservation) -> Option<&str> {
    if witness.phase == PgWindowsWitnessPhase::NoLauncherWitness
        || witness.launcher_process_id.is_none()
        || witness.launcher_creation_file_time.is_none()
        || !witness.admitted_job_object_name.starts_with("Ordivon.")
        || witness.admitted_job_object_name.len() <= "Ordivon.".len()
    {
        None
    } else {
        Some(&witness.admitted_job_object_name)
    }
}

#[cfg(windows)]
fn query_windows_named_job_object(name: &str) -> PgWindowsJobObjectState {
    use std::os::windows::ffi::OsStrExt;
    use windows_sys::Win32::Foundation::{CloseHandle, GetLastError};
    use windows_sys::Win32::System::JobObjects::OpenJobObjectW;
    // Win32 JOB_OBJECT_QUERY; no terminate, assign or change-config rights.
    const JOB_OBJECT_QUERY: u32 = 0x0004;
    const ERROR_FILE_NOT_FOUND: u32 = 2;
    if name.is_empty() || name.encode_utf16().any(|c| c == 0) {
        return PgWindowsJobObjectState::Unknown;
    }
    let mut wide: Vec<u16> = std::ffi::OsStr::new(name).encode_wide().collect();
    wide.push(0);
    unsafe {
        let handle = OpenJobObjectW(JOB_OBJECT_QUERY, 0, wide.as_ptr());
        if handle.is_null() {
            return if GetLastError() == ERROR_FILE_NOT_FOUND {
                PgWindowsJobObjectState::NotFound
            } else {
                PgWindowsJobObjectState::Unknown
            };
        }
        let result = query_windows_job_object_handle(handle);
        CloseHandle(handle);
        result
    }
}

#[cfg(windows)]
unsafe fn query_windows_job_object_handle(
    handle: windows_sys::Win32::Foundation::HANDLE,
) -> PgWindowsJobObjectState {
    use windows_sys::Win32::System::JobObjects::{
        JobObjectBasicAccountingInformation, QueryInformationJobObject,
        JOBOBJECT_BASIC_ACCOUNTING_INFORMATION,
    };
    let mut accounting = JOBOBJECT_BASIC_ACCOUNTING_INFORMATION::default();
    let mut returned = 0_u32;
    let ok = unsafe {
        QueryInformationJobObject(
            handle,
            JobObjectBasicAccountingInformation,
            (&mut accounting as *mut JOBOBJECT_BASIC_ACCOUNTING_INFORMATION).cast(),
            std::mem::size_of::<JOBOBJECT_BASIC_ACCOUNTING_INFORMATION>() as u32,
            &mut returned,
        )
    };
    if ok == 0 || returned as usize != std::mem::size_of::<JOBOBJECT_BASIC_ACCOUNTING_INFORMATION>()
    {
        PgWindowsJobObjectState::Unknown
    } else if accounting.ActiveProcesses == 0 {
        PgWindowsJobObjectState::Empty
    } else {
        PgWindowsJobObjectState::Populated
    }
}

/// Diagnostics only. Win32 QueryInformationJobObject(NULL) observes the
/// calling process's immediate assigned Job Object when one exists. It is
/// NOT a PG-qualified owner lookup and is never used for terminal CAS.
#[cfg(windows)]
pub fn selftest_windows_pg_enclosing_job_object_state() -> PgWindowsJobObjectState {
    unsafe { query_windows_job_object_handle(std::ptr::null_mut()) }
}

#[cfg(windows)]
pub fn inspect_windows_pg_job_object(
    witness: &PgWindowsWitnessObservation,
) -> PgWindowsJobObjectState {
    let Some(name) = eligible_job_object_name(witness) else {
        return PgWindowsJobObjectState::Unknown;
    };
    query_windows_named_job_object(name)
}

#[cfg(not(windows))]
pub fn inspect_windows_pg_job_object(
    _witness: &PgWindowsWitnessObservation,
) -> PgWindowsJobObjectState {
    PgWindowsJobObjectState::Unknown
}

/// A live kernel-only completion gate for the original Windows Launcher.
/// Preserve the Linux-only formal/unit falsifiers without exporting an unused
/// production native pipe path on the Linux PG host.
#[cfg(any(windows, test))]
pub mod native_terminal_gate {
    #[cfg(windows)]
    use super::{
        PgWindowsJobObjectState, PgWindowsWitnessIdentity, PgWindowsWitnessObservation,
        PgWindowsWitnessPhase,
    };

    /// A pipe identity is allowed to be derived only from an exact Attempt
    /// already qualified by PostgreSQL. Never use caller-supplied arbitrary paths.
    pub(crate) fn pipe_name(attempt: &str) -> Result<String, String> {
        if attempt.is_empty()
            || attempt.len() > 96
            || !attempt
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
        {
            return Err("unsafe Windows PG terminal Attempt identifier".into());
        }
        Ok(format!(r"\\.\pipe\Ordivon.WinPG.Terminal.{attempt}"))
    }

    #[cfg(windows)]
    pub(crate) struct PgWindowsNativeTerminalGate {
        pipe: windows_sys::Win32::Foundation::HANDLE,
        job_id: String,
    }

    #[cfg(windows)]
    impl Drop for PgWindowsNativeTerminalGate {
        fn drop(&mut self) {
            unsafe {
                windows_sys::Win32::Foundation::CloseHandle(self.pipe);
            }
        }
    }

    #[cfg(windows)]
    impl PgWindowsNativeTerminalGate {
        /// Call ONLY after the original PostgreSQL native drain Journal event
        /// COMMIT returned Committed or exact Existing. ACK is not an authorization.
        pub(crate) fn ack_after_pg_durable_drain_commit(
            self,
            outcome: &crate::pg_admission::PgNativeWindowsDrainOutcome,
        ) -> Result<(), String> {
            use windows_sys::Win32::Storage::FileSystem::WriteFile;
            let recorded = match outcome {
                crate::pg_admission::PgNativeWindowsDrainOutcome::Committed(id)
                | crate::pg_admission::PgNativeWindowsDrainOutcome::Existing(id) => id,
            };
            if recorded != &self.job_id {
                return Err("native drain PG journal commit owner mismatch".into());
            }
            let mut written = 0u32;
            let ok = unsafe {
                WriteFile(
                    self.pipe,
                    b"T".as_ptr(),
                    1,
                    &mut written,
                    std::ptr::null_mut(),
                )
            };
            if ok == 0 || written != 1 {
                return Err(format!(
                    "native drain ACK pipe write failed: {}",
                    std::io::Error::last_os_error()
                ));
            }
            Ok(())
        }
    }

    /// Connect only while the ORIGINAL Launcher holds its Job Object handle.
    /// Native pipe server PID/birth and Job accounting are read from Windows
    /// kernel, not a target-authored JSON or hash. The caller must hold the
    /// gate through a durable same-PG native witness event commit, then ACK.
    /// The separate terminal+Artifact CAS requires the original Launcher to exit.
    ///
    /// Missing gate -> None/UNKNOWN, never a synthetic terminal. A wrong
    /// issuer or nonempty job causes an explicit error without ACK.
    #[cfg(windows)]
    pub(crate) fn connect_verified(
        expected: &PgWindowsWitnessIdentity,
        witness: &PgWindowsWitnessObservation,
    ) -> Result<Option<PgWindowsNativeTerminalGate>, String> {
        use windows_sys::Win32::Foundation::{
            CloseHandle, GetLastError, FILETIME, INVALID_HANDLE_VALUE,
        };
        use windows_sys::Win32::Storage::FileSystem::{CreateFileW, OPEN_EXISTING};
        use windows_sys::Win32::System::Pipes::GetNamedPipeServerProcessId;
        use windows_sys::Win32::System::Threading::{
            GetProcessTimes, OpenProcess, PROCESS_QUERY_LIMITED_INFORMATION,
        };

        if witness.phase != PgWindowsWitnessPhase::ResultWitnessPendingOsReconciliation
            || witness.result_digest.is_none()
            || witness.admitted_job_object_name != format!("Ordivon.{}", expected.attempt_id)
        {
            return Ok(None);
        }
        let (Some(pid), Some(birth)) = (
            witness.launcher_process_id,
            witness.launcher_creation_file_time,
        ) else {
            return Ok(None);
        };
        if pid == 0 || pid > u32::MAX as u64 || birth == 0 {
            return Err("unqualified original launcher process identity".into());
        }
        let name = pipe_name(&expected.attempt_id)?;
        let wide: Vec<u16> = name.encode_utf16().chain(Some(0)).collect();
        // Generic read/write for a single bounded ACK, no sharing and no
        // inheritable handle. The server only accepts the original PG parent.
        let handle = unsafe {
            CreateFileW(
                wide.as_ptr(),
                0x8000_0000 | 0x4000_0000,
                0,
                std::ptr::null(),
                OPEN_EXISTING,
                0,
                std::ptr::null_mut(),
            )
        };
        if handle == INVALID_HANDLE_VALUE {
            let code = unsafe { GetLastError() };
            if code == 2 || code == 231 {
                // no server / busy: remain UNKNOWN
                return Ok(None);
            }
            return Err(format!(
                "PG terminal native pipe unavailable (Win32 {code})"
            ));
        }
        let gate = PgWindowsNativeTerminalGate {
            pipe: handle,
            job_id: expected.job_id.clone(),
        };
        let mut native_pid = 0u32;
        if unsafe { GetNamedPipeServerProcessId(handle, &mut native_pid) } == 0
            || native_pid != pid as u32
        {
            return Err("PG terminal native pipe server is not the original Launcher".into());
        }
        const SYNCHRONIZE: u32 = 0x0010_0000;
        let process = unsafe {
            OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE,
                0,
                native_pid,
            )
        };
        if process.is_null() {
            return Err("PG terminal launcher process cannot be authenticated".into());
        }
        let blank = FILETIME {
            dwLowDateTime: 0,
            dwHighDateTime: 0,
        };
        let (mut created, mut exited, mut kernel, mut user) = (blank, blank, blank, blank);
        let verified =
            unsafe { GetProcessTimes(process, &mut created, &mut exited, &mut kernel, &mut user) };
        unsafe {
            CloseHandle(process);
        }
        let kernel_birth = ((created.dwHighDateTime as u64) << 32) | created.dwLowDateTime as u64;
        if verified == 0 || kernel_birth != birth {
            return Err(
                "PG terminal native pipe Launcher birth differs from admitted Attempt".into(),
            );
        }
        if super::inspect_windows_pg_job_object(witness) != PgWindowsJobObjectState::Empty {
            return Err(
                "PG terminal original Job Object lacks positive kernel Empty observation".into(),
            );
        }
        // Two-way issuer confirmation. The original Launcher first checks
        // GetNamedPipeClientProcessId against the admission-frozen parent PID
        // and only then writes 'R'. An arbitrary PG client must not persist
        // a supposed issuer-owned drain event before this issuer confirmation.
        // A rejected/closed pipe is UNKNOWN, never an authorized journal.
        let mut ready = [0u8; 1];
        let mut count = 0u32;
        let accepted = unsafe {
            windows_sys::Win32::Storage::FileSystem::ReadFile(
                gate.pipe,
                ready.as_mut_ptr(),
                1,
                &mut count,
                std::ptr::null_mut(),
            )
        };
        if accepted == 0 || count != 1 || ready[0] != b'R' {
            return Err("PG native drain original Launcher did not confirm client identity".into());
        }
        // Return with the connection HELD. Dropping it without PG CAS does
        // not send ACK; original Launcher times out and closes its Job handle.
        Ok(Some(gate))
    }

    /// The actual Windows PG Runtime owner calls this while the original
    /// Launcher is alive, after inspect_windows_pg_bundle validated the
    /// immutable request+Result. It persists the positive OS observation in
    /// the EXISTING PG Job Journal and releases the Launcher only after
    /// commit. A separate reconciliation after Launcher exit consumes it.
    #[cfg(windows)]
    pub(crate) fn record_verified_native_drain(
        store: &mut crate::pg_admission::PgAdmissionStore,
        source_sha256: &str,
        expected_row_version: i64,
        expected: &PgWindowsWitnessIdentity,
        witness: &PgWindowsWitnessObservation,
    ) -> Result<bool, String> {
        use crate::pg_admission::PgNativeWindowsDrainInput;
        let Some(gate) = connect_verified(expected, witness)? else {
            return Ok(false);
        };
        let event = PgNativeWindowsDrainInput {
            job_id: expected.job_id.clone(),
            attempt_id: expected.attempt_id.clone(),
            expected_row_version,
            expected_source_sha256: source_sha256.to_owned(),
            launch_token_digest: expected.launch_token_digest.clone(),
            request_digest: expected.request_digest.clone(),
            result_digest: witness
                .result_digest
                .clone()
                .ok_or("native drain missing bound Result")?,
            launcher_process_id: u32::try_from(
                witness.launcher_process_id.ok_or("launcher PID absent")?,
            )
            .map_err(|_| "launcher PID out of range")?,
            launcher_creation_file_time: witness
                .launcher_creation_file_time
                .ok_or("launcher birth absent")?,
            observed_at_ms: crate::universal::now_unix_ms().map_err(|e| e.to_string())? as i64,
        };
        let recorded = store
            .record_native_windows_drain(&event)
            .map_err(|e| format!("native Windows drain PG commit: {e:?}"))?;
        gate.ack_after_pg_durable_drain_commit(&recorded)?;
        Ok(true)
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        #[test]
        fn native_terminal_pipe_does_not_allow_aliases_or_device_names() {
            for rejected in [
                "",
                "../attempt",
                "a/b",
                "a\\b",
                "a.b",
                "a b",
                "a\0b",
                "a:b",
                "🔒",
                &"x".repeat(97),
            ] {
                assert!(pipe_name(rejected).is_err(), "{rejected:?}");
            }
            assert_eq!(
                pipe_name("attempt-01a1").unwrap(),
                r"\\.\pipe\Ordivon.WinPG.Terminal.attempt-01a1"
            );
        }
    }
}

/// One bounded native diagnostic: create a unique empty Win32 Job Object,
/// observe it using the identical read-only production query and close the
/// handle. Never starts a child, changes service ACL or touches PostgreSQL.
#[cfg(windows)]
pub fn selftest_windows_pg_job_object_query() -> bool {
    use std::os::windows::ffi::OsStrExt;
    use windows_sys::Win32::Foundation::{CloseHandle, GetLastError};
    use windows_sys::Win32::System::JobObjects::CreateJobObjectW;
    let name = format!(
        "Ordivon.WinPgProbe.{}.{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_nanos())
            .unwrap_or(0)
    );
    let mut wide: Vec<u16> = std::ffi::OsStr::new(&name).encode_wide().collect();
    wide.push(0);
    unsafe {
        let handle = CreateJobObjectW(std::ptr::null(), wide.as_ptr());
        if handle.is_null() {
            return false;
        }
        // Do not accept a preexisting named Job even if the unlikely name collides.
        let fresh = GetLastError() != 183; // ERROR_ALREADY_EXISTS
        let empty = query_windows_named_job_object(&name) == PgWindowsJobObjectState::Empty;
        CloseHandle(handle);
        fresh && empty && query_windows_named_job_object(&name) == PgWindowsJobObjectState::NotFound
    }
}

/// Native OS observation must be independent of the target-writable bundle.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PgWindowsOwnerState {
    /// The launcher PID and exact Windows creation FILETIME are still alive.
    Alive,
    /// An exact matching launcher handle is signalled; not a PG terminal.
    Exited,
    /// PID not currently allocated. This does not prove that launch never happened.
    PidAbsent,
    /// PID was recycled, or observed process creation identity differs.
    IdentityConflict,
    /// Windows ownership unavailable/inaccessible, including non-Windows host.
    Unknown,
}

/// Predicate pure enough to falsify on all hosts before using Windows API calls.
#[cfg(any(windows, test))]
fn same_win32_owner(
    expected_pid: u64,
    expected_birth: u64,
    observed_pid: u64,
    observed_birth: u64,
) -> bool {
    expected_pid > 0
        && expected_pid <= u32::MAX as u64
        && expected_birth > 0
        && expected_pid == observed_pid
        && expected_birth == observed_birth
}

#[cfg(windows)]
pub fn inspect_windows_pg_os_owner(witness: &PgWindowsWitnessObservation) -> PgWindowsOwnerState {
    use windows_sys::Win32::Foundation::{CloseHandle, GetLastError, FILETIME};
    use windows_sys::Win32::System::Threading::{
        GetProcessTimes, OpenProcess, WaitForSingleObject, PROCESS_QUERY_LIMITED_INFORMATION,
    };
    // Standard Win32 process access right (not exposed by Threading module).
    const SYNCHRONIZE: u32 = 0x0010_0000;
    const ERROR_INVALID_PARAMETER: u32 = 87;
    const WAIT_OBJECT_0: u32 = 0;
    const WAIT_TIMEOUT: u32 = 258;
    let (Some(pid), Some(birth)) = (
        witness.launcher_process_id,
        witness.launcher_creation_file_time,
    ) else {
        return PgWindowsOwnerState::Unknown;
    };
    if pid == 0 || pid > u32::MAX as u64 || birth == 0 {
        return PgWindowsOwnerState::Unknown;
    }
    // Query only. Never open PROCESS_TERMINATE or broaden token privilege.
    unsafe {
        let handle = OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE,
            0,
            pid as u32,
        );
        if handle.is_null() {
            return if GetLastError() == ERROR_INVALID_PARAMETER {
                PgWindowsOwnerState::PidAbsent
            } else {
                PgWindowsOwnerState::Unknown
            };
        }
        let blank = FILETIME {
            dwLowDateTime: 0,
            dwHighDateTime: 0,
        };
        let (mut creation, mut exit, mut kernel, mut user) = (blank, blank, blank, blank);
        let ok = GetProcessTimes(handle, &mut creation, &mut exit, &mut kernel, &mut user);
        let state = if ok == 0 {
            PgWindowsOwnerState::Unknown
        } else {
            let actual = ((creation.dwHighDateTime as u64) << 32) | creation.dwLowDateTime as u64;
            if !same_win32_owner(pid, birth, pid, actual) {
                PgWindowsOwnerState::IdentityConflict
            } else {
                match WaitForSingleObject(handle, 0) {
                    WAIT_OBJECT_0 => PgWindowsOwnerState::Exited,
                    WAIT_TIMEOUT => PgWindowsOwnerState::Alive,
                    _ => PgWindowsOwnerState::Unknown,
                }
            }
        };
        CloseHandle(handle);
        state
    }
}

#[cfg(not(windows))]
pub fn inspect_windows_pg_os_owner(_witness: &PgWindowsWitnessObservation) -> PgWindowsOwnerState {
    PgWindowsOwnerState::Unknown
}

#[cfg(test)]
mod owner_identity_tests {
    use super::*;
    #[test]
    fn job_object_lookup_requires_bound_launcher_evidence() {
        let mut x = PgWindowsWitnessObservation {
            phase: PgWindowsWitnessPhase::NoLauncherWitness,
            admitted_job_object_name: "Ordivon.attempt-probe".into(),
            launcher_process_id: None,
            launcher_creation_file_time: None,
            target_process_id: None,
            target_creation_file_time: None,
            result_digest: None,
            terminal_proven: false,
        };
        assert_eq!(eligible_job_object_name(&x), None);
        assert_eq!(x.admitted_job_object_name, "Ordivon.attempt-probe");
        x.phase = PgWindowsWitnessPhase::LauncherWitness;
        assert_eq!(eligible_job_object_name(&x), None);
        x.launcher_process_id = Some(19);
        x.launcher_creation_file_time = Some(11);
        assert_eq!(
            eligible_job_object_name(&x),
            Some(x.admitted_job_object_name.as_str())
        );
    }

    #[test]
    fn pid_reuse_cannot_transfer_ownership() {
        assert!(same_win32_owner(45, 10, 45, 10));
        assert!(!same_win32_owner(45, 10, 45, 11));
        assert!(!same_win32_owner(45, 10, 46, 10));
        assert!(!same_win32_owner(0, 10, 0, 10));
        assert!(!same_win32_owner(45, 0, 45, 0));
        assert!(!same_win32_owner(
            u32::MAX as u64 + 1,
            10,
            u32::MAX as u64 + 1,
            10
        ));
    }
}

#[cfg(test)]
mod qualified_pg18_preflight_tests {
    use super::*;
    use crate::pg_admission::{
        pg_writer_epoch_digest, PgAdmissionInput, PgAdmissionStore, PgBundleReady,
    };
    use postgres::{Client, NoTls};
    use uuid::Uuid;

    // Test-only isolated schema on an explicitly supplied disposable PG18.
    // The production database and Windows service are never modified.
    struct Scratch {
        admin: Client,
        schema: String,
    }

    impl Scratch {
        fn new(dsn: &str, source: &str) -> Self {
            let schema = format!("test_win_preflight_{}", Uuid::now_v7().simple());
            let mut admin = Client::connect(dsn, NoTls).expect("test PG18 connection");
            admin
                .batch_execute(&format!("CREATE SCHEMA \"{schema}\""))
                .expect("create isolated PG schema");
            admin
                .query_one(
                    "SELECT set_config('search_path',$1,false)",
                    &[&format!("\"{schema}\"")],
                )
                .expect("scope isolated PG schema");
            admin
                .batch_execute(include_str!("../sql/pg_fresh_epoch.sql"))
                .expect("native PG constraints");
            admin
                .execute(
                    "INSERT INTO _stage_control VALUES('source','QUALIFIED_WRITER',$1,true)",
                    &[&source],
                )
                .expect("qualify fixture source");
            let identity = admin
                .query_one(
                    "SELECT (SELECT system_identifier::text FROM pg_control_system()), \
                            (SELECT timeline_id FROM pg_control_checkpoint())",
                    &[],
                )
                .expect("read physical PostgreSQL epoch");
            let seal = pg_writer_epoch_digest(
                source,
                &identity.get::<_, String>(0),
                identity.get::<_, i32>(1),
            );
            admin
                .execute(
                    "INSERT INTO _stage_control VALUES('epoch','QUALIFIED_EPOCH',$1,true)",
                    &[&seal],
                )
                .expect("qualify native epoch");
            Self { admin, schema }
        }
    }

    impl Drop for Scratch {
        fn drop(&mut self) {
            let _ = self.admin.batch_execute(&format!(
                "SET search_path TO public; DROP SCHEMA IF EXISTS \"{}\" CASCADE",
                self.schema
            ));
        }
    }

    #[test]
    #[ignore = "requires explicit ORDIVON_PG_TEST_DSN disposable PostgreSQL18"]
    fn preflight_uses_pg_writer_epoch_and_rejects_incoherent_attempt_and_terminal() {
        let dsn = std::env::var("ORDIVON_PG_TEST_DSN").expect("disposable PG18 DSN");
        let source = "a".repeat(64);
        let mut scratch = Scratch::new(&dsn, &source);
        let temp = tempfile::tempdir().expect("isolated bundle directory");
        let attempt = "attempt-win-pg-readback";
        let job = "job-win-pg-readback";
        let bundle = temp.path().join("pg-attempts").join(attempt);
        fs::create_dir_all(&bundle).unwrap();
        let request = b"immutable-typed-windows-native-request";
        fs::write(bundle.join("request.json"), request).unwrap();
        let request_digest = sha256(request);
        let input = PgAdmissionInput {
            job_id: job.into(),
            attempt_id: attempt.into(),
            reservation_id: "reservation-win-readback".into(),
            principal: "c-physical-pg-test".into(),
            client_request_id: "c-physical-preflight".into(),
            request_digest: format!("sha256:{}", "b".repeat(64)),
            operation_digest: format!("sha256:{}", "d".repeat(64)),
            workspace_id: "ws-c-physical".into(),
            workspace_snapshot_json: serde_json::json!({
                "executionProvider": {
                    "contract": "windows_native_launcher_v1",
                    "executableDigest": format!("sha256:{}", "c".repeat(64))
                }
            })
            .to_string(),
            execution_plan_json: "{}".into(),
            execution_plan_digest: format!("sha256:{}", "e".repeat(64)),
            launch_token_digest: format!("sha256:{}", "f".repeat(64)),
            bundle_path: bundle.to_string_lossy().into_owned(),
            unit_name: format!("Ordivon.{attempt}"),
            global_limit: 2,
            created_at_ms: 1234567,
            expected_source_sha256: source.clone(),
        };
        let mut writer = PgAdmissionStore::connect(&dsn, &scratch.schema).unwrap();
        writer.admit(&input).expect("admit scratch PG Job");
        scratch.admin.execute(
            "INSERT INTO job_allocations(attempt_id,resources_json,workspace_access_json,owner,state,acquired_at_ms) VALUES($1,'{}','{}',$2,'active',$3)",
            &[&input.attempt_id,&input.principal,&input.created_at_ms],
        ).unwrap();
        let row = writer
            .client
            .query_one(
                "SELECT row_version FROM attempts WHERE attempt_id=$1",
                &[&input.attempt_id],
            )
            .unwrap();
        writer
            .commit_bundle_ready_pg(&PgBundleReady {
                attempt_id: input.attempt_id.clone(),
                expected_row_version: row.get(0),
                bundle_digest: request_digest,
                observed_at_ms: input.created_at_ms + 1,
                expected_source_sha256: source.clone(),
            })
            .expect("commit native immutable bundle");

        let inspect = || {
            inspect_admitted_windows_pg_bundle(
                &dsn,
                &scratch.schema,
                &source,
                &input.principal,
                &input.job_id,
                temp.path(),
            )
        };
        assert_eq!(
            inspect().unwrap().phase,
            PgWindowsWitnessPhase::NoLauncherWitness
        );
        // Source qualification alone survives a simulated restored/stale epoch.
        // No actual WAL promotion is performed in this disposable test.
        scratch
            .admin
            .execute(
                "UPDATE _stage_control SET source_sha256='stale-epoch' WHERE id='epoch'",
                &[],
            )
            .unwrap();
        assert!(inspect().unwrap_err().contains("writer/currentness"));
        let physical = scratch
            .admin
            .query_one(
                "SELECT (SELECT system_identifier::text FROM pg_control_system()), \
                    (SELECT timeline_id FROM pg_control_checkpoint())",
                &[],
            )
            .unwrap();
        let correct_epoch = pg_writer_epoch_digest(
            &source,
            &physical.get::<_, String>(0),
            physical.get::<_, i32>(1),
        );
        scratch
            .admin
            .execute(
                "UPDATE _stage_control SET source_sha256=$1 WHERE id='epoch'",
                &[&correct_epoch],
            )
            .unwrap();
        assert_eq!(
            inspect().unwrap().phase,
            PgWindowsWitnessPhase::NoLauncherWitness
        );

        // The old local preflight would have accepted this latest Attempt bundle.
        // The canonical lifecycle readback must not.
        scratch.admin.execute(
            "UPDATE attempts SET state='succeeded',row_version=row_version+1 WHERE attempt_id=$1",
            &[&input.attempt_id],
        ).unwrap();
        assert!(inspect().unwrap_err().contains("lifecycle inconclusive"));
        scratch.admin.execute(
            "UPDATE attempts SET state='accepted',row_version=row_version+1 WHERE attempt_id=$1",
            &[&input.attempt_id],
        ).unwrap();
        assert_eq!(
            inspect().unwrap().phase,
            PgWindowsWitnessPhase::NoLauncherWitness
        );
        // A terminal resolution without native terminal events and released
        // reservation is not a qualified Windows result, even with no current ID.
        scratch.admin.execute(
            "UPDATE jobs SET resolution='succeeded',current_attempt_id=NULL,row_version=row_version+1 WHERE job_id=$1",
            &[&input.job_id],
        ).unwrap();
        assert!(inspect().unwrap_err().contains("lifecycle inconclusive"));
    }
}
