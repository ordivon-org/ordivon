//! Original runtime release domain wire contract and behavior.
use super::{
    default_schema_version, AttemptState, JobResolution, RuntimeDeliveryDisposition,
    CLIENT_REQUEST_ID_MAX_LENGTH, CLIENT_REQUEST_ID_MIN_LENGTH, CLIENT_REQUEST_ID_PATTERN,
    WORKSPACE_ID_MAX_LENGTH, WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RuntimeReleaseContract {
    RuntimeReleaseV1,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeReleaseRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
    pub principal: String,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    pub commit: String,
    pub candidate_manifest_digest: String,
    pub expected_tool_count: u32,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct RuntimeReleaseGetRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    pub principal: String,
    #[schemars(length(min = CLIENT_REQUEST_ID_MIN_LENGTH, max = CLIENT_REQUEST_ID_MAX_LENGTH), extend("pattern" = CLIENT_REQUEST_ID_PATTERN))]
    pub client_request_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RuntimeReleaseEffectBinding {
    pub contract: RuntimeReleaseContract,
    pub effect_id: String,
    pub request_digest: String,
    pub workspace_id: String,
    pub commit: String,
    pub candidate_manifest_digest: String,
    pub expected_tool_count: u32,
    pub receipt_path: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RuntimeReleaseDisposition {
    Admitted,
    InProgress,
    Deployed,
    NotCommitted,
    RolledBack,
    ReconciliationRequired,
}

#[derive(Clone, Debug, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeReleaseProjection {
    pub contract: RuntimeReleaseContract,
    pub effect_id: String,
    pub client_request_id: String,
    pub job_id: String,
    pub workspace_id: String,
    pub commit: String,
    pub candidate_manifest_digest: String,
    pub expected_tool_count: u32,
    pub effect_disposition: RuntimeReleaseDisposition,
    pub effect_terminal: bool,
    pub receipt_available: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub receipt_digest: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub deployed_tool_count: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_catalog_digest: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub rollback_status: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub reconciliation_issue: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attempt_state: Option<AttemptState>,
    pub execution_terminal: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub execution_disposition: Option<JobResolution>,
    pub delivery_disposition: RuntimeDeliveryDisposition,
    pub recovery_required: bool,
    pub semantic_completion_evaluated: bool,
}

#[derive(Clone, Debug, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RuntimeReleaseAdmission {
    pub replayed: bool,
    pub release: RuntimeReleaseProjection,
}
