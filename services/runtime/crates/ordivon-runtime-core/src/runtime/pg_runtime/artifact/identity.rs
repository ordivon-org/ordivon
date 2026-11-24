//! Original committed PostgreSQL Artifact digest/byte-length contradiction checker.
//! A mismatched disk receipt is an integrity error, never a transient DB outage.
use super::PathBuf;
use super::{io, universal, PgAdmissionStore, RuntimeError, RuntimeErrorCode, RuntimeResult};

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

/// One durable registration carrier for both text and exact-byte readers.
/// The independently stored Job/Attempt identities must name the same row
/// relationship before either reader opens the filesystem. A contradictory
/// registration is not absence, and correct bytes cannot repair its owner.
pub(super) struct PgArtifactReadRegistration {
    pub bundle: PathBuf,
    pub relative_path: String,
    pub digest: String,
    pub byte_length: i64,
    pub media_type: String,
    pub truncated: bool,
}

pub(super) fn read_bound_pg_artifact_registration(
    db: &mut PgAdmissionStore,
    job_id: &str,
    artifact_id: &str,
) -> RuntimeResult<PgArtifactReadRegistration> {
    let row = db
        .client
        .query_opt(
            "SELECT a.bundle_path,r.relative_path,r.digest,r.byte_length,r.media_type,r.truncated \
         FROM artifacts r LEFT JOIN attempts a ON a.attempt_id=r.attempt_id AND a.job_id=r.job_id \
         WHERE r.job_id=$1 AND r.artifact_id=$2",
            &[&job_id, &artifact_id],
        )
        .map_err(io)?
        .ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::ArtifactNotFound,
                "Artifact not found for this Job",
                Some("artifactId"),
                false,
            )
        })?;
    let bundle: Option<String> = row.get(0);
    let bundle = bundle.ok_or_else(|| {
        RuntimeError::new(
            RuntimeErrorCode::ArtifactIdentityConflict,
            "Artifact registration does not belong to an Attempt of this Job",
            Some("artifactId"),
            false,
        )
    })?;
    Ok(PgArtifactReadRegistration {
        bundle: bundle.into(),
        relative_path: row.get(1),
        digest: row.get(2),
        byte_length: row.get(3),
        media_type: row.get(4),
        truncated: row.get(5),
    })
}
