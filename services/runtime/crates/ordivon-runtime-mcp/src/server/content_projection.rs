//! Read-only transport projection of owner-qualified bytes and metadata.
//! This module owns MCP presentation, not source identity, retention, or authorization.

use base64::{engine::general_purpose::STANDARD as BASE64_STANDARD, Engine as _};
use ordivon_runtime_core::{
    ArtifactContentReadResult, WorkspaceContentReadResult, WorkspaceFileReadResult,
};
use rmcp::{
    model::{CallToolResult, ContentBlock, ResourceContents},
    ErrorData as McpError,
};

use super::{
    tool_error_call_result, ArtifactContentProjectionMetadata, ToolOutcome,
    WorkspaceFileProjectionMetadata,
};

fn binary_resource_response(
    uri: &str,
    media_type: &str,
    bytes: &[u8],
    structured: serde_json::Value,
) -> CallToolResult {
    let resource = ResourceContents::BlobResourceContents {
        uri: uri.to_string(),
        mime_type: Some(media_type.to_string()),
        blob: BASE64_STANDARD.encode(bytes),
        meta: None,
    };
    let mut response = CallToolResult::success(vec![ContentBlock::resource(resource)]);
    response.structured_content = Some(structured);
    response
}

fn artifact_content_projection_metadata(
    result: &ArtifactContentReadResult,
) -> ArtifactContentProjectionMetadata {
    let registered = result.metadata.media_type.clone();
    let valid_registered_media_type = registered.contains('/')
        && registered.len() <= 256
        && registered
            .bytes()
            .all(|byte| byte.is_ascii_graphic() || byte == b' ');
    let (media_type, media_type_standing) = if valid_registered_media_type {
        (
            registered.clone(),
            "REGISTERED_METADATA_UNVERIFIED".to_string(),
        )
    } else {
        (
            "application/octet-stream".to_string(),
            "REGISTERED_METADATA_INVALID_FALLBACK".to_string(),
        )
    };
    let digest_hex = result
        .metadata
        .digest
        .strip_prefix("sha256:")
        .unwrap_or(result.metadata.digest.as_str());
    ArtifactContentProjectionMetadata {
        job_id: result.metadata.job_id.clone(),
        artifact_id: result.metadata.artifact_id.clone(),
        digest: result.metadata.digest.clone(),
        byte_length: result.metadata.byte_length,
        truncated: result.metadata.truncated,
        registered_media_type: registered,
        media_type,
        media_type_standing,
        resource_uri: format!("ordivon://artifact/sha256/{digest_hex}"),
    }
}

pub(super) fn artifact_content_call_result(
    outcome: ToolOutcome<ArtifactContentReadResult>,
) -> Result<CallToolResult, McpError> {
    match outcome {
        ToolOutcome::Success(result) => {
            let metadata = artifact_content_projection_metadata(&result);
            let structured = serde_json::to_value(&metadata).map_err(|error| {
                McpError::internal_error(
                    format!("cannot serialize Artifact content metadata: {error}"),
                    None,
                )
            })?;
            Ok(binary_resource_response(
                &metadata.resource_uri,
                &metadata.media_type,
                &result.bytes,
                structured,
            ))
        }
        ToolOutcome::Error(error) => Ok(tool_error_call_result(error)),
    }
}

fn workspace_file_projection_metadata(
    result: &WorkspaceFileReadResult,
    media_type: String,
    media_type_standing: String,
) -> WorkspaceFileProjectionMetadata {
    let digest_hex = result
        .metadata
        .digest
        .strip_prefix("sha256:")
        .unwrap_or(result.metadata.digest.as_str());
    WorkspaceFileProjectionMetadata {
        workspace_id: result.metadata.workspace_id.clone(),
        relative_path: result.metadata.relative_path.clone(),
        digest: result.metadata.digest.clone(),
        byte_length: result.metadata.byte_length,
        media_type,
        media_type_standing,
        resource_uri: format!(
            "ordivon://workspace/{}/sha256/{digest_hex}",
            result.metadata.workspace_id
        ),
    }
}

pub(super) fn workspace_file_call_result(
    outcome: ToolOutcome<WorkspaceFileReadResult>,
    media_type: String,
    media_type_standing: String,
) -> Result<CallToolResult, McpError> {
    match outcome {
        ToolOutcome::Success(result) => {
            let metadata =
                workspace_file_projection_metadata(&result, media_type, media_type_standing);
            let structured = serde_json::to_value(&metadata).map_err(|error| {
                McpError::internal_error(
                    format!("cannot serialize workspace file metadata: {error}"),
                    None,
                )
            })?;
            Ok(binary_resource_response(
                &metadata.resource_uri,
                &metadata.media_type,
                &result.bytes,
                structured,
            ))
        }
        ToolOutcome::Error(error) => Ok(tool_error_call_result(error)),
    }
}

