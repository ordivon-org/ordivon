//! Pure Artifact manifest, terminal transitions and Attempt terminal DTOs.
//! The PostgreSQL transaction committing the transition is in pg_admission/terminal.rs.
use sha2::{Digest, Sha256};
use std::collections::HashSet;

#[derive(Clone)]
pub struct PgTerminalNoArtifacts {
    pub attempt_id: String,
    pub expected_row_version: i64,
    pub terminal_state: String,
    pub result_digest: String,
    pub reason_code: String,
    pub exit_code: Option<i32>,
    pub finished_at_ms: i64,
    pub expected_source_sha256: String,
}
#[derive(Debug, PartialEq, Eq)]
pub enum PgTerminalOutcome {
    Committed(String),
    Existing(String),
}

/// PG only commits metadata; physical bytes must be validated by the Runner.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PgArtifactRegistration {
    pub artifact_id: String,
    pub kind: String,
    pub relative_path: String,
    pub digest: String,
    pub media_type: String,
    pub byte_length: i64,
    pub truncated: bool,
    pub created_at_ms: i64,
}
pub(crate) fn pg_artifact_manifest_digest(artifacts: &[PgArtifactRegistration]) -> String {
    let mut ordered = artifacts.to_vec();
    ordered.sort_by(|a, b| a.artifact_id.cmp(&b.artifact_id));
    let manifest: Vec<_> = ordered
        .iter()
        .map(|a| {
            serde_json::json!({
                "artifactId":a.artifact_id, "kind":a.kind, "relativePath":a.relative_path,
                "digest":a.digest, "mediaType":a.media_type,"byteLength":a.byte_length,
                "truncated":a.truncated, "createdAtMs":a.created_at_ms
            })
        })
        .collect();
    let bytes = serde_json::to_vec(&manifest).expect("bounded Artifact manifest is JSON");
    format!("sha256:{}", hex::encode(Sha256::digest(&bytes)))
}
pub(crate) fn valid_pg_artifacts(artifacts: &[PgArtifactRegistration]) -> bool {
    let mut ids = HashSet::new();
    let mut paths = HashSet::new();
    artifacts.iter().all(|a| {
        !a.artifact_id.is_empty()
            && !a.kind.is_empty()
            && !a.media_type.is_empty()
            && a.media_type.len() <= 256
            && a.byte_length >= 0
            && a.created_at_ms >= 0
            && a.digest.starts_with("sha256:")
            && a.digest.len() == 71
            && a.digest[7..].bytes().all(|b| b.is_ascii_hexdigit())
            && !a.relative_path.is_empty()
            && !a.relative_path.starts_with('/')
            && !a.relative_path.contains('\\')
            && !a
                .relative_path
                .split('/')
                .any(|p| p == ".." || p.is_empty())
            && ids.insert(a.artifact_id.as_str())
            && paths.insert((a.kind.as_str(), a.relative_path.as_str()))
    })
}
pub(super) fn terminal_transition(from: &str, to: &str) -> bool {
    match from {
        "accepted" => matches!(to, "cancelled" | "failed" | "lost" | "orphaned"),
        "starting" | "running" | "stopping" | "recovering" => matches!(
            to,
            "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
        ),
        _ => false,
    }
}
#[cfg(kani)]
mod kani_transition_proofs {
    use super::terminal_transition;

    #[kani::proof]
    fn proof_pg_terminal_transition_matches_contract() {
        let from_id: u8 = kani::any();
        let to_id: u8 = kani::any();
        kani::assume(from_id < 12 && to_id < 12);
        let state = |id: u8| match id {
            0 => "accepted",
            1 => "starting",
            2 => "running",
            3 => "stopping",
            4 => "recovering",
            5 => "succeeded",
            6 => "failed",
            7 => "timed_out",
            8 => "cancelled",
            9 => "lost",
            10 => "orphaned",
            _ => "unqualified",
        };
        // Independent, finite contract for the declared runtime state alphabet.
        let expected = match from_id {
            0 => matches!(to_id, 6 | 8 | 9 | 10),
            1..=4 => matches!(to_id, 5..=10),
            _ => false,
        };
        assert_eq!(terminal_transition(state(from_id), state(to_id)), expected);
    }
}
