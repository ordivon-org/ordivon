use super::super::{
    runtime_release_effect_id, runtime_release_request_identity_digest, ArtifactReadRequest,
    ArtifactRegistration, AttemptState, JobResolution, RuntimeReleaseContract,
    RuntimeReleaseDisposition, RuntimeReleaseEffectBinding, RuntimeReleaseRequest,
    MAX_ARTIFACT_READ_BYTES, RUNTIME_SCHEMA_VERSION,
};
use super::{ArtifactStateContract, ReleaseStateContract};

fn artifact() -> ArtifactRegistration {
    ArtifactRegistration {
        artifact_id: "attempt-1.stdout".to_string(),
        kind: "stdout".to_string(),
        relative_path: "stdout.log".to_string(),
        digest: format!("sha256:{}", "a".repeat(64)),
        media_type: "text/plain; charset=utf-8".to_string(),
        byte_length: 12,
        truncated: false,
    }
}

fn release_request() -> RuntimeReleaseRequest {
    RuntimeReleaseRequest {
        schema_version: RUNTIME_SCHEMA_VERSION,
        client_request_id: "release-r05-test".to_string(),
        principal: "runtime-test".to_string(),
        workspace_id: "ws-r05-test".to_string(),
        commit: "a".repeat(40),
        candidate_manifest_digest: format!("sha256:{}", "b".repeat(64)),
        expected_tool_count: 23,
    }
}

#[test]
fn artifact_contract_preserves_bounded_identity_and_relative_path_law() {
    ArtifactStateContract::validate_registration(&artifact()).unwrap();
    let mut invalid = artifact();
    invalid.relative_path = "../escape".to_string();
    assert_eq!(
        ArtifactStateContract::validate_registration(&invalid)
            .unwrap_err()
            .field
            .as_deref(),
        Some("artifact.relativePath")
    );
    let mut invalid = artifact();
    invalid.digest = "sha256:bad".to_string();
    assert_eq!(
        ArtifactStateContract::validate_registration(&invalid)
            .unwrap_err()
            .field
            .as_deref(),
        Some("artifact.digest")
    );
}

#[test]
fn artifact_read_contract_keeps_schema_and_bound_checks() {
    let request = ArtifactReadRequest {
        schema_version: RUNTIME_SCHEMA_VERSION,
        job_id: "job-r05".to_string(),
        artifact_id: "artifact-r05".to_string(),
        offset: 0,
        max_bytes: 4096,
    };
    ArtifactStateContract::validate_read_request(&request).unwrap();
    let mut invalid = request.clone();
    invalid.max_bytes = MAX_ARTIFACT_READ_BYTES + 1;
    assert_eq!(
        ArtifactStateContract::validate_read_request(&invalid)
            .unwrap_err()
            .field
            .as_deref(),
        Some("maxBytes")
    );
}

#[test]
fn release_request_contract_preserves_exact_identity_inputs() {
    ReleaseStateContract::validate_request(&release_request()).unwrap();
    let mut invalid = release_request();
    invalid.expected_tool_count = 0;
    assert_eq!(
        ReleaseStateContract::validate_request(&invalid)
            .unwrap_err()
            .field
            .as_deref(),
        Some("expectedToolCount")
    );
    let mut invalid = release_request();
    invalid.commit = "A".repeat(40);
    assert_eq!(
        ReleaseStateContract::validate_request(&invalid)
            .unwrap_err()
            .field
            .as_deref(),
        Some("commit")
    );
}

#[test]
fn release_receipt_missing_is_unresolved_until_job_terminal() {
    let request = release_request();
    let missing_receipt_root = tempfile::tempdir().unwrap();
    let binding = RuntimeReleaseEffectBinding {
        contract: RuntimeReleaseContract::RuntimeReleaseV1,
        effect_id: runtime_release_effect_id(&request),
        request_digest: runtime_release_request_identity_digest(&request).unwrap(),
        workspace_id: request.workspace_id.clone(),
        commit: request.commit.clone(),
        candidate_manifest_digest: request.candidate_manifest_digest.clone(),
        expected_tool_count: request.expected_tool_count,
        receipt_path: missing_receipt_root
            .path()
            .join("absent-effect-directory")
            .to_string_lossy()
            .into_owned(),
    };
    let unresolved =
        ReleaseStateContract::inspect_receipt(&binding, None, Some(AttemptState::Accepted))
            .unwrap();
    assert_eq!(unresolved.disposition, RuntimeReleaseDisposition::Admitted);
    assert!(!unresolved.terminal);
    let terminal = ReleaseStateContract::inspect_receipt(
        &binding,
        Some(JobResolution::Failed),
        Some(AttemptState::Failed),
    )
    .unwrap();
    assert_eq!(
        terminal.disposition,
        RuntimeReleaseDisposition::ReconciliationRequired
    );
    assert_eq!(
        terminal.issue.as_deref(),
        Some("RELEASE_RECEIPT_MISSING_AFTER_JOB_TERMINAL")
    );
}

