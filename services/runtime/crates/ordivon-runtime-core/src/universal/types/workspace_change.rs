//! Original workspace change behavior and native data contract.
use super::{
    invalid, is_false, require_schema, valid_digest, validate_id, UniversalExecError,
    MAX_WORKSPACE_IO_BYTES, WORKSPACE_ID_MAX_LENGTH, WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceDiffRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    #[schemars(range(min = 1, max = MAX_WORKSPACE_IO_BYTES))]
    pub max_bytes: u64,
}

impl WorkspaceDiffRequest {
    pub fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
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
pub struct WorkspaceRenamedPath {
    pub from_path: String,
    pub to_path: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WorkspaceDiffResult {
    pub workspace_id: String,
    pub diff: String,
    pub digest: String,
    pub byte_length: u64,
    pub truncated: bool,
    pub changed_paths: Vec<String>,
    pub modified_paths: Vec<String>,
    pub added_paths: Vec<String>,
    pub deleted_paths: Vec<String>,
    pub renamed_paths: Vec<WorkspaceRenamedPath>,
    pub untracked_paths: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct CompactWorkspaceDiffResult {
    pub diff: String,
    #[serde(default, skip_serializing_if = "is_false")]
    pub truncated: bool,
    pub changed_paths: Vec<String>,
    pub modified_paths: Vec<String>,
    pub added_paths: Vec<String>,
    pub deleted_paths: Vec<String>,
    pub renamed_paths: Vec<WorkspaceRenamedPath>,
    pub untracked_paths: Vec<String>,
}

pub const MAX_WORKSPACE_CHANGE_PAGE_ENTRIES: u32 = 1024;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceChangeCursor {
    pub change_set_digest: String,
    pub after_path: String,
    pub after_kind: WorkspaceChangeKind,
}

#[derive(
    Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, JsonSchema, Serialize,
)]
#[serde(rename_all = "snake_case")]
pub enum WorkspaceChangeKind {
    Added,
    Deleted,
    Modified,
    Untracked,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceChangeEntry {
    pub kind: WorkspaceChangeKind,
    pub path: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceChangePageRequest {
    #[schemars(range(min = 1, max = 1), extend("const" = 1))]
    pub schema_version: u32,
    #[schemars(length(min = WORKSPACE_ID_MIN_LENGTH, max = WORKSPACE_ID_MAX_LENGTH), regex(pattern = WORKSPACE_ID_PATTERN))]
    pub workspace_id: String,
    #[schemars(range(min = 1, max = MAX_WORKSPACE_CHANGE_PAGE_ENTRIES))]
    pub limit: u32,
    #[schemars(range(min = 1, max = MAX_WORKSPACE_IO_BYTES))]
    pub max_bytes: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub cursor: Option<WorkspaceChangeCursor>,
}

impl WorkspaceChangePageRequest {
    pub fn validate_shape(&self) -> Result<(), UniversalExecError> {
        require_schema(self.schema_version)?;
        validate_id(&self.workspace_id, "workspaceId")?;
        if self.limit == 0 || self.limit > MAX_WORKSPACE_CHANGE_PAGE_ENTRIES {
            return Err(invalid(
                format!("limit must be in 1..={MAX_WORKSPACE_CHANGE_PAGE_ENTRIES}"),
                "limit",
            ));
        }
        if self.max_bytes == 0 || self.max_bytes > MAX_WORKSPACE_IO_BYTES {
            return Err(invalid(
                format!("maxBytes must be in 1..={MAX_WORKSPACE_IO_BYTES}"),
                "maxBytes",
            ));
        }
        if let Some(cursor) = &self.cursor {
            if !valid_digest(&cursor.change_set_digest) {
                return Err(invalid(
                    "cursor.changeSetDigest must be SHA-256",
                    "cursor.changeSetDigest",
                ));
            }
            if cursor.after_path.is_empty()
                || cursor.after_path.len() as u64 > MAX_WORKSPACE_IO_BYTES
                || cursor.after_path.as_bytes().contains(&0)
            {
                return Err(invalid(
                    "cursor.afterPath must be non-empty UTF-8 within the Workspace I/O byte ceiling",
                    "cursor.afterPath",
                ));
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceChangePageResult {
    pub workspace_id: String,
    pub change_set_digest: String,
    #[schemars(length(max = MAX_WORKSPACE_CHANGE_PAGE_ENTRIES))]
    pub entries: Vec<WorkspaceChangeEntry>,
    pub entry_bytes: u64,
    pub total_entries: u64,
    pub remaining_entries: u64,
    pub complete: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub next_cursor: Option<WorkspaceChangeCursor>,
}

#[cfg(test)]
mod page_cursor_behavior_tests {
    use super::*;

    #[test]
    fn cursor_binds_exact_digest_and_bounded_nonempty_resume_key() {
        let mut request = WorkspaceChangePageRequest {
            schema_version: 1,
            workspace_id: "ws-native-original".to_owned(),
            limit: 64,
            max_bytes: 4096,
            cursor: Some(WorkspaceChangeCursor {
                change_set_digest: format!("sha256:{}", "a".repeat(64)),
                after_path: "src/original.rs".to_owned(),
                after_kind: WorkspaceChangeKind::Modified,
            }),
        };
        assert!(request.validate_shape().is_ok());
        request.cursor.as_mut().unwrap().change_set_digest = "unbound".to_owned();
        assert!(request.validate_shape().is_err());
        request.cursor.as_mut().unwrap().change_set_digest = format!("sha256:{}", "b".repeat(64));
        request.cursor.as_mut().unwrap().after_path.clear();
        assert!(request.validate_shape().is_err());
        request.cursor.as_mut().unwrap().after_path = "src/original.rs".to_owned();
        assert!(request.validate_shape().is_ok());
        request.limit = 0;
        assert!(request.validate_shape().is_err());
        request.limit = MAX_WORKSPACE_CHANGE_PAGE_ENTRIES + 1;
        assert!(request.validate_shape().is_err());
    }
}
