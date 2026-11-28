use super::super::{
    ArtifactRegistration, AttemptRecord, RuntimeError, RuntimeErrorCode, RuntimeResult,
};
use super::errors::io_error;
use crate::universal::{
    sha256_bytes, RunnerResourceReceipt, RESOURCE_RECEIPT_FILE,
    RESOURCE_RECEIPT_PROVIDER_LINUX_CGROUP_V2, RESOURCE_RECEIPT_SCHEMA_VERSION,
    RESOURCE_RECEIPT_SCOPE_ATTEMPT_CGROUP,
};
use std::{fs, path::Path};

pub(super) fn validate_resource_receipt(
    current: &AttemptRecord,
) -> RuntimeResult<Option<ArtifactRegistration>> {
    let path = Path::new(&current.bundle_path).join(RESOURCE_RECEIPT_FILE);
    let bytes = match fs::read(&path) {
        Ok(bytes) => bytes,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => return Err(io_error("read Runner resource receipt", error)),
    };
    let receipt: RunnerResourceReceipt = serde_json::from_slice(&bytes).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            format!("invalid Runner resource receipt: {error}"),
            Some("resourceReceipt"),
            false,
        )
    })?;
    if receipt.schema_version != RESOURCE_RECEIPT_SCHEMA_VERSION
        || receipt.task_id != current.attempt_id
        || receipt.job_id != current.job_id
        || receipt.attempt_id != current.attempt_id
        || receipt.launch_token_digest != current.launch_token_digest
        || receipt.scope != RESOURCE_RECEIPT_SCOPE_ATTEMPT_CGROUP
        || receipt.provider != RESOURCE_RECEIPT_PROVIDER_LINUX_CGROUP_V2
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "Runner resource receipt identity does not match committed Attempt",
            Some("resourceReceipt"),
            false,
        ));
    }
    Ok(Some(ArtifactRegistration {
        artifact_id: format!("{}.resource-receipt", current.attempt_id),
        kind: "resource_receipt".to_string(),
        relative_path: RESOURCE_RECEIPT_FILE.to_string(),
        digest: sha256_bytes(&bytes),
        media_type: "application/json".to_string(),
        byte_length: u64::try_from(bytes.len()).unwrap_or(u64::MAX),
        truncated: false,
    }))
}
