use std::fs;
use std::fs::OpenOptions;
use std::io::Read;
#[cfg(unix)]
use std::os::unix::fs::OpenOptionsExt;
use std::path::Path;

use crate::universal::sha256_bytes;

use super::job_attempt_state::JobIdentityContract;
use super::{
    runtime_release_effect_id, runtime_release_request_identity_digest, validate_client_request_id,
    ArtifactReadRequest, ArtifactRegistration, AttemptState, ExecutionProfile,
    ExecutionProviderContract, ExecutionTarget, JobResolution, RuntimeError, RuntimeErrorCode,
    RuntimeReleaseContract, RuntimeReleaseDisposition, RuntimeReleaseEffectBinding,
    RuntimeReleaseRequest, RuntimeResult, SubmitRequest, WindowsAuthority, WindowsTokenClass,
    MAX_ARTIFACT_READ_BYTES, RUNTIME_RELEASE_IDENTITY_PREFIX, RUNTIME_SCHEMA_VERSION,
};

pub(crate) struct ArtifactStateContract;

impl ArtifactStateContract {
    pub(crate) fn validate_registration(artifact: &ArtifactRegistration) -> RuntimeResult<()> {
        validate_identifier(&artifact.artifact_id, "artifactId")?;
        validate_identifier(&artifact.kind, "artifact.kind")?;
        validate_sha256(&artifact.digest, "artifact.digest")?;
        if artifact.relative_path.is_empty()
            || Path::new(&artifact.relative_path).is_absolute()
            || artifact
                .relative_path
                .split('/')
                .any(|segment| segment == "..")
        {
            return Err(RuntimeError::invalid(
                "Artifact path must be a bounded relative path",
                "artifact.relativePath",
            ));
        }
        if artifact.media_type.is_empty() || artifact.media_type.len() > 256 {
            return Err(RuntimeError::invalid(
                "Artifact mediaType must be non-empty and bounded",
                "artifact.mediaType",
            ));
        }
        Ok(())
    }

    pub(crate) fn validate_read_request(request: &ArtifactReadRequest) -> RuntimeResult<()> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(RuntimeError::invalid(
                "unsupported runtime schema version",
                "schemaVersion",
            ));
        }
        if request.max_bytes == 0 || request.max_bytes > MAX_ARTIFACT_READ_BYTES {
            return Err(RuntimeError::invalid(
                format!("maxBytes must be in 1..={MAX_ARTIFACT_READ_BYTES}"),
                "maxBytes",
            ));
        }
        Ok(())
    }
}

pub(crate) struct ReleaseStateContract;

impl ReleaseStateContract {
    pub(crate) fn validate_request(request: &RuntimeReleaseRequest) -> RuntimeResult<()> {
        if request.schema_version != RUNTIME_SCHEMA_VERSION {
            return Err(RuntimeError::invalid(
                "unsupported runtime schema version",
                "schemaVersion",
            ));
        }
        validate_client_request_id(&request.client_request_id, "clientRequestId")?;
        if request.expected_tool_count == 0 {
            return Err(RuntimeError::invalid(
                "Runtime Release expectedToolCount must be positive",
                "expectedToolCount",
            ));
        }
        if !is_lower_hex(&request.commit, 40) {
            return Err(RuntimeError::invalid(
                "Runtime Release commit must be exactly 40 lowercase hexadecimal characters",
                "commit",
            ));
        }
        validate_sha256_lowercase(
            &request.candidate_manifest_digest,
            "candidateManifestDigest",
            "candidate manifest digest must use sha256",
            "candidate manifest digest must contain 64 lowercase hexadecimal characters",
        )
    }

