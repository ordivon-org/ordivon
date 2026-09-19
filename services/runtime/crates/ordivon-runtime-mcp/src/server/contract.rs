/// Pinned MCP tool-input schema version. Omitted `schemaVersion` defaults to
/// the current pinned version so external clients (which do not read the
/// `const` pin) can call tools without carrying an internal version field;
/// explicit non-pinned values are still rejected by handlers.
fn default_schema_version() -> u32 {
    1
}

#[allow(dead_code)]
#[derive(JsonSchema)]
#[schemars(extend("pattern" = ENVIRONMENT_VARIABLE_NAME_PATTERN))]
struct EnvironmentVariableNameSchema(String);

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceOpenRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: Option<String>,
    pub source_repo: String,
    pub source_revision: String,
}

impl WorkspaceOpenRequest {
    fn bind(self) -> GitWorkspaceCreateRequest {
        GitWorkspaceCreateRequest {
            schema_version: self.schema_version,
            workspace_id: self
                .workspace_id
                .unwrap_or_else(|| format!("ws-{}", Uuid::now_v7())),
            source_repo: self.source_repo,
            source_revision: self.source_revision,
        }
    }
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum WorkspaceReadMode {
    Full,
    Slice,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceReadRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    pub relative_path: String,
    pub mode: WorkspaceReadMode,
    #[serde(default)]
    pub offset: u64,
    #[schemars(range(min = 1, max = MAX_WORKSPACE_IO_BYTES))]
    pub max_bytes: u64,
}

#[derive(Clone, Debug, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct WorkspaceReadResult {
    pub content: String,
    pub digest: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub file_byte_length: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub eof: Option<bool>,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceDiffRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    #[schemars(range(min = 1, max = MAX_WORKSPACE_IO_BYTES))]
    pub max_bytes: u64,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct JobGetRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    pub job_id: String,
    #[serde(default = "default_task_get_event_limit")]
    #[schemars(range(min = 1, max = MAX_INSPECTION_EVENT_LIMIT))]
    pub event_limit: u32,
}

fn default_task_get_event_limit() -> u32 {
    DEFAULT_INSPECTION_EVENT_LIMIT
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeDescribeRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
}

#[derive(Clone, Debug, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeDescribeResult {
    pub schema_version: u32,
    pub node: RuntimeNodeIdentity,
    pub global_execution_limit: u32,
    pub default_runtime_ms: u64,
    pub max_runtime_ms: u64,
    pub max_output_bytes: u64,
    pub allowed_executable_roots: Vec<String>,
    pub input_authorities: Vec<String>,
    pub credential_authorities: Vec<String>,
    pub input_ingress_authorities: Vec<String>,
    pub targets: Vec<RuntimeExecutionTargetCapability>,
    pub structured_release_configured: bool,
}

impl RuntimeDescribeResult {
    fn from_capabilities(
        capabilities: RuntimeCapabilities,
        global_execution_limit: u32,
        structured_release_configured: bool,
        input_ingress_authorities: Vec<String>,
    ) -> Self {
        Self {
            schema_version: capabilities.schema_version,
            node: capabilities.node,
            global_execution_limit,
            default_runtime_ms: capabilities.default_runtime_ms,
            max_runtime_ms: capabilities.max_runtime_ms,
            max_output_bytes: capabilities.max_output_bytes,
            allowed_executable_roots: capabilities.allowed_executable_roots,
            input_authorities: capabilities.input_authorities,
            credential_authorities: capabilities.credential_authorities,
            input_ingress_authorities,
            targets: capabilities.targets,
            structured_release_configured,
        }
    }
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeReleaseApplyToolRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    pub commit: String,
    pub candidate_manifest_digest: String,
    #[schemars(range(min = 1))]
    pub expected_tool_count: u32,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeReleaseGetToolRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct InputIngressFilePayload {
    #[serde(rename = "download_url")]
    #[schemars(rename = "download_url")]
    pub download_url: String,
    #[serde(rename = "file_id")]
    #[schemars(rename = "file_id")]
    pub file_id: String,
    #[serde(default, rename = "file_name", skip_serializing_if = "Option::is_none")]
    #[schemars(rename = "file_name")]
    pub file_name: Option<String>,
    #[serde(default, rename = "mime_type", skip_serializing_if = "Option::is_none")]
    #[schemars(rename = "mime_type")]
    pub mime_type: Option<String>,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct InputIngressToolRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
    pub authority: String,
    pub relative_object: String,
    pub expected_sha256: String,
    #[schemars(range(min = 1))]
    pub expected_size_bytes: u64,
    pub file: InputIngressFilePayload,
}

#[derive(Clone, Debug, Serialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct InputIngressToolResult {
    pub schema_version: u32,
    pub kind: String,
    pub authority: String,
    pub relative_object: String,
    pub expected_sha256: String,
    pub expected_size_bytes: u64,
    pub host_file_reference_digest: String,
    pub source_identity_standing: String,
    pub workstation_receipt: serde_json::Value,
    pub non_claims: Vec<String>,
}

#[derive(Clone, Debug)]
pub struct InputIngressExecutionConfig {
    pub staging_root: PathBuf,
    pub workstation_tool: PathBuf,
    pub workstation_config: PathBuf,
    pub workstation_carrier: String,
    pub authorities: Vec<String>,
    pub download_hosts: Vec<String>,
    pub max_bytes: u64,
}

