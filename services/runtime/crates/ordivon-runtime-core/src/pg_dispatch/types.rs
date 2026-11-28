use super::super::PgAdmissionError;

#[derive(Clone)]
pub struct PgBundleReady {
    pub attempt_id: String,
    pub expected_row_version: i64,
    pub bundle_digest: String,
    pub observed_at_ms: i64,
    pub expected_source_sha256: String,
}

#[derive(Clone)]
pub struct PgDispatchIssued {
    pub attempt_id: String,
    pub expected_row_version: i64,
    pub expected_bundle_digest: String,
    pub observed_at_ms: i64,
    pub expected_source_sha256: String,
}

#[derive(Clone)]
pub(crate) struct PgRunnerBound {
    pub attempt_id: String,
    pub expected_row_version: i64,
    pub expected_bundle_digest: String,
    pub runner_start_digest: String,
    pub native_invocation_id: String,
    pub observed_at_ms: i64,
    pub expected_source_sha256: String,
}

pub(super) fn sha256_id(s: &str) -> bool {
    s.len() == 71 && s.starts_with("sha256:") && s[7..].bytes().all(|b| b.is_ascii_hexdigit())
}

pub(super) fn validate(
    attempt_id: &str,
    version: i64,
    digest: &str,
    at: i64,
    source: &str,
) -> Result<(), PgAdmissionError> {
    if attempt_id.is_empty()
        || version < 0
        || at < 0
        || !sha256_id(digest)
        || source.len() != 64
        || !source.bytes().all(|b| b.is_ascii_hexdigit())
    {
        return Err(PgAdmissionError::InvalidInput);
    }
    Ok(())
}
