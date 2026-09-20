#[cfg(windows)]
use std::path::Path;
use std::path::PathBuf;

#[cfg(windows)]
use serde::{Deserialize, Serialize};

use super::{RuntimeError, RuntimeErrorCode, RuntimeResult};
use crate::universal::sha256_file;

#[cfg(windows)]
const BROKER_SCHEMA_VERSION: u32 = 1;
#[cfg(windows)]
const MAX_BROKER_MESSAGE_BYTES: usize = 256 * 1024;
#[cfg(windows)]
const MAX_BROKER_CAPTURE_BYTES: usize = 64 * 1024;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WindowsPrivilegedBrokerConfig {
    pub executable_path: PathBuf,
    pub pipe_name: String,
}

impl WindowsPrivilegedBrokerConfig {
    pub(crate) fn validate_shape(&self) -> RuntimeResult<()> {
        if !self.executable_path.is_absolute() {
            return Err(RuntimeError::invalid(
                "Windows privileged broker path must be absolute",
                "windows.privilegedBrokerPath",
            ));
        }
        if self.pipe_name.is_empty()
            || self.pipe_name.len() > 128
            || !self
                .pipe_name
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
        {
            return Err(RuntimeError::invalid(
                "Windows privileged broker pipe name must contain only ASCII alphanumeric, '.', '_' or '-' and be at most 128 bytes",
                "windows.privilegedBrokerPipe",
            ));
        }
        Ok(())
    }

    pub(crate) fn executable_digest(&self) -> RuntimeResult<String> {
        self.validate_shape()?;
        let metadata = std::fs::symlink_metadata(&self.executable_path).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::IoError,
                format!("inspect Windows privileged broker: {error}"),
                Some("windows.privilegedBrokerPath"),
                false,
            )
        })?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(RuntimeError::invalid(
                "Windows privileged broker must be a non-symlink executable file",
                "windows.privilegedBrokerPath",
            ));
        }
        sha256_file(&self.executable_path).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::IoError,
                format!("digest Windows privileged broker: {error}"),
                Some("windows.privilegedBrokerPath"),
                false,
            )
        })
    }

    pub(crate) fn verify_digest(&self, expected: &str) -> RuntimeResult<()> {
        let observed = self.executable_digest()?;
        if observed != expected {
            return Err(RuntimeError::new(
                RuntimeErrorCode::LaunchIdentityMismatch,
                format!(
                    "Windows privileged broker digest changed after admission: expected {expected}, observed {observed}"
                ),
                Some("windowsExecutionContext.privilegedBrokerDigest"),
                false,
            ));
        }
        Ok(())
    }
}

#[cfg(windows)]
#[derive(Clone, Debug)]
pub(crate) struct BrokerCapture {
    pub exit_code: i32,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
}

#[cfg(windows)]
#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct BrokerRequest<'a> {
    schema_version: u32,
    request_id: &'a str,
    operation: &'a str,
    #[serde(skip_serializing_if = "Option::is_none")]
    launcher_args: Option<&'a [String]>,
    #[serde(skip_serializing_if = "Option::is_none")]
    launcher_stderr_path: Option<&'a str>,
}

#[cfg(windows)]
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct BrokerResponse {
    schema_version: u32,
    request_id: String,
    ok: bool,
    #[serde(default)]
    operation: Option<String>,
    #[serde(default)]
    exit_code: Option<i32>,
    #[serde(default)]
    stdout: Option<String>,
    #[serde(default)]
    stderr: Option<String>,
    #[serde(default)]
    process_id: Option<u32>,
    #[serde(default)]
    process_creation_time_file_time: Option<u64>,
    #[serde(default)]
    error_code: Option<String>,
    #[serde(default)]
    error_message: Option<String>,
}

#[cfg(windows)]
fn invoke(
    config: &WindowsPrivilegedBrokerConfig,
    request: &BrokerRequest<'_>,
) -> RuntimeResult<BrokerResponse> {
    use std::io::Write;
    use std::process::{Command, Stdio};

    config.validate_shape()?;
    let expected_request_id = request.request_id.to_string();
    let request_bytes = serde_json::to_vec(request).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            format!("serialize Windows privileged broker request: {error}"),
            Some("windows.privilegedBroker"),
            false,
        )
    })?;
    if request_bytes.len() > MAX_BROKER_MESSAGE_BYTES {
        return Err(RuntimeError::invalid(
            "Windows privileged broker request exceeded bounded size",
            "windows.privilegedBroker",
        ));
    }

    let mut child = Command::new(&config.executable_path)
        .arg("--client")
        .arg("--pipe-name")
        .arg(&config.pipe_name)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::ToolFailed,
                format!("start Windows privileged broker client: {error}"),
                Some("windows.privilegedBroker"),
                true,
            )
        })?;
    child
        .stdin
        .take()
        .ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::ToolFailed,
                "Windows privileged broker client stdin was unavailable",
                Some("windows.privilegedBroker"),
                true,
            )
        })?
        .write_all(&request_bytes)
        .map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::ToolFailed,
                format!("write Windows privileged broker request: {error}"),
                Some("windows.privilegedBroker"),
                true,
            )
        })?;
    let output = child.wait_with_output().map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::ToolFailed,
            format!("wait for Windows privileged broker client: {error}"),
            Some("windows.privilegedBroker"),
            true,
        )
    })?;
    if output.stdout.len() > MAX_BROKER_MESSAGE_BYTES
        || output.stderr.len() > MAX_BROKER_CAPTURE_BYTES
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            "Windows privileged broker client output exceeded bounded size",
            Some("windows.privilegedBroker"),
            false,
        ));
    }
    if !output.status.success() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ToolFailed,
            format!(
                "Windows privileged broker client failed: {}",
                String::from_utf8_lossy(&output.stderr).trim()
            ),
            Some("windows.privilegedBroker"),
            true,
        ));
    }
    let response: BrokerResponse = serde_json::from_slice(&output.stdout).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            format!("invalid Windows privileged broker response: {error}"),
            Some("windows.privilegedBroker"),
            false,
        )
    })?;
    if response.schema_version != BROKER_SCHEMA_VERSION
        || response.request_id != expected_request_id
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::LaunchIdentityMismatch,
            "Windows privileged broker response identity did not match request",
            Some("windows.privilegedBroker"),
            false,
        ));
    }
    if !response.ok {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ToolFailed,
            format!(
                "Windows privileged broker rejected request: {}: {}",
                response.error_code.as_deref().unwrap_or("BROKER_ERROR"),
                response.error_message.as_deref().unwrap_or("no detail")
            ),
            Some("windows.privilegedBroker"),
            true,
        ));
    }
    Ok(response)
}

