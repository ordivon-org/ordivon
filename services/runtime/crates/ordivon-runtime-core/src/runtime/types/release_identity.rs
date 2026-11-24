//! Original release identity domain wire contract and behavior.
use super::{
    RuntimeError, RuntimeErrorCode, RuntimeReleaseRequest, RuntimeResult,
    RUNTIME_RELEASE_IDENTITY_PREFIX,
};

use serde::Serialize;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeReleaseRequestIdentity {
    schema_version: u32,
    principal: String,
    workspace_id: String,
    commit: String,
    candidate_manifest_digest: String,
    expected_tool_count: u32,
}

pub fn runtime_release_request_identity_digest(
    request: &RuntimeReleaseRequest,
) -> RuntimeResult<String> {
    let identity = RuntimeReleaseRequestIdentity {
        schema_version: request.schema_version,
        principal: request.principal.clone(),
        workspace_id: request.workspace_id.clone(),
        commit: request.commit.clone(),
        candidate_manifest_digest: request.candidate_manifest_digest.clone(),
        expected_tool_count: request.expected_tool_count,
    };
    let bytes = serde_json::to_vec(&identity).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            format!("cannot serialize Runtime release request identity: {error}"),
            None,
            false,
        )
    })?;
    Ok(format!(
        "{RUNTIME_RELEASE_IDENTITY_PREFIX}{}",
        crate::universal::sha256_bytes(&bytes)
    ))
}

pub fn runtime_release_effect_id(request: &RuntimeReleaseRequest) -> String {
    crate::universal::sha256_bytes(
        format!(
            "runtime-release-effect-v1\0{}\0{}",
            request.principal, request.client_request_id
        )
        .as_bytes(),
    )
    .trim_start_matches("sha256:")
    .to_string()
}

#[cfg(test)]
mod release_business_identity_tests {
    use super::*;

    fn request() -> RuntimeReleaseRequest {
        RuntimeReleaseRequest {
            schema_version: 1,
            client_request_id: "release-native-1".to_owned(),
            principal: "agent:original".to_owned(),
            workspace_id: "ws-original".to_owned(),
            commit: "a".repeat(40),
            candidate_manifest_digest: format!("sha256:{}", "b".repeat(64)),
            expected_tool_count: 23,
        }
    }

    #[test]
    fn release_effect_request_key_and_semantic_content_identity_remain_distinct() {
        let mut original = request();
        let content_digest = runtime_release_request_identity_digest(&original).unwrap();
        let effect_id = runtime_release_effect_id(&original);
        assert!(content_digest.starts_with("runtime-release-v1:sha256:"));
        assert_eq!(effect_id.len(), 64);

        original.client_request_id = "release-native-2".to_owned();
        assert_eq!(
            runtime_release_request_identity_digest(&original).unwrap(),
            content_digest,
            "the client replay key is not a change to release content"
        );
        assert_ne!(
            runtime_release_effect_id(&original),
            effect_id,
            "new client request creates a different effect identity"
        );

        original.client_request_id = "release-native-1".to_owned();
        original.expected_tool_count += 1;
        assert_ne!(
            runtime_release_request_identity_digest(&original).unwrap(),
            content_digest,
            "the actual MCP tool count is part of the candidate release identity"
        );
        assert_eq!(runtime_release_effect_id(&original), effect_id);
        original.expected_tool_count -= 1;
        original.workspace_id = "ws-different-source".to_owned();
        assert_ne!(
            runtime_release_request_identity_digest(&original).unwrap(),
            content_digest,
            "moving the release to a different Workspace changes semantic source identity"
        );
    }
}
