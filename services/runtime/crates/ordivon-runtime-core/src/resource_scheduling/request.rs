//! Original caller resource estimates and validation; native hard budgets live elsewhere.
use super::workspace_access::WorkspaceAccess;
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::path::{Component, Path};

#[derive(Clone, Debug, Deserialize, Serialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ResourceRequest {
    pub cpu_millis: u32,
    pub memory_bytes: u64,
    pub pids: u32,
    #[serde(default)]
    pub io_intensive: bool,
}
impl Default for ResourceRequest {
    fn default() -> Self {
        Self {
            cpu_millis: 100,
            memory_bytes: 128 * 1024 * 1024,
            pids: 16,
            io_intensive: false,
        }
    }
}

#[derive(Clone, Debug, Default, Deserialize, Serialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ResourceScheduling {
    #[serde(default)]
    pub resources: ResourceRequest,
    #[serde(default)]
    pub workspace_access: WorkspaceAccess,
    /// Trusted operator accounting label, not an authentication identity.
    #[serde(default)]
    pub owner: String,
    #[serde(default)]
    pub priority: i16,
    #[serde(default)]
    pub memory_high_bytes: Option<u64>,
    #[serde(default)]
    pub io_weight: Option<u16>,
}
impl ResourceScheduling {
    pub fn validate(&self) -> Result<(), String> {
        if self.resources.memory_bytes == 0
            || self.resources.memory_bytes > i64::MAX as u64
            || self.resources.pids == 0
            || self.owner.len() > 128
            || self.owner.contains(['\0', '\n'])
        {
            return Err("invalid resource request or accounting owner".into());
        }
        if self.memory_high_bytes == Some(0)
            || self.io_weight.is_some_and(|w| !(1..=10000).contains(&w))
        {
            return Err("invalid soft native resource control".into());
        }
        let a = &self.workspace_access;
        if a.read_only && !a.write_paths.is_empty() {
            return Err("readOnly conflicts with writePaths".into());
        }
        if a.read_paths.len() > 64 || a.write_paths.len() > 64 {
            return Err("too many Workspace access paths".into());
        }
        for path in a.read_paths.iter().chain(&a.write_paths) {
            if path.is_empty()
                || Path::new(path).is_absolute()
                || path.contains(['\0', ':', '\n', ' '])
                || Path::new(path)
                    .components()
                    .any(|p| !matches!(p, Component::Normal(_) | Component::CurDir))
                || path.split('/').any(|p| p == ".git")
            {
                return Err(
                    "Workspace access paths must be contained relative paths outside .git".into(),
                );
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod resource_request_business_tests {
    use super::*;

    #[test]
    fn scoped_writer_may_use_normal_subtrees_but_never_git_metadata() {
        let mut scheduling = ResourceScheduling::default();
        scheduling.workspace_access.write_paths = vec!["docs".to_string()];
        assert!(scheduling.validate().is_ok());
        scheduling.workspace_access.write_paths = vec!["docs/.git/objects".to_string()];
        assert!(scheduling.validate().is_err());
        scheduling.workspace_access.write_paths = vec!["../foreign".to_string()];
        assert!(scheduling.validate().is_err());
    }
}
