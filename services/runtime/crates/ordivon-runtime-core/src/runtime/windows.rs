//! Windows-native execution provider.
//!
//! Runtime retains Job/Attempt authority while the repository-owned launcher owns the Windows
//! Job Object. The provider is native-Windows only; non-Windows Runtime nodes fail closed rather
//! than projecting paths or transporting execution through WSL.

use std::collections::BTreeMap;
use std::fs;
#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;
#[cfg(windows)]
use std::os::windows::io::AsRawHandle;
use std::path::{Path, PathBuf};
#[cfg(windows)]
use std::process::Stdio;
use std::process::{Command, Output};

use serde::{Deserialize, Serialize};

#[cfg(windows)]
use windows_sys::Win32::Foundation::FILETIME;
#[cfg(windows)]
use windows_sys::Win32::System::Threading::GetProcessTimes;

use super::supervisor::WindowsLauncherOwnerObservation;
#[cfg(windows)]
use super::windows_broker;
use super::windows_broker::WindowsPrivilegedBrokerConfig;
use super::{ExecutionBudget, RuntimeError, RuntimeErrorCode, RuntimeResult, WindowsAuthority};

const WINDOWS_BASELINE_ENVIRONMENT_NAMES: &[&str] = &[
    "APPDATA",
    "CommonProgramFiles",
    "CommonProgramW6432",
    "COMPUTERNAME",
    "ComSpec",
    "HOMEDRIVE",
    "HOMEPATH",
    "LOCALAPPDATA",
    "NUMBER_OF_PROCESSORS",
    "OS",
    "Path",
    "PATHEXT",
    "PROCESSOR_ARCHITECTURE",
    "ProgramData",
    "ProgramFiles",
    "ProgramW6432",
    "PUBLIC",
    "SystemDrive",
    "SystemRoot",
    "TEMP",
    "TMP",
    "USERDOMAIN",
    "USERNAME",
    "USERPROFILE",
    "windir",
];

const REQUIRED_WINDOWS_BASELINE_ENVIRONMENT_NAMES: &[&str] = &[
    "ComSpec",
    "Path",
    "PATHEXT",
    "SystemDrive",
    "SystemRoot",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "LOCALAPPDATA",
    "APPDATA",
    "ProgramData",
    "ProgramFiles",
];

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WindowsExecutionConfig {
    /// Exact native Windows launcher executable.
    pub launcher_path: PathBuf,
    pub privileged_broker: Option<WindowsPrivilegedBrokerConfig>,
}

impl WindowsExecutionConfig {
    pub(crate) fn validate(&self) -> RuntimeResult<()> {
        if !self.launcher_path.is_absolute() {
            return Err(RuntimeError::invalid(
                "Windows launcher path must be absolute",
                "windows.launcherPath",
            ));
        }
        let metadata = fs::symlink_metadata(&self.launcher_path).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::IoError,
                format!("inspect Windows launcher: {error}"),
                Some("windows.launcherPath"),
                false,
            )
        })?;
        if metadata.file_type().is_symlink()
            || !metadata.is_file()
            || !launcher_is_executable(&metadata)
        {
            return Err(RuntimeError::invalid(
                "Windows launcher must be a non-symlink executable file",
                "windows.launcherPath",
            ));
        }
        validate_windows_control_plane(self)?;
        if let Some(broker) = &self.privileged_broker {
            broker.validate_shape()?;
            if broker.executable_path == self.launcher_path {
                return Err(RuntimeError::invalid(
                    "Windows privileged broker must be distinct from the Job launcher",
                    "windows.privilegedBrokerPath",
                ));
            }
            #[cfg(windows)]
            {
                let _ = broker.executable_digest()?;
            }
        }
        Ok(())
    }
}

#[cfg(unix)]
fn launcher_is_executable(metadata: &fs::Metadata) -> bool {
    metadata.permissions().mode() & 0o111 != 0
}

#[cfg(windows)]
fn launcher_is_executable(_metadata: &fs::Metadata) -> bool {
    true
}

#[cfg(not(windows))]
fn validate_windows_control_plane(_config: &WindowsExecutionConfig) -> RuntimeResult<()> {
    Err(RuntimeError::new(
        RuntimeErrorCode::ToolUnavailable,
        "Windows execution provider is available only on a native Windows Runtime",
        Some("windows"),
        false,
    ))
}

#[cfg(windows)]
fn validate_windows_control_plane(_config: &WindowsExecutionConfig) -> RuntimeResult<()> {
    Ok(())
}

#[cfg(not(windows))]
fn windows_launcher_output_with_transport<F>(
    _launcher: &Path,
    _configure: F,
    _context: &str,
) -> RuntimeResult<(Output, Option<PathBuf>)>
where
    F: Fn(&mut Command),
{
    Err(RuntimeError::new(
        RuntimeErrorCode::ToolUnavailable,
        "Windows launcher transport is available only on a native Windows Runtime",
        Some("windows"),
        false,
    ))
}

#[cfg(windows)]
fn windows_launcher_output_with_transport<F>(
    launcher: &Path,
    configure: F,
    context: &str,
) -> RuntimeResult<(Output, Option<PathBuf>)>
where
    F: Fn(&mut Command),
{
    let mut command = Command::new(launcher);
    configure(&mut command);
    let output = command
        .output()
        .map_err(|error| tool_error(context, error))?;
    Ok((output, None))
}

#[derive(Debug)]
struct WindowsLauncherCapture {
    success: bool,
    exit_code: Option<i32>,
    stdout: Vec<u8>,
    stderr: Vec<u8>,
    transport: Option<PathBuf>,
}

