use super::super::super::{
    ArtifactRegistration, AttemptRecord, RuntimeError, RuntimeErrorCode, RuntimeResult,
};
use super::super::errors::io_error;
use super::super::{REQUEST_FILE, WORKSPACE_SOURCE_OBSERVATION_FILE};
use super::contract::{validate_source_observation_relation, SourceObservationRequirement};
use crate::universal::{sha256_bytes, RunnerRequest, UNIVERSAL_EXEC_SCHEMA_VERSION};
use serde::Deserialize;
use std::{fs, path::Path};

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct WorkspaceSourceObservationEvidence {
    schema_version: u32,
    task_id: String,
    job_id: String,
    attempt_id: String,
    launch_token_digest: String,
    committed_workspace_source_digest: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    observed_workspace_source_digest: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    matches_commitment: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    observation_error_code: Option<String>,
    observed_unix_ms: u128,
}

pub(crate) fn validate_workspace_source_observation_artifact(
    current: &AttemptRecord,
    committed_workspace_source_digest: Option<&str>,
    require_if_committed: bool,
    requirement: SourceObservationRequirement,
) -> RuntimeResult<Option<ArtifactRegistration>> {
    let path = Path::new(&current.bundle_path).join(WORKSPACE_SOURCE_OBSERVATION_FILE);
    if !require_if_committed && !path.exists() {
        return Ok(None);
    }

    let request_path = Path::new(&current.bundle_path).join(REQUEST_FILE);
    let request_bytes =
        fs::read(&request_path).map_err(|error| io_error("read Runner request", error))?;
    let request: RunnerRequest = serde_json::from_slice(&request_bytes).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            format!("invalid Runner request while validating source observation: {error}"),
            Some("workspaceSourceObservation"),
            false,
        )
    })?;
    if request.task_id != current.attempt_id
        || request.job_id.as_deref() != Some(current.job_id.as_str())
        || request.attempt_id.as_deref() != Some(current.attempt_id.as_str())
        || request
            .launch_token
            .as_deref()
            .map(|value| sha256_bytes(value.as_bytes()))
            .as_deref()
            != Some(current.launch_token_digest.as_str())
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ResultIdentityConflict,
            "Runner request identity does not match committed Attempt while validating source observation",
            Some("workspaceSourceObservation"),
            false,
        ));
    }

    if request.workspace_source_digest.as_deref() != committed_workspace_source_digest {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Runner request Workspace source commitment does not match the Registry execution plan",
            Some("workspaceSourceObservation"),
            false,
        ));
    }

    let committed = committed_workspace_source_digest;
    if committed.is_none() {
        if path.exists() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Workspace source observation exists without a committed source digest",
                Some("workspaceSourceObservation"),
                false,
            ));
        }
        return Ok(None);
    }
    let bytes = match fs::read(&path) {
        Ok(bytes) => bytes,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound && !require_if_committed => {
            return Ok(None);
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                "Committed Workspace source result omitted exact source observation evidence",
                Some("workspaceSourceObservation"),
                false,
            ));
        }
        Err(error) => return Err(io_error("read Workspace source observation", error)),
    };
    let evidence: WorkspaceSourceObservationEvidence =
        serde_json::from_slice(&bytes).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::ArtifactIdentityConflict,
                format!("invalid Workspace source observation: {error}"),
                Some("workspaceSourceObservation"),
                false,
            )
        })?;
    let committed = committed.expect("checked above");
    if evidence.schema_version != UNIVERSAL_EXEC_SCHEMA_VERSION
        || evidence.task_id != current.attempt_id
        || evidence.job_id != current.job_id
        || evidence.attempt_id != current.attempt_id
        || evidence.launch_token_digest != current.launch_token_digest
        || evidence.committed_workspace_source_digest != committed
        || !crate::runtime::types::is_sha256_digest(&evidence.committed_workspace_source_digest)
        || evidence.observed_unix_ms == 0
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Workspace source observation identity does not match committed Attempt",
            Some("workspaceSourceObservation"),
            false,
        ));
    }
    validate_source_observation_relation(
        evidence.observed_workspace_source_digest.as_deref(),
        evidence.matches_commitment,
        evidence.observation_error_code.as_deref(),
        committed,
        requirement,
    )?;
    Ok(Some(ArtifactRegistration {
        artifact_id: format!("{}.workspace-source-observation", current.attempt_id),
        kind: "workspace_source_observation".to_string(),
        relative_path: WORKSPACE_SOURCE_OBSERVATION_FILE.to_string(),
        digest: sha256_bytes(&bytes),
        media_type: "application/json".to_string(),
        byte_length: u64::try_from(bytes.len()).unwrap_or(u64::MAX),
        truncated: false,
    }))
}
