//! Original committed PostgreSQL Artifact digest/byte-length contradiction checker.
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