fn capture_windows_launcher(
    config: &WindowsExecutionConfig,
    authority: WindowsAuthority,
    expected_broker_digest: Option<&str>,
    launcher_args: &[String],
    context: &str,
) -> RuntimeResult<WindowsLauncherCapture> {
    config.validate()?;
    #[cfg(not(windows))]
    let _ = (authority, expected_broker_digest);

    #[cfg(windows)]
    if authority != WindowsAuthority::Limited {
        if let Some(broker) = config.privileged_broker.as_ref() {
            let capture =
                windows_broker::capture(broker, expected_broker_digest, context, launcher_args)?;
            return Ok(WindowsLauncherCapture {
                success: capture.exit_code == 0,
                exit_code: Some(capture.exit_code),
                stdout: capture.stdout,
                stderr: capture.stderr,
                transport: None,
            });
        }
    }

    let launcher = fs::canonicalize(&config.launcher_path).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!("canonicalize Windows launcher: {error}"),
            Some("windows.launcherPath"),
            false,
        )
    })?;
    let (output, transport) = windows_launcher_output_with_transport(
        &launcher,
        |command| {
            command.args(launcher_args);
        },
        context,
    )?;
    Ok(WindowsLauncherCapture {
        success: output.status.success(),
        exit_code: output.status.code(),
        stdout: output.stdout,
        stderr: output.stderr,
        transport,
    })
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WindowsRuntimeContextSnapshot {
    pub schema_version: u32,
    pub token_selection: String,
    #[serde(default)]
    pub execution_identity: String,
    #[serde(default)]
    pub session_id: Option<u32>,
    pub token_user_sid: String,
    pub token_type: i32,
    pub token_elevation_type: i32,
    pub token_is_elevated: bool,
    pub token_integrity_level_rid: i32,
    pub token_is_restricted: bool,
    pub administrators_group_attributes: u32,
    pub environment: BTreeMap<String, String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WindowsStartEvidence {
    pub schema_version: u32,
    pub job_id: String,
    pub attempt_id: String,
    pub launch_token_digest: String,
    pub request_digest: String,
    pub job_name: String,
    pub launcher_process_id: u32,
    #[serde(default)]
    pub launcher_process_creation_time_file_time: Option<u64>,
    #[serde(default)]
    pub launcher_image_digest: Option<String>,
    pub process_id: u32,
    pub process_creation_time_file_time: u64,
    pub image_path: String,
    pub image_digest: String,
    pub token_selection: String,
    #[serde(default)]
    pub execution_identity: String,
    #[serde(default)]
    pub session_id: Option<u32>,
    pub token_user_sid: String,
    pub token_type: i32,
    pub token_elevation_type: i32,
    pub token_is_elevated: bool,
    pub token_integrity_level_rid: i32,
    pub token_is_restricted: bool,
    pub administrators_group_attributes: u32,
    pub power_request_type: String,
    pub power_request_acquired: bool,
    #[serde(default)]
    pub input_set_id: Option<String>,
    #[serde(default)]
    pub input_presentation_root: Option<String>,
    #[serde(default)]
    pub input_bindings_digest: Option<String>,
    pub observed_unix_ms: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WindowsLauncherStartEvidence {
    pub schema_version: u32,
    pub job_id: String,
    pub attempt_id: String,
    pub launch_token_digest: String,
    pub request_digest: String,
    pub job_name: String,
    pub launcher_process_id: u32,
    pub launcher_process_creation_time_file_time: u64,
    pub launcher_image_digest: String,
    pub observed_unix_ms: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct WindowsProcessOwnerSnapshot {
    schema_version: u32,
    process_id: u32,
    process_alive: bool,
    #[serde(default)]
    process_creation_time_file_time: Option<u64>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum WindowsDeadlineOwnerTerminationDisposition {
    Terminated,
    AlreadyAbsent,
    IdentityMismatch,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct WindowsDeadlineOwnerTerminationSnapshot {
    schema_version: u32,
    process_id: u32,
    expected_process_creation_time_file_time: u64,
    #[serde(default)]
    observed_process_creation_time_file_time: Option<u64>,
    disposition: String,
}

pub(crate) fn observe_windows_launcher_owner(
    config: &WindowsExecutionConfig,
    authority: WindowsAuthority,
    expected_broker_digest: Option<&str>,
    process_id: u32,
) -> RuntimeResult<WindowsLauncherOwnerObservation> {
    config.validate()?;
    if process_id == 0 {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "persisted Windows launcher process id is zero",
            Some("attemptSupervisorOwner.launcherProcessId"),
            false,
        ));
    }
    let launcher_args = vec![
        "--describe-process-owner".to_string(),
        "--process-id".to_string(),
        process_id.to_string(),
    ];
    let output = capture_windows_launcher(
        config,
        authority,
        expected_broker_digest,
        &launcher_args,
        "describe-windows-launcher-owner",
    )?;
    if !output.success {
        return Err(RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!(
                "Windows launcher owner probe failed: {}",
                String::from_utf8_lossy(&output.stderr).trim()
            ),
            Some("windows.launcherOwner"),
            true,
        ));
    }
    if output.stdout.len() > 64 * 1024 || output.stderr.len() > 64 * 1024 {
        return Err(RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            "Windows launcher owner probe output exceeded bounded size",
            Some("windows.launcherOwner"),
            false,
        ));
    }
    let snapshot: WindowsProcessOwnerSnapshot =
        serde_json::from_slice(&output.stdout).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                format!("invalid Windows launcher owner evidence: {error}"),
                Some("windows.launcherOwner"),
                false,
            )
        })?;
    if snapshot.schema_version != 1
        || snapshot.process_id != process_id
        || (snapshot.process_alive
            && snapshot
                .process_creation_time_file_time
                .is_none_or(|identity| identity == 0))
        || (!snapshot.process_alive && snapshot.process_creation_time_file_time.is_some())
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::LaunchIdentityMismatch,
            "Windows launcher owner probe returned inconsistent identity",
            Some("windows.launcherOwner"),
            false,
        ));
    }
    Ok(WindowsLauncherOwnerObservation {
        process_alive: snapshot.process_alive,
        process_creation_time_file_time: snapshot.process_creation_time_file_time,
    })
}

pub(crate) fn terminate_windows_launcher_owner_for_deadline(
    config: &WindowsExecutionConfig,
    authority: WindowsAuthority,
    expected_broker_digest: Option<&str>,
    process_id: u32,
    process_creation_time_file_time: u64,
) -> RuntimeResult<WindowsDeadlineOwnerTerminationDisposition> {
    config.validate()?;
    if process_id == 0 || process_creation_time_file_time == 0 {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "persisted Windows launcher deadline owner identity is incomplete",
            Some("attemptSupervisorOwner"),
            false,
        ));
    }
    let launcher_args = vec![
        "--terminate-process-owner-for-deadline".to_string(),
        "--process-id".to_string(),
        process_id.to_string(),
        "--process-creation-time-file-time".to_string(),
        process_creation_time_file_time.to_string(),
    ];
    let output = capture_windows_launcher(
        config,
        authority,
        expected_broker_digest,
        &launcher_args,
        "terminate-windows-launcher-deadline-owner",
    )?;
    if output.stdout.len() > 64 * 1024 || output.stderr.len() > 64 * 1024 {
        return Err(RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            "Windows launcher deadline owner termination output exceeded bounded size",
            Some("windows.launcherDeadlineOwner"),
            false,
        ));
    }
    if !output.success {
        return Err(RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!(
                "Windows launcher deadline owner termination failed (exit {:?}): {}",
                output.exit_code,
                String::from_utf8_lossy(&output.stderr).trim()
            ),
            Some("windows.launcherDeadlineOwner"),
            true,
        ));
    }
    parse_windows_deadline_owner_termination(
        &output.stdout,
        process_id,
        process_creation_time_file_time,
    )
}

