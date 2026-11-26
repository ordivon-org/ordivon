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
#[cfg(test)]
use super::windows_authorization::{
    validate_windows_elevated_principals, WINDOWS_PRIVILEGED_PROFILE_NAMESPACE,
    WINDOWS_PRIVILEGED_PROFILE_TYPE,
};
#[cfg(windows)]
use super::windows_broker;
use super::windows_broker::WindowsPrivilegedBrokerConfig;
#[cfg(test)]
use super::{ForeignReference, WindowsElevatedCommandProfile, WindowsElevatedExecutionProfile};

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
    /// Authenticated Runtime principals allowed to request an elevated Windows payload token.
    ///
    /// This is operator-owned admission authority. Callers choose a requested Windows context,
    /// but cannot widen this set through tool arguments or foreign references. An empty set fails
    /// closed for all new generic elevated Windows Jobs while preserving limited execution.
    pub elevated_principals: Vec<String>,
    /// Operator-owned privileged-effect profiles for new elevated Windows admissions.
    ///
    /// Agent-authored foreignReferences may select one profile by id, but cannot create or widen
    /// a profile.  The profile binds both principal authority and the exact executable/argument
    /// surface allowed to receive an elevated token.
    pub elevated_profiles: Vec<super::windows_authorization::WindowsElevatedExecutionProfile>,
    /// Operator-owned owner-native maintenance lease. While one valid unexpired lease exists,
    /// Runtime rejects every new Windows execution admission; exact Job replay is resolved before
    /// this policy so an already-admitted maintenance owner can reconnect safely.
    pub maintenance_lease_path: Option<PathBuf>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct WindowsCredentialMaterializationObservation {
    pub binding: String,
    pub disposition: String,
    pub endpoint_count: u32,
    pub bytes: u64,
}

pub fn materialize_windows_credential_binding(
    broker: &WindowsPrivilegedBrokerConfig,
    request_id: &str,
    binding: &str,
) -> RuntimeResult<WindowsCredentialMaterializationObservation> {
    #[cfg(not(windows))]
    {
        let _ = (broker, request_id, binding);
        Err(RuntimeError::new(
            RuntimeErrorCode::ToolUnavailable,
            "Windows credential materialization is available only on a native Windows Runtime",
            Some("credentialMaterialization"),
            false,
        ))
    }
    #[cfg(windows)]
    {
        let observed = windows_broker::materialize(broker, request_id, binding)?;
        Ok(WindowsCredentialMaterializationObservation {
            binding: observed.binding,
            disposition: observed.disposition,
            endpoint_count: observed.endpoint_count,
            bytes: observed.bytes,
        })
    }
}

