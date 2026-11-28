//! Cancellation intent is an immutable request, not proof of native stop.
use sha2::{Digest, Sha256};

#[derive(Clone)]
pub struct PgCancelIntent {
    pub job_id: String,
    pub observed_at_ms: i64,
    pub expected_source_sha256: String,
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgCancelOutcome {
    IntentRecorded(String),
    Existing(String),
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgCancelObservation {
    Confirmed(String),
    Inconclusive,
}

pub(super) fn cancel_detail(i: &PgCancelIntent) -> String {
    // The original cancel timestamp is part of the immutable request identity
    // used for reconciliation after an ambiguous COMMIT.
    let identity = format!(
        "pg-cancel-intent\\0{}\\0{}\\0{}",
        i.expected_source_sha256, i.job_id, i.observed_at_ms
    );
    let digest = format!(
        "sha256:{}",
        hex::encode(Sha256::digest(identity.as_bytes()))
    );
    serde_json::json!({"cancelIntentDigest":digest}).to_string()
}