fn parse_windows_deadline_owner_termination(
    output: &[u8],
    process_id: u32,
    process_creation_time_file_time: u64,
) -> RuntimeResult<WindowsDeadlineOwnerTerminationDisposition> {
    let snapshot: WindowsDeadlineOwnerTerminationSnapshot = serde_json::from_slice(output)
        .map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                format!("invalid Windows launcher deadline termination evidence: {error}"),
                Some("windows.launcherDeadlineOwner"),
                false,
            )
        })?;
    let disposition = match snapshot.disposition.as_str() {
        "terminated" => WindowsDeadlineOwnerTerminationDisposition::Terminated,
        "already_absent" => WindowsDeadlineOwnerTerminationDisposition::AlreadyAbsent,
        "identity_mismatch" => WindowsDeadlineOwnerTerminationDisposition::IdentityMismatch,
        _ => {
            return Err(RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                "Windows launcher deadline termination returned an unknown disposition",
                Some("windows.launcherDeadlineOwner.disposition"),
                false,
            ));
        }
    };
    let observed_identity_valid = match disposition {
        WindowsDeadlineOwnerTerminationDisposition::Terminated => {
            snapshot.observed_process_creation_time_file_time
                == Some(process_creation_time_file_time)
        }
        WindowsDeadlineOwnerTerminationDisposition::AlreadyAbsent => {
            snapshot.observed_process_creation_time_file_time.is_none()
        }
        WindowsDeadlineOwnerTerminationDisposition::IdentityMismatch => snapshot
            .observed_process_creation_time_file_time
            .is_some_and(|observed| observed != 0 && observed != process_creation_time_file_time),
    };
    if snapshot.schema_version != 1
        || snapshot.process_id != process_id
        || snapshot.expected_process_creation_time_file_time != process_creation_time_file_time
        || !observed_identity_valid
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::LaunchIdentityMismatch,
            "Windows launcher deadline termination returned inconsistent identity evidence",
            Some("windows.launcherDeadlineOwner"),
            false,
        ));
    }
    Ok(disposition)
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct WindowsNativeLaunchObservation {
    pub launcher_process_id: u32,
    pub launcher_process_creation_time_file_time: u64,
}

pub(crate) struct WindowsNativeRunSpec<'a> {
    pub config: &'a WindowsExecutionConfig,
    pub bundle_path: &'a Path,
    pub job_id: &'a str,
    pub attempt_id: &'a str,
    pub launch_token_digest: &'a str,
    pub request_digest: &'a str,
    pub authority: WindowsAuthority,
    pub expected_privileged_broker_digest: Option<&'a str>,
    pub expected_user_sid: Option<&'a str>,
    pub expected_session_id: Option<u32>,
    pub executable: &'a Path,
    pub args: &'a [String],
    pub cwd: &'a Path,
    pub environment: &'a BTreeMap<String, String>,
    pub input_source_root: Option<&'a Path>,
    pub input_set_id: Option<&'a str>,
    pub input_presentation_root: Option<&'a str>,
    pub input_bindings_digest: Option<&'a str>,
    pub budget: &'a ExecutionBudget,
    pub timeout_ms: u64,
    pub stdout_limit_bytes: u64,
    pub stderr_limit_bytes: u64,
}

/// Windows-native launcher contract after all control-plane path projection has completed.
///
/// The launcher semantics are intentionally independent from the transport that starts it.
/// The current provider wraps this contract in `systemd-run` from WSL; a native Windows
/// provider can invoke the same contract directly without changing Job/Attempt semantics.
#[cfg(any(windows, test))]
pub(crate) struct WindowsLauncherInvocationSpec<'a> {
    pub bundle: &'a str,
    pub job_id: &'a str,
    pub attempt_id: &'a str,
    pub launch_token_digest: &'a str,
    pub request_digest: &'a str,
    pub job_name: &'a str,
    pub authority: WindowsAuthority,
    pub expected_user_sid: Option<&'a str>,
    pub expected_session_id: Option<u32>,
    pub executable: &'a str,
    pub args: &'a [String],
    pub cwd: &'a str,
    pub environment: &'a BTreeMap<String, String>,
    pub input_source_root: Option<&'a str>,
    pub input_set_id: Option<&'a str>,
    pub input_presentation_root: Option<&'a str>,
    pub input_bindings_digest: Option<&'a str>,
    pub budget: &'a ExecutionBudget,
    pub timeout_ms: u64,
    pub stdout_limit_bytes: u64,
    pub stderr_limit_bytes: u64,
    pub emit_launcher_start: bool,
}

pub(crate) fn snapshot_windows_runtime_context(
    config: &WindowsExecutionConfig,
    authority: WindowsAuthority,
) -> RuntimeResult<WindowsRuntimeContextSnapshot> {
    snapshot_windows_runtime_context_with_transport(config, authority).map(|(snapshot, _)| snapshot)
}

pub(crate) fn snapshot_windows_runtime_context_with_transport(
    config: &WindowsExecutionConfig,
    authority: WindowsAuthority,
) -> RuntimeResult<(WindowsRuntimeContextSnapshot, Option<PathBuf>)> {
    config.validate()?;
    let (launcher_authority, launcher_identity) = match authority {
        WindowsAuthority::ActiveUser => ("elevated", Some("active_user")),
        _ => (authority.as_str(), None),
    };
    let mut launcher_args = vec![
        "--describe-runtime-context".to_string(),
        "--authority".to_string(),
        launcher_authority.to_string(),
    ];
    if let Some(identity) = launcher_identity {
        launcher_args.push("--identity".to_string());
        launcher_args.push(identity.to_string());
    }
    for name in WINDOWS_BASELINE_ENVIRONMENT_NAMES {
        launcher_args.push("--context-env".to_string());
        launcher_args.push((*name).to_string());
    }
    let output = capture_windows_launcher(
        config,
        authority,
        None,
        &launcher_args,
        "describe-windows-runtime-context",
    )?;
    if !output.success {
        return Err(RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!(
                "Windows runtime context probe failed: {}",
                String::from_utf8_lossy(&output.stderr).trim()
            ),
            Some("windows.runtimeContext"),
            true,
        ));
    }
    if output.stdout.len() > 64 * 1024 || output.stderr.len() > 64 * 1024 {
        return Err(RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            "Windows runtime context probe output exceeded bounded size",
            Some("windows.runtimeContext"),
            false,
        ));
    }
    let snapshot: WindowsRuntimeContextSnapshot =
        serde_json::from_slice(&output.stdout).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                format!("invalid Windows runtime context evidence: {error}"),
                Some("windows.runtimeContext"),
                false,
            )
        })?;
    validate_windows_runtime_context(&snapshot, authority)?;
    Ok((snapshot, output.transport))
}