    pub(crate) fn validate_binding_matches_request(
        binding: &RuntimeReleaseEffectBinding,
        request: &RuntimeReleaseRequest,
    ) -> RuntimeResult<()> {
        let expected_request_digest = runtime_release_request_identity_digest(request)?;
        let expected_effect_id = runtime_release_effect_id(request);
        if binding.contract != RuntimeReleaseContract::RuntimeReleaseV1
            || binding.effect_id != expected_effect_id
            || binding.request_digest != expected_request_digest
            || binding.workspace_id != request.workspace_id
            || binding.commit != request.commit
            || binding.candidate_manifest_digest != request.candidate_manifest_digest
            || binding.expected_tool_count != request.expected_tool_count
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "stored Runtime Release side truth does not match the request identity",
                Some("runtimeReleaseEffect"),
                false,
            ));
        }
        Ok(())
    }

    pub(crate) fn validate_committed_binding(
        release: &RuntimeReleaseEffectBinding,
        request: &SubmitRequest,
    ) -> RuntimeResult<()> {
        if release.contract != RuntimeReleaseContract::RuntimeReleaseV1 {
            return Err(RuntimeError::invalid(
                "unsupported Runtime Release contract",
                "runtimeReleaseEffect.contract",
            ));
        }
        if !is_lower_hex(&release.effect_id, 64) {
            return Err(RuntimeError::invalid(
                "Runtime Release effectId must be 64 lowercase hexadecimal characters",
                "runtimeReleaseEffect.effectId",
            ));
        }
        if !release
            .request_digest
            .starts_with(RUNTIME_RELEASE_IDENTITY_PREFIX)
        {
            return Err(RuntimeError::invalid(
                "Runtime Release request digest has the wrong contract prefix",
                "runtimeReleaseEffect.requestDigest",
            ));
        }
        JobIdentityContract::validate_request_identity_digest(&release.request_digest)?;
        if request.request_identity_digest.as_deref() != Some(release.request_digest.as_str()) {
            return Err(RuntimeError::invalid(
                "Runtime Release side truth must match the committed request identity",
                "runtimeReleaseEffect.requestDigest",
            ));
        }
        if release.workspace_id != request.plan.workspace_id {
            return Err(RuntimeError::invalid(
                "Runtime Release workspace does not match the execution plan",
                "runtimeReleaseEffect.workspaceId",
            ));
        }
        if !is_lower_hex(&release.commit, 40) {
            return Err(RuntimeError::invalid(
                "Runtime Release commit must be exactly 40 lowercase hexadecimal characters",
                "runtimeReleaseEffect.commit",
            ));
        }
        validate_sha256(
            &release.candidate_manifest_digest,
            "runtimeReleaseEffect.candidateManifestDigest",
        )?;
        if !Path::new(&release.receipt_path).is_absolute()
            || release.receipt_path.as_bytes().contains(&0)
        {
            return Err(RuntimeError::invalid(
                "Runtime Release receipt path must be absolute and NUL-free",
                "runtimeReleaseEffect.receiptPath",
            ));
        }
        if request.plan.execution_profile != ExecutionProfile::TrustedLocal {
            return Err(RuntimeError::invalid(
                "Runtime Release v1 requires trusted_local execution",
                "runtimeReleaseEffect.contract",
            ));
        }
        match request.plan.execution_target {
            ExecutionTarget::LocalLinux => {
                if request.plan.windows_authority != WindowsAuthority::Limited
                    || request.plan.windows_execution_context.is_some()
                {
                    return Err(RuntimeError::invalid(
                        "local Linux Runtime Release cannot carry Windows elevated authority",
                        "plan.windowsAuthority",
                    ));
                }
                if !matches!(
                    request
                        .execution_provider
                        .as_ref()
                        .map(|provider| provider.contract),
                    Some(ExecutionProviderContract::LocalLinuxRunnerV1)
                ) {
                    return Err(RuntimeError::invalid(
                        "local Linux Runtime Release requires a committed local Linux Runner",
                        "executionProvider",
                    ));
                }
            }
            ExecutionTarget::WindowsNative => {
                if request.plan.windows_authority != WindowsAuthority::Elevated {
                    return Err(RuntimeError::invalid(
                        "native Windows Runtime Release requires elevated authority",
                        "plan.windowsAuthority",
                    ));
                }
                if !matches!(
                    request
                        .execution_provider
                        .as_ref()
                        .map(|provider| provider.contract),
                    Some(ExecutionProviderContract::WindowsNativeLauncherV1)
                ) {
                    return Err(RuntimeError::invalid(
                        "native Windows Runtime Release requires a committed Windows launcher",
                        "executionProvider",
                    ));
                }
                let context = request
                    .plan
                    .windows_execution_context
                    .as_ref()
                    .ok_or_else(|| {
                        RuntimeError::invalid(
                        "native Windows Runtime Release requires frozen elevated execution context",
                        "plan.windowsExecutionContext",
                    )
                    })?;
                if context.token_class != WindowsTokenClass::Elevated
                    || context.environment_source
                        != "windows_privileged_broker_profile_allowlist_v1"
                {
                    return Err(RuntimeError::invalid(
                        "native Windows Runtime Release requires privileged broker execution context",
                        "plan.windowsExecutionContext",
                    ));
                }
                let broker_digest =
                    context.privileged_broker_digest.as_deref().ok_or_else(|| {
                        RuntimeError::invalid(
                        "native Windows Runtime Release requires a frozen privileged broker digest",
                        "plan.windowsExecutionContext.privilegedBrokerDigest",
                    )
                    })?;
                validate_sha256(
                    broker_digest,
                    "plan.windowsExecutionContext.privilegedBrokerDigest",
                )?;
            }
        }
        Ok(())
    }

    pub(crate) fn inspect_receipt(
        binding: &RuntimeReleaseEffectBinding,
        job_resolution: Option<JobResolution>,
        attempt_state: Option<AttemptState>,
    ) -> RuntimeResult<ReleaseReceiptProjection> {
        let receipt = Path::new(&binding.receipt_path);
        let directory = match fs::symlink_metadata(receipt) {
            Ok(metadata) => Some(metadata),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => None,
            Err(_) => {
                return Ok(ReleaseReceiptProjection::reconciliation(
                    "RELEASE_RECEIPT_DIRECTORY_UNAVAILABLE",
                ));
            }
        };
        let Some(directory) = directory else {
            return if job_resolution.is_none() {
                Ok(ReleaseReceiptProjection::unresolved(attempt_state))
            } else {
                Ok(ReleaseReceiptProjection::reconciliation(
                    "RELEASE_RECEIPT_MISSING_AFTER_JOB_TERMINAL",
                ))
            };
        };
        if directory.file_type().is_symlink() || !directory.is_dir() {
            return Ok(ReleaseReceiptProjection::reconciliation(
                "RELEASE_RECEIPT_DIRECTORY_UNSAFE",
            ));
        }

        let effect_request = match release_receipt_json(&receipt.join("effect-request.json")) {
            Ok(Some((value, _))) => value,
            Ok(None) if job_resolution.is_none() => {
                return Ok(ReleaseReceiptProjection::unresolved(attempt_state));
            }
            Ok(None) => {
                return Ok(ReleaseReceiptProjection::reconciliation(
                    "RELEASE_EFFECT_REQUEST_MISSING_AFTER_JOB_TERMINAL",
                ));
            }
            Err(issue) => return Ok(ReleaseReceiptProjection::reconciliation(&issue)),
        };
        if !release_effect_json_matches(&effect_request, binding) {
            return Ok(ReleaseReceiptProjection::reconciliation(
                "RELEASE_EFFECT_REQUEST_MISMATCH",
            ));
        }

        let result = match release_receipt_json(&receipt.join("result.json")) {
            Ok(Some(value)) => value,
            Ok(None) if job_resolution.is_none() => {
                return Ok(ReleaseReceiptProjection::unresolved(attempt_state));
            }
            Ok(None) => {
                return Ok(ReleaseReceiptProjection::reconciliation(
                    "RELEASE_RESULT_MISSING_AFTER_JOB_TERMINAL",
                ));
            }
            Err(issue) => return Ok(ReleaseReceiptProjection::reconciliation(&issue)),
        };
        let (result, result_digest) = result;
        if result.get("commit").and_then(|value| value.as_str()) != Some(binding.commit.as_str())
            || !result
                .get("releaseEffect")
                .is_some_and(|value| release_effect_json_matches(value, binding))
        {
            return Ok(ReleaseReceiptProjection::reconciliation(
                "RELEASE_RESULT_MISMATCH",
            ));
        }

        let rollback = match release_receipt_json(&receipt.join("rollback-result.json")) {
            Ok(Some((value, _))) => value
                .get("status")
                .and_then(|status| status.as_str())
                .map(str::to_string),
            Ok(None) => None,
            Err(issue) => return Ok(ReleaseReceiptProjection::reconciliation(&issue)),
        };
        if rollback.as_deref() == Some("restored_previous") {
            return Ok(ReleaseReceiptProjection {
                disposition: RuntimeReleaseDisposition::RolledBack,
                terminal: true,
                available: true,
                digest: Some(result_digest),
                deployed_tool_count: result
                    .pointer("/probe/toolCount")
                    .and_then(|value| value.as_u64())
                    .and_then(|value| u32::try_from(value).ok()),
                tool_catalog_digest: result
                    .pointer("/probe/toolCatalogDigest")
                    .and_then(|value| value.as_str())
                    .map(str::to_string),
                rollback_status: rollback,
                issue: None,
            });
        }

        let status = result.get("status").and_then(|value| value.as_str());
        let deployed_tool_count = result
            .pointer("/probe/toolCount")
            .and_then(|value| value.as_u64())
            .and_then(|value| u32::try_from(value).ok());
        let tool_catalog_digest = result
            .pointer("/probe/toolCatalogDigest")
            .and_then(|value| value.as_str())
            .map(str::to_string);
        if status == Some("deployed") && deployed_tool_count != Some(binding.expected_tool_count) {
            return Ok(ReleaseReceiptProjection::reconciliation(
                "RELEASE_RESULT_TOOL_COUNT_MISMATCH",
            ));
        }
        let (disposition, terminal, issue) = match status {
            Some("deployed") => (RuntimeReleaseDisposition::Deployed, true, None),
            Some("not_committed") => (RuntimeReleaseDisposition::NotCommitted, true, None),
            Some("rolled_back") => (RuntimeReleaseDisposition::RolledBack, true, None),
            Some("rollback_failed") => (
                RuntimeReleaseDisposition::ReconciliationRequired,
                false,
                Some("RELEASE_ROLLBACK_FAILED".to_string()),
            ),
            Some("reconciliation_required") => (
                RuntimeReleaseDisposition::ReconciliationRequired,
                false,
                Some(
                    result
                        .get("reconciliationIssue")
                        .and_then(|value| value.as_str())
                        .unwrap_or("RELEASE_RECONCILIATION_REQUIRED")
                        .to_string(),
                ),
            ),
            Some("recovery_failed") => (
                RuntimeReleaseDisposition::ReconciliationRequired,
                false,
                Some("RELEASE_RECOVERY_FAILED".to_string()),
            ),
            _ => (
                RuntimeReleaseDisposition::ReconciliationRequired,
                false,
                Some("RELEASE_RESULT_STATUS_UNKNOWN".to_string()),
            ),
        };
        Ok(ReleaseReceiptProjection {
            disposition,
            terminal,
            available: true,
            digest: Some(result_digest),
            deployed_tool_count,
            tool_catalog_digest,
            rollback_status: rollback,
            issue,
        })
    }
}