impl WindowsExecutionConfig {
    pub(crate) fn validate(&self) -> RuntimeResult<()> {
        super::windows_authorization::validate_configuration(self)?;
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
    pub payload_privilege: super::WindowsPayloadPrivilege,
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
    /// PG-only original Runtime process identity. Ordinary legacy jobs leave None.
    #[cfg(windows)]
    pub pg_terminal_peer_pid: Option<u32>,
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
    pub payload_privilege: super::WindowsPayloadPrivilege,
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
    pub pg_terminal_peer_pid: Option<u32>,
    pub emit_launcher_start: bool,
}

/// PG consumer affordance projection. Only the configured original launcher
/// and contexts supported by the selected product may be advertised. It is
/// not a dispatch authorization or a physical terminal witness.
#[cfg(windows)]
pub(crate) fn windows_pg_execution_target(
    config: &WindowsExecutionConfig,
    configured_runner: &Path,
    supported_contexts: &[super::WindowsExecutionContextRequest],
) -> RuntimeResult<serde_json::Value> {
    config.validate()?;
    let io = |err: std::io::Error| {
        RuntimeError::new(
            RuntimeErrorCode::IoError,
            format!("inspect Windows PG launcher: {err}"),
            Some("executionProvider"),
            false,
        )
    };
    let launcher = fs::canonicalize(&config.launcher_path).map_err(io)?;
    if fs::canonicalize(configured_runner).map_err(io)? != launcher {
        return Err(RuntimeError::invalid(
            "Windows PG launcher and configured runner differ",
            "executionProvider",
        ));
    }
    let digest = crate::universal::sha256_file(&launcher).map_err(|err| {
        RuntimeError::new(
            RuntimeErrorCode::IoError,
            err.to_string(),
            Some("executionProvider"),
            false,
        )
    })?;
    let contexts = supported_contexts
        .iter()
        .copied()
        .filter(|context| snapshot_windows_runtime_context_for(config, *context).is_ok())
        .collect::<Vec<_>>();
    Ok(windows_pg_target_projection(
        digest,
        &contexts,
        config.maintenance_lease_path.is_some(),
    ))
}

#[cfg(any(windows, test))]
fn windows_pg_target_projection(
    digest: String,
    contexts: &[super::WindowsExecutionContextRequest],
    maintenance_fence_configured: bool,
) -> serde_json::Value {
    let authorities = contexts
        .iter()
        .filter_map(|context| context.legacy_authority())
        .collect::<Vec<_>>();
    serde_json::json!({
        "target": "windows_native",
        "configured": true,
        "available": !contexts.is_empty(),
        "executionProfiles": ["trusted_local"],
        "structuredPlan": false,
        "immutableInputs": false,
        "hostDependencyCommitments": false,
        "windowsContexts": contexts,
        "windowsAuthorities": authorities,
        "windowsMaintenanceFenceConfigured": maintenance_fence_configured,
        "executionProvider": {"contract":"windows_native_launcher_v1","executableDigest":digest},
        "availabilityIssue": if contexts.is_empty() {Some("WINDOWS_CONTEXT_UNAVAILABLE")} else {None}
    })
}

#[cfg(test)]
mod windows_pg_projection_tests {
    use super::*;
    #[test]
    fn native_pg_projection_does_not_invent_contexts_or_linux_capability() {
        use crate::runtime::{
            WindowsExecutionContextRequest, WindowsExecutionIdentity, WindowsPayloadPrivilege,
        };
        let digest = format!("sha256:{}", "a".repeat(64));
        let unavailable = windows_pg_target_projection(digest.clone(), &[], false);
        assert_eq!(unavailable["available"], false);
        assert_eq!(
            unavailable["availabilityIssue"],
            "WINDOWS_CONTEXT_UNAVAILABLE"
        );
        assert_eq!(unavailable["windowsContexts"], serde_json::json!([]));
        let context = WindowsExecutionContextRequest::new(
            WindowsExecutionIdentity::ActiveUser,
            WindowsPayloadPrivilege::Limited,
        );
        let available = windows_pg_target_projection(digest.clone(), &[context], true);
        assert_eq!(available["available"], true);
        assert_eq!(available["target"], "windows_native");
        assert_eq!(available["windowsContexts"], serde_json::json!([context]));
        assert_eq!(available["executionProvider"]["executableDigest"], digest);
        assert_eq!(available["immutableInputs"], false);
        assert_eq!(available["structuredPlan"], false);
        assert_eq!(available["hostDependencyCommitments"], false);
    }
}

pub(crate) fn snapshot_windows_runtime_context_for(
    config: &WindowsExecutionConfig,
    context: super::WindowsExecutionContextRequest,
) -> RuntimeResult<WindowsRuntimeContextSnapshot> {
    snapshot_windows_runtime_context_for_with_transport(config, context)
        .map(|(snapshot, _)| snapshot)
}

pub(crate) fn snapshot_windows_runtime_context_for_with_transport(
    config: &WindowsExecutionConfig,
    context: super::WindowsExecutionContextRequest,
) -> RuntimeResult<(WindowsRuntimeContextSnapshot, Option<PathBuf>)> {
    config.validate()?;
    let authority = context.transport_authority();
    let launcher_identity = match context.identity {
        super::WindowsExecutionIdentity::ActiveUser => Some("active_user"),
        super::WindowsExecutionIdentity::Service => None,
    };
    let launcher_authority = match authority {
        WindowsAuthority::ActiveUser => "elevated",
        _ => authority.as_str(),
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
    if context.identity == super::WindowsExecutionIdentity::ActiveUser
        && context.privilege == super::WindowsPayloadPrivilege::Elevated
    {
        launcher_args.push("--payload-privilege".to_string());
        launcher_args.push("elevated".to_string());
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
    validate_windows_runtime_context_request(&snapshot, context)?;
    Ok((snapshot, output.transport))
}

fn validate_windows_runtime_context_request(
    snapshot: &WindowsRuntimeContextSnapshot,
    context: super::WindowsExecutionContextRequest,
) -> RuntimeResult<()> {
    let token_authority_valid = match (context.identity, context.privilege) {
        (super::WindowsExecutionIdentity::Service, crate::WindowsPayloadPrivilege::Limited) => {
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
        (super::WindowsExecutionIdentity::Service, super::WindowsPayloadPrivilege::Elevated) => {
            snapshot.token_is_elevated
                && snapshot.token_integrity_level_rid >= 12288
                && snapshot.administrators_group_attributes != u32::MAX
                && (snapshot.administrators_group_attributes & 0x4) != 0
                && (snapshot.administrators_group_attributes & 0x10) == 0
                && snapshot.token_selection == "current_elevated"
                && matches!(snapshot.execution_identity.as_str(), "" | "service")
        }
        (super::WindowsExecutionIdentity::ActiveUser, crate::WindowsPayloadPrivilege::Limited) => {
            !snapshot.token_is_elevated
                && snapshot.token_integrity_level_rid <= 8192
                && (snapshot.administrators_group_attributes == u32::MAX
                    || (snapshot.administrators_group_attributes & 0x4) == 0
                    || (snapshot.administrators_group_attributes & 0x10) != 0)
                && snapshot.token_selection == "active_user"
                && snapshot.execution_identity == "active_user"
                && snapshot.session_id.is_some()
        }
        (super::WindowsExecutionIdentity::ActiveUser, super::WindowsPayloadPrivilege::Elevated) => {
            snapshot.token_is_elevated
                && snapshot.token_integrity_level_rid >= 12288
                && snapshot.administrators_group_attributes != u32::MAX
                && (snapshot.administrators_group_attributes & 0x4) != 0
                && (snapshot.administrators_group_attributes & 0x10) == 0
                && matches!(snapshot.token_elevation_type, 1 | 2)
                && matches!(
                    snapshot.token_selection.as_str(),
                    "active_user_elevated_current" | "active_user_elevated_linked"
                )
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
                "Windows runtime context did not prove requested {} x {} context",
                context.identity.as_str(),
                context.privilege.as_str()
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

/// Keep Git's ownership protection enabled globally. Runtime has already frozen
/// this exact worktree in the Job, so only its active-user consumer may opt in
/// to the existing Git command-scope safe.directory primitive. No gitconfig
/// is written, no wildcard trust is granted, and service jobs are unaffected.
#[cfg(all(windows, feature = "postgres-registry-admission"))]
pub(crate) fn bind_pg_execution_context(
    config: &WindowsExecutionConfig,
    proposal: &super::JobRunProposal,
    plan: &mut super::RuntimeExecutionPlan,
) -> RuntimeResult<()> {
    use super::types::{WindowsExecutionContext, WindowsTokenClass};
    use super::{WindowsExecutionIdentity, WindowsPayloadPrivilege};
    super::authority_contract::AuthorityContract::ordinary(proposal)?
        .authorize_windows_elevation(&config.elevated_principals)?;
    config.authorize_new_proposal(proposal)?;
    let explicit = proposal.execution.windows_context;
    let context =
        explicit.unwrap_or_else(|| proposal.execution.windows_authority.canonical_context());
    if explicit.is_some() && !context.compatible_with_legacy(proposal.execution.windows_authority) {
        return Err(RuntimeError::invalid(
            "windowsContext conflicts with windowsAuthority",
            "execution.windowsContext",
        ));
    }
    let snapshot = snapshot_windows_runtime_context_for(config, context)?;
    let authority = context.transport_authority();
    let privileged_broker_digest = if authority == WindowsAuthority::Limited {
        None
    } else {
        config
            .privileged_broker
            .as_ref()
            .map(|broker| broker.executable_digest())
            .transpose()?
    };
    let (token_class, environment_source) = match (context.identity, context.privilege) {
        (WindowsExecutionIdentity::ActiveUser, _) => (
            WindowsTokenClass::ActiveUser,
            "windows_active_user_profile_allowlist_v1",
        ),
        (WindowsExecutionIdentity::Service, WindowsPayloadPrivilege::Elevated) => (
            WindowsTokenClass::Elevated,
            "windows_privileged_broker_profile_allowlist_v1",
        ),
        _ => (
            WindowsTokenClass::Limited,
            "windows_user_machine_profile_allowlist_v1",
        ),
    };
    plan.env = merge_windows_workspace_environment(
        &snapshot.environment,
        &proposal.execution.env,
        context.identity == WindowsExecutionIdentity::ActiveUser,
        Path::new(&plan.workspace_path),
    )?;
    plan.windows_authority = authority;
    plan.windows_context = explicit;
    plan.windows_execution_context = Some(WindowsExecutionContext {
        token_class,
        payload_identity: explicit.map(|context| context.identity),
        payload_privilege: explicit.map(|context| context.privilege),
        token_user_sid: snapshot.token_user_sid,
        session_id: snapshot.session_id,
        environment_source: environment_source.into(),
        privileged_broker_digest,
    });
    Ok(())
}

/// Bind the already prepared independent Git carrier to a normal PG Job.
/// The paths have been qualified by the native provider, not supplied by
/// the caller. This is execution identity, not a filesystem ACL or sandbox.
#[cfg(any(windows, test))]
pub(crate) fn bind_pg_private_git_environment(
    environment: &mut BTreeMap<String, String>,
    git_dir: &str,
    work_tree: &str,
) -> RuntimeResult<()> {
    // These redirects would replace the repository, index or object set
    // whose lifetime the existing Workspace open/close contract owns.
    const REDIRECTS: &[&str] = &[
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_QUARANTINE_PATH",
    ];
    if environment
        .keys()
        .any(|key| REDIRECTS.iter().any(|name| key.eq_ignore_ascii_case(name)))
    {
        return Err(RuntimeError::invalid(
            "Windows PG Git cannot redirect the prepared private repository",
            "execution.env",
        ));
    }
    for (key, expected) in [("GIT_DIR", git_dir), ("GIT_WORK_TREE", work_tree)] {
        if environment
            .iter()
            .any(|(name, actual)| name.eq_ignore_ascii_case(key) && actual != expected)
        {
            return Err(RuntimeError::invalid(
                format!("Windows PG {key} must match the prepared Workspace Git carrier"),
                "execution.env",
            ));
        }
    }
    for (key, expected) in [("GIT_DIR", git_dir), ("GIT_WORK_TREE", work_tree)] {
        environment.retain(|name, _| !name.eq_ignore_ascii_case(key));
        environment.insert(key.to_owned(), expected.to_owned());
    }
    Ok(())
}

pub(crate) fn merge_windows_workspace_environment(
    baseline: &BTreeMap<String, String>,
    overlay: &BTreeMap<String, String>,
    active_user: bool,
    workspace_path: &Path,
) -> RuntimeResult<BTreeMap<String, String>> {
    let mut environment = merge_windows_environment(baseline, overlay)?;
    if !active_user {
        return Ok(environment);
    }

    // Git reads protected safe.directory from system/global files as well
    // as command scope. Appending an exact workspace trust value cannot
    // cancel a wildcard loaded earlier via an alternative config file.
    // Keep the active-user token's observed profile/home as the only profile
    // input; ordinary service execution retains its own environment policy.
    const GIT_CONFIG_REDIRECTS: &[&str] = &[
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM",
        "XDG_CONFIG_HOME",
        "HOME",
    ];
    const PROFILE_OVERLAY_REDIRECTS: &[&str] = &[
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "APPDATA",
        "LOCALAPPDATA",
    ];
    if environment.keys().any(|name| {
        GIT_CONFIG_REDIRECTS
            .iter()
            .any(|blocked| name.eq_ignore_ascii_case(blocked))
    }) || overlay.keys().any(|name| {
        PROFILE_OVERLAY_REDIRECTS
            .iter()
            .any(|blocked| name.eq_ignore_ascii_case(blocked))
    }) {
        return Err(RuntimeError::invalid(
            "active_user Git trust cannot redirect Git config or token-derived profile",
            "execution.env",
        ));
    }

    let original = workspace_path.to_string_lossy();
    let visible = if let Some(path) = original.strip_prefix(r"\\?\UNC\") {
        format!(r"\\{path}")
    } else {
        original
            .strip_prefix(r"\\?\")
            .unwrap_or(&original)
            .to_string()
    };
    let windows_drive = visible.as_bytes().get(1) == Some(&b':')
        && visible
            .as_bytes()
            .first()
            .is_some_and(u8::is_ascii_alphabetic)
        && visible
            .as_bytes()
            .get(2)
            .is_some_and(|byte| *byte == b'\\' || *byte == b'/');
    let windows_unc = visible.strip_prefix(r"\\").is_some_and(|unc| {
        let mut parts = unc.split(['\\', '/']);
        let server = parts.next().unwrap_or("");
        let share = parts.next().unwrap_or("");
        let first_workspace_part = parts.next().unwrap_or("");
        !server.is_empty() && !share.is_empty() && !first_workspace_part.is_empty()
    });
    if (!windows_drive && !windows_unc)
        || visible
            .split(['/', '\\'])
            .any(|part| part == ".." || part == ".")
        || visible.contains('*')
        || visible.contains('?')
    {
        return Err(RuntimeError::invalid(
            "active_user Git trust requires an exact absolute Windows workspace path",
            "execution.cwdRelative",
        ));
    }

    let count = environment
        .iter()
        .find(|(key, _)| key.eq_ignore_ascii_case("GIT_CONFIG_COUNT"))
        .map(|(_, value)| value.as_str())
        .unwrap_or("0")
        .parse::<usize>()
        .map_err(|_| {
            RuntimeError::invalid("invalid Git command configuration count", "execution.env")
        })?;
    if count > 62 {
        return Err(RuntimeError::invalid(
            "Git command configuration exceeds bounded workspace environment",
            "execution.env",
        ));
    }
    // A previous command-scoped wildcard would defeat the exact-workspace
    // restriction even if Runtime appended its own narrower safe.directory.
    if environment
        .keys()
        .any(|name| name.eq_ignore_ascii_case("GIT_CONFIG_PARAMETERS"))
    {
        return Err(RuntimeError::invalid(
            "active_user Git trust cannot inherit arbitrary command parameters",
            "execution.env",
        ));
    }
    for index in 0..count {
        let config_name = format!("GIT_CONFIG_KEY_{index}");
        if environment.iter().any(|(name, value)| {
            name.eq_ignore_ascii_case(&config_name)
                && (value.eq_ignore_ascii_case("safe.directory")
                    || value.eq_ignore_ascii_case("include.path")
                    || (value.to_ascii_lowercase().starts_with("includeif.")
                        && value.to_ascii_lowercase().ends_with(".path")))
        }) {
            return Err(RuntimeError::invalid(
                "active_user Git trust cannot inherit a pre-existing safe.directory override",
                "execution.env",
            ));
        }
        for prefix in ["GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"] {
            let name = format!("{prefix}{index}");
            if !environment
                .keys()
                .any(|key| key.eq_ignore_ascii_case(&name))
            {
                return Err(RuntimeError::invalid(
                    "Git command configuration is missing an indexed key or value",
                    "execution.env",
                ));
            }
        }
    }
    // Git safe.directory is multi-valued: appending an exact path alone
    // does not revoke an inherited protected safe.directory=*. Git's
    // documented empty value resets that list. Force reset -> exact
    // workspace at the end of command-scope configuration, retaining any
    // unrelated caller keys only before the reset.
    for index in [count, count + 1] {
        let key = format!("GIT_CONFIG_KEY_{index}");
        let value = format!("GIT_CONFIG_VALUE_{index}");
        if environment.keys().any(|existing| {
            existing.eq_ignore_ascii_case(&key) || existing.eq_ignore_ascii_case(&value)
        }) {
            return Err(RuntimeError::invalid(
                "Git command configuration contains an unexpected indexed override",
                "execution.env",
            ));
        }
    }
    if let Some(existing) = environment
        .keys()
        .find(|name| name.eq_ignore_ascii_case("GIT_CONFIG_COUNT"))
        .cloned()
    {
        environment.remove(&existing);
    }
    environment.insert("GIT_CONFIG_COUNT".to_string(), (count + 2).to_string());
    environment.insert(
        format!("GIT_CONFIG_KEY_{count}"),
        "safe.directory".to_string(),
    );
    environment.insert(format!("GIT_CONFIG_VALUE_{count}"), String::new());
    environment.insert(
        format!("GIT_CONFIG_KEY_{}", count + 1),
        "safe.directory".to_string(),
    );
    environment.insert(format!("GIT_CONFIG_VALUE_{}", count + 1), visible);
    Ok(environment)
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
    let executable = windows_visible_path(spec.executable, "execution.executable")?;
    let cwd = windows_visible_path(spec.cwd, "execution.cwdRelative")?;
    let bundle = windows_visible_path(spec.bundle_path, "bundlePath")?;
    let input_source_root = spec
        .input_source_root
        .map(|source_root| windows_visible_path(source_root, "execution.effectiveInputs"))
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
        payload_privilege: spec.payload_privilege,
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
        pg_terminal_peer_pid: spec.pg_terminal_peer_pid,
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
        spec.payload_privilege,
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
        if spec.payload_privilege == super::WindowsPayloadPrivilege::Elevated {
            command.arg("--payload-privilege").arg("elevated");
        }
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
    if let Some(peer) = spec.pg_terminal_peer_pid {
        if peer == 0 {
            return Err(RuntimeError::invalid(
                "PG terminal peer process ID must be nonzero",
                "windows.pgTerminalPeerProcessId",
            ));
        }
        command
            .arg("--pg-terminal-peer-process-id")
            .arg(peer.to_string());
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

pub(crate) fn windows_visible_path(path: &Path, field: &str) -> RuntimeResult<String> {
    #[cfg(windows)]
    {
        if !path.is_absolute() {
            return Err(RuntimeError::invalid(
                "Windows-visible path source must be absolute",
                field,
            ));
        }
        // Win32 treats repeated separators and explicit current-directory components as
        // lexical aliases. Rebuild the path from std::path components before crossing the
        // native launcher/evidence boundary so an equivalent OS-rendered path cannot be
        // misclassified as a different execution identity. Do not canonicalize here:
        // canonicalization would consult filesystem/reparse-point state and would change the
        // meaning of the frozen path identity rather than only its lexical presentation.
        let normalized = path.components().collect::<PathBuf>();
        return normalized
            .to_str()
            .map(str::to_string)
            .ok_or_else(|| RuntimeError::invalid("Windows-visible path must be UTF-8", field));
    }
    #[cfg(not(windows))]
    {
        let _ = path;
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
    fn elevated_principal_authority_accepts_explicit_unique_principals() {
        validate_windows_elevated_principals(&[
            "principal:test-alpha".to_string(),
            "principal:test-beta".to_string(),
        ])
        .unwrap();
    }

    #[test]
    fn elevated_principal_authority_rejects_empty_whitespace_and_duplicates() {
        for principals in [
            vec!["".to_string()],
            vec!["principal:bad value".to_string()],
            vec!["principal:dup".to_string(), "principal:dup".to_string()],
        ] {
            let error = validate_windows_elevated_principals(&principals).unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
            assert_eq!(error.field.as_deref(), Some("windows.elevatedPrincipals"));
        }
    }

    #[test]
    fn windows_pg_private_git_binding_preserves_only_exact_case_insensitive_identity() {
        let work_tree = r"C:\Ordivon\workspaces\ws-one";
        let git_dir = r"C:\Ordivon\workspaces\.ws-one.agent-git";
        let mut environment = BTreeMap::from([
            ("git_dir".to_owned(), git_dir.to_owned()),
            ("Git_Work_Tree".to_owned(), work_tree.to_owned()),
            ("PATH".to_owned(), r"C:\Windows".to_owned()),
        ]);
        bind_pg_private_git_environment(&mut environment, git_dir, work_tree).unwrap();
        assert_eq!(environment["GIT_DIR"], git_dir);
        assert_eq!(environment["GIT_WORK_TREE"], work_tree);
        assert_eq!(environment.len(), 3);
        assert_eq!(environment["PATH"], r"C:\Windows");
        for key in [
            "git_dir",
            "Git_Work_Tree",
            "GIT_COMMON_DIR",
            "git_index_file",
            "GIT_OBJECT_DIRECTORY",
            "git_alternate_object_directories",
            "GIT_NAMESPACE",
            "GIT_QUARANTINE_PATH",
        ] {
            let mut conflicting = BTreeMap::from([(key.to_owned(), r"C:\other".to_owned())]);
            let before = conflicting.clone();
            assert!(bind_pg_private_git_environment(&mut conflicting, git_dir, work_tree).is_err());
            assert_eq!(conflicting, before);
        }
    }

    #[test]
    fn windows_active_user_git_workspace_trust_is_exact_and_job_local() {
        let baseline = BTreeMap::from([("Path".to_string(), r"C:\Windows".to_string())]);
        let overlay = BTreeMap::new();
        let env = merge_windows_workspace_environment(
            &baseline,
            &overlay,
            true,
            Path::new(r"\\?\C:\ProgramData\Ordivon\workspaces\ws-1"),
        )
        .unwrap();
        assert_eq!(env["GIT_CONFIG_COUNT"], "2");
        assert_eq!(env["GIT_CONFIG_KEY_0"], "safe.directory");
        assert_eq!(env["GIT_CONFIG_VALUE_0"], ""); // clears earlier protected wildcard
        assert_eq!(env["GIT_CONFIG_KEY_1"], "safe.directory");
        assert_eq!(
            env["GIT_CONFIG_VALUE_1"],
            r"C:\ProgramData\Ordivon\workspaces\ws-1"
        );
        assert!(!env.values().any(|value| value == "*"));
        assert!(!baseline.contains_key("GIT_CONFIG_COUNT"));
    }

    #[test]
    fn windows_git_workspace_environment_preserves_existing_git_command_config() {
        let overlay = BTreeMap::from([
            ("GIT_CONFIG_COUNT".to_string(), "1".to_string()),
            ("GIT_CONFIG_KEY_0".to_string(), "color.ui".to_string()),
            ("GIT_CONFIG_VALUE_0".to_string(), "never".to_string()),
        ]);
        let env = merge_windows_workspace_environment(
            &BTreeMap::new(),
            &overlay,
            true,
            Path::new(r"C:\Ordivon\workspaces\ws-2"),
        )
        .unwrap();
        assert_eq!(env["GIT_CONFIG_COUNT"], "3");
        assert_eq!(env["GIT_CONFIG_KEY_0"], "color.ui");
        assert_eq!(env["GIT_CONFIG_VALUE_0"], "never");
        assert_eq!(env["GIT_CONFIG_KEY_1"], "safe.directory");
        assert_eq!(env["GIT_CONFIG_VALUE_1"], "");
        assert_eq!(env["GIT_CONFIG_KEY_2"], "safe.directory");
        assert_eq!(env["GIT_CONFIG_VALUE_2"], r"C:\Ordivon\workspaces\ws-2");

        let service = merge_windows_workspace_environment(
            &BTreeMap::new(),
            &BTreeMap::new(),
            false,
            Path::new(r"C:\Ordivon\workspaces\ws-2"),
        )
        .unwrap();
        assert!(!service.contains_key("GIT_CONFIG_COUNT"));
    }

    #[test]
    fn windows_git_workspace_environment_fails_closed_on_inconsistent_config() {
        for overlay in [
            BTreeMap::from([("GIT_CONFIG_COUNT".to_string(), "1".to_string())]),
            BTreeMap::from([("GIT_CONFIG_COUNT".to_string(), "-1".to_string())]),
            BTreeMap::from([("GIT_CONFIG_COUNT".to_string(), "999999".to_string())]),
        ] {
            let error = merge_windows_workspace_environment(
                &BTreeMap::new(),
                &overlay,
                true,
                Path::new(r"C:\Ordivon\workspaces\ws-2"),
            )
            .unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
        }
    }

    #[test]
    fn windows_git_workspace_environment_rejects_incomplete_or_wildcard_trust() {
        for path in [
            r"\\",
            r"\\server\",
            r"\\server\share\",
            r"\\?\UNC\server\",
            r"C:\ProgramData\Ordivon\..\workspaces",
            r"C:\ProgramData\Ordivon\ws*",
            r"C:\ProgramData\Ordivon\ws?",
            "relative/workspaces/ws-1",
        ] {
            let error = merge_windows_workspace_environment(
                &BTreeMap::new(),
                &BTreeMap::new(),
                true,
                Path::new(path),
            )
            .unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::InvalidRequest, "{path}");
        }
    }

    #[test]
    fn windows_git_workspace_environment_rejects_preexisting_wildcard_command_trust() {
        let baseline = BTreeMap::from([
            ("GIT_CONFIG_COUNT".to_string(), "1".to_string()),
            ("GIT_CONFIG_KEY_0".to_string(), "safe.directory".to_string()),
            ("GIT_CONFIG_VALUE_0".to_string(), "*".to_string()),
        ]);
        let error = merge_windows_workspace_environment(
            &baseline,
            &BTreeMap::new(),
            true,
            Path::new(r"C:\Ordivon\workspaces\ws-2"),
        )
        .unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
    }

    #[test]
    fn windows_active_user_git_workspace_trust_rejects_external_config_redirection() {
        // Git's native protected safe.directory wildcard is still effective
        // when a narrower command-scoped safe.directory is appended later.
        // A caller-controlled alternate config file must never be mistaken
        // for this Job's exact-only workspace trust.
        for key in ["GIT_CONFIG_GLOBAL", "git_config_system"] {
            let overlay = BTreeMap::from([(
                key.to_string(),
                r"C:\Agent\attacker-global.gitconfig".to_string(),
            )]);
            let error = merge_windows_workspace_environment(
                &BTreeMap::new(),
                &overlay,
                true,
                Path::new(r"C:\Ordivon\workspaces\ws-2"),
            )
            .unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::InvalidRequest, "{key}");
            assert_eq!(error.field.as_deref(), Some("execution.env"));
        }
        // Ambient or caller-supplied Git include/config paths can load an
        // earlier protected safe.directory=* entry. Appending the scoped
        // workspace value does not undo that wildcard.
        for name in ["HOME", "xdg_config_home", "USERPROFILE"] {
            let overlay = BTreeMap::from([(
                name.to_string(),
                r"C:\Agent\alternative-profile".to_string(),
            )]);
            let error = merge_windows_workspace_environment(
                &BTreeMap::new(),
                &overlay,
                true,
                Path::new(r"C:\Ordivon\workspaces\ws-2"),
            )
            .unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::InvalidRequest, "{name}");
            assert_eq!(error.field.as_deref(), Some("execution.env"));
        }
        for key in ["include.path", "includeIf.gitdir:/.path"] {
            let overlay = BTreeMap::from([
                ("GIT_CONFIG_COUNT".to_string(), "1".to_string()),
                ("GIT_CONFIG_KEY_0".to_string(), key.to_string()),
                (
                    "GIT_CONFIG_VALUE_0".to_string(),
                    r"C:\Agent\attacker-global.gitconfig".to_string(),
                ),
            ]);
            let error = merge_windows_workspace_environment(
                &BTreeMap::new(),
                &overlay,
                true,
                Path::new(r"C:\Ordivon\workspaces\ws-2"),
            )
            .unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::InvalidRequest, "{key}");
        }
        // Context-specific guarantee: a service payload is not silently
        // rewritten into active_user Git trust.
        let service = merge_windows_workspace_environment(
            &BTreeMap::new(),
            &BTreeMap::from([(
                "GIT_CONFIG_GLOBAL".to_string(),
                r"C:\Agent\allowed-for-service.gitconfig".to_string(),
            )]),
            false,
            Path::new(r"C:\Ordivon\workspaces\ws-2"),
        )
        .unwrap();
        assert!(!service.contains_key("GIT_CONFIG_COUNT"));
    }

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
    fn windows_git_workspace_trust_reserves_bounded_reset_and_exact_slots() {
        // A valid 62-entry caller prefix leaves precisely two Git-native
        // command scope slots: an empty reset and one exact Workspace path.
        let mut overlay = BTreeMap::from([("GIT_CONFIG_COUNT".to_string(), "62".to_string())]);
        for index in 0..62 {
            overlay.insert(format!("GIT_CONFIG_KEY_{index}"), "color.ui".to_string());
            overlay.insert(format!("GIT_CONFIG_VALUE_{index}"), "never".to_string());
        }
        let workspace = Path::new(r"C:\Ordivon\workspaces\ws-2");
        let permitted =
            merge_windows_workspace_environment(&BTreeMap::new(), &overlay, true, workspace)
                .unwrap();
        assert_eq!(permitted["GIT_CONFIG_COUNT"], "64");
        assert_eq!(permitted["GIT_CONFIG_KEY_62"], "safe.directory");
        assert_eq!(permitted["GIT_CONFIG_VALUE_62"], "");
        assert_eq!(permitted["GIT_CONFIG_KEY_63"], "safe.directory");
        assert_eq!(
            permitted["GIT_CONFIG_VALUE_63"],
            r"C:\Ordivon\workspaces\ws-2"
        );

        overlay.insert("GIT_CONFIG_COUNT".to_string(), "63".to_string());
        overlay.insert("GIT_CONFIG_KEY_62".to_string(), "color.ui".to_string());
        overlay.insert("GIT_CONFIG_VALUE_62".to_string(), "never".to_string());
        let error =
            merge_windows_workspace_environment(&BTreeMap::new(), &overlay, true, workspace)
                .unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
        assert_eq!(error.field.as_deref(), Some("execution.env"));
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
        validate_windows_runtime_context_request(
            &snapshot,
            WindowsAuthority::Limited.canonical_context(),
        )
        .unwrap();
        snapshot.token_is_elevated = true;
        assert!(validate_windows_runtime_context_request(
            &snapshot,
            WindowsAuthority::Limited.canonical_context()
        )
        .is_err());
        snapshot.token_is_elevated = false;
        snapshot
            .environment
            .insert("PNPM_HOME".to_string(), "C:\\pnpm".to_string());
        assert!(validate_windows_runtime_context_request(
            &snapshot,
            WindowsAuthority::Limited.canonical_context()
        )
        .is_err());
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
        validate_windows_runtime_context_request(
            &elevated,
            WindowsAuthority::Elevated.canonical_context(),
        )
        .unwrap();
        assert!(validate_windows_runtime_context_request(
            &elevated,
            WindowsAuthority::Limited.canonical_context()
        )
        .is_err());
        elevated.token_is_elevated = false;
        assert!(validate_windows_runtime_context_request(
            &elevated,
            WindowsAuthority::Elevated.canonical_context()
        )
        .is_err());
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
        validate_windows_runtime_context_request(
            &active_user,
            WindowsAuthority::ActiveUser.canonical_context(),
        )
        .unwrap();
        assert!(validate_windows_runtime_context_request(
            &active_user,
            WindowsAuthority::Limited.canonical_context()
        )
        .is_err());
        active_user.session_id = None;
        assert!(validate_windows_runtime_context_request(
            &active_user,
            WindowsAuthority::ActiveUser.canonical_context()
        )
        .is_err());
        active_user.session_id = Some(1);
        active_user.execution_identity = "service".to_string();
        assert!(validate_windows_runtime_context_request(
            &active_user,
            WindowsAuthority::ActiveUser.canonical_context()
        )
        .is_err());
    }

    #[test]
    fn windows_runtime_context_proves_active_user_elevated_as_a_distinct_fourth_cell() {
        let environment: BTreeMap<String, String> = REQUIRED_WINDOWS_BASELINE_ENVIRONMENT_NAMES
            .iter()
            .map(|name| ((*name).to_string(), format!("value:{name}")))
            .collect();
        let requested = super::super::WindowsExecutionContextRequest::new(
            super::super::WindowsExecutionIdentity::ActiveUser,
            super::super::WindowsPayloadPrivilege::Elevated,
        );
        let mut snapshot = WindowsRuntimeContextSnapshot {
            schema_version: 1,
            token_selection: "active_user_elevated_linked".to_string(),
            execution_identity: "active_user".to_string(),
            session_id: Some(7),
            token_user_sid: "S-1-5-21-test-1001".to_string(),
            token_type: 1,
            token_elevation_type: 2,
            token_is_elevated: true,
            token_integrity_level_rid: 12288,
            token_is_restricted: false,
            administrators_group_attributes: 0x4,
            environment,
        };
        validate_windows_runtime_context_request(&snapshot, requested).unwrap();

        snapshot.token_is_elevated = false;
        assert!(validate_windows_runtime_context_request(&snapshot, requested).is_err());
        snapshot.token_is_elevated = true;
        snapshot.token_integrity_level_rid = 8192;
        assert!(validate_windows_runtime_context_request(&snapshot, requested).is_err());
        snapshot.token_integrity_level_rid = 12288;
        snapshot.administrators_group_attributes = 0x10;
        assert!(validate_windows_runtime_context_request(&snapshot, requested).is_err());
        snapshot.administrators_group_attributes = 0x4;
        snapshot.session_id = None;
        assert!(validate_windows_runtime_context_request(&snapshot, requested).is_err());
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
            payload_privilege: crate::WindowsPayloadPrivilege::Limited,
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
            pg_terminal_peer_pid: None,
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

        spec.payload_privilege = crate::WindowsPayloadPrivilege::Elevated;
        let mut elevated = Command::new("/native/Ordivon.WindowsJobLauncher.exe");
        append_windows_launcher_arguments(&mut elevated, &spec).unwrap();
        let elevated_args = elevated
            .get_args()
            .map(|arg| arg.to_string_lossy().into_owned())
            .collect::<Vec<_>>();
        assert!(
            elevated_args
                .windows(2)
                .any(|pair| pair == ["--payload-privilege", "elevated"]),
            "active_user x elevated must explicitly bind elevated payload privilege"
        );
        assert!(elevated_args
            .windows(2)
            .any(|pair| pair == ["--authority", "elevated"]));
        assert!(elevated_args
            .windows(2)
            .any(|pair| pair == ["--identity", "active_user"]));

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
            scheduling: None,
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
            payload_privilege: crate::WindowsPayloadPrivilege::Limited,
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
            pg_terminal_peer_pid: None,
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
    #[cfg(windows)]
    #[test]
    fn windows_visible_path_normalizes_equivalent_repeated_separators() {
        let repeated = Path::new(r"C:\\Windows\\System32\\cmd.exe");
        let canonical = Path::new(r"C:\Windows\System32\cmd.exe");

        let repeated = windows_visible_path(repeated, "execution.executable").unwrap();
        let canonical = windows_visible_path(canonical, "execution.executable").unwrap();

        assert_eq!(repeated, canonical);
        assert_eq!(canonical, r"C:\Windows\System32\cmd.exe");
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
        let mut spec = WindowsLauncherInvocationSpec {
            bundle: "C:\\ProgramData\\Ordivon\\attempts\\attempt-2",
            job_id: "job-2",
            attempt_id: "attempt-2",
            launch_token_digest:
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            request_digest:
                "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            job_name: "Ordivon.attempt-2",
            authority: WindowsAuthority::Limited,
            payload_privilege: crate::WindowsPayloadPrivilege::Limited,
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
            pg_terminal_peer_pid: None,
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
        // The actual PG parent holds the original process handle and writes
        // windows-launcher-start.json. It MUST NOT enable the competing
        // Launcher self-writer merely to obtain the native drain gate.
        spec.emit_launcher_start = false;
        spec.pg_terminal_peer_pid = Some(12345);
        let mut pg_command = Command::new("/native/Ordivon.WindowsJobLauncher.exe");
        append_windows_launcher_arguments(&mut pg_command, &spec).unwrap();
        let pg_arguments = pg_command
            .get_args()
            .map(|arg| arg.to_string_lossy().into_owned())
            .collect::<Vec<_>>();
        assert!(!pg_arguments
            .iter()
            .any(|arg| arg == "--emit-launcher-start"));
        assert!(pg_arguments
            .windows(2)
            .any(|pair| pair[0] == "--pg-terminal-peer-process-id" && pair[1] == "12345"));
        spec.pg_terminal_peer_pid = Some(0);
        assert_eq!(
            append_windows_launcher_arguments(&mut Command::new("launcher"), &spec)
                .unwrap_err()
                .code,
            RuntimeErrorCode::InvalidRequest
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

#[cfg(test)]
mod privileged_profile_tests {
    use super::*;
    use crate::runtime::{
        ExecutionProfile, ExecutionProposal, ExecutionStepProposal, ExecutionTarget,
        JobRunProposal, WindowsAuthority,
    };
    use std::collections::BTreeMap;

    fn profile_ref(id: &str) -> ForeignReference {
        ForeignReference {
            namespace: WINDOWS_PRIVILEGED_PROFILE_NAMESPACE.to_string(),
            reference_type: WINDOWS_PRIVILEGED_PROFILE_TYPE.to_string(),
            id: id.to_string(),
            generation: None,
            digest: None,
        }
    }

    fn proposal(
        executable: &str,
        args: &[&str],
        references: Vec<ForeignReference>,
    ) -> JobRunProposal {
        JobRunProposal {
            schema_version: 1,
            client_request_id: "privileged-profile-test".to_string(),
            principal: "principal:windows-main".to_string(),
            global_limit: 4,
            execution: ExecutionProposal {
                workspace_id: "workspace-profile-test".to_string(),
                executable: executable.to_string(),
                args: args.iter().map(|value| (*value).to_string()).collect(),
                cwd_relative: ".".to_string(),
                env: BTreeMap::new(),
                timeout_ms: Some(1_000),
                stdout_limit_bytes: Some(4_096),
                stderr_limit_bytes: Some(4_096),
                steps: Vec::new(),
                budget: ExecutionBudget::default(),
                execution_profile: ExecutionProfile::TrustedLocal,
                execution_target: ExecutionTarget::WindowsNative,
                windows_authority: WindowsAuthority::Elevated,
                windows_context: None,
                foreign_references: references,
                host_dependencies: Vec::new(),
            },
            wait_ms: 0,
            stdout_tail_bytes: 0,
            stderr_tail_bytes: 0,
        }
    }

    fn config() -> WindowsExecutionConfig {
        WindowsExecutionConfig {
            launcher_path: PathBuf::from("/bin/true"),
            privileged_broker: None,
            elevated_principals: vec!["principal:windows-main".to_string()],
            elevated_profiles: vec![WindowsElevatedExecutionProfile {
                id: "workstation.d-drive-compact-r3".to_string(),
                principals: vec!["principal:windows-main".to_string()],
                commands: vec![WindowsElevatedCommandProfile {
                    executable: r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
                        .to_string(),
                    argument_prefix: vec![
                        "-NoProfile".to_string(),
                        "-NonInteractive".to_string(),
                        "-ExecutionPolicy".to_string(),
                        "Bypass".to_string(),
                        "-File".to_string(),
                        r"D:\OrdivonStudio\d-drive-compact-run-r3.ps1".to_string(),
                    ],
                    allow_additional_arguments: false,
                }],
            }],
            maintenance_lease_path: None,
        }
    }

    #[test]
    fn elevated_windows_requires_privileged_profile_reference() {
        let error = config()
            .authorize_elevated_proposal(&proposal(
                r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                &["-Command", "Write-Output unsafe"],
                Vec::new(),
            ))
            .unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::AuthorizationDenied);
    }

    #[test]
    fn matching_provider_profile_allows_only_bound_entrypoint() {
        let reference = profile_ref("workstation.d-drive-compact-r3");
        config()
            .authorize_elevated_proposal(&proposal(
                r"c:\windows\system32\windowspowershell\v1.0\powershell.exe",
                &[
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    r"D:\OrdivonStudio\d-drive-compact-run-r3.ps1",
                ],
                vec![reference.clone()],
            ))
            .unwrap();
        let error = config()
            .authorize_elevated_proposal(&proposal(
                r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                &["-Command", "Optimize-VHD -Path arbitrary.vhdx -Mode Full"],
                vec![reference],
            ))
            .unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::AuthorizationDenied);
    }

    #[test]
    fn profile_principal_and_all_structured_steps_are_enforced() {
        let reference = profile_ref("workstation.d-drive-compact-r3");
        let mut denied_principal = proposal(
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            &[
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                r"D:\OrdivonStudio\d-drive-compact-run-r3.ps1",
            ],
            vec![reference.clone()],
        );
        denied_principal.principal = "principal:other".to_string();
        assert_eq!(
            config()
                .authorize_elevated_proposal(&denied_principal)
                .unwrap_err()
                .code,
            RuntimeErrorCode::AuthorizationDenied
        );

        let mut extra_step = proposal(
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            &[
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                r"D:\OrdivonStudio\d-drive-compact-run-r3.ps1",
            ],
            vec![reference],
        );
        extra_step.execution.steps.push(ExecutionStepProposal {
            id: "escape".to_string(),
            executable: r"C:\Windows\System32\cmd.exe".to_string(),
            args: vec!["/c".to_string(), "whoami".to_string()],
            cwd_relative: ".".to_string(),
            env: BTreeMap::new(),
            timeout_ms: Some(1_000),
            continue_on_error: false,
        });
        assert_eq!(
            config()
                .authorize_elevated_proposal(&extra_step)
                .unwrap_err()
                .code,
            RuntimeErrorCode::AuthorizationDenied
        );
    }
    #[test]
    fn active_maintenance_lease_fences_all_new_windows_execution() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-windows-maintenance-lease-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(&root).unwrap();
        let lease = root.join("active-request.json");
        fs::write(
            &lease,
            serde_json::json!({
                "schemaVersion": 3,
                "kind": "ordivon.d-drive-compact-request",
                "maintenanceId": "cap-test-active",
                "expiresAtUtc": "2099-01-01T00:00:00Z",
                "expiresAtUnixMs": (std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis() as u64) + 300_000,
                "transactionDir": "D:\\OrdivonStudio\\maintenance\\cap-test-active"
            })
            .to_string(),
        )
        .unwrap();
        let mut cfg = config();
        cfg.maintenance_lease_path = Some(lease.clone());
        let mut limited = proposal(
            r"C:\Windows\System32\cmd.exe",
            &["/c", "echo", "ok"],
            Vec::new(),
        );
        limited.execution.windows_authority = WindowsAuthority::Limited;
        assert_eq!(
            cfg.authorize_new_proposal(&limited).unwrap_err().code,
            RuntimeErrorCode::AuthorizationDenied
        );

        fs::write(
            &lease,
            serde_json::json!({
                "schemaVersion": 3,
                "kind": "ordivon.d-drive-compact-request",
                "maintenanceId": "cap-test-expired",
                "expiresAtUtc": "2000-01-01T00:00:00Z",
                "expiresAtUnixMs": 1
            })
            .to_string(),
        )
        .unwrap();
        cfg.authorize_new_proposal(&limited).unwrap();
        fs::remove_dir_all(root).unwrap();
    }
}
