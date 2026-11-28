//! Original artifact access domain wire contract and behavior.
use super::{default_schema_version, MAX_ARTIFACT_READ_BYTES};

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ArtifactReadRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    pub job_id: String,
    pub artifact_id: String,
    pub offset: u64,
    #[schemars(range(min = 1, max = MAX_ARTIFACT_READ_BYTES))]
    pub max_bytes: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ArtifactReadResult {
    pub job_id: String,
    pub artifact_id: String,
    pub content: String,
    pub offset: u64,
    pub next_offset: u64,
    pub eof: bool,
    pub digest: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ArtifactContentRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    pub job_id: String,
    pub artifact_id: String,
    #[schemars(range(min = 1, max = MAX_ARTIFACT_READ_BYTES))]
    pub max_bytes: u64,
}

#[derive(Clone, Debug, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ArtifactContentMetadata {
    pub job_id: String,
    pub artifact_id: String,
    pub digest: String,
    pub media_type: String,
    pub byte_length: u64,
    pub truncated: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ArtifactContentReadResult {
    pub metadata: ArtifactContentMetadata,
    pub bytes: Vec<u8>,
}