/// Assert user-visible release facts using actual receipt files, not source
/// locations or a fixed arrangement of internal Rust modules.
#[test]
fn original_release_receipt_distinguishes_deployed_mismatch_and_real_rollback() {
    let dir = tempfile::tempdir().unwrap();
    let request = release_request();
    let binding = RuntimeReleaseEffectBinding {
        contract: RuntimeReleaseContract::RuntimeReleaseV1,
        effect_id: runtime_release_effect_id(&request),
        request_digest: runtime_release_request_identity_digest(&request).unwrap(),
        workspace_id: request.workspace_id,
        commit: request.commit,
        candidate_manifest_digest: request.candidate_manifest_digest,
        expected_tool_count: request.expected_tool_count,
        receipt_path: dir.path().to_string_lossy().into_owned(),
    };
    let original_effect = serde_json::json!({
        "contract": "runtime_release_v1",
        "effectId": binding.effect_id,
        "requestDigest": binding.request_digest,
        "commit": binding.commit,
        "candidateManifestDigest": binding.candidate_manifest_digest,
        "expectedToolCount": binding.expected_tool_count,
    });
    std::fs::write(
        dir.path().join("effect-request.json"),
        serde_json::to_vec(&original_effect).unwrap(),
    )
    .unwrap();
    let original_result = serde_json::json!({
        "status": "deployed",
        "commit": binding.commit,
        "releaseEffect": original_effect,
        "probe": {
            "toolCount": binding.expected_tool_count,
            "toolCatalogDigest": format!("sha256:{}", "c".repeat(64)),
        }
    });
    let result_path = dir.path().join("result.json");
    std::fs::write(&result_path, serde_json::to_vec(&original_result).unwrap()).unwrap();

    let deployed = ReleaseStateContract::inspect_receipt(
        &binding,
        Some(JobResolution::Succeeded),
        Some(AttemptState::Succeeded),
    )
    .unwrap();
    assert_eq!(deployed.disposition, RuntimeReleaseDisposition::Deployed);
    assert!(deployed.terminal && deployed.available);
    assert_eq!(
        deployed.deployed_tool_count,
        Some(binding.expected_tool_count)
    );
    assert!(deployed
        .digest
        .as_ref()
        .is_some_and(|digest| digest.starts_with("sha256:")));

    // A physically present receipt with the wrong deployed tool catalog
    // must never be projected as a successful real-world installation.
    let mut mismatched = original_result.clone();
    mismatched["probe"]["toolCount"] = serde_json::json!(22);
    std::fs::write(&result_path, serde_json::to_vec(&mismatched).unwrap()).unwrap();
    let refused = ReleaseStateContract::inspect_receipt(
        &binding,
        Some(JobResolution::Succeeded),
        Some(AttemptState::Succeeded),
    )
    .unwrap();
    assert_eq!(
        refused.issue.as_deref(),
        Some("RELEASE_RESULT_TOOL_COUNT_MISMATCH"),
    );
    assert!(!refused.terminal);

    // Original rollback receipt is stronger than the earlier deployment
    // result; a verified restored_previous must project RolledBack.
    std::fs::write(
        dir.path().join("rollback-result.json"),
        br#"{"status":"restored_previous"}"#,
    )
    .unwrap();
    let rolled_back = ReleaseStateContract::inspect_receipt(
        &binding,
        Some(JobResolution::Succeeded),
        Some(AttemptState::Succeeded),
    )
    .unwrap();
    assert_eq!(
        rolled_back.disposition,
        RuntimeReleaseDisposition::RolledBack
    );
    assert!(rolled_back.terminal);
    assert_eq!(
        rolled_back.rollback_status.as_deref(),
        Some("restored_previous")
    );
}

#[cfg(unix)]
#[test]
fn original_release_receipt_does_not_follow_a_symlink_to_foreign_effect_files() {
    let dir = tempfile::tempdir().unwrap();
    let other = tempfile::tempdir().unwrap();
    let request = release_request();
    let binding = RuntimeReleaseEffectBinding {
        contract: RuntimeReleaseContract::RuntimeReleaseV1,
        effect_id: runtime_release_effect_id(&request),
        request_digest: runtime_release_request_identity_digest(&request).unwrap(),
        workspace_id: request.workspace_id,
        commit: request.commit,
        candidate_manifest_digest: request.candidate_manifest_digest,
        expected_tool_count: request.expected_tool_count,
        receipt_path: dir.path().to_string_lossy().into_owned(),
    };
    std::fs::write(other.path().join("effect-request.json"), b"{}").unwrap();
    std::os::unix::fs::symlink(
        other.path().join("effect-request.json"),
        dir.path().join("effect-request.json"),
    )
    .unwrap();
    let observed = ReleaseStateContract::inspect_receipt(
        &binding,
        Some(JobResolution::Succeeded),
        Some(AttemptState::Succeeded),
    )
    .unwrap();
    assert_eq!(
        observed.issue.as_deref(),
        Some("RELEASE_RECEIPT_FILE_UNSAFE")
    );
    assert!(!observed.terminal);
}
