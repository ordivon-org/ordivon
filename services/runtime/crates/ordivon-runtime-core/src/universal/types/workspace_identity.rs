//! Original workspace identity behavior and native data contract.
use super::{
    invalid, require_schema, validate_id, UniversalExecError, WORKSPACE_ID_MAX_LENGTH,
    WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct GitWorkspaceCreateRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    pub source_repo: String,
    pub source_revision: String,
}

impl GitWorkspaceCreateRequest {
    pub fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
        if self.source_repo.is_empty()
            || !std::path::Path::new(&self.source_repo).is_absolute()
            || self.source_repo.as_bytes().contains(&0)
        {
            return Err(invalid(
                "sourceRepo must be an absolute NUL-free path",
                "sourceRepo",
            ));
        }
        if self.source_revision.trim().is_empty()
            || self.source_revision.len() > 256
            || self.source_revision.as_bytes().contains(&0)
        {
            return Err(invalid(
                "sourceRevision must be non-empty, bounded, and NUL-free",
                "sourceRevision",
            ));
        }
        Ok(())
    }
}
