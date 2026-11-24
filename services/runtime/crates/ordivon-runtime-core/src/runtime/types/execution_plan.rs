//! Original execution plan domain wire contract and behavior.
use super::{
    EffectiveInputBinding, EnvironmentVariableNameSchema, ExecutionProfile,
    ExecutionProviderSnapshot, ExecutionTarget, ForeignReference, HostDependencyBinding,
    RuntimeReleaseEffectBinding, WindowsAuthority, WindowsExecutionContext,
    WindowsExecutionContextRequest, LOGICAL_ID_MAX_LENGTH, LOGICAL_ID_MIN_LENGTH,
    LOGICAL_ID_PATTERN,
};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ExecutionBudget {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scheduling: Option<crate::resource_scheduling::ResourceScheduling>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(range(min = 1))]
    pub memory_max_bytes: Option<u64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(range(min = 1))]
    pub tasks_max: Option<u32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(range(min = 1))]
    pub cpu_quota_percent: Option<u32>,
}

impl ExecutionBudget {
    pub fn is_empty(&self) -> bool {
        self.scheduling.is_none()
            && self.memory_max_bytes.is_none()
            && self.tasks_max.is_none()
            && self.cpu_quota_percent.is_none()
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct UniversalExecutionStep {
    pub id: String,
    /// Absolute host path to the executable; PATH lookup is intentionally not performed.
    pub executable: String,
    #[serde(default)]
    pub args: Vec<String>,
    /// Working directory relative to the Workspace root.
    pub cwd_relative: String,
    #[serde(default)]
    pub env: BTreeMap<String, String>,
    pub timeout_ms: u64,
    #[serde(default)]
    pub continue_on_error: bool,
}

/// Agent-authored execution step before Runtime resolves omitted mechanical limits.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ExecutionStepProposal {
    #[schemars(length(min = LOGICAL_ID_MIN_LENGTH, max = LOGICAL_ID_MAX_LENGTH), extend("pattern" = LOGICAL_ID_PATTERN))]
    pub id: String,
    /// Absolute host path to the executable; PATH lookup is intentionally not performed.
    pub executable: String,
    #[serde(default)]
    pub args: Vec<String>,
    /// Working directory relative to the Workspace root.
    pub cwd_relative: String,
    #[serde(default)]
    #[schemars(with = "BTreeMap<EnvironmentVariableNameSchema, String>")]
    pub env: BTreeMap<String, String>,
    /// Optional step-local upper bound. Omission delegates only this mechanical limit to Runtime.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(range(min = 1))]
    pub timeout_ms: Option<u64>,
    #[serde(default)]
    pub continue_on_error: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RuntimeExecutionStep {
    pub id: String,
    pub executable: String,
    pub executable_digest: String,
    #[serde(default)]
    pub args: Vec<String>,
    pub cwd: String,
    #[serde(default)]
    pub env: BTreeMap<String, String>,
    pub timeout_ms: u64,
    #[serde(default)]
    pub continue_on_error: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RuntimeExecutionPlan {
    pub schema_version: u32,
    pub workspace_id: String,
    pub workspace_path: String,
    pub source_revision: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub workspace_source_digest: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub workspace_git_common_dir: Option<String>,
    pub executable: String,
    pub executable_digest: String,
    #[serde(default)]
    pub args: Vec<String>,
    pub cwd: String,
    #[serde(default)]
    pub env: BTreeMap<String, String>,
    pub timeout_ms: u64,
    pub stdout_limit_bytes: u64,
    pub stderr_limit_bytes: u64,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub steps: Vec<RuntimeExecutionStep>,
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
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub windows_execution_context: Option<WindowsExecutionContext>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub foreign_references: Vec<ForeignReference>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub host_dependencies: Vec<HostDependencyBinding>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub input_set_id: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub effective_inputs: Vec<EffectiveInputBinding>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub credential_set_id: Option<String>,
    pub principal: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct SubmitRequest {
    pub schema_version: u32,
    pub client_request_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub request_identity_digest: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_provider: Option<ExecutionProviderSnapshot>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub runtime_release_effect: Option<RuntimeReleaseEffectBinding>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub host_dependencies: Vec<HostDependencyBinding>,
    pub plan: RuntimeExecutionPlan,
    pub global_limit: u32,
}
