//! Original workspace content behavior and native data contract.
use super::{
    default_schema_version, invalid, is_false, require_schema, valid_digest, validate_id,
    validate_relative_path, UniversalExecError, MAX_WORKSPACE_IO_BYTES, WORKSPACE_ID_MAX_LENGTH,
    WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceReadRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    pub relative_path: String,
    #[schemars(range(min = 1, max = MAX_WORKSPACE_IO_BYTES))]
    pub max_bytes: u64,
}

impl WorkspaceReadRequest {
    pub fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
        validate_relative_path(&self.relative_path, "relativePath")?;
        if self.max_bytes == 0 || self.max_bytes > MAX_WORKSPACE_IO_BYTES {
            return Err(invalid(
                format!("maxBytes must be in 1..={MAX_WORKSPACE_IO_BYTES}"),
                "maxBytes",
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WorkspaceReadResult {
    pub workspace_id: String,
    pub relative_path: String,
    pub content: String,
    pub digest: String,
    pub byte_length: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceContentRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    pub relative_path: String,
    #[schemars(regex(pattern = r"^sha256:[0-9a-f]{64}$"))]
    pub expected_digest: String,
    #[schemars(range(min = 1, max = MAX_WORKSPACE_IO_BYTES))]
    pub max_bytes: u64,
}

impl WorkspaceContentRequest {
    pub fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
        validate_relative_path(&self.relative_path, "relativePath")?;
        if !valid_digest(&self.expected_digest) {
            return Err(invalid(
                "expectedDigest must be canonical lowercase SHA-256",
                "expectedDigest",
            ));
        }
        if self.max_bytes == 0 || self.max_bytes > MAX_WORKSPACE_IO_BYTES {
            return Err(invalid(
                format!("maxBytes must be in 1..={MAX_WORKSPACE_IO_BYTES}"),
                "maxBytes",
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceFileRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    #[serde(default = "default_schema_version")]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    pub relative_path: String,
    #[schemars(regex(pattern = r"^sha256:[0-9a-f]{64}$"))]
    pub expected_digest: String,
    #[schemars(range(min = 1, max = MAX_WORKSPACE_IO_BYTES))]
    pub max_bytes: u64,
}

impl WorkspaceFileRequest {
    pub fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
        validate_relative_path(&self.relative_path, "relativePath")?;
        if !valid_digest(&self.expected_digest) {
            return Err(invalid(
                "expectedDigest must be canonical lowercase SHA-256",
                "expectedDigest",
            ));
        }
        if self.max_bytes == 0 || self.max_bytes > MAX_WORKSPACE_IO_BYTES {
            return Err(invalid(
                format!("maxBytes must be in 1..={MAX_WORKSPACE_IO_BYTES}"),
                "maxBytes",
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceFileMetadata {
    pub workspace_id: String,
    pub relative_path: String,
    pub digest: String,
    pub byte_length: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WorkspaceFileReadResult {
    pub metadata: WorkspaceFileMetadata,
    pub bytes: Vec<u8>,
}

#[derive(Clone, Debug, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceContentMetadata {
    pub workspace_id: String,
    pub relative_path: String,
    pub digest: String,
    pub media_type: String,
    pub byte_length: u64,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WorkspaceContentReadResult {
    pub metadata: WorkspaceContentMetadata,
    pub bytes: Vec<u8>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct CompactWorkspaceReadResult {
    pub content: String,
    pub digest: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WorkspaceWriteRequest {
    pub schema_version: u32,
    pub workspace_id: String,
    pub relative_path: String,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expected_digest: Option<String>,
}

impl WorkspaceWriteRequest {
    pub(crate) fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
        validate_relative_path(&self.relative_path, "relativePath")?;
        if self.content.len() as u64 > MAX_WORKSPACE_IO_BYTES {
            return Err(invalid(
                format!("content exceeds {MAX_WORKSPACE_IO_BYTES} bytes"),
                "content",
            ));
        }
        if self
            .expected_digest
            .as_ref()
            .is_some_and(|digest| !valid_digest(digest))
        {
            return Err(invalid(
                "expectedDigest must be canonical lowercase SHA-256",
                "expectedDigest",
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WorkspaceWriteResult {
    pub workspace_id: String,
    pub relative_path: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub before_digest: Option<String>,
    pub after_digest: String,
    pub byte_length: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceReadSliceRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    pub relative_path: String,
    #[serde(default)]
    pub offset: u64,
    #[schemars(range(min = 1, max = MAX_WORKSPACE_IO_BYTES))]
    pub max_bytes: u64,
}

impl WorkspaceReadSliceRequest {
    pub fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
        validate_relative_path(&self.relative_path, "relativePath")?;
        if self.max_bytes == 0 || self.max_bytes > MAX_WORKSPACE_IO_BYTES {
            return Err(invalid(
                format!("maxBytes must be in 1..={MAX_WORKSPACE_IO_BYTES}"),
                "maxBytes",
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WorkspaceReadSliceResult {
    pub workspace_id: String,
    pub relative_path: String,
    pub content: String,
    pub offset: u64,
    pub next_offset: u64,
    pub eof: bool,
    pub file_digest: String,
    pub file_byte_length: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct CompactWorkspaceSliceResult {
    pub content: String,
    pub file_digest: String,
    pub file_byte_length: u64,
    #[serde(default, skip_serializing_if = "is_false")]
    pub eof: bool,
}