const MAX_RUNTIME_RELEASE_RECEIPT_BYTES: u64 = 1_048_576;

pub(crate) struct ReleaseReceiptProjection {
    pub(crate) disposition: RuntimeReleaseDisposition,
    pub(crate) terminal: bool,
    pub(crate) available: bool,
    pub(crate) digest: Option<String>,
    pub(crate) deployed_tool_count: Option<u32>,
    pub(crate) tool_catalog_digest: Option<String>,
    pub(crate) rollback_status: Option<String>,
    pub(crate) issue: Option<String>,
}

impl ReleaseReceiptProjection {
    fn unresolved(attempt_state: Option<AttemptState>) -> Self {
        let admitted = attempt_state.is_some_and(|state| state == AttemptState::Accepted);
        Self {
            disposition: if admitted {
                RuntimeReleaseDisposition::Admitted
            } else {
                RuntimeReleaseDisposition::InProgress
            },
            terminal: false,
            available: false,
            digest: None,
            deployed_tool_count: None,
            tool_catalog_digest: None,
            rollback_status: None,
            issue: None,
        }
    }

    fn reconciliation(issue: &str) -> Self {
        Self {
            disposition: RuntimeReleaseDisposition::ReconciliationRequired,
            terminal: false,
            available: false,
            digest: None,
            deployed_tool_count: None,
            tool_catalog_digest: None,
            rollback_status: None,
            issue: Some(issue.to_string()),
        }
    }
}

