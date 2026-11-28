//! Original node capability domain wire contract and behavior.
use super::{
    ExecutionProfile, ExecutionProviderSnapshot, ExecutionTarget, WindowsAuthority,
    WindowsExecutionContextRequest,
};

use schemars::JsonSchema;
use serde::Serialize;

#[derive(Clone, Copy, Debug, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RuntimeNodePlatform {
    Linux,
    Windows,
    Other,
}

impl RuntimeNodePlatform {
    pub(crate) fn current() -> Self {
        if cfg!(target_os = "linux") {
            Self::Linux
        } else if cfg!(windows) {
            Self::Windows
        } else {
            Self::Other
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeNodeIdentity {
    pub node_id: String,
    pub platform: RuntimeNodePlatform,
    /// True when this Runtime process is hosted by the platform it claims rather than
    /// projecting a foreign execution target through another host OS.
    pub native: bool,
}

#[derive(Clone, Debug, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeExecutionTargetCapability {
    pub target: ExecutionTarget,
    pub configured: bool,
    pub available: bool,
    pub execution_profiles: Vec<ExecutionProfile>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub windows_authorities: Vec<WindowsAuthority>,
    /// Canonical Windows identity x payload-privilege contexts proven available by the live provider.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub windows_contexts: Vec<WindowsExecutionContextRequest>,
    /// Windows authorities for which Runtime can present exact immutable inputs.
    /// Empty for non-Windows targets and when no safe native presentation is available.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub windows_immutable_input_authorities: Vec<WindowsAuthority>,
    /// Operator-configured privileged profile ids discoverable by Agents without exposing
    /// executable rules, filesystem paths, or principal ceilings.
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub windows_privileged_profiles: Vec<String>,
    /// Whether this Runtime has an owner-native Windows maintenance admission fence configured.
    #[serde(default)]
    pub windows_maintenance_fence_configured: bool,
    pub structured_plan: bool,
    pub immutable_inputs: bool,
    /// Whether trusted-local Jobs on this target may bind Agent-declared exact host file prerequisites.
    pub host_dependency_commitments: bool,
    /// Machine-readable boundary for Host Dependency continuity evidence on this target.
    /// This describes what Runtime witnesses; it is not a claim that target code cannot
    /// intentionally establish another mount/root namespace view.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub host_dependency_continuity_scope: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub execution_provider: Option<ExecutionProviderSnapshot>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub availability_issue: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeCapabilities {
    pub schema_version: u32,
    pub node: RuntimeNodeIdentity,
    pub default_runtime_ms: u64,
    pub max_runtime_ms: u64,
    pub max_output_bytes: u64,
    pub allowed_executable_roots: Vec<String>,
    pub input_authorities: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub credential_authorities: Vec<String>,
    pub targets: Vec<RuntimeExecutionTargetCapability>,
}
