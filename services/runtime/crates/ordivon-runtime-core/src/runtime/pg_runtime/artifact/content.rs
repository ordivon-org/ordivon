//! Exact byte resource read for MCP, backed by a PostgreSQL registration.
//! No SQLite Registry, no new permission engine and no unsealed output.
use super::{
    io, read_bound_pg_artifact_registration, require_pg_artifact_identity, universal,
    ArtifactContentMetadata, ArtifactContentReadResult, ArtifactContentRequest, PgRuntime,
    RuntimeError, RuntimeResult,
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
            || request.max_bytes > 4 * 1024 * 1024
        {
            return Err(RuntimeError::invalid(
                "invalid artifact content bound",
                "maxBytes",
            ));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, &request.job_id, principal)?;
        let registration =
            read_bound_pg_artifact_registration(&mut db, &request.job_id, &request.artifact_id)?;
        let relative = registration.relative_path;
        universal::validate_relative_path(&relative, "artifactPath").map_err(io)?;
        let base = registration.bundle;
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
        let digest = registration.digest;
        let len = registration.byte_length;
        require_pg_artifact_identity(&bytes, len, &digest)?;
        Ok(ArtifactContentReadResult {
            metadata: ArtifactContentMetadata {
                job_id: request.job_id.clone(),
                artifact_id: request.artifact_id.clone(),
                digest,
                media_type: registration.media_type,
                byte_length: len as u64,
                truncated: registration.truncated,
            },
            bytes,
        })
    }
}