#[cfg(unix)]
fn open_regular_file_nofollow(path: &Path) -> std::io::Result<std::fs::File> {
    OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)
}

#[cfg(windows)]
fn open_regular_file_nofollow(path: &Path) -> std::io::Result<std::fs::File> {
    use std::os::windows::fs::{MetadataExt, OpenOptionsExt};

    const FILE_FLAG_OPEN_REPARSE_POINT: u32 = 0x0020_0000;
    const FILE_ATTRIBUTE_DIRECTORY: u32 = 0x0000_0010;
    const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x0000_0400;

    let file = OpenOptions::new()
        .read(true)
        .custom_flags(FILE_FLAG_OPEN_REPARSE_POINT)
        .open(path)?;
    let metadata = file.metadata()?;
    let attributes = metadata.file_attributes();
    if !metadata.is_file()
        || attributes & FILE_ATTRIBUTE_DIRECTORY != 0
        || attributes & FILE_ATTRIBUTE_REPARSE_POINT != 0
    {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "secure receipt open requires a regular non-reparse file",
        ));
    }
    Ok(file)
}

#[cfg(not(any(unix, windows)))]
fn open_regular_file_nofollow(_path: &Path) -> std::io::Result<std::fs::File> {
    Err(std::io::Error::new(
        std::io::ErrorKind::Unsupported,
        "secure no-follow regular-file open is not implemented for this platform",
    ))
}

