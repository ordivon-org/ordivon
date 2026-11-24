//! Original workspace lifecycle behavior and native data contract.
use super::{
    default_schema_version, invalid, require_schema, valid_digest, validate_id, UniversalExecError,
    WORKSPACE_ID_MAX_LENGTH, WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WorkspaceRecord {
    pub(crate) schema_version: u32,
    /// Legacy read-compatibility only. New open records omit workspaceId;
    /// Runtime binds it from the record filename/request identity.
    #[serde(default, skip_serializing)]
    pub(crate) workspace_id: String,
    pub(crate) source_repo: String,
    pub(crate) source_revision: String,
    /// Legacy read-compatibility only. New records omit workspacePath; Runtime
    /// reconstructs the physical path from workspaces_root/workspaceId.
    #[serde(default, skip_serializing)]
    pub(crate) workspace_path: String,
    pub(crate) created_unix_ms: u128,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct CompactWorkspaceOpenResult {
    pub workspace_id: String,
    pub source_revision: String,
    /// PG Runtime opens warn the Agent of operator-owned ephemeral Workspace retention.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub retention_notice: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceCloseRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    #[serde(default)]
    pub force: bool,
    /// Explicit caller assertion that the task consumer has relinquished
    /// this Workspace. This is not an identity/authorization proof.
    #[serde(default)]
    pub consumer_released: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expected_source_state_digest: Option<String>,
}

impl WorkspaceCloseRequest {
    pub fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
        if self
            .expected_source_state_digest
            .as_ref()
            .is_some_and(|digest| !valid_digest(digest))
        {
            return Err(invalid(
                "expectedSourceStateDigest must be SHA-256",
                "expectedSourceStateDigest",
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum WorkspaceClosureDisposition {
    /// This call physically removed the Workspace and committed its closed tombstone.
    Removed,
    /// A closed tombstone already proved the Workspace was closed.
    AlreadyClosed,
    /// Neither Workspace identity record nor directory existed; no exact source state was proven.
    AlreadyAbsent,
    /// The identity record existed but the directory was already missing; Runtime repaired closure metadata.
    RecoveredMissing,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceCloseResult {
    pub workspace_id: String,
    /// Compatibility flag: true only when this call physically removed the Workspace.
    pub removed: bool,
    /// How Runtime proved or completed the closed state.
    pub closure_disposition: WorkspaceClosureDisposition,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source_state_digest: Option<String>,
}