#[cfg(windows)]
pub(crate) fn capture(
    config: &WindowsPrivilegedBrokerConfig,
    expected_digest: Option<&str>,
    request_id: &str,
    launcher_args: &[String],
) -> RuntimeResult<BrokerCapture> {
    if let Some(expected) = expected_digest {
        config.verify_digest(expected)?;
    } else {
        let _ = config.executable_digest()?;
    }
    let response = invoke(
        config,
        &BrokerRequest {
            schema_version: BROKER_SCHEMA_VERSION,
            request_id,
            operation: "capture",
            launcher_args: Some(launcher_args),
            launcher_stderr_path: None,
        },
    )?;
    if response.operation.as_deref() != Some("capture")
        || response.exit_code.is_none()
        || response.process_id.is_some()
        || response.process_creation_time_file_time.is_some()
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::LaunchIdentityMismatch,
            "Windows privileged broker capture response shape was inconsistent",
            Some("windows.privilegedBroker"),
            false,
        ));
    }
    let stdout = response.stdout.unwrap_or_default().into_bytes();
    let stderr = response.stderr.unwrap_or_default().into_bytes();
    if stdout.len() > MAX_BROKER_CAPTURE_BYTES || stderr.len() > MAX_BROKER_CAPTURE_BYTES {
        return Err(RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            "Windows privileged broker capture payload exceeded bounded size",
            Some("windows.privilegedBroker"),
            false,
        ));
    }
    Ok(BrokerCapture {
        exit_code: response.exit_code.unwrap_or(125),
        stdout,
        stderr,
    })
}

#[cfg(windows)]
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct BrokerSpawnObservation {
    pub launcher_process_id: u32,
    pub launcher_process_creation_time_file_time: u64,
}

#[cfg(windows)]
pub(crate) fn spawn(
    config: &WindowsPrivilegedBrokerConfig,
    expected_digest: &str,
    request_id: &str,
    launcher_args: &[String],
    launcher_stderr_path: &Path,
) -> RuntimeResult<BrokerSpawnObservation> {
    config.verify_digest(expected_digest)?;
    let launcher_stderr_path = launcher_stderr_path.to_str().ok_or_else(|| {
        RuntimeError::invalid(
            "Windows launcher stderr carrier path must be UTF-8 for privileged broker transport",
            "windows.launcherStderr",
        )
    })?;
    let response = invoke(
        config,
        &BrokerRequest {
            schema_version: BROKER_SCHEMA_VERSION,
            request_id,
            operation: "spawn",
            launcher_args: Some(launcher_args),
            launcher_stderr_path: Some(launcher_stderr_path),
        },
    )?;
    let process_id = response.process_id.unwrap_or(0);
    let creation = response.process_creation_time_file_time.unwrap_or(0);
    if response.operation.as_deref() != Some("spawn")
        || process_id == 0
        || creation == 0
        || response.exit_code.is_some()
        || response.stdout.is_some()
        || response.stderr.is_some()
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::LaunchIdentityMismatch,
            "Windows privileged broker spawn response shape was inconsistent",
            Some("windows.privilegedBroker"),
            false,
        ));
    }
    Ok(BrokerSpawnObservation {
        launcher_process_id: process_id,
        launcher_process_creation_time_file_time: creation,
    })
}

#[cfg(test)]
mod tests {
    use super::WindowsPrivilegedBrokerConfig;
    use std::path::PathBuf;

    #[test]
    fn broker_pipe_name_is_fail_closed() {
        let valid = WindowsPrivilegedBrokerConfig {
            executable_path: PathBuf::from(if cfg!(windows) {
                r"C:\ProgramData\Ordivon\broker.exe"
            } else {
                "/mnt/c/ProgramData/Ordivon/broker.exe"
            }),
            pipe_name: "Ordivon.Runtime.Privileged.R1".to_string(),
        };
        valid.validate_shape().unwrap();

        for invalid in ["", r"\\.\pipe\escape", "has space", "semi;colon"] {
            let mut candidate = valid.clone();
            candidate.pipe_name = invalid.to_string();
            assert!(candidate.validate_shape().is_err());
        }
    }
}
