use std::borrow::Cow;
use std::collections::BTreeMap;
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr};
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex, OnceLock};
use std::time::{Instant, SystemTime, UNIX_EPOCH};

use base64::{engine::general_purpose::STANDARD as BASE64_STANDARD, Engine as _};
use ordivon_runtime_core::{
    read_workspace_content, read_workspace_slice_compact, read_workspace_text_compact,
    workspace_changes_page, workspace_diff_compact, ArtifactReadRequest, ArtifactReadResult,
    CompactWorkspaceDiffResult, CompactWorkspaceOpenResult, CredentialAuthority,
    CredentialBindingRequest, ExecutionBudget, ExecutionProfile, ExecutionProposal,
    ExecutionStepProposal, ExecutionTarget, ForeignReference, GitWorkspaceCreateRequest,
    HostDependencyBinding, InputAuthority, InputBindingRequest, JobCancelRequest, JobObservation,
    JobObserveRequest, JobRunProposal, Runtime, RuntimeCapabilities, RuntimeCapacity,
    RuntimeConfig, RuntimeError, RuntimeExecutionTargetCapability, RuntimeJobInspection,
    RuntimeJobListRequest, RuntimeJobListResult, RuntimeNodeIdentity, RuntimeReleaseAdmission,
    RuntimeReleaseGetRequest, RuntimeReleaseProjection, RuntimeReleaseRequest,
    RuntimeWorkspaceGetRequest, RuntimeWorkspaceListRequest, RuntimeWorkspaceListResult,
    RuntimeWorkspaceSummary, UniversalExecError, UniversalExecutorConfig, WindowsAuthority,
    WindowsExecutionContextRequest, WorkspaceChangeCursor,
    WorkspaceChangePageRequest as ExecWorkspaceChangePageRequest, WorkspaceChangePageResult,
    WorkspaceCloseRequest, WorkspaceCloseResult, WorkspaceContentMetadata, WorkspaceContentRequest,
    WorkspaceDiffRequest as ExecWorkspaceDiffRequest, WorkspaceHeadroomConfig,
    WorkspaceMutateRequest, WorkspaceMutateResult,
    WorkspaceReadRequest as ExecWorkspaceReadRequest, WorkspaceReadSliceRequest,
    CLIENT_REQUEST_ID_MAX_LENGTH, CLIENT_REQUEST_ID_MIN_LENGTH, CLIENT_REQUEST_ID_PATTERN,
    DEFAULT_INSPECTION_EVENT_LIMIT, ENVIRONMENT_VARIABLE_NAME_PATTERN, MAX_INSPECTION_EVENT_LIMIT,
    MAX_TASK_TAIL_BYTES, MAX_TASK_WAIT_MS, MAX_WORKSPACE_CHANGE_PAGE_ENTRIES,
    MAX_WORKSPACE_IO_BYTES, RUNTIME_SCHEMA_VERSION, WORKSPACE_ID_MAX_LENGTH,
    WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};
use rmcp::handler::server::common::FromContextPart;
use rmcp::handler::server::router::tool::ToolRouter;
use rmcp::handler::server::tool::{IntoCallToolResult, ToolCallContext};
use rmcp::handler::server::wrapper::Parameters;
use rmcp::model::*;
use rmcp::service::{RequestContext, RoleServer};
use rmcp::{tool, tool_router, ErrorData as McpError, ServerHandler};
use schemars::{JsonSchema, Schema, SchemaGenerator};
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use uuid::Uuid;

#[cfg(test)]
use ordivon_runtime_core::{LOGICAL_ID_MAX_LENGTH, LOGICAL_ID_MIN_LENGTH, LOGICAL_ID_PATTERN};

use crate::{append_rotating_jsonl, DEFAULT_TRACE_ROTATION_BYTES};

static GLOBAL_TRACE_SEQUENCE: AtomicU64 = AtomicU64::new(1);
static GLOBAL_TRACE_LOCK: OnceLock<Mutex<()>> = OnceLock::new();

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AuthenticatedPrincipalBinding {
    principal: String,
    auth_source: String,
}

impl AuthenticatedPrincipalBinding {
    pub fn new(principal: impl Into<String>, auth_source: impl Into<String>) -> Self {
        Self {
            principal: principal.into(),
            auth_source: auth_source.into(),
        }
    }

    pub fn principal(&self) -> &str {
        &self.principal
    }

    pub fn auth_source(&self) -> &str {
        &self.auth_source
    }
}

fn authenticated_principal_from_http_parts(parts: &axum::http::request::Parts) -> Option<String> {
    parts
        .extensions
        .get::<AuthenticatedPrincipalBinding>()
        .map(|binding| binding.principal.clone())
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct EffectivePrincipal(String);

impl FromContextPart<ToolCallContext<'_, RuntimeServer>> for EffectivePrincipal {
    fn from_context_part(context: &mut ToolCallContext<RuntimeServer>) -> Result<Self, McpError> {
        let request_principal = context
            .request_context
            .extensions
            .get::<axum::http::request::Parts>()
            .and_then(authenticated_principal_from_http_parts);
        Ok(Self(request_principal.unwrap_or_else(|| {
            context.service.state.execution.principal.clone()
        })))
    }
}

include!("contract.rs");
include!("execution_binding.rs");
include!("input_ingress.rs");
include!("server_state.rs");
include!("tool_error.rs");
include!("tracing.rs");

mod handler;
mod tools;

#[cfg(test)]
mod tests;