fn validate_windows_runtime_context(
    snapshot: &WindowsRuntimeContextSnapshot,
    authority: WindowsAuthority,
) -> RuntimeResult<()> {
    let token_authority_valid = match authority {
        WindowsAuthority::Limited => {
            !snapshot.token_is_elevated
                && snapshot.token_integrity_level_rid <= 8192
                && (snapshot.administrators_group_attributes == u32::MAX
                    || (snapshot.administrators_group_attributes & 0x4) == 0
                    || (snapshot.administrators_group_attributes & 0x10) != 0)
                && matches!(
                    snapshot.token_selection.as_str(),
                    "lua_medium_filtered" | "current_limited"
                )
                && (snapshot.token_selection != "lua_medium_filtered"
                    || snapshot.administrators_group_attributes == u32::MAX
                    || (snapshot.administrators_group_attributes & 0x10) != 0)
                && matches!(snapshot.execution_identity.as_str(), "" | "service")
        }
        WindowsAuthority::Elevated => {
            snapshot.token_is_elevated
                && snapshot.token_integrity_level_rid >= 12288
                && snapshot.administrators_group_attributes != u32::MAX
                && (snapshot.administrators_group_attributes & 0x4) != 0
                && (snapshot.administrators_group_attributes & 0x10) == 0
                && snapshot.token_selection == "current_elevated"
                && matches!(snapshot.execution_identity.as_str(), "" | "service")
        }
        WindowsAuthority::ActiveUser => {
            !snapshot.token_is_elevated
                && snapshot.token_integrity_level_rid <= 8192
                && (snapshot.administrators_group_attributes == u32::MAX
                    || (snapshot.administrators_group_attributes & 0x4) == 0
                    || (snapshot.administrators_group_attributes & 0x10) != 0)
                && snapshot.token_selection == "active_user"
                && snapshot.execution_identity == "active_user"
                && snapshot.session_id.is_some()
        }
    };
    if snapshot.schema_version != 1
        || snapshot.token_user_sid.is_empty()
        || snapshot.token_type != 1
        || !token_authority_valid
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            format!(
                "Windows runtime context did not prove requested {} authority",
                authority.as_str()
            ),
            Some("windows.runtimeContext"),
            false,
        ));
    }
    for name in REQUIRED_WINDOWS_BASELINE_ENVIRONMENT_NAMES {
        if !snapshot
            .environment
            .iter()
            .any(|(actual, value)| actual.eq_ignore_ascii_case(name) && !value.is_empty())
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                format!("Windows runtime context omitted required baseline variable {name}"),
                Some("windows.runtimeContext.environment"),
                false,
            ));
        }
    }
    for name in snapshot.environment.keys() {
        if !WINDOWS_BASELINE_ENVIRONMENT_NAMES
            .iter()
            .any(|allowed| name.eq_ignore_ascii_case(allowed))
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                format!("Windows runtime context returned non-allowlisted variable {name}"),
                Some("windows.runtimeContext.environment"),
                false,
            ));
        }
    }
    Ok(())
}

const WINDOWS_CREATE_PROCESS_COMMAND_LINE_LIMIT_UTF16: usize = 32_767;
const WINDOWS_ENVIRONMENT_VARIABLE_LIMIT_UTF16: usize = 32_767;

fn checked_windows_quoted_argument_utf16_len(value: &str, field: &str) -> RuntimeResult<usize> {
    if value.as_bytes().contains(&0) {
        return Err(RuntimeError::invalid(
            "Windows command-line value contains NUL",
            field,
        ));
    }
    let needs_quotes = value.is_empty()
        || value
            .chars()
            .any(|character| character.is_whitespace() || character == '"');
    if !needs_quotes {
        return Ok(value.encode_utf16().count());
    }

    // Mirror Ordivon.WindowsJobLauncher.QuoteWindowsArgument without allocating the quoted value.
    let mut length = 2usize; // opening + closing quotes
    let mut backslashes = 0usize;
    for character in value.chars() {
        if character == '\\' {
            backslashes = backslashes.checked_add(1).ok_or_else(|| {
                RuntimeError::invalid("Windows command-line length overflow", field)
            })?;
            continue;
        }
        if character == '"' {
            length = length
                .checked_add(
                    backslashes
                        .checked_mul(2)
                        .and_then(|value| value.checked_add(2))
                        .ok_or_else(|| {
                            RuntimeError::invalid("Windows command-line length overflow", field)
                        })?,
                )
                .ok_or_else(|| {
                    RuntimeError::invalid("Windows command-line length overflow", field)
                })?;
            backslashes = 0;
            continue;
        }
        length = length
            .checked_add(backslashes)
            .and_then(|value| value.checked_add(character.len_utf16()))
            .ok_or_else(|| RuntimeError::invalid("Windows command-line length overflow", field))?;
        backslashes = 0;
    }
    length
        .checked_add(
            backslashes.checked_mul(2).ok_or_else(|| {
                RuntimeError::invalid("Windows command-line length overflow", field)
            })?,
        )
        .ok_or_else(|| RuntimeError::invalid("Windows command-line length overflow", field))
}

pub(crate) fn validate_windows_exec_payload(
    executable: &str,
    args: &[String],
    env: &BTreeMap<String, String>,
    field: &str,
) -> RuntimeResult<()> {
    crate::universal::validate_env(env).map_err(|error| {
        RuntimeError::invalid(error.message, error.field.as_deref().unwrap_or(field))
    })?;

    let mut command_line_utf16 = checked_windows_quoted_argument_utf16_len(executable, field)?;
    for arg in args {
        command_line_utf16 = command_line_utf16
            .checked_add(1)
            .and_then(|value| {
                checked_windows_quoted_argument_utf16_len(arg, field)
                    .ok()
                    .and_then(|arg_len| value.checked_add(arg_len))
            })
            .ok_or_else(|| RuntimeError::invalid("Windows command-line length overflow", field))?;
    }
    // CreateProcessW documents 32,767 UTF-16 code units including the terminating NUL.
    let command_line_with_nul = command_line_utf16
        .checked_add(1)
        .ok_or_else(|| RuntimeError::invalid("Windows command-line length overflow", field))?;
    if command_line_with_nul > WINDOWS_CREATE_PROCESS_COMMAND_LINE_LIMIT_UTF16 {
        return Err(RuntimeError::invalid(
            format!(
                "Windows command line requires {command_line_with_nul} UTF-16 code units including NUL, exceeding the CreateProcessW limit of {WINDOWS_CREATE_PROCESS_COMMAND_LINE_LIMIT_UTF16}"
            ),
            field,
        ));
    }

    // Modern Windows does not impose the historical 32,767-character total Unicode environment
    // block limit, but one user-defined environment variable remains bounded. Enforce each
    // NAME=VALUE entry conservatively including its terminating NUL.
    for (name, value) in env {
        let entry_utf16 = name
            .encode_utf16()
            .count()
            .checked_add(1)
            .and_then(|length| length.checked_add(value.encode_utf16().count()))
            .and_then(|length| length.checked_add(1))
            .ok_or_else(|| {
                RuntimeError::invalid("Windows environment entry length overflow", field)
            })?;
        if entry_utf16 > WINDOWS_ENVIRONMENT_VARIABLE_LIMIT_UTF16 {
            return Err(RuntimeError::invalid(
                format!(
                    "Windows environment entry {name} requires {entry_utf16} UTF-16 code units including separator/NUL, exceeding the per-variable limit of {WINDOWS_ENVIRONMENT_VARIABLE_LIMIT_UTF16}"
                ),
                field,
            ));
        }
    }
    Ok(())
}

pub(crate) fn merge_windows_environment(
    baseline: &BTreeMap<String, String>,
    overlay: &BTreeMap<String, String>,
) -> RuntimeResult<BTreeMap<String, String>> {
    let mut seen = Vec::<String>::new();
    for name in overlay.keys() {
        if name.is_empty() || name.contains('=') || name.contains('\0') {
            return Err(RuntimeError::invalid(
                "invalid Windows environment variable name",
                "execution.env",
            ));
        }
        if seen
            .iter()
            .any(|existing| existing.eq_ignore_ascii_case(name))
        {
            return Err(RuntimeError::invalid(
                "Windows environment variable names must be unique case-insensitively",
                "execution.env",
            ));
        }
        seen.push(name.clone());
    }
    let mut result = baseline.clone();
    for (name, value) in overlay {
        if let Some(existing) = result
            .keys()
            .find(|existing| existing.eq_ignore_ascii_case(name))
            .cloned()
        {
            result.remove(&existing);
        }
        result.insert(name.clone(), value.clone());
    }
    Ok(result)
}