fn release_receipt_json(path: &Path) -> Result<Option<(serde_json::Value, String)>, String> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(_) => return Err("RELEASE_RECEIPT_METADATA_UNAVAILABLE".to_string()),
    };
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        return Err("RELEASE_RECEIPT_FILE_UNSAFE".to_string());
    }
    if metadata.len() > MAX_RUNTIME_RELEASE_RECEIPT_BYTES {
        return Err("RELEASE_RECEIPT_FILE_TOO_LARGE".to_string());
    }
    let mut file =
        open_regular_file_nofollow(path).map_err(|_| "RELEASE_RECEIPT_OPEN_FAILED".to_string())?;
    let mut bytes = Vec::new();
    std::io::Read::by_ref(&mut file)
        .take(MAX_RUNTIME_RELEASE_RECEIPT_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| "RELEASE_RECEIPT_READ_FAILED".to_string())?;
    if bytes.len() as u64 > MAX_RUNTIME_RELEASE_RECEIPT_BYTES {
        return Err("RELEASE_RECEIPT_FILE_TOO_LARGE".to_string());
    }
    let value = serde_json::from_slice::<serde_json::Value>(&bytes)
        .map_err(|_| "RELEASE_RECEIPT_JSON_INVALID".to_string())?;
    if !value.is_object() {
        return Err("RELEASE_RECEIPT_JSON_INVALID".to_string());
    }
    Ok(Some((value, sha256_bytes(&bytes))))
}

fn release_effect_json_matches(
    value: &serde_json::Value,
    binding: &RuntimeReleaseEffectBinding,
) -> bool {
    let Some(object) = value.as_object() else {
        return false;
    };
    object.get("contract").and_then(|value| value.as_str()) == Some("runtime_release_v1")
        && object.get("effectId").and_then(|value| value.as_str())
            == Some(binding.effect_id.as_str())
        && object.get("requestDigest").and_then(|value| value.as_str())
            == Some(binding.request_digest.as_str())
        && object.get("commit").and_then(|value| value.as_str()) == Some(binding.commit.as_str())
        && object
            .get("candidateManifestDigest")
            .and_then(|value| value.as_str())
            == Some(binding.candidate_manifest_digest.as_str())
        && object
            .get("expectedToolCount")
            .and_then(|value| value.as_u64())
            == Some(u64::from(binding.expected_tool_count))
}

fn validate_identifier(value: &str, field: &str) -> RuntimeResult<()> {
    if value.trim().is_empty()
        || value.len() > 256
        || value.as_bytes().contains(&0)
        || value.chars().any(char::is_control)
    {
        return Err(RuntimeError::invalid(
            format!("{field} must be non-empty, bounded, and control-free"),
            field,
        ));
    }
    Ok(())
}

fn validate_sha256(value: &str, field: &str) -> RuntimeResult<()> {
    let valid = value
        .strip_prefix("sha256:")
        .is_some_and(|hex| hex.len() == 64 && hex.bytes().all(|byte| byte.is_ascii_hexdigit()));
    if !valid {
        return Err(RuntimeError::invalid(
            format!("{field} must be a SHA-256 digest"),
            field,
        ));
    }
    Ok(())
}

fn validate_sha256_lowercase(
    value: &str,
    field: &str,
    prefix_message: &str,
    body_message: &str,
) -> RuntimeResult<()> {
    let hex = value
        .strip_prefix("sha256:")
        .ok_or_else(|| RuntimeError::invalid(prefix_message, field))?;
    if !is_lower_hex(hex, 64) {
        return Err(RuntimeError::invalid(body_message, field));
    }
    Ok(())
}