#[derive(Clone, Debug)]
pub struct RuntimeReleaseExecutionConfig {
    pub source_repo: PathBuf,
    pub install_dir: PathBuf,
    pub database: PathBuf,
    pub env_file: PathBuf,
    pub receipt_root: PathBuf,
    pub required_ref: String,
    pub timeout_ms: u64,
}

impl RuntimeReleaseExecutionConfig {
    fn candidate_dir(&self, commit: &str) -> PathBuf {
        self.source_repo
            .join("target")
            .join("ordivon-release-candidates")
            .join(commit)
            .join("release")
    }
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceChangesRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    #[serde(default = "default_change_page_limit")]
    #[schemars(range(min = 1, max = MAX_WORKSPACE_CHANGE_PAGE_ENTRIES))]
    pub limit: u32,
    #[serde(default = "default_change_page_bytes")]
    #[schemars(range(min = 1, max = MAX_WORKSPACE_IO_BYTES))]
    pub max_bytes: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub cursor: Option<WorkspaceChangeCursor>,
}

fn default_change_page_limit() -> u32 {
    64
}

fn default_change_page_bytes() -> u64 {
    256 * 1024
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceExecRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
    pub execution: ExecutionProposal,
    /// Maximum time this MCP call waits for observation before returning. This does not
    /// change the Job execution timeout; use `execution.timeoutMs` for that limit.
    #[serde(default = "default_exec_wait_ms")]
    #[schemars(range(max = MAX_TASK_WAIT_MS))]
    pub wait_ms: u64,
    /// Maximum retained stdout bytes included in this MCP response tail (0..=65536).
    /// This does not change Job output retention; use `execution.stdoutLimitBytes` for that.
    #[serde(default = "default_exec_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stdout_tail_bytes: u64,
    /// Maximum retained stderr bytes included in this MCP response tail (0..=65536).
    /// This does not change Job output retention; use `execution.stderrLimitBytes` for that.
    #[serde(default = "default_exec_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stderr_tail_bytes: u64,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceExecBoundExecution {
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
    pub execution_target: ExecutionTarget,
    #[serde(default)]
    pub windows_authority: WindowsAuthority,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub foreign_references: Vec<ForeignReference>,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceExecBoundRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
    pub execution: WorkspaceExecBoundExecution,
    #[schemars(length(min = 1))]
    pub inputs: Vec<InputBindingRequest>,
    /// Maximum time this MCP call waits for observation before returning. This does not
    /// change the Job execution timeout; use `execution.timeoutMs` for that limit.
    #[serde(default = "default_exec_wait_ms")]
    #[schemars(range(max = MAX_TASK_WAIT_MS))]
    pub wait_ms: u64,
    /// Maximum retained stdout bytes included in this MCP response tail (0..=65536).
    /// This does not change Job output retention; use `execution.stdoutLimitBytes` for that.
    #[serde(default = "default_exec_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stdout_tail_bytes: u64,
    /// Maximum retained stderr bytes included in this MCP response tail (0..=65536).
    /// This does not change Job output retention; use `execution.stderrLimitBytes` for that.
    #[serde(default = "default_exec_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stderr_tail_bytes: u64,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceExecCredentialBoundRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
    pub execution: WorkspaceExecBoundExecution,
    #[schemars(length(min = 1))]
    pub credentials: Vec<CredentialBindingRequest>,
    #[serde(default = "default_exec_wait_ms")]
    #[schemars(range(max = MAX_TASK_WAIT_MS))]
    pub wait_ms: u64,
    #[serde(default = "default_exec_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stdout_tail_bytes: u64,
    #[serde(default = "default_exec_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stderr_tail_bytes: u64,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceExecPlanInput {
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    #[schemars(length(min = 1))]
    pub steps: Vec<ExecutionStepProposal>,
    /// Optional Job-wide deadline. The fully explicit legacy request shape preserves its
    /// historical step-sum identity; every proposal-shaped omission delegates to Runtime.
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
    #[serde(default, skip_serializing_if = "ExecutionBudget::is_empty")]
    pub budget: ExecutionBudget,
    #[serde(default)]
    pub execution_profile: ExecutionProfile,
    #[serde(default)]
    pub execution_target: ExecutionTarget,
    #[serde(default)]
    pub windows_authority: WindowsAuthority,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub foreign_references: Vec<ForeignReference>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub host_dependencies: Vec<HostDependencyBinding>,
}

#[derive(Clone, Debug, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceExecPlanRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
    pub execution: WorkspaceExecPlanInput,
    /// Maximum time this MCP call waits for observation before returning. This does not
    /// change the Job execution timeout; use `execution.timeoutMs` for that limit.
    #[serde(default = "default_exec_wait_ms")]
    #[schemars(range(max = MAX_TASK_WAIT_MS))]
    pub wait_ms: u64,
    /// Maximum retained stdout bytes included in this MCP response tail (0..=65536).
    /// This does not change Job output retention; use `execution.stdoutLimitBytes` for that.
    #[serde(default = "default_exec_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stdout_tail_bytes: u64,
    /// Maximum retained stderr bytes included in this MCP response tail (0..=65536).
    /// This does not change Job output retention; use `execution.stderrLimitBytes` for that.
    #[serde(default = "default_exec_tail_bytes")]
    #[schemars(range(max = MAX_TASK_TAIL_BYTES))]
    pub stderr_tail_bytes: u64,
}
