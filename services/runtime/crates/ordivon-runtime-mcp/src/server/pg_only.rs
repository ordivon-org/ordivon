//! PostgreSQL-native MCP transport without the historical SQLite Runtime Engine.
//! Reuse the exact portable Core types, Serde contracts and SDK schema code.

use std::borrow::Cow;
use std::collections::BTreeMap;
use std::path::PathBuf;
use std::sync::Arc;

use ordivon_runtime_core::*;
use ordivon_runtime_core::{
    WorkspaceChangePageRequest as ExecWorkspaceChangePageRequest,
    WorkspaceDiffRequest as ExecWorkspaceDiffRequest,
    WorkspaceReadRequest as ExecWorkspaceReadRequest,
};
use rmcp::handler::server::tool::IntoCallToolResult;
use rmcp::model::*;
use rmcp::service::{RequestContext, RoleServer};
use rmcp::{ErrorData as McpError, ServerHandler};
use schemars::{JsonSchema, Schema, SchemaGenerator};
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use uuid::Uuid;

include!("contract.rs");
include!("execution_binding.rs");
include!("tool_error.rs");
include!("pg_catalog.rs");
include!("pg_output_contract.rs");
include!("pg_server.rs");

#[cfg(test)]
mod workspace_open_identity_negative_tests {
    use super::*;

    #[test]
    fn pg_only_workspace_open_requires_caller_owned_stable_identity() {
        let input = serde_json::json!({
            "sourceRepo": "/tmp/source",
            "sourceRevision": "HEAD",
        });
        assert!(
            serde_json::from_value::<WorkspaceOpenRequest>(input).is_err(),
            "a lost response without a caller-owned ID must never create a second Git worktree"
        );
        let null_id = serde_json::json!({
            "workspaceId": null,
            "sourceRepo": "/tmp/source",
            "sourceRevision": "HEAD",
        });
        assert!(serde_json::from_value::<WorkspaceOpenRequest>(null_id).is_err());

        let explicit: WorkspaceOpenRequest = serde_json::from_value(serde_json::json!({
            "workspaceId": "ws-stable-request-001",
            "sourceRepo": "/tmp/source",
            "sourceRevision": "HEAD",
        }))
        .unwrap();
        assert_eq!(explicit.bind().workspace_id, "ws-stable-request-001");
    }

    #[test]
    fn pg_only_workspace_open_schema_requires_workspace_id_in_caller_contract() {
        let schema = serde_json::to_value(schemars::schema_for!(WorkspaceOpenRequest)).unwrap();
        let required = schema
            .pointer("/required")
            .and_then(serde_json::Value::as_array)
            .unwrap();
        assert!(required.iter().any(|x| x == "workspaceId"));
        assert!(required.iter().any(|x| x == "sourceRepo"));
        assert!(required.iter().any(|x| x == "sourceRevision"));
    }
}