fn is_lower_hex(value: &str, len: usize) -> bool {
    value.len() == len
        && value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn artifact() -> ArtifactRegistration {
        ArtifactRegistration {
            artifact_id: "attempt-1.stdout".to_string(),
            kind: "stdout".to_string(),
            relative_path: "stdout.log".to_string(),
            digest: format!("sha256:{}", "a".repeat(64)),
            media_type: "text/plain; charset=utf-8".to_string(),
            byte_length: 12,
            truncated: false,
        }
    }

    fn release_request() -> RuntimeReleaseRequest {
        RuntimeReleaseRequest {
            schema_version: RUNTIME_SCHEMA_VERSION,
            client_request_id: "release-r05-test".to_string(),
            principal: "runtime-test".to_string(),
            workspace_id: "ws-r05-test".to_string(),
            commit: "a".repeat(40),
            candidate_manifest_digest: format!("sha256:{}", "b".repeat(64)),
            expected_tool_count: 23,
        }
    }

    #[test]
    fn artifact_contract_preserves_bounded_identity_and_relative_path_law() {
        ArtifactStateContract::validate_registration(&artifact()).unwrap();
        let mut invalid = artifact();
        invalid.relative_path = "../escape".to_string();
        assert_eq!(
            ArtifactStateContract::validate_registration(&invalid)
                .unwrap_err()
                .field
                .as_deref(),
            Some("artifact.relativePath")
        );
        let mut invalid = artifact();
        invalid.digest = "sha256:bad".to_string();
        assert_eq!(
            ArtifactStateContract::validate_registration(&invalid)
                .unwrap_err()
                .field
                .as_deref(),
            Some("artifact.digest")
        );
    }

    #[test]
    fn artifact_read_contract_keeps_schema_and_bound_checks() {
        let request = ArtifactReadRequest {
            schema_version: RUNTIME_SCHEMA_VERSION,
            job_id: "job-r05".to_string(),
            artifact_id: "artifact-r05".to_string(),
            offset: 0,
            max_bytes: 4096,
        };
        ArtifactStateContract::validate_read_request(&request).unwrap();
        let mut invalid = request.clone();
        invalid.max_bytes = MAX_ARTIFACT_READ_BYTES + 1;
        assert_eq!(
            ArtifactStateContract::validate_read_request(&invalid)
                .unwrap_err()
                .field
                .as_deref(),
            Some("maxBytes")
        );
    }

    #[test]
    fn release_request_contract_preserves_exact_identity_inputs() {
        ReleaseStateContract::validate_request(&release_request()).unwrap();
        let mut invalid = release_request();
        invalid.expected_tool_count = 0;
        assert_eq!(
            ReleaseStateContract::validate_request(&invalid)
                .unwrap_err()
                .field
                .as_deref(),
            Some("expectedToolCount")
        );
        let mut invalid = release_request();
        invalid.commit = "A".repeat(40);
        assert_eq!(
            ReleaseStateContract::validate_request(&invalid)
                .unwrap_err()
                .field
                .as_deref(),
            Some("commit")
        );
    }

    #[test]
    fn release_receipt_missing_is_unresolved_until_job_terminal() {
        let request = release_request();
        let binding = RuntimeReleaseEffectBinding {
            contract: RuntimeReleaseContract::RuntimeReleaseV1,
            effect_id: runtime_release_effect_id(&request),
            request_digest: runtime_release_request_identity_digest(&request).unwrap(),
            workspace_id: request.workspace_id.clone(),
            commit: request.commit.clone(),
            candidate_manifest_digest: request.candidate_manifest_digest.clone(),
            expected_tool_count: request.expected_tool_count,
            receipt_path: format!("/tmp/ordivon-r05-missing-{}", std::process::id()),
        };
        let unresolved =
            ReleaseStateContract::inspect_receipt(&binding, None, Some(AttemptState::Accepted))
                .unwrap();
        assert_eq!(unresolved.disposition, RuntimeReleaseDisposition::Admitted);
        assert!(!unresolved.terminal);
        let terminal = ReleaseStateContract::inspect_receipt(
            &binding,
            Some(JobResolution::Failed),
            Some(AttemptState::Failed),
        )
        .unwrap();
        assert_eq!(
            terminal.disposition,
            RuntimeReleaseDisposition::ReconciliationRequired
        );
        assert_eq!(
            terminal.issue.as_deref(),
            Some("RELEASE_RECEIPT_MISSING_AFTER_JOB_TERMINAL")
        );
    }
}
