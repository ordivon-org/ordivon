//! PostgreSQL Runtime digest-bound Artifact reads.
use super::*;

impl PgRuntime {
    /// Full byte projection for MCP embedded Artifact resources. PostgreSQL
    /// owns the identity/metadata; no SQLite artifact registry is consulted.
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
        let row=db.client.query_opt(
            "SELECT a.bundle_path,r.relative_path,r.digest,r.byte_length,r.media_type,r.truncated              FROM artifacts r JOIN attempts a ON a.attempt_id=r.attempt_id              WHERE r.job_id=$1 AND r.artifact_id=$2",
            &[&request.job_id,&request.artifact_id]
        ).map_err(io)?.ok_or_else(||error("Artifact not found"))?;
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
        if bytes.len() as i64 != len || universal::sha256_bytes(&bytes) != digest {
            return Err(error("Artifact bytes do not match PostgreSQL registration"));
        }
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
        if bytes.len() as i64 != r.get::<_, i64>(3) || universal::sha256_bytes(&bytes) != digest {
            return Err(error("Artifact bytes do not match PG registration"));
        }
        let text = std::str::from_utf8(&bytes).map_err(io)?;
        let begin = usize::try_from(request.offset).map_err(io)?;
        if begin > bytes.len() || !text.is_char_boundary(begin) {
            return Err(RuntimeError::invalid("invalid UTF-8 offset", "offset"));
        }
        let mut end = begin
            .saturating_add(request.max_bytes as usize)
            .min(bytes.len());
        while !text.is_char_boundary(end) {
            end -= 1;
        }
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