#[cfg(windows)]
pub(crate) fn spawn_windows_native(
    spec: &WindowsNativeRunSpec<'_>,
) -> RuntimeResult<WindowsNativeLaunchObservation> {
    spec.config.validate()?;
    let launcher = fs::canonicalize(&spec.config.launcher_path).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!("canonicalize native Windows launcher: {error}"),
            Some("windows.launcherPath"),
            false,
        )
    })?;
    let executable = windows_visible_path(spec.config, spec.executable, "execution.executable")?;
    let cwd = windows_visible_path(spec.config, spec.cwd, "execution.cwdRelative")?;
    let bundle = windows_visible_path(spec.config, spec.bundle_path, "bundlePath")?;
    let input_source_root = spec
        .input_source_root
        .map(|source_root| {
            windows_visible_path(spec.config, source_root, "execution.effectiveInputs")
        })
        .transpose()?;
    let job_name = format!("Ordivon.{}", spec.attempt_id);
    let invocation = WindowsLauncherInvocationSpec {
        bundle: &bundle,
        job_id: spec.job_id,
        attempt_id: spec.attempt_id,
        launch_token_digest: spec.launch_token_digest,
        request_digest: spec.request_digest,
        job_name: &job_name,
        authority: spec.authority,
        expected_user_sid: spec.expected_user_sid,
        expected_session_id: spec.expected_session_id,
        executable: &executable,
        args: spec.args,
        cwd: &cwd,
        environment: spec.environment,
        input_source_root: input_source_root.as_deref(),
        input_set_id: spec.input_set_id,
        input_presentation_root: spec.input_presentation_root,
        input_bindings_digest: spec.input_bindings_digest,
        budget: spec.budget,
        timeout_ms: spec.timeout_ms,
        stdout_limit_bytes: spec.stdout_limit_bytes,
        stderr_limit_bytes: spec.stderr_limit_bytes,
        // The native Runtime parent already owns the authoritative CreateProcess handle.
        // It records launcher identity from that OS handle immediately after spawn, so the
        // launcher must not race the parent by self-publishing the same first-stage evidence.
        emit_launcher_start: false,
    };
    let launcher_stderr_path = spec.bundle_path.join("launcher-stderr.log");
    let mut command = Command::new(&launcher);
    append_windows_launcher_arguments(&mut command, &invocation)?;
    if spec.authority != WindowsAuthority::Limited {
        if let Some(broker) = spec.config.privileged_broker.as_ref() {
            let expected_broker_digest = spec.expected_privileged_broker_digest.ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "elevated native Windows dispatch through broker has no admission-frozen broker digest",
                    Some("windowsExecutionContext.privilegedBrokerDigest"),
                    false,
                )
            })?;
            let launcher_args = command
                .get_args()
                .map(|argument| {
                    argument.to_str().map(str::to_string).ok_or_else(|| {
                        RuntimeError::invalid(
                            "Windows launcher argument must be UTF-8 for privileged broker transport",
                            "execution",
                        )
                    })
                })
                .collect::<RuntimeResult<Vec<_>>>()?;
            let observation = windows_broker::spawn(
                broker,
                expected_broker_digest,
                &format!("spawn-{}", spec.attempt_id),
                &launcher_args,
                &launcher_stderr_path,
            )?;
            return Ok(WindowsNativeLaunchObservation {
                launcher_process_id: observation.launcher_process_id,
                launcher_process_creation_time_file_time: observation
                    .launcher_process_creation_time_file_time,
            });
        }
    }
    let launcher_stderr = fs::File::create(&launcher_stderr_path).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!("create native Windows launcher stderr carrier: {error}"),
            Some("windows.launcherStderr"),
            false,
        )
    })?;
    command
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::from(launcher_stderr));
    let child = command
        .spawn()
        .map_err(|error| tool_error("spawn native Windows launcher", error))?;
    let launcher_process_creation_time_file_time = child_process_creation_time_file_time(&child)?;
    Ok(WindowsNativeLaunchObservation {
        launcher_process_id: child.id(),
        launcher_process_creation_time_file_time,
    })
}

#[cfg(windows)]
fn child_process_creation_time_file_time(child: &std::process::Child) -> RuntimeResult<u64> {
    let mut creation = FILETIME {
        dwLowDateTime: 0,
        dwHighDateTime: 0,
    };
    let mut exit = creation;
    let mut kernel = creation;
    let mut user = creation;
    let ok = unsafe {
        GetProcessTimes(
            child.as_raw_handle() as windows_sys::Win32::Foundation::HANDLE,
            &mut creation,
            &mut exit,
            &mut kernel,
            &mut user,
        )
    };
    if ok == 0 {
        return Err(tool_error(
            "observe native Windows launcher creation identity",
            std::io::Error::last_os_error(),
        ));
    }
    let value = ((creation.dwHighDateTime as u64) << 32) | creation.dwLowDateTime as u64;
    if value == 0 {
        return Err(RuntimeError::new(
            RuntimeErrorCode::LaunchIdentityMismatch,
            "native Windows launcher creation identity is zero",
            Some("windowsLauncherStart.launcherProcessCreationTimeFileTime"),
            false,
        ));
    }
    Ok(value)
}

#[cfg(not(windows))]
pub(crate) fn spawn_windows_native(
    spec: &WindowsNativeRunSpec<'_>,
) -> RuntimeResult<WindowsNativeLaunchObservation> {
    let _ = (
        spec.config,
        spec.bundle_path,
        spec.job_id,
        spec.attempt_id,
        spec.launch_token_digest,
        spec.request_digest,
        spec.authority,
        spec.expected_privileged_broker_digest,
        spec.expected_user_sid,
        spec.expected_session_id,
        spec.executable,
        spec.args,
        spec.cwd,
        spec.environment,
        spec.input_source_root,
        spec.input_set_id,
        spec.input_presentation_root,
        spec.input_bindings_digest,
        spec.budget,
        spec.timeout_ms,
        spec.stdout_limit_bytes,
        spec.stderr_limit_bytes,
    );
    Err(RuntimeError::new(
        RuntimeErrorCode::InvalidRequest,
        "direct native Windows dispatch is unavailable on a non-Windows control plane",
        Some("executionTarget"),
        false,
    ))
}