pub(super) fn workspace_content_call_result(
    outcome: ToolOutcome<WorkspaceContentReadResult>,
) -> Result<CallToolResult, McpError> {
    match outcome {
        ToolOutcome::Success(result) => {
            let structured = serde_json::to_value(&result.metadata).map_err(|error| {
                McpError::internal_error(
                    format!("cannot serialize workspace content metadata: {error}"),
                    None,
                )
            })?;
            let block = ContentBlock::image(
                BASE64_STANDARD.encode(&result.bytes),
                result.metadata.media_type.clone(),
            );
            let mut response = CallToolResult::success(vec![block]);
            response.structured_content = Some(structured);
            Ok(response)
        }
        ToolOutcome::Error(error) => Ok(tool_error_call_result(error)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::server::{ToolCommitState, ToolError, ToolRetryClass};
    use ordivon_runtime_core::{ArtifactContentMetadata, WorkspaceFileMetadata};
    use serde_json::{json, Value};
    use sha2::{Digest, Sha256};

    #[test]
    fn all_content_paths_preserve_the_same_error_without_fabricating_bytes() {
        let error = ToolError::invalid("digest does not match", "expectedDigest");
        let expected = json!({"error": error.clone()});
        let responses = [
            artifact_content_call_result(ToolOutcome::Error(error.clone())).unwrap(),
            workspace_file_call_result(
                ToolOutcome::Error(error.clone()),
                "application/octet-stream".into(),
                "CALLER_DECLARED_UNVERIFIED".into(),
            )
            .unwrap(),
            workspace_content_call_result(ToolOutcome::Error(error)).unwrap(),
        ];
        for response in responses {
            assert_eq!(response.is_error, Some(true));
            assert_eq!(response.structured_content, Some(expected.clone()));
            assert_eq!(response.content.len(), 1);
            let wire = serde_json::to_value(&response.content[0]).unwrap();
            assert_eq!(wire.pointer("/type"), Some(&json!("text")));
            assert_eq!(wire.pointer("/text"), Some(&json!("digest does not match")));
        }
        assert_eq!(
            expected.pointer("/error/retryClass"),
            Some(&json!(ToolRetryClass::Never))
        );
        assert_eq!(
            expected.pointer("/error/commitState"),
            Some(&json!(ToolCommitState::NotStarted))
        );
    }

    #[test]
    fn both_binary_carriers_preserve_qualified_bytes_digest_and_metadata() {
        let bytes = vec![0, 255, 1, 128, 42];
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(&bytes)));
        let responses = [
            artifact_content_call_result(ToolOutcome::Success(ArtifactContentReadResult {
                metadata: ArtifactContentMetadata {
                    job_id: "job-1".into(),
                    artifact_id: "artifact-1".into(),
                    digest: digest.clone(),
                    media_type: "application/octet-stream".into(),
                    byte_length: bytes.len() as u64,
                    truncated: false,
                },
                bytes: bytes.clone(),
            }))
            .unwrap(),
            workspace_file_call_result(
                ToolOutcome::Success(WorkspaceFileReadResult {
                    metadata: WorkspaceFileMetadata {
                        workspace_id: "ws-1".into(),
                        relative_path: "out/raw.bin".into(),
                        digest: digest.clone(),
                        byte_length: bytes.len() as u64,
                    },
                    bytes: bytes.clone(),
                }),
                "application/octet-stream".into(),
                "CALLER_DECLARED_UNVERIFIED".into(),
            )
            .unwrap(),
        ];
        for response in responses {
            assert_eq!(response.is_error, Some(false));
            let wire = serde_json::to_value(&response.content[0]).unwrap();
            let blob = wire
                .pointer("/resource/blob")
                .and_then(Value::as_str)
                .unwrap();
            let actual = BASE64_STANDARD.decode(blob).unwrap();
            assert_eq!(actual, bytes);
            let metadata = response.structured_content.unwrap();
            assert_eq!(metadata.get("digest"), Some(&json!(digest)));
            assert_eq!(metadata.get("byteLength"), Some(&json!(bytes.len())));
            assert_eq!(metadata.get("resourceUri"), wire.pointer("/resource/uri"));
        }
    }
}
