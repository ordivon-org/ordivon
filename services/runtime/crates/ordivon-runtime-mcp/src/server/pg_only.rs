//! PostgreSQL-native MCP transport without the historical SQLite Runtime Engine.
//! Reuse the exact portable Core types, Serde contracts and SDK schema code.

use std::borrow::Cow;
use std::collections::BTreeMap;
use std::path::PathBuf;
use std::sync::Arc;

use base64::{engine::general_purpose::STANDARD as BASE64_STANDARD, Engine as _};
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
