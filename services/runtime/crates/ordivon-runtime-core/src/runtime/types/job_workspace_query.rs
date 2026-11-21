//! Original job workspace query domain wire contract and behavior.
use super::{
    default_schema_version, AttemptState, AttemptTerminationIntent, JobDesiredState, JobResolution,
    RuntimeDeliveryDisposition, CLIENT_REQUEST_ID_MAX_LENGTH, CLIENT_REQUEST_ID_MIN_LENGTH,
    CLIENT_REQUEST_ID_PATTERN, MAX_RUNTIME_LIST_LIMIT, WORKSPACE_ID_MAX_LENGTH,
    WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeWorkspaceGetRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeWorkspaceListCursor {
    pub created_at_ms: u64,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeWorkspaceListRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[serde(default = "default_runtime_list_limit")]
    #[schemars(range(min = 1, max = MAX_RUNTIME_LIST_LIMIT))]
    pub limit: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<RuntimeWorkspaceListCursor>,
    #[serde(default)]
    pub include_source_state_digest: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeWorkspaceSummary {
    pub workspace_id: String,
    /// Canonical source repository identity used to create this Workspace.
    pub source_repo: String,
    /// Exact commit from which the Workspace was opened; this is lineage, not the current HEAD.
    pub source_revision: String,
    /// Exact commit currently checked out at Workspace HEAD.
    pub current_head_revision: String,
    pub created_at_ms: u64,
    pub head_mode: String,
    pub dirty: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source_state_digest: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub active_job_ids: Vec<String>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RuntimeWorkspaceIssueStage {
    Inventory,
    Reconcile,
    Projection,
    ActiveJobs,
    DirtyProbe,
    SourceStateDigest,
    HeadRevision,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeWorkspaceIssue {
    pub workspace_id: String,
    /// Workspace-local projection stage that could not be proven.
    pub stage: RuntimeWorkspaceIssueStage,
    pub code: String,
    pub message: String,
    pub retryable: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeWorkspaceListResult {
    pub workspaces: Vec<RuntimeWorkspaceSummary>,
    /// Stable continuation over healthy Workspace records. Inventory issues are global diagnostics.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<RuntimeWorkspaceListCursor>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub issues: Vec<RuntimeWorkspaceIssue>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeJobListCursor {
    pub created_at_ms: u64,
    pub job_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeJobListRequest {
    #[serde(default = "default_runtime_list_limit")]
    #[schemars(range(min = 1, max = MAX_RUNTIME_LIST_LIMIT))]
    pub limit: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cursor: Option<RuntimeJobListCursor>,
    #[serde(skip_serializing_if = "Option::is_none")]
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: Option<String>,
    /// Exact Runtime Workspace identity used to bound Job reattachment.
    #[serde(skip_serializing_if = "Option::is_none")]
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeJobSummary {
    pub job_id: String,
    /// Stable identity of the committed Runtime Operation represented by this Job.
    pub operation_digest: String,
    /// Compatibility summary only. Use the explicit semantic fields below for control decisions.
    pub status: String,
    /// Persisted Runtime Job intent (`run` or `cancelled`).
    pub desired_state: JobDesiredState,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attempt_id: Option<String>,
    /// Exact current or latest Runtime Attempt state; never collapsed into queued/working.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attempt_state: Option<AttemptState>,
    /// Exact current/latest Attempt termination intent, including stop and deadline intent.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub termination_intent: Option<AttemptTerminationIntent>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub exit_code: Option<i32>,
    /// True only when Runtime has committed a terminal Job resolution.
    pub execution_terminal: bool,
    /// Terminal physical execution resolution; absent while execution is unresolved.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub execution_disposition: Option<JobResolution>,
    /// Stable machine reason for the current terminal execution resolution, when recorded.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub execution_reason_code: Option<String>,
    /// Runtime certainty/reconciliation class for the physical result.
    pub delivery_disposition: RuntimeDeliveryDisposition,
    /// True when Runtime requires mechanical recovery/reconciliation for this Job.
    pub recovery_required: bool,
    /// Always false: Runtime does not judge Task/domain semantic completion.
    pub semantic_completion_evaluated: bool,
    pub client_request_id: String,
    pub workspace_id: String,
    pub source_revision: String,
    pub executable_name: String,
    pub cwd_relative: String,
    pub created_at_ms: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub started_at_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub finished_at_ms: Option<u64>,
    pub duration_ms: u64,
    /// A Runtime terminal result is durably available; this does not imply semantic completion.
    pub result_available: bool,
    /// True only when at least one registered Runtime Artifact exists for this Job.
    pub artifacts_available: bool,
    pub artifact_count: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub poll_after_ms: Option<u64>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeJobListResult {
    pub jobs: Vec<RuntimeJobSummary>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<RuntimeJobListCursor>,
}

#[cfg(any(test, feature = "operator-tools"))]
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeInvariantViolation {
    pub code: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub job_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attempt_id: Option<String>,
    pub detail: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerIdentity {
    pub boot_id: String,
    pub unit_name: String,
    pub invocation_id: String,
    pub control_group: String,
    pub main_pid: u32,
    pub process_start_identity: String,
    pub runner_start_digest: String,
    pub observed_at_ms: u64,
}

pub(crate) fn default_runtime_list_limit() -> u32 {
    20
}
