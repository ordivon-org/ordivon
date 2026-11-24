//! Original bounded UTF-8 text Artifact paging by stable byte cursor.
use super::PathBuf;
use super::{
    artifact_utf8_window, error, io, require_pg_artifact_identity, universal, ArtifactReadRequest,
    ArtifactReadResult, PgRuntime, RuntimeError, RuntimeResult,
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
        let r=db.client.query_opt("SELECT a.bundle_path,r.relative_path,r.digest,r.byte_length FROM artifacts r JOIN attempts a ON a.attempt_id=r.attempt_id WHERE r.job_id=$1 AND r.artifact_id=$2", &[&request.job_id,&request.artifact_id]).map_err(io)?.ok_or_else(|| error("Artifact not found"))?;
        let bundle: PathBuf = r.get::<_, String>(0).into();
        let relative: String = r.get(1);
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
        let digest: String = r.get(2);
        require_pg_artifact_identity(&bytes, r.get::<_, i64>(3), &digest)?;
        let text = std::str::from_utf8(&bytes).map_err(io)?;
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
