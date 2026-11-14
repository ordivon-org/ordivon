//! Read-only Windows-native evidence check for the PostgreSQL Runtime.
//! Phase is an observation, not a terminal or proof that a Job Object is dead.
//! The authoritative effect transition remains PG CAS + OS process ownership.
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{fs, path::Path};

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
        return Ok(output);
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
    let Some((start, _)) = target else {
        if result.is_some() {
            return Err("result without bound target-start identity".into());
        }
        return Ok(output);
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
        return Ok(output);
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
    Ok(output)
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
    use crate::pg_admission::PgAdmissionStore;
    use postgres::IsolationLevel;
    if source_sha256.len() != 64
        || !source_sha256.bytes().all(|v| v.is_ascii_hexdigit())
        || principal.is_empty()
        || job_id.is_empty()
    {
        return Err("invalid PG readback query identity".into());
    }
    let mut store = PgAdmissionStore::connect(dsn, schema)
        .map_err(|_| "PG schema unavailable or invalid".to_string())?;
    let mut tx = store
        .client
        .build_transaction()
        .isolation_level(IsolationLevel::RepeatableRead)
        .read_only(true)
        .start()
        .map_err(|_| "PG read-only snapshot failed".to_string())?;
    let source = tx
        .query_opt(
            "SELECT state,source_sha256,promotion_allowed FROM _stage_control WHERE id='source'",
            &[],
        )
        .map_err(|_| "PG source gate unavailable".to_string())?;
    let source_ok = source.is_some_and(|row| {
        row.get::<_, String>(0) == "QUALIFIED_WRITER"
            && row.get::<_, String>(1) == source_sha256
            && row.get::<_, bool>(2)
    });
    if !source_ok {
        return Err("PG source is not qualified".into());
    }
    let row = tx
        .query_opt(
            "SELECT j.principal,j.workspace_snapshot_json,a.attempt_id,a.launch_token_digest, \
            a.bundle_path,a.unit_name,a.bundle_digest,j.resolution,j.current_attempt_id \
            FROM jobs j JOIN attempts a ON a.job_id=j.job_id \
            WHERE j.job_id=$1 ORDER BY a.attempt_number DESC LIMIT 1",
            &[&job_id],
        )
        .map_err(|_| "PG Job lookup failed".to_string())?
        .ok_or_else(|| "unknown PG Job".to_string())?;
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
    let attempt_id: String = row.get(2);
    // A historical terminal may read back the latest Attempt after the current
    // pointer has been cleared. An *unresolved* Job must never borrow the
    // latest available bundle unless PG still designates that exact Attempt.
    // The read-only preflight cannot infer this from attempt_number alone.
    let resolution: Option<String> = row.get(7);
    let current_attempt: Option<String> = row.get(8);
    if resolution.is_none() && current_attempt.as_deref() != Some(&attempt_id) {
        return Err("unresolved PG Job has no matching current Attempt".into());
    }
    if resolution.is_some() && current_attempt.is_some() {
        return Err("resolved PG Job retains an unexpected current Attempt".into());
    }
    let token: String = row.get(3);
    let bundle: String = row.get(4);
    let name: String = row.get(5);
    let request_digest: String = row
        .get::<_, Option<String>>(6)
        .ok_or_else(|| "PG dispatch has not committed immutable bundle".to_string())?;
    if name != format!("Ordivon.{attempt_id}") {
        return Err("PG attempt does not bind the Windows native Job Object".into());
    }
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
        launcher_image_digest: launcher_digest.to_owned(),
    };
    inspect_windows_pg_bundle(&root, &identity)
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
