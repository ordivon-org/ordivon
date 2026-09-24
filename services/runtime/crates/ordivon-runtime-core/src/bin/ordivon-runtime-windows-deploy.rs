#![cfg_attr(not(windows), allow(dead_code, unused_imports))]

#[cfg(windows)]
use ordivon_runtime_core::windows_current_token_is_local_system;
use ordivon_runtime_core::{
    inspect_registry, inspect_runtime, inspect_runtime_release_effect, AttemptState,
    ReservationState, RuntimeDoctorConfig, RuntimeDoctorReport, RuntimeInspectionConfig,
    RuntimeOperatorRegistryInspection,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
#[cfg(windows)]
use std::ffi::OsStr;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

const MANIFEST_SCHEMA_VERSION: u32 = 2;
const RECEIPT_SCHEMA_VERSION: u32 = 1;
// Match the mature Core file-digest helper. Keep Windows main-thread stack usage bounded.
const SHA256_BUFFER_BYTES: usize = 64 * 1024;
const REQUIRED_ARTIFACTS: [&str; 6] = [
    "ordivon-runtime.exe",
    "ordivon-windows-job-launcher.exe",
    "ordivon-windows-privileged-broker.exe",
    "ordivon-runtime-doctor.exe",
    "ordivon-runtime-inspect.exe",
    "ordivon-runtime-windows-deploy.exe",
];
const BOOTSTRAP_RECOVERY_ATTEMPT_ENV: &str = "ORDIVON_RELEASE_BOOTSTRAP_RECOVERY_ATTEMPT_ID";
const BOOTSTRAP_LAUNCHER_START_FILE: &str = "windows-launcher-start.json";

#[derive(Debug)]
struct Args {
    command: String,
    source_repo: PathBuf,
    commit: String,
    confirm_commit: String,
    candidate_dir: PathBuf,
    candidate_manifest: PathBuf,
    install_dir: PathBuf,
    database: PathBuf,
    env_file: PathBuf,
    receipt_root: PathBuf,
    service: String,
    broker_service: String,
    workspace_id: String,
    expected_tool_count: u32,
    require_ref: String,
    effect_id: String,
    effect_request_digest: String,
    candidate_manifest_digest: String,
    drain_seconds: u64,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct CandidateManifest {
    schema_version: u32,
    platform: String,
    commit: String,
    source_repo: String,
    #[serde(default)]
    source_owner_prefix: Option<String>,
    source_materialization: String,
    candidate_dir: String,
    required_ref: String,
    required_ref_commit: String,
    max_migration_version: i64,
    compiled_tool_count: u32,
    compiled_base_tool_catalog_digest: String,
    artifacts: Vec<ManifestArtifact>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ManifestArtifact {
    name: String,
    kind: String,
    digest: String,
    bytes: u64,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
struct CompiledSelfCheck {
    schema_version: u32,
    status: String,
    catalog_scope: String,
    compiled_tool_count: u32,
    compiled_base_tool_catalog_digest: String,
    max_migration_version: i64,
}

#[derive(Debug)]
struct CandidateProof {
    manifest_digest: String,
    manifest: CandidateManifest,
    self_check: CompiledSelfCheck,
    artifacts: BTreeMap<String, PathBuf>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct PlanReceipt {
    schema_version: u32,
    status: &'static str,
    commit: String,
    effect_id: String,
    candidate_manifest_digest: String,
    pre_migration_version: i64,
    candidate_max_migration_version: i64,
    compiled_tool_count: u32,
    compiled_base_tool_catalog_digest: String,
    release_dir: String,
    owner_job_id: String,
    active_job_ids: Vec<String>,
    blockers: Vec<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    bootstrap_recovery: Option<BootstrapRecoveryProof>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct EffectIdentity<'a> {
    contract: &'static str,
    effect_id: &'a str,
    request_digest: &'a str,
    commit: &'a str,
    candidate_manifest_digest: &'a str,
    expected_tool_count: u32,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct EffectRequestReceipt<'a> {
    contract: &'static str,
    effect_id: &'a str,
    request_digest: &'a str,
    commit: &'a str,
    candidate_manifest_digest: &'a str,
    expected_tool_count: u32,
    workspace_id: &'a str,
    platform: &'static str,
}

#[derive(Debug, Clone)]
struct EnvSnapshot {
    bytes: Vec<u8>,
    values: BTreeMap<String, String>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
struct BootstrapRecoveryProof {
    attempt_id: String,
    job_id: String,
    supervisor_launcher_process_id: u32,
    supervisor_launcher_process_creation_time_file_time: u64,
    start_evidence_digest: String,
    runner_result_digest: String,
    control_result_digest: String,
    owner_observed_absent: bool,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ProcessOwnerProbe {
    schema_version: u32,
    process_id: u32,
    process_alive: bool,
    #[serde(default)]
    process_creation_time_file_time: Option<u64>,
}

#[cfg(windows)]
mod scm {
    use super::*;
    use std::mem::size_of;
    use std::os::windows::ffi::OsStrExt;
    use std::ptr::{null, null_mut};
    use windows_sys::Win32::Foundation::{
        GetLastError, LocalFree, ERROR_INSUFFICIENT_BUFFER, ERROR_SERVICE_ALREADY_RUNNING,
        ERROR_SERVICE_NOT_ACTIVE,
    };
    use windows_sys::Win32::Security::Authorization::ConvertSidToStringSidW;
    use windows_sys::Win32::Security::{LookupAccountNameW, SID_NAME_USE};
    use windows_sys::Win32::System::Services::{
        ChangeServiceConfigW, CloseServiceHandle, ControlService, OpenSCManagerW, OpenServiceW,
        QueryServiceConfigW, QueryServiceStatusEx, StartServiceW, QUERY_SERVICE_CONFIGW, SC_HANDLE,
        SC_MANAGER_CONNECT, SC_STATUS_PROCESS_INFO, SERVICE_CHANGE_CONFIG, SERVICE_CONTROL_STOP,
        SERVICE_NO_CHANGE, SERVICE_QUERY_CONFIG, SERVICE_QUERY_STATUS, SERVICE_RUNNING,
        SERVICE_START, SERVICE_STATUS, SERVICE_STATUS_PROCESS, SERVICE_STOP, SERVICE_STOPPED,
    };

    pub struct Handle(SC_HANDLE);
    impl Drop for Handle {
        fn drop(&mut self) {
            if !self.0.is_null() {
                unsafe {
                    let _ = CloseServiceHandle(self.0);
                }
            }
        }
    }

    #[derive(Clone, Debug)]
    pub struct ServiceSnapshot {
        pub binary_path: String,
        pub state: u32,
        pub process_id: u32,
    }

    fn wide(value: &OsStr) -> Vec<u16> {
        value.encode_wide().chain(std::iter::once(0)).collect()
    }

    unsafe fn wide_ptr_to_string(ptr: *const u16) -> Result<String, String> {
        if ptr.is_null() {
            return Ok(String::new());
        }
        let mut len = 0usize;
        while *ptr.add(len) != 0 {
            len += 1;
            if len > 32768 {
                return Err("SCM returned an unbounded UTF-16 string".to_string());
            }
        }
        String::from_utf16(std::slice::from_raw_parts(ptr, len))
            .map_err(|_| "SCM returned invalid UTF-16".to_string())
    }

    fn manager() -> Result<Handle, String> {
        let raw = unsafe { OpenSCManagerW(null(), null(), SC_MANAGER_CONNECT) };
        if raw.is_null() {
            return Err(format!(
                "OpenSCManagerW failed with Win32 error {}",
                unsafe { GetLastError() }
            ));
        }
        Ok(Handle(raw))
    }

    fn service(name: &str, access: u32) -> Result<Handle, String> {
        let manager = manager()?;
        let name = wide(OsStr::new(name));
        let raw = unsafe { OpenServiceW(manager.0, name.as_ptr(), access) };
        if raw.is_null() {
            return Err(format!("OpenServiceW failed with Win32 error {}", unsafe {
                GetLastError()
            }));
        }
        Ok(Handle(raw))
    }

    pub fn query_status(name: &str) -> Result<SERVICE_STATUS_PROCESS, String> {
        let handle = service(name, SERVICE_QUERY_STATUS)?;
        let mut status = SERVICE_STATUS_PROCESS::default();
        let mut needed = 0u32;
        let ok = unsafe {
            QueryServiceStatusEx(
                handle.0,
                SC_STATUS_PROCESS_INFO,
                (&mut status as *mut SERVICE_STATUS_PROCESS).cast(),
                size_of::<SERVICE_STATUS_PROCESS>() as u32,
                &mut needed,
            )
        };
        if ok == 0 {
            return Err(format!(
                "QueryServiceStatusEx failed with Win32 error {}",
                unsafe { GetLastError() }
            ));
        }
        Ok(status)
    }

    pub fn snapshot(name: &str) -> Result<ServiceSnapshot, String> {
        let handle = service(name, SERVICE_QUERY_CONFIG | SERVICE_QUERY_STATUS)?;
        let mut needed = 0u32;
        unsafe {
            let _ = QueryServiceConfigW(handle.0, null_mut(), 0, &mut needed);
        }
        if needed == 0 {
            return Err(format!(
                "QueryServiceConfigW size probe failed with Win32 error {}",
                unsafe { GetLastError() }
            ));
        }
        let words = (needed as usize).div_ceil(size_of::<usize>());
        let mut buffer = vec![0usize; words];
        let config = buffer.as_mut_ptr().cast::<QUERY_SERVICE_CONFIGW>();
        let ok = unsafe { QueryServiceConfigW(handle.0, config, needed, &mut needed) };
        if ok == 0 {
            return Err(format!(
                "QueryServiceConfigW failed with Win32 error {}",
                unsafe { GetLastError() }
            ));
        }
        let binary_path = unsafe { wide_ptr_to_string((*config).lpBinaryPathName) }?;

        let mut status = SERVICE_STATUS_PROCESS::default();
        let mut status_needed = 0u32;
        let ok = unsafe {
            QueryServiceStatusEx(
                handle.0,
                SC_STATUS_PROCESS_INFO,
                (&mut status as *mut SERVICE_STATUS_PROCESS).cast(),
                size_of::<SERVICE_STATUS_PROCESS>() as u32,
                &mut status_needed,
            )
        };
        if ok == 0 {
            return Err(format!(
                "QueryServiceStatusEx failed with Win32 error {}",
                unsafe { GetLastError() }
            ));
        }
        Ok(ServiceSnapshot {
            binary_path,
            state: status.dwCurrentState,
            process_id: status.dwProcessId,
        })
    }

    pub fn set_binary_path(name: &str, binary_path: &str) -> Result<(), String> {
        let handle = service(name, SERVICE_CHANGE_CONFIG)?;
        let path = wide(OsStr::new(binary_path));
        let ok = unsafe {
            ChangeServiceConfigW(
                handle.0,
                SERVICE_NO_CHANGE,
                SERVICE_NO_CHANGE,
                SERVICE_NO_CHANGE,
                path.as_ptr(),
                null(),
                null_mut(),
                null(),
                null(),
                null(),
                null(),
            )
        };
        if ok == 0 {
            return Err(format!(
                "ChangeServiceConfigW failed with Win32 error {}",
                unsafe { GetLastError() }
            ));
        }
        Ok(())
    }

    pub fn stop(name: &str, wait: Duration) -> Result<(), String> {
        let handle = service(name, SERVICE_STOP | SERVICE_QUERY_STATUS)?;
        let mut status = SERVICE_STATUS::default();
        let current = query_status(name)?;
        if current.dwCurrentState == SERVICE_STOPPED {
            return Ok(());
        }
        let ok = unsafe { ControlService(handle.0, SERVICE_CONTROL_STOP, &mut status) };
        if ok == 0 {
            let error = unsafe { GetLastError() };
            if error != ERROR_SERVICE_NOT_ACTIVE {
                return Err(format!(
                    "ControlService(STOP) failed with Win32 error {error}"
                ));
            }
        }
        wait_for_state(name, SERVICE_STOPPED, wait)
    }

    pub fn start(name: &str, wait: Duration) -> Result<(), String> {
        let handle = service(name, SERVICE_START | SERVICE_QUERY_STATUS)?;
        if query_status(name)?.dwCurrentState == SERVICE_RUNNING {
            return Ok(());
        }
        let ok = unsafe { StartServiceW(handle.0, 0, null()) };
        if ok == 0 {
            let error = unsafe { GetLastError() };
            if error != ERROR_SERVICE_ALREADY_RUNNING {
                return Err(format!("StartServiceW failed with Win32 error {error}"));
            }
        }
        wait_for_state(name, SERVICE_RUNNING, wait)
    }

    pub fn wait_for_state(name: &str, expected: u32, wait: Duration) -> Result<(), String> {
        let deadline = Instant::now() + wait;
        loop {
            let status = query_status(name)?;
            if status.dwCurrentState == expected {
                return Ok(());
            }
            if Instant::now() >= deadline {
                return Err(format!(
                    "service {name} did not reach state {expected}; last state={} pid={}",
                    status.dwCurrentState, status.dwProcessId
                ));
            }
            thread::sleep(Duration::from_millis(200));
        }
    }

    pub fn account_sid_string(account_name: &str) -> Result<String, String> {
        let account = wide(OsStr::new(account_name));
        let mut sid_bytes = 0u32;
        let mut domain_chars = 0u32;
        let mut use_kind = 0 as SID_NAME_USE;
        unsafe {
            let _ = LookupAccountNameW(
                null(),
                account.as_ptr(),
                null_mut(),
                &mut sid_bytes,
                null_mut(),
                &mut domain_chars,
                &mut use_kind,
            );
        }
        let error = unsafe { GetLastError() };
        if error != ERROR_INSUFFICIENT_BUFFER || sid_bytes == 0 {
            return Err(format!(
                "LookupAccountNameW size probe failed with Win32 error {error}"
            ));
        }
        let mut sid = vec![0u8; sid_bytes as usize];
        let mut domain = vec![0u16; domain_chars.max(1) as usize];
        let ok = unsafe {
            LookupAccountNameW(
                null(),
                account.as_ptr(),
                sid.as_mut_ptr().cast(),
                &mut sid_bytes,
                domain.as_mut_ptr(),
                &mut domain_chars,
                &mut use_kind,
            )
        };
        if ok == 0 {
            return Err(format!(
                "LookupAccountNameW failed with Win32 error {}",
                unsafe { GetLastError() }
            ));
        }
        let mut string_sid = null_mut();
        let ok = unsafe { ConvertSidToStringSidW(sid.as_mut_ptr().cast(), &mut string_sid) };
        if ok == 0 {
            return Err(format!(
                "ConvertSidToStringSidW failed with Win32 error {}",
                unsafe { GetLastError() }
            ));
        }
        let text = unsafe { wide_ptr_to_string(string_sid) };
        unsafe {
            let _ = LocalFree(string_sid.cast());
        }
        text
    }
}

fn usage() -> String {
    "usage: ordivon-runtime-windows-deploy <plan|apply> --source-repo PATH --commit SHA40 --confirm-commit SHA40 --candidate-dir PATH --candidate-manifest PATH --install-dir PATH --database PATH --env-file PATH --receipt-root PATH --service NAME --broker-service NAME --workspace-id ID --expected-tool-count N --require-ref REF --effect-id HEX64 --effect-request-digest sha256:HEX64 --candidate-manifest-digest sha256:HEX64 --drain-seconds N".to_string()
}

fn require_value<I: Iterator<Item = String>>(args: &mut I, flag: &str) -> Result<String, String> {
    args.next()
        .ok_or_else(|| format!("{flag} requires a value"))
}

fn parse_args() -> Result<Args, String> {
    let mut raw = std::env::args().skip(1);
    let command = raw.next().ok_or_else(usage)?;
    if command != "plan" && command != "apply" {
        return Err(usage());
    }
    let mut values = BTreeMap::<String, String>::new();
    while let Some(flag) = raw.next() {
        if !flag.starts_with("--") {
            return Err(format!("unexpected argument: {flag}\n{}", usage()));
        }
        if values.contains_key(&flag) {
            return Err(format!("duplicate argument: {flag}"));
        }
        let value = require_value(&mut raw, &flag)?;
        values.insert(flag, value);
    }
    let take = |name: &str, map: &BTreeMap<String, String>| {
        map.get(name)
            .cloned()
            .ok_or_else(|| format!("missing required argument: {name}"))
    };
    let result = Args {
        command,
        source_repo: PathBuf::from(take("--source-repo", &values)?),
        commit: take("--commit", &values)?,
        confirm_commit: take("--confirm-commit", &values)?,
        candidate_dir: PathBuf::from(take("--candidate-dir", &values)?),
        candidate_manifest: PathBuf::from(take("--candidate-manifest", &values)?),
        install_dir: PathBuf::from(take("--install-dir", &values)?),
        database: PathBuf::from(take("--database", &values)?),
        env_file: PathBuf::from(take("--env-file", &values)?),
        receipt_root: PathBuf::from(take("--receipt-root", &values)?),
        service: take("--service", &values)?,
        broker_service: take("--broker-service", &values)?,
        workspace_id: take("--workspace-id", &values)?,
        expected_tool_count: take("--expected-tool-count", &values)?
            .parse()
            .map_err(|_| "--expected-tool-count must be an integer".to_string())?,
        require_ref: take("--require-ref", &values)?,
        effect_id: take("--effect-id", &values)?,
        effect_request_digest: take("--effect-request-digest", &values)?,
        candidate_manifest_digest: take("--candidate-manifest-digest", &values)?,
        drain_seconds: take("--drain-seconds", &values)?
            .parse()
            .map_err(|_| "--drain-seconds must be an integer".to_string())?,
    };
    let known: BTreeSet<&str> = [
        "--source-repo",
        "--commit",
        "--confirm-commit",
        "--candidate-dir",
        "--candidate-manifest",
        "--install-dir",
        "--database",
        "--env-file",
        "--receipt-root",
        "--service",
        "--broker-service",
        "--workspace-id",
        "--expected-tool-count",
        "--require-ref",
        "--effect-id",
        "--effect-request-digest",
        "--candidate-manifest-digest",
        "--drain-seconds",
    ]
    .into_iter()
    .collect();
    let unknown = values
        .keys()
        .filter(|key| !known.contains(key.as_str()))
        .cloned()
        .collect::<Vec<_>>();
    if !unknown.is_empty() {
        return Err(format!("unknown arguments: {}", unknown.join(", ")));
    }
    validate_args(&result)?;
    Ok(result)
}

fn is_lower_hex(value: &str, count: usize) -> bool {
    value.len() == count
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn is_sha256(value: &str) -> bool {
    value
        .strip_prefix("sha256:")
        .is_some_and(|hex| is_lower_hex(hex, 64))
}

fn is_safe_service_name(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 256
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
}

fn validate_args(args: &Args) -> Result<(), String> {
    for (label, path) in [
        ("source-repo", &args.source_repo),
        ("candidate-dir", &args.candidate_dir),
        ("candidate-manifest", &args.candidate_manifest),
        ("install-dir", &args.install_dir),
        ("database", &args.database),
        ("env-file", &args.env_file),
        ("receipt-root", &args.receipt_root),
    ] {
        if !path.is_absolute() {
            return Err(format!("--{label} must be absolute"));
        }
    }
    if !is_lower_hex(&args.commit, 40) || args.confirm_commit != args.commit {
        return Err("commit must be lowercase SHA-1 and confirm-commit must match".to_string());
    }
    if !is_lower_hex(&args.effect_id, 64) {
        return Err("effect-id must be 64 lowercase hexadecimal characters".to_string());
    }
    if !args
        .effect_request_digest
        .strip_prefix("runtime-release-v1:")
        .is_some_and(is_sha256)
        || !is_sha256(&args.candidate_manifest_digest)
    {
        return Err(
            "effect request digest must be runtime-release-v1:sha256:... and candidate digest must be sha256:..."
                .to_string(),
        );
    }
    if args.expected_tool_count == 0 || args.drain_seconds == 0 {
        return Err("expected-tool-count and drain-seconds must be positive".to_string());
    }
    if !is_safe_service_name(&args.service) || !is_safe_service_name(&args.broker_service) {
        return Err("service names are invalid".to_string());
    }
    if args.workspace_id.is_empty()
        || args.workspace_id.len() > 128
        || !args
            .workspace_id
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-' | b':'))
    {
        return Err("workspace-id is invalid".to_string());
    }
    if args.require_ref.trim().is_empty() || args.require_ref.len() > 256 {
        return Err("require-ref is invalid".to_string());
    }
    Ok(())
}

fn sha256_file(path: &Path) -> Result<String, String> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("cannot stat {}: {error}", path.display()))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err(format!(
            "not a regular non-symlink file: {}",
            path.display()
        ));
    }
    let mut file =
        File::open(path).map_err(|error| format!("cannot open {}: {error}", path.display()))?;
    let mut digest = Sha256::new();
    let mut buffer = [0u8; SHA256_BUFFER_BYTES];
    loop {
        let read = file
            .read(&mut buffer)
            .map_err(|error| format!("cannot read {}: {error}", path.display()))?;
        if read == 0 {
            break;
        }
        digest.update(&buffer[..read]);
    }
    Ok(format!("sha256:{:x}", digest.finalize()))
}

fn canonical(path: &Path) -> Result<PathBuf, String> {
    fs::canonicalize(path)
        .map_err(|error| format!("cannot canonicalize {}: {error}", path.display()))
}

fn same_path(left: &Path, right: &Path) -> Result<bool, String> {
    Ok(canonical(left)? == canonical(right)?)
}

fn git_safe_root(cwd: &Path) -> Result<PathBuf, String> {
    let mut candidate = canonical(cwd)?;
    loop {
        let marker = candidate.join(".git");
        if marker.exists() {
            return Ok(candidate);
        }
        if !candidate.pop() {
            return Err(format!(
                "cannot locate Git root above Runtime owner {}",
                cwd.display()
            ));
        }
    }
}

fn git_output(cwd: &Path, args: &[&str]) -> Result<String, String> {
    let safe_root = git_safe_root(cwd)?;
    let output = Command::new("git")
        .arg("-c")
        .arg(format!("safe.directory={}", safe_root.display()))
        .arg("-C")
        .arg(cwd)
        .args(args)
        .output()
        .map_err(|error| format!("cannot execute Git release-authority check: {error}"))?;
    if !output.status.success() {
        return Err(format!(
            "Git release-authority check failed (git -C {} {}): {}",
            cwd.display(),
            args.join(" "),
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

fn git_status(cwd: &Path, args: &[&str]) -> Result<std::process::ExitStatus, String> {
    let safe_root = git_safe_root(cwd)?;
    Command::new("git")
        .arg("-c")
        .arg(format!("safe.directory={}", safe_root.display()))
        .arg("-C")
        .arg(cwd)
        .args(args)
        .status()
        .map_err(|error| format!("cannot execute Git release-authority check: {error}"))
}

fn verify_publication_authority(
    source_repo: &Path,
    owner_commit: &str,
    required_ref: &str,
    manifest_required_ref_commit: &str,
    manifest_owner_prefix: Option<&str>,
) -> Result<(), String> {
    let git_root = PathBuf::from(git_output(source_repo, &["rev-parse", "--show-toplevel"])?);
    let git_root = canonical(&git_root)?;
    let owner_root = canonical(source_repo)?;
    let prefix = git_output(source_repo, &["rev-parse", "--show-prefix"])?
        .trim_end_matches('/')
        .to_string();
    let expected_owner_root = if prefix.is_empty() {
        git_root.clone()
    } else {
        canonical(&git_root.join(Path::new(&prefix)))?
    };
    if expected_owner_root != owner_root {
        return Err("configured Runtime owner path does not match its Git prefix".to_string());
    }
    match (prefix.is_empty(), manifest_owner_prefix) {
        (true, None | Some("")) => {}
        (false, Some(value)) if value == prefix => {}
        _ => {
            return Err(
                "candidate manifest sourceOwnerPrefix does not match source repository".to_string(),
            )
        }
    }

    let required_ref_commit = git_output(
        source_repo,
        &[
            "rev-parse",
            "--verify",
            &format!("{required_ref}^{{commit}}"),
        ],
    )?;
    if required_ref_commit != manifest_required_ref_commit {
        return Err(
            "candidate manifest requiredRefCommit does not match current publication ref"
                .to_string(),
        );
    }

    let resolved_owner_commit = if prefix.is_empty() {
        required_ref_commit.clone()
    } else {
        git_output(
            source_repo,
            &["log", "-1", "--format=%H", &required_ref_commit, "--", "."],
        )?
    };
    if resolved_owner_commit != owner_commit {
        return Err(
            "requested Runtime owner commit is not the owner revision published by required ref"
                .to_string(),
        );
    }

    let ancestry = git_status(
        &git_root,
        &[
            "merge-base",
            "--is-ancestor",
            owner_commit,
            &required_ref_commit,
        ],
    )?;
    if !ancestry.success() {
        return Err(
            "Runtime owner commit is not an ancestor of the required publication ref".to_string(),
        );
    }

    if !prefix.is_empty() {
        let owner_tree = git_output(
            &git_root,
            &["rev-parse", &format!("{owner_commit}:{prefix}")],
        )?;
        let published_tree = git_output(
            &git_root,
            &["rev-parse", &format!("{required_ref_commit}:{prefix}")],
        )?;
        if owner_tree != published_tree {
            return Err(
                "required publication ref does not preserve the candidate Runtime owner tree"
                    .to_string(),
            );
        }
    }
    Ok(())
}

fn run_self_check(runtime: &Path) -> Result<CompiledSelfCheck, String> {
    let output = Command::new(runtime)
        .arg("--self-check")
        .output()
        .map_err(|error| format!("cannot execute candidate Runtime self-check: {error}"))?;
    if !output.status.success() {
        return Err(format!(
            "candidate Runtime self-check failed: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    serde_json::from_slice(&output.stdout)
        .map_err(|error| format!("candidate Runtime self-check returned invalid JSON: {error}"))
}

fn load_candidate(args: &Args) -> Result<CandidateProof, String> {
    let observed_manifest_digest = sha256_file(&args.candidate_manifest)?;
    if observed_manifest_digest != args.candidate_manifest_digest {
        return Err(
            "candidate manifest digest does not match structured release request".to_string(),
        );
    }
    let manifest_bytes = fs::read(&args.candidate_manifest)
        .map_err(|error| format!("cannot read candidate manifest: {error}"))?;
    let manifest: CandidateManifest = serde_json::from_slice(&manifest_bytes)
        .map_err(|error| format!("candidate manifest JSON is invalid: {error}"))?;
    if manifest.schema_version != MANIFEST_SCHEMA_VERSION {
        return Err("candidate manifest schemaVersion is unsupported".to_string());
    }
    if manifest.platform != "windows_native"
        || manifest.commit != args.commit
        || manifest.source_materialization != "detached_git_checkout"
        || manifest.required_ref != args.require_ref
    {
        return Err("candidate manifest release identity does not match request".to_string());
    }
    if !same_path(Path::new(&manifest.source_repo), &args.source_repo)?
        || !same_path(Path::new(&manifest.candidate_dir), &args.candidate_dir)?
    {
        return Err("candidate manifest path identity does not match request".to_string());
    }
    verify_publication_authority(
        &args.source_repo,
        &args.commit,
        &args.require_ref,
        &manifest.required_ref_commit,
        manifest.source_owner_prefix.as_deref(),
    )?;

    let expected_names = REQUIRED_ARTIFACTS.into_iter().collect::<BTreeSet<_>>();
    let observed_names = manifest
        .artifacts
        .iter()
        .map(|artifact| artifact.name.as_str())
        .collect::<BTreeSet<_>>();
    if observed_names != expected_names || manifest.artifacts.len() != expected_names.len() {
        return Err(
            "candidate manifest artifact set is not the complete Windows release set".to_string(),
        );
    }

    let mut artifacts = BTreeMap::new();
    for artifact in &manifest.artifacts {
        if artifact.kind != "binary" || !is_sha256(&artifact.digest) || artifact.bytes == 0 {
            return Err(format!(
                "invalid candidate artifact metadata: {}",
                artifact.name
            ));
        }
        let path = args.candidate_dir.join(&artifact.name);
        let metadata = fs::symlink_metadata(&path).map_err(|error| {
            format!(
                "candidate artifact {} is unavailable: {error}",
                artifact.name
            )
        })?;
        if metadata.file_type().is_symlink()
            || !metadata.is_file()
            || metadata.len() != artifact.bytes
        {
            return Err(format!(
                "candidate artifact does not match manifest: {}",
                artifact.name
            ));
        }
        if sha256_file(&path)? != artifact.digest {
            return Err(format!(
                "candidate artifact digest mismatch: {}",
                artifact.name
            ));
        }
        artifacts.insert(artifact.name.clone(), path);
    }

    let current = std::env::current_exe()
        .map_err(|error| format!("cannot inspect deployer path: {error}"))?;
    let expected_deployer = artifacts
        .get("ordivon-runtime-windows-deploy.exe")
        .ok_or("candidate deployer missing")?;
    if !same_path(&current, expected_deployer)? {
        return Err("running Windows deployer is not the candidate manifest deployer".to_string());
    }

    let runtime = artifacts
        .get("ordivon-runtime.exe")
        .ok_or("candidate Runtime missing")?;
    let self_check = run_self_check(runtime)?;
    if self_check.schema_version != 1
        || self_check.status != "ok"
        || self_check.catalog_scope != "compiled_base"
        || self_check.compiled_tool_count != args.expected_tool_count
        || self_check.compiled_tool_count != manifest.compiled_tool_count
        || self_check.compiled_base_tool_catalog_digest
            != manifest.compiled_base_tool_catalog_digest
        || self_check.max_migration_version != manifest.max_migration_version
    {
        return Err(
            "candidate Runtime self-check does not match candidate manifest/request".to_string(),
        );
    }
    if !is_sha256(&self_check.compiled_base_tool_catalog_digest) {
        return Err("candidate Runtime compiled catalog digest is invalid".to_string());
    }

    Ok(CandidateProof {
        manifest_digest: observed_manifest_digest,
        manifest,
        self_check,
        artifacts,
    })
}

fn doctor(args: &Args) -> Result<ordivon_runtime_core::RuntimeDoctorReport, String> {
    let registry_root = args
        .database
        .parent()
        .ok_or("database has no Registry root")?
        .to_path_buf();
    inspect_runtime(&RuntimeDoctorConfig {
        db_path: args.database.clone(),
        store_root: registry_root,
        busy_timeout_ms: 5_000,
    })
    .map_err(|error| format!("Runtime Doctor failed: {error}"))
}

fn inspect(args: &Args) -> Result<ordivon_runtime_core::RuntimeOperatorRegistryInspection, String> {
    inspect_registry(
        &RuntimeInspectionConfig {
            db_path: args.database.clone(),
            busy_timeout_ms: 5_000,
        },
        None,
    )
    .map_err(|error| format!("Registry inspection failed: {error}"))
}

fn inspect_attempt(
    args: &Args,
    attempt_id: &str,
) -> Result<RuntimeOperatorRegistryInspection, String> {
    inspect_registry(
        &RuntimeInspectionConfig {
            db_path: args.database.clone(),
            busy_timeout_ms: 5_000,
        },
        Some(attempt_id),
    )
    .map_err(|error| format!("Registry attempt inspection failed: {error}"))
}

fn release_effect(
    args: &Args,
) -> Result<ordivon_runtime_core::RuntimeOperatorReleaseEffectInspection, String> {
    let effect = inspect_runtime_release_effect(
        &RuntimeInspectionConfig {
            db_path: args.database.clone(),
            busy_timeout_ms: 5_000,
        },
        &args.effect_id,
    )
    .map_err(|error| format!("release effect inspection failed: {error}"))?
    .ok_or_else(|| "release effect has no durable side truth".to_string())?;
    let expected_receipt = args.receipt_root.join(format!("effect-{}", args.effect_id));
    if effect.effect_id != args.effect_id
        || effect.request_digest != args.effect_request_digest
        || effect.workspace_id != args.workspace_id
        || effect.commit != args.commit
        || effect.candidate_manifest_digest != args.candidate_manifest_digest
        || effect.expected_tool_count != args.expected_tool_count
        || Path::new(&effect.receipt_path) != expected_receipt
    {
        return Err("durable Runtime Release side truth does not match deployer argv".to_string());
    }
    Ok(effect)
}

fn blockers(active: &[String], owner: &str, bootstrap_job: Option<&str>) -> Vec<String> {
    active
        .iter()
        .filter(|job_id| {
            job_id.as_str() != owner
                && bootstrap_job.is_none_or(|bootstrap| job_id.as_str() != bootstrap)
        })
        .cloned()
        .collect()
}

fn admission_lock_path(args: &Args) -> Result<PathBuf, String> {
    Ok(args
        .database
        .parent()
        .ok_or("database has no Registry root")?
        .join("admission.lock"))
}

fn acquire_admission_fence(args: &Args) -> Result<File, String> {
    let path = admission_lock_path(args)?;
    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(&path)
        .map_err(|error| format!("cannot open admission fence {}: {error}", path.display()))?;
    file.try_lock()
        .map_err(|error| format!("cannot acquire exclusive admission fence: {error}"))?;
    Ok(file)
}

fn wait_for_drain(
    args: &Args,
    owner: &str,
    bootstrap_job: Option<&str>,
) -> Result<Vec<String>, String> {
    let deadline = Instant::now() + Duration::from_secs(args.drain_seconds);
    loop {
        let registry = inspect(args)?;
        let pending = blockers(&registry.active_job_ids, owner, bootstrap_job);
        if pending.is_empty() {
            return Ok(registry.active_job_ids);
        }
        if Instant::now() >= deadline {
            return Err(format!(
                "Runtime release drain timed out with active Jobs: {}",
                pending.join(",")
            ));
        }
        thread::sleep(Duration::from_millis(250));
    }
}

fn load_env(path: &Path) -> Result<EnvSnapshot, String> {
    let bytes = fs::read(path).map_err(|error| format!("cannot read Runtime env file: {error}"))?;
    let text = std::str::from_utf8(&bytes)
        .map_err(|_| "Runtime env file must be UTF-8 for structured release".to_string())?;
    let mut values = BTreeMap::new();
    for raw in text.lines() {
        let line = raw.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let Some((name, value)) = line.split_once('=') else {
            return Err("Runtime env file contains a non-assignment line".to_string());
        };
        values.insert(name.to_string(), value.trim_end_matches('\r').to_string());
    }
    Ok(EnvSnapshot { bytes, values })
}

fn valid_bootstrap_attempt_id(value: &str) -> bool {
    value.starts_with("attempt-")
        && value.len() <= 96
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
}

fn regular_file_digest(path: &Path, label: &str) -> Result<String, String> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("cannot stat {label} {}: {error}", path.display()))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err(format!("{label} must be a regular non-symlink file"));
    }
    sha256_file(path)
}

fn bootstrap_control_result_is_supported(control: &serde_json::Value) -> bool {
    control
        .get("reasonCode")
        .and_then(serde_json::Value::as_str)
        == Some("RUNNER_RESULT_QUARANTINED")
        && control
            .get("detail")
            .and_then(serde_json::Value::as_str)
            .is_some_and(|detail| detail.contains("LaunchIdentityMismatch"))
}
fn bootstrap_recovery_proof(
    args: &Args,
    candidate: &CandidateProof,
    report: &RuntimeDoctorReport,
) -> Result<Option<BootstrapRecoveryProof>, String> {
    let env = load_env(&args.env_file)?;
    let Some(attempt_id) = env.values.get(BOOTSTRAP_RECOVERY_ATTEMPT_ENV) else {
        if report.integrity_check != "ok"
            || report.violation_count != 0
            || report.summary.recovery_required_attempts != 0
        {
            return Err("Runtime Doctor preflight is not healthy enough for release".to_string());
        }
        return Ok(None);
    };
    if !valid_bootstrap_attempt_id(attempt_id) {
        return Err("bootstrap recovery Attempt ID is invalid".to_string());
    }
    if report.integrity_check != "ok"
        || report.violation_count != 0
        || report.summary.recovery_required_attempts != 1
        || report.summary.capacity_holders_truncated
    {
        return Err(
            "bootstrap recovery requires exactly one visible recovery-required Attempt and no Doctor violations"
                .to_string(),
        );
    }
    let holders = report
        .summary
        .capacity_holders
        .iter()
        .filter(|holder| holder.attempt_id == *attempt_id)
        .collect::<Vec<_>>();
    if holders.len() != 1 {
        return Err(
            "bootstrap recovery Attempt is not the unique matching capacity holder".to_string(),
        );
    }
    let holder = holders[0];
    if holder.attempt_state != AttemptState::Orphaned
        || holder.reservation_state != ReservationState::HeldOrphaned
        || !holder.recovery_required
    {
        return Err(
            "bootstrap recovery Attempt must be orphaned, held_orphaned, and recovery-required"
                .to_string(),
        );
    }

    let inspection = inspect_attempt(args, attempt_id)?;
    if inspection.resolved_attempt_job_id.as_deref() != Some(holder.job_id.as_str()) {
        return Err(
            "bootstrap recovery Attempt/Job identity changed during inspection".to_string(),
        );
    }
    let owner = inspection
        .resolved_attempt_supervisor_owner
        .ok_or("bootstrap recovery Attempt lacks persisted supervisor owner evidence")?;

    let registry_root = args
        .database
        .parent()
        .ok_or("database has no Registry root")?;
    let bundle = registry_root.join("attempts").join(attempt_id);
    let result_path = bundle.join("result.json");
    let control_path = bundle.join("control-result.json");
    let start_path = bundle.join(BOOTSTRAP_LAUNCHER_START_FILE);
    let runner_result_digest = regular_file_digest(&result_path, "bootstrap Runner Result")?;
    let control_result_digest = regular_file_digest(&control_path, "bootstrap control result")?;
    let start_digest = regular_file_digest(&start_path, "bootstrap Windows start evidence")?;
    if start_digest != owner.start_evidence_digest {
        return Err(
            "bootstrap Windows start evidence digest does not match persisted owner".to_string(),
        );
    }
    let control_bytes = fs::read(&control_path)
        .map_err(|error| format!("cannot read bootstrap control result: {error}"))?;
    let control: serde_json::Value = serde_json::from_slice(&control_bytes)
        .map_err(|error| format!("cannot decode bootstrap control result: {error}"))?;
    if !bootstrap_control_result_is_supported(&control) {
        return Err(
            "bootstrap recovery is limited to quarantined Windows LaunchIdentityMismatch results"
                .to_string(),
        );
    }

    let launcher = candidate
        .artifacts
        .get("ordivon-windows-job-launcher.exe")
        .ok_or("candidate launcher artifact is unavailable")?;
    let output = Command::new(launcher)
        .args([
            "--describe-process-owner",
            "--process-id",
            &owner.launcher_process_id.to_string(),
        ])
        .output()
        .map_err(|error| format!("cannot execute candidate launcher owner probe: {error}"))?;
    if !output.status.success() {
        return Err(format!(
            "candidate launcher owner probe failed: {}",
            String::from_utf8_lossy(&output.stderr)
        ));
    }
    let probe: ProcessOwnerProbe = serde_json::from_slice(&output.stdout)
        .map_err(|error| format!("cannot decode candidate launcher owner probe: {error}"))?;
    if probe.schema_version != 1 || probe.process_id != owner.launcher_process_id {
        return Err("candidate launcher owner probe identity is invalid".to_string());
    }
    let owner_observed_absent = if !probe.process_alive {
        true
    } else {
        let observed_creation_time = probe
            .process_creation_time_file_time
            .ok_or("candidate launcher owner probe omitted creation time for a live process")?;
        observed_creation_time != owner.launcher_process_creation_time_file_time
    };
    if !owner_observed_absent {
        return Err("bootstrap recovery supervisor process is still physically alive".to_string());
    }

    Ok(Some(BootstrapRecoveryProof {
        attempt_id: attempt_id.clone(),
        job_id: holder.job_id.clone(),
        supervisor_launcher_process_id: owner.launcher_process_id,
        supervisor_launcher_process_creation_time_file_time: owner
            .launcher_process_creation_time_file_time,
        start_evidence_digest: owner.start_evidence_digest,
        runner_result_digest,
        control_result_digest,
        owner_observed_absent,
    }))
}

fn replace_env_release_paths(
    snapshot: &EnvSnapshot,
    launcher: &Path,
    broker: &Path,
) -> Result<Vec<u8>, String> {
    let text = std::str::from_utf8(&snapshot.bytes)
        .map_err(|_| "Runtime env file must be UTF-8".to_string())?;
    let launcher = launcher.to_string_lossy();
    let broker = broker.to_string_lossy();
    let mut output = Vec::<String>::new();
    let mut launcher_seen = false;
    let mut broker_seen = false;
    for raw in text.lines() {
        let line = raw.trim_end_matches('\r');
        if line.starts_with("ORDIVON_WINDOWS_LAUNCHER_PATH=") {
            output.push(format!("ORDIVON_WINDOWS_LAUNCHER_PATH={launcher}"));
            launcher_seen = true;
        } else if line.starts_with("ORDIVON_WINDOWS_PRIVILEGED_BROKER_PATH=") {
            output.push(format!("ORDIVON_WINDOWS_PRIVILEGED_BROKER_PATH={broker}"));
            broker_seen = true;
        } else if line.starts_with(&format!("{BOOTSTRAP_RECOVERY_ATTEMPT_ENV}=")) {
            continue;
        } else {
            output.push(line.to_string());
        }
    }
    if !launcher_seen || !broker_seen {
        return Err("Runtime env file lacks Windows launcher/broker path authorities".to_string());
    }
    let newline = if text.contains("\r\n") { "\r\n" } else { "\n" };
    Ok((output.join(newline) + newline).into_bytes())
}

fn write_existing_file_preserving_acl(path: &Path, bytes: &[u8]) -> Result<(), String> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("cannot stat Runtime env file: {error}"))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err("Runtime env file must be a regular non-symlink file".to_string());
    }
    let mut file = OpenOptions::new()
        .write(true)
        .truncate(true)
        .open(path)
        .map_err(|error| format!("cannot open Runtime env file for update: {error}"))?;
    file.write_all(bytes)
        .map_err(|error| format!("cannot update Runtime env file: {error}"))?;
    file.sync_all()
        .map_err(|error| format!("cannot fsync Runtime env file: {error}"))
}

fn stage_release(args: &Args, proof: &CandidateProof) -> Result<PathBuf, String> {
    fs::create_dir_all(&args.install_dir)
        .map_err(|error| format!("cannot create release root: {error}"))?;
    let final_dir = args.install_dir.join(&args.commit);
    if final_dir.exists() {
        for artifact in &proof.manifest.artifacts {
            let observed = final_dir.join(&artifact.name);
            if sha256_file(&observed)? != artifact.digest {
                return Err(format!(
                    "existing release directory conflicts with candidate: {}",
                    artifact.name
                ));
            }
        }
        return Ok(final_dir);
    }

    let staging = args.install_dir.join(format!(
        ".{}.{}.staging",
        args.commit,
        &args.effect_id[..12]
    ));
    if staging.exists() {
        fs::remove_dir_all(&staging)
            .map_err(|error| format!("cannot clear stale release staging directory: {error}"))?;
    }
    fs::create_dir(&staging)
        .map_err(|error| format!("cannot create release staging directory: {error}"))?;
    for artifact in &proof.manifest.artifacts {
        let source = proof
            .artifacts
            .get(&artifact.name)
            .ok_or_else(|| format!("candidate artifact disappeared: {}", artifact.name))?;
        let destination = staging.join(&artifact.name);
        fs::copy(source, &destination)
            .map_err(|error| format!("cannot stage {}: {error}", artifact.name))?;
        if sha256_file(&destination)? != artifact.digest {
            return Err(format!(
                "staged artifact digest mismatch: {}",
                artifact.name
            ));
        }
    }
    fs::copy(
        &args.candidate_manifest,
        staging.join("ordivon-deployment-manifest.json"),
    )
    .map_err(|error| format!("cannot stage candidate manifest: {error}"))?;
    fs::rename(&staging, &final_dir)
        .map_err(|error| format!("cannot atomically publish release directory: {error}"))?;
    Ok(final_dir)
}

fn now_ms() -> Result<u64, String> {
    let value = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|_| "system clock is before Unix epoch".to_string())?
        .as_millis();
    u64::try_from(value).map_err(|_| "timestamp exceeds u64".to_string())
}

fn write_json_sync<T: Serialize>(path: &Path, value: &T) -> Result<(), String> {
    let parent = path.parent().ok_or("receipt path has no parent")?;
    fs::create_dir_all(parent)
        .map_err(|error| format!("cannot create receipt directory: {error}"))?;
    let bytes = serde_json::to_vec_pretty(value)
        .map_err(|error| format!("cannot encode receipt JSON: {error}"))?;
    let temp = path.with_extension("json.tmp");
    {
        let mut file = File::create(&temp)
            .map_err(|error| format!("cannot create receipt temp file: {error}"))?;
        file.write_all(&bytes)
            .map_err(|error| format!("cannot write receipt temp file: {error}"))?;
        file.write_all(b"\n")
            .map_err(|error| format!("cannot finish receipt temp file: {error}"))?;
        file.sync_all()
            .map_err(|error| format!("cannot fsync receipt temp file: {error}"))?;
    }
    fs::rename(&temp, path).map_err(|error| format!("cannot publish receipt file: {error}"))
}

fn effect_identity(args: &Args) -> EffectIdentity<'_> {
    EffectIdentity {
        contract: "runtime_release_v1",
        effect_id: &args.effect_id,
        request_digest: &args.effect_request_digest,
        commit: &args.commit,
        candidate_manifest_digest: &args.candidate_manifest_digest,
        expected_tool_count: args.expected_tool_count,
    }
}

fn quote_windows_argument(value: &str) -> String {
    if !value.contains([' ', '\t', '"']) {
        return value.to_string();
    }
    let mut out = String::from("\"");
    let mut backslashes = 0usize;
    for character in value.chars() {
        if character == '\\' {
            backslashes += 1;
        } else if character == '"' {
            out.push_str(&"\\".repeat(backslashes * 2 + 1));
            out.push('"');
            backslashes = 0;
        } else {
            out.push_str(&"\\".repeat(backslashes));
            backslashes = 0;
            out.push(character);
        }
    }
    out.push_str(&"\\".repeat(backslashes * 2));
    out.push('"');
    out
}

#[cfg(windows)]
fn new_service_paths(
    args: &Args,
    release_dir: &Path,
    env: &EnvSnapshot,
    proof: &CandidateProof,
) -> Result<(String, String, Vec<u8>), String> {
    let runtime = release_dir.join("ordivon-runtime.exe");
    let launcher = release_dir.join("ordivon-windows-job-launcher.exe");
    let broker = release_dir.join("ordivon-windows-privileged-broker.exe");
    let pipe = env
        .values
        .get("ORDIVON_WINDOWS_PRIVILEGED_BROKER_PIPE")
        .ok_or("Runtime env file lacks ORDIVON_WINDOWS_PRIVILEGED_BROKER_PIPE")?;
    if pipe.is_empty() || pipe.len() > 128 {
        return Err("broker pipe name is invalid".to_string());
    }
    let registry_root = args
        .database
        .parent()
        .ok_or("database has no Registry root")?;
    let runtime_account = format!("NT SERVICE\\{}", args.service);
    let runtime_sid = scm::account_sid_string(&runtime_account)?;
    let launcher_digest = proof
        .manifest
        .artifacts
        .iter()
        .find(|artifact| artifact.name == "ordivon-windows-job-launcher.exe")
        .ok_or("candidate launcher metadata missing")?
        .digest
        .strip_prefix("sha256:")
        .ok_or("candidate launcher digest is invalid")?;
    let runtime_image = format!(
        "{} --windows-service --env-file {}",
        quote_windows_argument(&runtime.to_string_lossy()),
        quote_windows_argument(&args.env_file.to_string_lossy())
    );
    let broker_image = format!(
        "{} --service --service-name {} --pipe-name {} --launcher-path {} --launcher-sha256 {} --allowed-client-sid {} --allowed-bundle-root {}",
        quote_windows_argument(&broker.to_string_lossy()),
        args.broker_service,
        pipe,
        quote_windows_argument(&launcher.to_string_lossy()),
        launcher_digest,
        runtime_sid,
        quote_windows_argument(&registry_root.join("attempts").to_string_lossy())
    );
    let env_bytes = replace_env_release_paths(env, &launcher, &broker)?;
    Ok((runtime_image, broker_image, env_bytes))
}

fn preflight(args: &Args) -> Result<(CandidateProof, PlanReceipt), String> {
    #[cfg(windows)]
    if !windows_current_token_is_local_system()
        .map_err(|error| format!("cannot inspect deployer token: {error}"))?
    {
        return Err("Windows structured release deployer must run as LocalSystem".to_string());
    }

    let proof = load_candidate(args)?;
    let report = doctor(args)?;
    let bootstrap_recovery = bootstrap_recovery_proof(args, &proof, &report)?;
    if report.migration_version > proof.self_check.max_migration_version {
        return Err(format!(
            "live Registry migration {} exceeds candidate support {}",
            report.migration_version, proof.self_check.max_migration_version
        ));
    }
    let effect = release_effect(args)?;
    let registry = inspect(args)?;
    let blocked = blockers(
        &registry.active_job_ids,
        &effect.job_id,
        bootstrap_recovery
            .as_ref()
            .map(|proof| proof.job_id.as_str()),
    );
    let release_dir = args.install_dir.join(&args.commit);
    let plan = PlanReceipt {
        schema_version: RECEIPT_SCHEMA_VERSION,
        status: "eligible",
        commit: args.commit.clone(),
        effect_id: args.effect_id.clone(),
        candidate_manifest_digest: proof.manifest_digest.clone(),
        pre_migration_version: report.migration_version,
        candidate_max_migration_version: proof.self_check.max_migration_version,
        compiled_tool_count: proof.self_check.compiled_tool_count,
        compiled_base_tool_catalog_digest: proof
            .self_check
            .compiled_base_tool_catalog_digest
            .clone(),
        release_dir: release_dir.to_string_lossy().into_owned(),
        owner_job_id: effect.job_id,
        active_job_ids: registry.active_job_ids,
        blockers: blocked,
        bootstrap_recovery,
    };
    Ok((proof, plan))
}

#[cfg(windows)]
fn apply(
    args: &Args,
    proof: CandidateProof,
    mut plan: PlanReceipt,
) -> Result<serde_json::Value, String> {
    let receipt_dir = args.receipt_root.join(format!("effect-{}", args.effect_id));
    let effect_request = EffectRequestReceipt {
        contract: "runtime_release_v1",
        effect_id: &args.effect_id,
        request_digest: &args.effect_request_digest,
        commit: &args.commit,
        candidate_manifest_digest: &args.candidate_manifest_digest,
        expected_tool_count: args.expected_tool_count,
        workspace_id: &args.workspace_id,
        platform: "windows_native",
    };
    write_json_sync(&receipt_dir.join("effect-request.json"), &effect_request)?;
    write_json_sync(&receipt_dir.join("plan.json"), &plan)?;

    let admission = acquire_admission_fence(args)?;
    let active = wait_for_drain(
        args,
        &plan.owner_job_id,
        plan.bootstrap_recovery
            .as_ref()
            .map(|proof| proof.job_id.as_str()),
    )?;
    plan.active_job_ids = active;
    plan.blockers.clear();
    write_json_sync(&receipt_dir.join("plan.json"), &plan)?;

    let post_drain_doctor = doctor(args)?;
    let post_drain_bootstrap = bootstrap_recovery_proof(args, &proof, &post_drain_doctor)?;
    if post_drain_bootstrap != plan.bootstrap_recovery {
        return Err("bootstrap recovery evidence changed during release drain".to_string());
    }
    if post_drain_doctor.migration_version > proof.self_check.max_migration_version {
        return Err("Runtime Doctor changed to an unsafe state during release drain".to_string());
    }

    let release_dir = stage_release(args, &proof)?;
    let env_snapshot = load_env(&args.env_file)?;
    let runtime_snapshot = scm::snapshot(&args.service)?;
    let broker_snapshot = scm::snapshot(&args.broker_service)?;
    let (runtime_image, broker_image, env_bytes) =
        new_service_paths(args, &release_dir, &env_snapshot, &proof)?;

    let preimage = serde_json::json!({
        "schemaVersion": RECEIPT_SCHEMA_VERSION,
        "capturedAtMs": now_ms()?,
        "preMigrationVersion": post_drain_doctor.migration_version,
        "runtimeService": {
            "name": args.service,
            "binaryPath": runtime_snapshot.binary_path,
            "state": runtime_snapshot.state,
            "processId": runtime_snapshot.process_id,
        },
        "brokerService": {
            "name": args.broker_service,
            "binaryPath": broker_snapshot.binary_path,
            "state": broker_snapshot.state,
            "processId": broker_snapshot.process_id,
        },
        "envFileSha256": sha256_file(&args.env_file)?,
    });
    write_json_sync(&receipt_dir.join("preimage.json"), &preimage)?;
    fs::write(receipt_dir.join("env-preimage.bin"), &env_snapshot.bytes)
        .map_err(|error| format!("cannot persist env preimage: {error}"))?;

    let cutover = (|| -> Result<(), String> {
        scm::stop(&args.service, Duration::from_secs(20))?;
        scm::stop(&args.broker_service, Duration::from_secs(20))?;
        write_existing_file_preserving_acl(&args.env_file, &env_bytes)?;
        scm::set_binary_path(&args.service, &runtime_image)?;
        scm::set_binary_path(&args.broker_service, &broker_image)?;
        scm::start(&args.broker_service, Duration::from_secs(20))?;
        scm::start(&args.service, Duration::from_secs(20))?;

        let live_runtime = release_dir.join("ordivon-runtime.exe");
        let live_check = run_self_check(&live_runtime)?;
        if live_check.compiled_tool_count != proof.self_check.compiled_tool_count
            || live_check.compiled_base_tool_catalog_digest
                != proof.self_check.compiled_base_tool_catalog_digest
            || live_check.max_migration_version != proof.self_check.max_migration_version
        {
            return Err("post-cutover Runtime self-check differs from candidate proof".to_string());
        }
        let post = doctor(args)?;
        if post.violation_count != 0
            || post.summary.recovery_required_attempts != 0
            || post.migration_version > proof.self_check.max_migration_version
        {
            return Err("post-cutover Runtime Doctor is unhealthy".to_string());
        }
        Ok(())
    })();

    let _ = admission.unlock();

    if let Err(error) = cutover {
        let post_failure = doctor(args);
        let rollback_safe = post_failure
            .as_ref()
            .map(|report| report.migration_version <= plan.pre_migration_version)
            .unwrap_or(false);
        if rollback_safe {
            let rollback = (|| -> Result<(), String> {
                let _ = scm::stop(&args.service, Duration::from_secs(20));
                let _ = scm::stop(&args.broker_service, Duration::from_secs(20));
                write_existing_file_preserving_acl(&args.env_file, &env_snapshot.bytes)?;
                scm::set_binary_path(&args.service, &runtime_snapshot.binary_path)?;
                scm::set_binary_path(&args.broker_service, &broker_snapshot.binary_path)?;
                scm::start(&args.broker_service, Duration::from_secs(20))?;
                scm::start(&args.service, Duration::from_secs(20))?;
                Ok(())
            })();
            match rollback {
                Ok(()) => {
                    write_json_sync(
                        &receipt_dir.join("rollback-result.json"),
                        &serde_json::json!({
                            "schemaVersion": RECEIPT_SCHEMA_VERSION,
                            "status": "restored_previous",
                            "reason": error,
                            "restoredAtMs": now_ms()?,
                        }),
                    )?;
                    let result = serde_json::json!({
                        "schemaVersion": RECEIPT_SCHEMA_VERSION,
                        "status": "rolled_back",
                        "commit": args.commit,
                        "releaseEffect": effect_identity(args),
                        "probe": {
                            "toolCount": proof.self_check.compiled_tool_count,
                            "toolCatalogDigest": proof.self_check.compiled_base_tool_catalog_digest,
                            "catalogScope": "compiled_base",
                        },
                        "issue": error,
                    });
                    write_json_sync(&receipt_dir.join("result.json"), &result)?;
                    return Ok(result);
                }
                Err(rollback_error) => {
                    let result = serde_json::json!({
                        "schemaVersion": RECEIPT_SCHEMA_VERSION,
                        "status": "rollback_failed",
                        "commit": args.commit,
                        "releaseEffect": effect_identity(args),
                        "issue": error,
                        "rollbackError": rollback_error,
                    });
                    write_json_sync(&receipt_dir.join("result.json"), &result)?;
                    return Ok(result);
                }
            }
        }
        let result = serde_json::json!({
            "schemaVersion": RECEIPT_SCHEMA_VERSION,
            "status": "recovery_failed",
            "commit": args.commit,
            "releaseEffect": effect_identity(args),
            "issue": error,
            "rollbackBlockedByMigration": true,
        });
        write_json_sync(&receipt_dir.join("result.json"), &result)?;
        return Ok(result);
    }

    let post = doctor(args)?;
    let result = serde_json::json!({
        "schemaVersion": RECEIPT_SCHEMA_VERSION,
        "status": "deployed",
        "commit": args.commit,
        "releaseEffect": effect_identity(args),
        "candidateManifestDigest": args.candidate_manifest_digest,
        "releaseDir": release_dir,
        "probe": {
            "toolCount": proof.self_check.compiled_tool_count,
            "toolCatalogDigest": proof.self_check.compiled_base_tool_catalog_digest,
            "catalogScope": "compiled_base",
        },
        "migrationVersion": post.migration_version,
        "maxMigrationVersion": proof.self_check.max_migration_version,
        "deployedAtMs": now_ms()?,
    });
    write_json_sync(&receipt_dir.join("result.json"), &result)?;
    Ok(result)
}

#[cfg(not(windows))]
fn main() {
    eprintln!("ordivon-runtime-windows-deploy is available only on Windows");
    std::process::exit(125);
}

#[cfg(windows)]
fn main() {
    let result = (|| -> Result<(), String> {
        let args = parse_args()?;
        let (proof, plan) = preflight(&args)?;
        if args.command == "plan" {
            println!(
                "{}",
                serde_json::to_string(&plan).map_err(|error| error.to_string())?
            );
            return Ok(());
        }
        let result = apply(&args, proof, plan)?;
        println!(
            "{}",
            serde_json::to_string(&result).map_err(|error| error.to_string())?
        );
        Ok(())
    })();
    if let Err(error) = result {
        eprintln!("ordivon-runtime-windows-deploy: {error}");
        std::process::exit(125);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn digest_buffer_matches_bounded_core_pattern() {
        assert_eq!(SHA256_BUFFER_BYTES, 64 * 1024);
        const {
            assert!(SHA256_BUFFER_BYTES <= 64 * 1024);
        }
    }

    #[test]
    fn required_windows_artifact_set_is_exact_and_unique() {
        let values = REQUIRED_ARTIFACTS.into_iter().collect::<BTreeSet<_>>();
        assert_eq!(values.len(), REQUIRED_ARTIFACTS.len());
        assert!(values.contains("ordivon-runtime.exe"));
        assert!(values.contains("ordivon-runtime-windows-deploy.exe"));
    }

    #[test]
    fn effect_and_commit_identity_validation_is_strict() {
        assert!(is_lower_hex(&"a".repeat(40), 40));
        assert!(!is_lower_hex(&"A".repeat(40), 40));
        assert!(is_sha256(&format!("sha256:{}", "f".repeat(64))));
        assert!(!is_sha256(&format!("sha256:{}", "F".repeat(64))));
        assert!(format!("runtime-release-v1:sha256:{}", "f".repeat(64))
            .strip_prefix("runtime-release-v1:")
            .is_some_and(is_sha256));
    }

    #[test]
    fn nested_owner_publication_allows_sibling_only_main_commit() {
        let unique = format!(
            "ordivon-windows-release-owner-tree-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .expect("clock")
                .as_nanos()
        );
        let root = std::env::temp_dir().join(unique);
        fs::create_dir_all(root.join("services/runtime")).expect("create owner");
        let git = |args: &[&str]| {
            let output = Command::new("git")
                .arg("-C")
                .arg(&root)
                .args(args)
                .output()
                .expect("git");
            assert!(
                output.status.success(),
                "git {:?}: {}",
                args,
                String::from_utf8_lossy(&output.stderr)
            );
            String::from_utf8_lossy(&output.stdout).trim().to_string()
        };
        git(&["init", "-q"]);
        git(&["config", "user.name", "Ordivon Test"]);
        git(&["config", "user.email", "ordivon-test@local.invalid"]);
        fs::write(root.join("services/runtime/runtime.txt"), b"runtime-v1\n").expect("write owner");
        git(&["add", "."]);
        git(&["commit", "-qm", "runtime"]);
        let owner_commit = git(&["rev-parse", "HEAD"]);
        fs::write(root.join("sibling.txt"), b"sibling-v1\n").expect("write sibling");
        git(&["add", "sibling.txt"]);
        git(&["commit", "-qm", "sibling"]);
        let main_commit = git(&["rev-parse", "HEAD"]);
        git(&["update-ref", "refs/remotes/origin/main", &main_commit]);

        let owner = root.join("services/runtime");
        verify_publication_authority(
            &owner,
            &owner_commit,
            "origin/main",
            &main_commit,
            Some("services/runtime"),
        )
        .expect("nested owner should be authorized by sibling-only main commit");
        assert_ne!(owner_commit, main_commit);

        fs::remove_dir_all(root).expect("cleanup");
    }

    #[test]
    fn windows_quoting_handles_spaces_quotes_and_trailing_slashes() {
        assert_eq!(
            quote_windows_argument(r"C:\Windows\cmd.exe"),
            r"C:\Windows\cmd.exe"
        );
        assert_eq!(
            quote_windows_argument(r"C:\Program Files\Ordivon\runtime.exe"),
            r#""C:\Program Files\Ordivon\runtime.exe""#
        );
        assert_eq!(quote_windows_argument(r#"a"b"#), r#""a\"b""#);
    }

    #[test]
    fn blockers_exclude_release_owner_and_explicit_bootstrap_job_only() {
        let active = vec![
            "job-a".to_string(),
            "job-release".to_string(),
            "job-bootstrap".to_string(),
            "job-b".to_string(),
        ];
        assert_eq!(
            blockers(&active, "job-release", Some("job-bootstrap")),
            vec!["job-a".to_string(), "job-b".to_string()]
        );
        assert_eq!(
            blockers(&active, "job-release", None),
            vec![
                "job-a".to_string(),
                "job-bootstrap".to_string(),
                "job-b".to_string()
            ]
        );
    }

    #[test]
    fn env_rewrite_consumes_one_shot_bootstrap_recovery_authority() {
        let input = concat!(
            "ORDIVON_WINDOWS_LAUNCHER_PATH=C:\\old\\launcher.exe\r\n",
            "ORDIVON_WINDOWS_PRIVILEGED_BROKER_PATH=C:\\old\\broker.exe\r\n",
            "ORDIVON_RELEASE_BOOTSTRAP_RECOVERY_ATTEMPT_ID=attempt-123\r\n",
            "OTHER=value\r\n"
        );
        let snapshot = EnvSnapshot {
            bytes: input.as_bytes().to_vec(),
            values: BTreeMap::new(),
        };
        let output = replace_env_release_paths(
            &snapshot,
            Path::new(r"C:\new\launcher.exe"),
            Path::new(r"C:\new\broker.exe"),
        )
        .expect("rewrite");
        let output = String::from_utf8(output).expect("utf8");
        assert!(!output.contains(BOOTSTRAP_RECOVERY_ATTEMPT_ENV));
        assert!(output.contains(r"ORDIVON_WINDOWS_LAUNCHER_PATH=C:\new\launcher.exe"));
        assert!(output.contains(r"ORDIVON_WINDOWS_PRIVILEGED_BROKER_PATH=C:\new\broker.exe"));
        assert!(output.contains("OTHER=value"));
    }

    #[test]
    fn bootstrap_recovery_uses_parent_observed_launcher_start_evidence() {
        assert_eq!(BOOTSTRAP_LAUNCHER_START_FILE, "windows-launcher-start.json");
        assert_ne!(BOOTSTRAP_LAUNCHER_START_FILE, "windows-start.json");
    }

    #[test]
    fn bootstrap_recovery_accepts_historical_control_result_shape() {
        let control = serde_json::json!({
            "schemaVersion": 1,
            "status": "orphaned",
            "reasonCode": "RUNNER_RESULT_QUARANTINED",
            "detail": "LaunchIdentityMismatch: Windows start identity does not match committed Attempt"
        });
        assert!(bootstrap_control_result_is_supported(&control));
        assert!(!bootstrap_control_result_is_supported(&serde_json::json!({
            "reason": "RUNNER_RESULT_QUARANTINED",
            "detail": "LaunchIdentityMismatch"
        })));
    }
    #[test]
    fn bootstrap_attempt_id_is_path_safe() {
        assert!(valid_bootstrap_attempt_id(
            "attempt-01a0c401-14b0-7850-bdea-b3883b58434d"
        ));
        assert!(!valid_bootstrap_attempt_id("../attempt-123"));
        assert!(!valid_bootstrap_attempt_id("attempt-123/child"));
    }
}
