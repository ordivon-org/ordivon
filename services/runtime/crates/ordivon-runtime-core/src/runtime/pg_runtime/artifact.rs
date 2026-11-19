//! PostgreSQL Runtime digest-bound Artifact reads.
use super::*;

fn artifact_utf8_window(text: &str, offset: u64, max_bytes: u64) -> RuntimeResult<(usize, usize)> {
    let begin = usize::try_from(offset).map_err(io)?;
    if begin > text.len() || !text.is_char_boundary(begin) {
        return Err(RuntimeError::invalid("invalid UTF-8 offset", "offset"));
    }
    let mut end = begin.saturating_add(max_bytes as usize).min(text.len());
    while !text.is_char_boundary(end) {
        end -= 1;
    }
    if end == begin && begin < text.len() {
        return Err(RuntimeError::invalid(
            "maxBytes is too small for the next UTF-8 character; use at least 4 bytes",
            "maxBytes",
        ));
    }
    Ok((begin, end))
}

// PostgreSQL is available when its committed Artifact disagrees with disk.
// Report an integrity contradiction, not a transient Registry outage: a
// consumer must not misclassify stale/mutable bytes as a retryable DB problem.
fn require_pg_artifact_identity(
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

#[cfg(test)]
mod utf8_artifact_progress_tests {
    use super::*;

    #[test]
    fn pg_artifact_integrity_mismatch_is_not_a_registry_failure() {
        let committed = b"initial sealed receipt";
        let digest = universal::sha256_bytes(committed);
        require_pg_artifact_identity(committed, committed.len() as i64, &digest).unwrap();
        for (bytes, expected_length) in [
            (
                b"initial sealed receipt".as_slice(),
                committed.len() as i64 + 1,
            ),
            (b"initial sealed receipT".as_slice(), committed.len() as i64),
        ] {
            let err = require_pg_artifact_identity(bytes, expected_length, &digest).unwrap_err();
            assert_eq!(err.code, RuntimeErrorCode::ArtifactIdentityConflict);
            assert_eq!(err.field.as_deref(), Some("artifactId"));
            assert!(!err.retryable);
        }
    }

    #[test]
    fn pg_artifact_page_rejects_zero_progress_in_the_middle_of_utf8() {
        let source = "A中文B🙂C\n";
        for (offset, max_bytes) in [(1, 1), (1, 2), (8, 1), (8, 2), (8, 3)] {
            let failure = artifact_utf8_window(source, offset, max_bytes).unwrap_err();
            assert_eq!(failure.field.as_deref(), Some("maxBytes"));
        }
    }

    #[test]
    fn pg_artifact_page_preserves_valid_byte_cursor_boundaries() {
        let source = "A中文B🙂C\n";
        for (offset, max_bytes, expected) in [
            (0, 5, (0, 4)),
            (4, 4, (4, 8)),
            (8, 4, (8, 12)),
            (12, 2, (12, 14)),
            (14, 1, (14, 14)),
        ] {
            let (begin, end) = artifact_utf8_window(source, offset, max_bytes).unwrap();
            assert_eq!((begin, end), expected);
        }
        let failure = artifact_utf8_window(source, 2, 4).unwrap_err();
        assert_eq!(failure.field.as_deref(), Some("offset"));
    }
}
