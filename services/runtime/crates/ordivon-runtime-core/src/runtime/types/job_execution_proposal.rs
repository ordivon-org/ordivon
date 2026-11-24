//! Original job execution proposal domain wire contract and behavior.
use super::{
    default_task_tail_bytes, default_task_wait_ms, EnvironmentVariableNameSchema, ExecutionBudget,
    ExecutionProfile, ExecutionStepProposal, ExecutionTarget, ForeignReference,
    HostDependencyBinding, UniversalExecutionStep, WindowsAuthority,
    WindowsExecutionContextRequest, CLIENT_REQUEST_ID_MAX_LENGTH, CLIENT_REQUEST_ID_MIN_LENGTH,
    CLIENT_REQUEST_ID_PATTERN, MAX_TASK_TAIL_BYTES, MAX_TASK_WAIT_MS, WORKSPACE_ID_MAX_LENGTH,
    WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Agent-authored execution proposal. Action fields are concrete; only proven mechanical
/// execution limits may be omitted and resolved by Runtime at new admission.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ExecutionProposal {
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    /// Absolute host path to the executable; PATH lookup is intentionally not performed.
    pub executable: String,
    #[serde(default)]
    pub args: Vec<String>,
    /// Working directory relative to the Workspace root.
    pub cwd_relative: String,
    #[serde(default)]
    #[schemars(with = "BTreeMap<EnvironmentVariableNameSchema, String>")]
    pub env: BTreeMap<String, String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(range(min = 1))]
    pub timeout_ms: Option<u64>,
    /// Maximum stdout bytes Runtime retains for the Job/Attempt. This is durable output
    /// capture, not the response tail returned by the admitting MCP call; callers tune that
    /// separately with top-level `stdoutTailBytes`.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(range(min = 1))]
    pub stdout_limit_bytes: Option<u64>,
    /// Maximum stderr bytes Runtime retains for the Job/Attempt. This is durable output
    /// capture, not the response tail returned by the admitting MCP call; callers tune that
    /// separately with top-level `stderrTailBytes`.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(range(min = 1))]
    pub stderr_limit_bytes: Option<u64>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub steps: Vec<ExecutionStepProposal>,
    #[serde(default, skip_serializing_if = "ExecutionBudget::is_empty")]
    pub budget: ExecutionBudget,
    #[serde(default)]
    pub execution_profile: ExecutionProfile,
    #[serde(default)]
    pub execution_target: ExecutionTarget,
    #[serde(default)]
    pub windows_authority: WindowsAuthority,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub windows_context: Option<WindowsExecutionContextRequest>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub foreign_references: Vec<ForeignReference>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub host_dependencies: Vec<HostDependencyBinding>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct JobRunProposal {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    pub schema_version: u32,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
    pub principal: String,
    pub global_limit: u32,
    pub execution: ExecutionProposal,
    #[serde(default = "default_task_wait_ms")]
    #[schemars(range(max = MAX_TASK_WAIT_MS))]
    pub wait_ms: u64,
    #[serde(default = "default_task_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stdout_tail_bytes: u64,
    #[serde(default = "default_task_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stderr_tail_bytes: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct UniversalExecutionRequest {
    pub workspace_id: String,
    /// Absolute host path to the executable; PATH lookup is intentionally not performed.
    pub executable: String,
    #[serde(default)]
    pub args: Vec<String>,
    /// Working directory relative to the Workspace root.
    pub cwd_relative: String,
    #[serde(default)]
    pub env: BTreeMap<String, String>,
    pub timeout_ms: u64,
    pub stdout_limit_bytes: u64,
    pub stderr_limit_bytes: u64,
    /// Optional ordered fail-fast steps. Empty preserves raw single-command execution.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub steps: Vec<UniversalExecutionStep>,
    #[serde(default, skip_serializing_if = "ExecutionBudget::is_empty")]
    pub budget: ExecutionBudget,
    #[serde(default)]
    pub execution_profile: ExecutionProfile,
    #[serde(default)]
    pub execution_target: ExecutionTarget,
    #[serde(default)]
    pub windows_authority: WindowsAuthority,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub windows_context: Option<WindowsExecutionContextRequest>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub foreign_references: Vec<ForeignReference>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub host_dependencies: Vec<HostDependencyBinding>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct JobRunRequest {
    pub schema_version: u32,
    pub client_request_id: String,
    pub principal: String,
    pub global_limit: u32,
    pub execution: UniversalExecutionRequest,
    #[serde(default = "default_task_wait_ms")]
    pub wait_ms: u64,
    #[serde(default = "default_task_tail_bytes")]
    pub stdout_tail_bytes: u64,
    #[serde(default = "default_task_tail_bytes")]
    pub stderr_tail_bytes: u64,
}