#[cfg(any(windows, test))]
pub(crate) fn append_windows_launcher_arguments(
    command: &mut Command,
    spec: &WindowsLauncherInvocationSpec<'_>,
) -> RuntimeResult<()> {
    command
        .arg("--runtime-bundle")
        .arg(spec.bundle)
        .arg("--runtime-job-id")
        .arg(spec.job_id)
        .arg("--runtime-attempt-id")
        .arg(spec.attempt_id)
        .arg("--runtime-launch-token-digest")
        .arg(spec.launch_token_digest)
        .arg("--runtime-request-digest")
        .arg(spec.request_digest)
        .arg("--job-name")
        .arg(spec.job_name)
        .arg("--authority")
        .arg(match spec.authority {
            WindowsAuthority::ActiveUser => "elevated",
            _ => spec.authority.as_str(),
        });
    if spec.authority == WindowsAuthority::ActiveUser {
        let expected_user_sid = spec.expected_user_sid.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "active_user Windows dispatch has no admission-frozen user SID",
                Some("windowsExecutionContext.tokenUserSid"),
                false,
            )
        })?;
        let expected_session_id = spec.expected_session_id.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "active_user Windows dispatch has no admission-frozen session ID",
                Some("windowsExecutionContext.sessionId"),
                false,
            )
        })?;
        command
            .arg("--identity")
            .arg("active_user")
            .arg("--expected-user-sid")
            .arg(expected_user_sid)
            .arg("--expected-session-id")
            .arg(expected_session_id.to_string());
    } else if spec.expected_user_sid.is_some() || spec.expected_session_id.is_some() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "non-active-user Windows dispatch carried active-user identity commitments",
            Some("windowsExecutionContext"),
            false,
        ));
    }
    command
        .arg("--timeout-ms")
        .arg(spec.timeout_ms.to_string())
        .arg("--stdout-limit-bytes")
        .arg(spec.stdout_limit_bytes.to_string())
        .arg("--stderr-limit-bytes")
        .arg(spec.stderr_limit_bytes.to_string())
        .arg("--executable")
        .arg(spec.executable)
        .arg("--cwd")
        .arg(spec.cwd)
        .arg("--inherit-environment")
        .arg("false");
    if spec.emit_launcher_start {
        command.arg("--emit-launcher-start");
    }

    match (
        spec.input_source_root,
        spec.input_set_id,
        spec.input_presentation_root,
        spec.input_bindings_digest,
    ) {
        (None, None, None, None) => {}
        (Some(source_root), Some(input_set_id), Some(presentation_root), Some(bindings_digest)) => {
            command
                .arg("--input-source-root")
                .arg(source_root)
                .arg("--input-set-id")
                .arg(input_set_id)
                .arg("--input-presentation-root")
                .arg(presentation_root)
                .arg("--input-bindings-digest")
                .arg(bindings_digest);
        }
        _ => {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "Windows immutable input launch metadata is incomplete",
                Some("executionPlan.inputSetId"),
                false,
            ));
        }
    }
    for (name, value) in spec.environment {
        command.arg("--env").arg(format!("{name}={value}"));
    }
    if let Some(value) = spec.budget.memory_max_bytes {
        command.arg("--memory-max-bytes").arg(value.to_string());
    }
    if let Some(value) = spec.budget.tasks_max {
        command.arg("--active-process-limit").arg(value.to_string());
    }
    if let Some(value) = spec.budget.cpu_quota_percent {
        command.arg("--cpu-quota-percent").arg(value.to_string());
    }
    command.arg("--").args(spec.args);
    Ok(())
}

pub(crate) fn windows_visible_path(
    config: &WindowsExecutionConfig,
    path: &Path,
    field: &str,
) -> RuntimeResult<String> {
    #[cfg(windows)]
    {
        if !path.is_absolute() {
            return Err(RuntimeError::invalid(
                "Windows-visible path source must be absolute",
                field,
            ));
        }
        return path
            .to_str()
            .map(str::to_string)
            .ok_or_else(|| RuntimeError::invalid("Windows-visible path must be UTF-8", field));
    }
    #[cfg(not(windows))]
    {
        let _ = (config, path);
        Err(RuntimeError::new(
            RuntimeErrorCode::ToolUnavailable,
            "Windows path projection is available only on a native Windows Runtime",
            Some(field),
            false,
        ))
    }
}

pub(crate) fn validate_windows_input_relative_path(path: &str, index: usize) -> RuntimeResult<()> {
    const RESERVED: [&str; 4] = ["CON", "PRN", "AUX", "NUL"];
    let field = format!("inputs[{index}].presentationRelativePath");
    if path.contains('\\') {
        return Err(RuntimeError::invalid(
            "Windows immutable input presentation paths must use '/' separators only",
            &field,
        ));
    }
    for component in path.split('/') {
        if component.is_empty()
            || component.ends_with(' ')
            || component.ends_with('.')
            || component
                .chars()
                .any(|ch| ch < ' ' || matches!(ch, '<' | '>' | ':' | '"' | '|' | '?' | '*'))
        {
            return Err(RuntimeError::invalid(
                "Windows immutable input presentation path contains an invalid component",
                &field,
            ));
        }
        let stem = component
            .split('.')
            .next()
            .unwrap_or(component)
            .to_ascii_uppercase();
        if RESERVED.contains(&stem.as_str())
            || (stem.len() == 4
                && (stem.starts_with("COM") || stem.starts_with("LPT"))
                && stem.as_bytes()[3].is_ascii_digit()
                && stem.as_bytes()[3] != b'0')
        {
            return Err(RuntimeError::invalid(
                "Windows immutable input presentation path uses a reserved device name",
                &field,
            ));
        }
    }
    Ok(())
}

pub(crate) fn validate_windows_input_relative_paths<'a>(
    paths: impl IntoIterator<Item = &'a str>,
) -> RuntimeResult<()> {
    let mut normalized = Vec::<String>::new();
    for (index, path) in paths.into_iter().enumerate() {
        validate_windows_input_relative_path(path, index)?;
        let folded = path
            .split('/')
            .map(str::to_lowercase)
            .collect::<Vec<_>>()
            .join("/");
        for existing in &normalized {
            if folded == *existing
                || folded
                    .strip_prefix(existing)
                    .is_some_and(|suffix| suffix.starts_with('/'))
                || existing
                    .strip_prefix(&folded)
                    .is_some_and(|suffix| suffix.starts_with('/'))
            {
                return Err(RuntimeError::invalid(
                    "Windows immutable input presentation paths must not alias or overlap case-insensitively",
                    &format!("inputs[{index}].presentationRelativePath"),
                ));
            }
        }
        normalized.push(folded);
    }
    Ok(())
}

