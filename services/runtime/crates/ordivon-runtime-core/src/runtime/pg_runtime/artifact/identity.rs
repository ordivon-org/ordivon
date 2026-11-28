//! Original committed PostgreSQL Artifact origin and content contradiction checks.
//! A mismatched disk receipt is an integrity error, never a transient DB outage.
use super::{universal, RuntimeError, RuntimeErrorCode, RuntimeResult};

// PostgreSQL is available when its committed Artifact disagrees with disk.
// Report an integrity contradiction, not a transient Registry outage: a
// consumer must not misclassify stale/mutable bytes as a retryable DB problem.
pub(super) fn require_pg_artifact_identity(
    bytes: &[u8],
    committed_byte_length: i64,
    committed_digest: &str,
) -> RuntimeResult<()> {
    if i64::try_from(bytes.len()).ok() != Some(committed_byte_length)
        || universal::sha256_bytes(bytes) != committed_digest
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Artifact bytes disagree with PostgreSQL registration",
            Some("artifactId"),
            false,
        ));
    }
    Ok(())
}

/// The authorized Job and the registered Attempt's owning Job must agree
/// before opening the Attempt's bundle. Matching bytes do not establish origin.
pub(super) fn require_pg_artifact_origin(
    requested_job: &str,
    attempt_job: &str,
) -> RuntimeResult<()> {
    if requested_job != attempt_job {
        return Err(RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Artifact registration and owning Attempt belong to different Jobs",
            Some("artifactId"),
            false,
        ));
    }
    Ok(())
}
