//! Original bounded UTF-8 text Artifact paging by stable byte cursor.
use super::{
    artifact_utf8_window, io, read_bound_pg_artifact_registration, require_pg_artifact_identity,
    universal, ArtifactReadRequest, ArtifactReadResult, PgRuntime, RuntimeError, RuntimeResult,
};
use std::path::Path;

impl PgRuntime {
    pub fn read_artifact(
        &self,
        principal: &str,
        request: &ArtifactReadRequest,
    ) -> RuntimeResult<ArtifactReadResult> {
        if request.schema_version != 1
            || request.max_bytes == 0
            || request.max_bytes > 4 * 1024 * 1024
        {
            return Err(RuntimeError::invalid(
                "invalid artifact read bounds",
                "maxBytes",
            ));
        }
        let mut db = self.store()?;
        self.authorize(&mut db, &request.job_id, principal)?;
        let registration =
            read_bound_pg_artifact_registration(&mut db, &request.job_id, &request.artifact_id)?;
        let bundle = registration.bundle;
        let relative = registration.relative_path;
        universal::validate_relative_path(&relative, "artifactPath").map_err(io)?;
        let mut file = universal::open_regular_file_beneath(
            &universal::open_directory_nofollow(&bundle).map_err(io)?,
            Path::new(&relative),
            true,
        )
        .map_err(io)?;
        use std::io::Read;
        let mut bytes = vec![];
        file.by_ref()
            .take(self.config.executor.max_output_bytes.max(4 * 1024 * 1024) + 1)
            .read_to_end(&mut bytes)
            .map_err(io)?;
        let digest = registration.digest;
        require_pg_artifact_identity(&bytes, registration.byte_length, &digest)?;
        let text = std::str::from_utf8(&bytes).map_err(|_| {
            RuntimeError::new(
                super::RuntimeErrorCode::ArtifactNotUtf8,
                "Artifact is not valid UTF-8; use artifact.content for verified binary bytes",
                Some("artifactId"),
                false,
            )
        })?;
        let (begin, end) = artifact_utf8_window(text, request.offset, request.max_bytes)?;
        Ok(ArtifactReadResult {
            job_id: request.job_id.clone(),
            artifact_id: request.artifact_id.clone(),
            content: text[begin..end].into(),
            offset: request.offset,
            next_offset: end as u64,
            eof: end == bytes.len(),
            digest,
        })
    }
}