#[cfg(windows)]
fn tool_error(operation: &str, error: std::io::Error) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::IoError,
        format!("{operation}: {error}"),
        None,
        true,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn windows_environment_overlay_is_case_insensitive_and_does_not_duplicate_baseline_keys() {
        let baseline = BTreeMap::from([
            ("Path".to_string(), "C:\\Windows\\System32".to_string()),
            ("SystemRoot".to_string(), "C:\\Windows".to_string()),
        ]);
        let overlay = BTreeMap::from([
            ("PATH".to_string(), "C:\\Agent\\Bin".to_string()),
            ("AgentFlag".to_string(), "1".to_string()),
        ]);
        let merged = merge_windows_environment(&baseline, &overlay).unwrap();
        assert_eq!(
            merged.get("PATH").map(String::as_str),
            Some("C:\\Agent\\Bin")
        );
        assert!(!merged.contains_key("Path"));
        assert_eq!(
            merged.get("SystemRoot").map(String::as_str),
            Some("C:\\Windows")
        );
        assert_eq!(merged.get("AgentFlag").map(String::as_str), Some("1"));
    }

    #[test]
    fn windows_runtime_context_rejects_elevated_or_ambient_environment_claims() {
        let mut snapshot = WindowsRuntimeContextSnapshot {
            schema_version: 1,
            token_selection: "lua_medium_filtered".to_string(),
            execution_identity: "service".to_string(),
            session_id: None,
            token_user_sid: "S-1-5-21-test-1001".to_string(),
            token_type: 1,
            token_elevation_type: 2,
            token_is_elevated: false,
            token_integrity_level_rid: 8192,
            token_is_restricted: false,
            administrators_group_attributes: 0x10,
            environment: REQUIRED_WINDOWS_BASELINE_ENVIRONMENT_NAMES
                .iter()
                .map(|name| ((*name).to_string(), format!("value:{name}")))
                .collect(),
        };
        validate_windows_runtime_context(&snapshot, WindowsAuthority::Limited).unwrap();
        snapshot.token_is_elevated = true;
        assert!(validate_windows_runtime_context(&snapshot, WindowsAuthority::Limited).is_err());
        snapshot.token_is_elevated = false;
        snapshot
            .environment
            .insert("PNPM_HOME".to_string(), "C:\\pnpm".to_string());
        assert!(validate_windows_runtime_context(&snapshot, WindowsAuthority::Limited).is_err());
    }

    #[test]
    fn windows_runtime_context_requires_requested_elevated_authority_to_be_effective() {
        let environment: BTreeMap<String, String> = REQUIRED_WINDOWS_BASELINE_ENVIRONMENT_NAMES
            .iter()
            .map(|name| ((*name).to_string(), format!("value:{name}")))
            .collect();
        let mut elevated = WindowsRuntimeContextSnapshot {
            schema_version: 1,
            token_selection: "current_elevated".to_string(),
            execution_identity: "service".to_string(),
            session_id: None,
            token_user_sid: "S-1-5-21-test-1001".to_string(),
            token_type: 1,
            token_elevation_type: 2,
            token_is_elevated: true,
            token_integrity_level_rid: 12288,
            token_is_restricted: false,
            administrators_group_attributes: 0x0f,
            environment,
        };
        validate_windows_runtime_context(&elevated, WindowsAuthority::Elevated).unwrap();
        assert!(validate_windows_runtime_context(&elevated, WindowsAuthority::Limited).is_err());
        elevated.token_is_elevated = false;
        assert!(validate_windows_runtime_context(&elevated, WindowsAuthority::Elevated).is_err());
    }

    #[test]
    fn windows_runtime_context_requires_active_user_identity_and_session() {
        let environment: BTreeMap<String, String> = REQUIRED_WINDOWS_BASELINE_ENVIRONMENT_NAMES
            .iter()
            .map(|name| ((*name).to_string(), format!("value:{name}")))
            .collect();
        let mut active_user = WindowsRuntimeContextSnapshot {
            schema_version: 1,
            token_selection: "active_user".to_string(),
            execution_identity: "active_user".to_string(),
            session_id: Some(1),
            token_user_sid: "S-1-5-21-test-1001".to_string(),
            token_type: 1,
            token_elevation_type: 2,
            token_is_elevated: false,
            token_integrity_level_rid: 8192,
            token_is_restricted: false,
            administrators_group_attributes: 0x10,
            environment,
        };
        validate_windows_runtime_context(&active_user, WindowsAuthority::ActiveUser).unwrap();
        assert!(validate_windows_runtime_context(&active_user, WindowsAuthority::Limited).is_err());
        active_user.session_id = None;
        assert!(
            validate_windows_runtime_context(&active_user, WindowsAuthority::ActiveUser).is_err()
        );
        active_user.session_id = Some(1);
        active_user.execution_identity = "service".to_string();
        assert!(
            validate_windows_runtime_context(&active_user, WindowsAuthority::ActiveUser).is_err()
        );
    }

    #[test]
    fn active_user_launcher_contract_uses_broker_authority_and_user_identity() {
        let args = Vec::<String>::new();
        let environment = BTreeMap::new();
        let budget = ExecutionBudget::default();
        let mut spec = WindowsLauncherInvocationSpec {
            bundle: "C:\\ProgramData\\Ordivon\\attempts\\attempt-active-user",
            job_id: "job-active-user",
            attempt_id: "attempt-active-user",
            launch_token_digest:
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            request_digest:
                "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            job_name: "Ordivon.attempt-active-user",
            authority: WindowsAuthority::ActiveUser,
            expected_user_sid: Some("S-1-5-21-test-1001"),
            expected_session_id: Some(1),
            executable: "C:\\Windows\\System32\\whoami.exe",
            args: &args,
            cwd: "C:\\Windows\\System32",
            environment: &environment,
            input_source_root: None,
            input_set_id: None,
            input_presentation_root: None,
            input_bindings_digest: None,
            budget: &budget,
            timeout_ms: 30_000,
            stdout_limit_bytes: 4096,
            stderr_limit_bytes: 4096,
            emit_launcher_start: false,
        };
        let mut command = Command::new("/native/Ordivon.WindowsJobLauncher.exe");
        append_windows_launcher_arguments(&mut command, &spec).unwrap();
        let observed = command
            .get_args()
            .map(|arg| arg.to_string_lossy().into_owned())
            .collect::<Vec<_>>();
        let authority = observed
            .windows(2)
            .any(|pair| pair == ["--authority", "elevated"]);
        let identity = observed
            .windows(2)
            .any(|pair| pair == ["--identity", "active_user"]);
        let expected_sid = observed
            .windows(2)
            .any(|pair| pair == ["--expected-user-sid", "S-1-5-21-test-1001"]);
        let expected_session = observed
            .windows(2)
            .any(|pair| pair == ["--expected-session-id", "1"]);
        assert!(
            authority,
            "active_user must use the existing elevated broker transport"
        );
        assert!(
            identity,
            "active_user target identity must be explicit to the launcher"
        );
        assert!(
            expected_sid,
            "active_user must bind the admission-frozen user SID"
        );
        assert!(
            expected_session,
            "active_user must bind the admission-frozen Windows session"
        );
        assert!(
            !observed.iter().any(|arg| arg == "active_user"
                && observed
                    .windows(2)
                    .any(|pair| pair == ["--authority", "active_user"])),
            "active_user must not be passed as a launcher authority"
        );

        spec.expected_session_id = None;
        let mut missing_fence = Command::new("/native/Ordivon.WindowsJobLauncher.exe");
        let error = append_windows_launcher_arguments(&mut missing_fence, &spec).unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::RegistryCorrupt);
        assert_eq!(
            error.field.as_deref(),
            Some("windowsExecutionContext.sessionId")
        );
    }

    #[test]
    fn launcher_argument_contract_is_independent_from_systemd_transport() {
        let args = vec!["--literal=$HOME".to_string(), "a b".to_string()];
        let environment = BTreeMap::from([("AgentFlag".to_string(), "1".to_string())]);
        let budget = ExecutionBudget {
            memory_max_bytes: Some(268_435_456),
            tasks_max: Some(3),
            cpu_quota_percent: Some(50),
        };
        let spec = WindowsLauncherInvocationSpec {
            bundle: "C:\\ProgramData\\Ordivon\\attempts\\attempt-1",
            job_id: "job-1",
            attempt_id: "attempt-1",
            launch_token_digest:
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            request_digest:
                "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            job_name: "Ordivon.attempt-1",
            authority: WindowsAuthority::Limited,
            expected_user_sid: None,
            expected_session_id: None,
            executable: "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            args: &args,
            cwd: "C:\\Work",
            environment: &environment,
            input_source_root: None,
            input_set_id: None,
            input_presentation_root: None,
            input_bindings_digest: None,
            budget: &budget,
            timeout_ms: 30_000,
            stdout_limit_bytes: 4096,
            stderr_limit_bytes: 4096,
            emit_launcher_start: false,
        };
        let mut command = Command::new("/native/Ordivon.WindowsJobLauncher.exe");
        append_windows_launcher_arguments(&mut command, &spec).unwrap();
        let observed = command
            .get_args()
            .map(|arg| arg.to_string_lossy().into_owned())
            .collect::<Vec<_>>();
        assert_eq!(
            observed,
            vec![
                "--runtime-bundle",
                "C:\\ProgramData\\Ordivon\\attempts\\attempt-1",
                "--runtime-job-id",
                "job-1",
                "--runtime-attempt-id",
                "attempt-1",
                "--runtime-launch-token-digest",
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "--runtime-request-digest",
                "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "--job-name",
                "Ordivon.attempt-1",
                "--authority",
                "limited",
                "--timeout-ms",
                "30000",
                "--stdout-limit-bytes",
                "4096",
                "--stderr-limit-bytes",
                "4096",
                "--executable",
                "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "--cwd",
                "C:\\Work",
                "--inherit-environment",
                "false",
                "--env",
                "AgentFlag=1",
                "--memory-max-bytes",
                "268435456",
                "--active-process-limit",
                "3",
                "--cpu-quota-percent",
                "50",
                "--",
                "--literal=$HOME",
                "a b",
            ]
        );
    }
    #[test]
    fn deadline_owner_termination_receipt_is_identity_bound_and_replay_safe() {
        let terminated = br#"{"schemaVersion":1,"processId":42,"expectedProcessCreationTimeFileTime":123,"observedProcessCreationTimeFileTime":123,"disposition":"terminated"}"#;
        assert_eq!(
            parse_windows_deadline_owner_termination(terminated, 42, 123).unwrap(),
            WindowsDeadlineOwnerTerminationDisposition::Terminated
        );

        let absent = br#"{"schemaVersion":1,"processId":42,"expectedProcessCreationTimeFileTime":123,"disposition":"already_absent"}"#;
        assert_eq!(
            parse_windows_deadline_owner_termination(absent, 42, 123).unwrap(),
            WindowsDeadlineOwnerTerminationDisposition::AlreadyAbsent
        );

        let mismatch = br#"{"schemaVersion":1,"processId":42,"expectedProcessCreationTimeFileTime":123,"observedProcessCreationTimeFileTime":456,"disposition":"identity_mismatch"}"#;
        assert_eq!(
            parse_windows_deadline_owner_termination(mismatch, 42, 123).unwrap(),
            WindowsDeadlineOwnerTerminationDisposition::IdentityMismatch
        );

        let invalid = br#"{"schemaVersion":1,"processId":42,"expectedProcessCreationTimeFileTime":123,"observedProcessCreationTimeFileTime":123,"disposition":"identity_mismatch"}"#;
        assert_eq!(
            parse_windows_deadline_owner_termination(invalid, 42, 123)
                .unwrap_err()
                .code,
            RuntimeErrorCode::LaunchIdentityMismatch
        );
    }

    #[test]
    fn launcher_start_evidence_is_explicit_opt_in() {
        let args = Vec::<String>::new();
        let environment = BTreeMap::new();
        let budget = ExecutionBudget::default();
        let spec = WindowsLauncherInvocationSpec {
            bundle: "C:\\ProgramData\\Ordivon\\attempts\\attempt-2",
            job_id: "job-2",
            attempt_id: "attempt-2",
            launch_token_digest:
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            request_digest:
                "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            job_name: "Ordivon.attempt-2",
            authority: WindowsAuthority::Limited,
            expected_user_sid: None,
            expected_session_id: None,
            executable: "C:\\Windows\\System32\\cmd.exe",
            args: &args,
            cwd: "C:\\Work",
            environment: &environment,
            input_source_root: None,
            input_set_id: None,
            input_presentation_root: None,
            input_bindings_digest: None,
            budget: &budget,
            timeout_ms: 1000,
            stdout_limit_bytes: 1024,
            stderr_limit_bytes: 1024,
            emit_launcher_start: true,
        };
        let mut command = Command::new("/native/Ordivon.WindowsJobLauncher.exe");
        append_windows_launcher_arguments(&mut command, &spec).unwrap();
        let observed = command
            .get_args()
            .map(|arg| arg.to_string_lossy().into_owned())
            .collect::<Vec<_>>();
        assert_eq!(
            observed
                .iter()
                .filter(|arg| arg.as_str() == "--emit-launcher-start")
                .count(),
            1
        );
    }

    #[test]
    fn windows_exec_payload_uses_utf16_create_process_boundary() {
        let executable = r"C:\Windows\System32\cmd.exe";
        let env = BTreeMap::new();
        validate_windows_exec_payload(executable, &[], &env, "execution").unwrap();

        let oversized = vec!["x".repeat(WINDOWS_CREATE_PROCESS_COMMAND_LINE_LIMIT_UTF16)];
        let error =
            validate_windows_exec_payload(executable, &oversized, &env, "execution").unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
        assert_eq!(error.field.as_deref(), Some("execution"));
        assert!(error.message.contains("CreateProcessW limit"));
    }

    #[test]
    fn windows_exec_payload_counts_unicode_and_launcher_quoting() {
        assert_eq!(
            checked_windows_quoted_argument_utf16_len("plain", "execution").unwrap(),
            5
        );
        assert_eq!(
            checked_windows_quoted_argument_utf16_len("", "execution").unwrap(),
            2
        );
        assert_eq!(
            checked_windows_quoted_argument_utf16_len("a b", "execution").unwrap(),
            5
        );
        assert_eq!(
            checked_windows_quoted_argument_utf16_len("😀", "execution").unwrap(),
            2
        );
        // QuoteWindowsArgument emits opening/closing quotes, doubles the backslash before the
        // embedded quote, and preserves the quoted character itself.
        assert_eq!(
            checked_windows_quoted_argument_utf16_len("a\\\"b", "execution").unwrap(),
            8
        );
    }

    #[test]
    fn windows_exec_payload_rejects_oversized_environment_entry() {
        let executable = r"C:\Windows\System32\cmd.exe";
        let env = BTreeMap::from([(
            "ORDIVON_TEST".to_string(),
            "x".repeat(WINDOWS_ENVIRONMENT_VARIABLE_LIMIT_UTF16),
        )]);
        let error = validate_windows_exec_payload(executable, &[], &env, "execution").unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
        assert_eq!(error.field.as_deref(), Some("execution"));
        assert!(error.message.contains("per-variable limit"));
    }
}
