//! Exact byte resource read for MCP, backed by a PostgreSQL registration.
//! No SQLite Registry, no new permission engine and no unsealed output.
use super::PathBuf;
use super::{
    io, require_pg_artifact_identity, require_pg_artifact_origin, universal,
    ArtifactContentMetadata, ArtifactContentReadResult, ArtifactContentRequest, PgRuntime,
    RuntimeError, RuntimeErrorCode, RuntimeResult,
};
use std::path::Path;

impl PgRuntime {
    pub fn read_artifact_content(
        &self,
        principal: &str,
        request: &ArtifactContentRequest,
    ) -> RuntimeResult<ArtifactContentReadResult> {
        if request.schema_version != 1
            || request.max_bytes == 0
            || request.max_bytes > crate::runtime::MAX_ARTIFACT_READ_BYTES
        {
            return Err(RuntimeError::invalid(
                "invalid artifact content bound",
                "maxBytes",
            ));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, &request.job_id, principal)?;
        let row=db.client.query_opt(
            "SELECT a.bundle_path,r.relative_path,r.digest,r.byte_length,r.media_type,r.truncated,a.job_id              FROM artifacts r JOIN attempts a ON a.attempt_id=r.attempt_id              WHERE r.job_id=$1 AND r.artifact_id=$2",
            &[&request.job_id,&request.artifact_id]
        ).map_err(io)?.ok_or_else(|| RuntimeError::new(
            RuntimeErrorCode::ArtifactNotFound,
            "Artifact not found for this Job",
            Some("artifactId"),
            false,
        ))?;
        require_pg_artifact_origin(&request.job_id, &row.get::<_, String>(6))?;
        let relative: String = row.get(1);
        universal::validate_relative_path(&relative, "artifactPath").map_err(io)?;
        let base = PathBuf::from(row.get::<_, String>(0));
        let dir = universal::open_directory_nofollow(&base).map_err(io)?;
        let mut file =
            universal::open_regular_file_beneath(&dir, Path::new(&relative), true).map_err(io)?;
        use std::io::Read;
        let mut bytes = Vec::new();
        file.by_ref()
            .take(request.max_bytes + 1)
            .read_to_end(&mut bytes)
            .map_err(io)?;
        if bytes.len() as u64 > request.max_bytes {
            return Err(RuntimeError::invalid(
                "Artifact exceeds maxBytes",
                "maxBytes",
            ));
        }
        let digest: String = row.get(2);
        let len: i64 = row.get(3);
        require_pg_artifact_identity(&bytes, len, &digest)?;
        Ok(ArtifactContentReadResult {
            metadata: ArtifactContentMetadata {
                job_id: request.job_id.clone(),
                artifact_id: request.artifact_id.clone(),
                digest,
                media_type: row.get(4),
                byte_length: len as u64,
                truncated: row.get(5),
            },
            bytes,
        })
    }
}
