//! Public Runtime-owned Workspace Claim contract and original caller identity validation.
use super::*;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

fn schema_one() -> u32 {
    1
}

#[derive(Clone, Debug, Deserialize, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceClaimReserveRequest {
    #[serde(default = "schema_one")]
    pub schema_version: u32,
    pub workspace_id: String,
    pub client_request_id: String,
    pub run_ref: String,
    pub expected_source_state_digest: String,
}

#[derive(Clone, Debug, Deserialize, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceClaimKeyRequest {
    #[serde(default = "schema_one")]
    pub schema_version: u32,
    pub client_request_id: String,
}

#[derive(Clone, Debug, Deserialize, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceClaimProjection {
    pub schema_version: u32,
    pub claim_id: String,
    pub workspace_id: String,
    pub client_request_id: String,
    pub run_ref: String,
    /// Canonical native Runtime store carrier; bare workspaceId is not globally unique.
    pub store_root: String,
    pub source_repo: String,
    pub source_revision: String,
    pub source_state_digest_at_reserve: String,
    /// "held" is a physical pin, NOT proof the Harness Run is READY or
    /// permission to execute. The Harness/Gateway must validate their own
    /// semantic authorization before exposing a Tool grant.
    pub state: String,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
}

pub(super) fn validate_key(
    schema: u32,
    principal: &str,
    client_request_id: &str,
) -> RuntimeResult<()> {
    if schema != 1 {
        return Err(RuntimeError::invalid(
            "schemaVersion must be 1",
            "schemaVersion",
        ));
    }
    crate::runtime::types::validate_logical_id(principal, "principal")?;
    crate::runtime::types::validate_client_request_id(client_request_id, "clientRequestId")?;
    Ok(())
}
