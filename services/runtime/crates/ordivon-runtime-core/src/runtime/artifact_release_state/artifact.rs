use super::super::{
    ArtifactContentRequest, ArtifactReadRequest, ArtifactRegistration, RuntimeError, RuntimeResult,
    MAX_ARTIFACT_READ_BYTES, RUNTIME_SCHEMA_VERSION,
};
use super::validation::{validate_identifier, validate_sha256};
use std::path::Path;

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

    pub(crate) fn validate_content_request(request: &ArtifactContentRequest) -> RuntimeResult<()> {
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
