//! Original scoped Workspace, cache, inputs and credentials path naming, no extra registry.
use super::UniversalExecutorConfig;
use std::path::PathBuf;

impl UniversalExecutorConfig {
    pub fn workspaces_root(&self) -> PathBuf {
        self.workspace_root
            .clone()
            .unwrap_or_else(|| self.store_root.join("workspaces"))
    }

    pub fn workspace_records_root(&self) -> PathBuf {
        self.store_root.join("workspace-records")
    }

    pub fn cache_root(&self) -> PathBuf {
        self.store_root.join("cache")
    }

    pub fn workspace_caches_root(&self) -> PathBuf {
        self.cache_root().join("workspaces")
    }

    pub fn build_caches_root(&self) -> PathBuf {
        self.cache_root().join("build")
    }

    pub fn source_build_caches_root(&self) -> PathBuf {
        self.build_caches_root().join("sources")
    }

    pub fn workspace_tmp_root(&self) -> PathBuf {
        self.cache_root().join("tmp")
    }

    pub fn shared_caches_root(&self) -> PathBuf {
        self.cache_root().join("shared")
    }

    pub fn input_materializations_root(&self) -> PathBuf {
        self.store_root.join("input-materializations")
    }

    pub fn job_inputs_root(&self) -> PathBuf {
        self.store_root.join("job-inputs")
    }

    pub fn job_input_path(&self, job_id: &str) -> PathBuf {
        self.job_inputs_root().join(job_id)
    }

    pub fn credential_materializations_root(&self) -> PathBuf {
        self.store_root.join("credential-materializations")
    }

    pub fn job_credentials_root(&self) -> PathBuf {
        self.store_root.join("job-credentials")
    }

    pub fn job_credential_path(&self, job_id: &str) -> PathBuf {
        self.job_credentials_root().join(job_id)
    }

    pub(crate) fn workspace_cache_path(&self, workspace_id: &str) -> PathBuf {
        self.workspace_caches_root().join(workspace_id)
    }

    /// The Windows PG presentation root is disjoint from the private Store.
    /// A leading-dot sibling cannot collide with a valid Workspace ID.
    /// The provider must grant only this leaf and the admitted worktree leaf.
    pub(crate) fn workspace_private_git_path(&self, workspace_id: &str) -> PathBuf {
        #[cfg(windows)]
        if let Some(root) = &self.workspace_root {
            return root.join(format!(".{workspace_id}.agent-git"));
        }
        self.workspace_cache_path(workspace_id).join("agent-git")
    }

    pub(crate) fn workspace_build_cache_path(&self, workspace_id: &str) -> PathBuf {
        self.build_caches_root().join(workspace_id)
    }

    pub(crate) fn workspace_tmp_path(&self, workspace_id: &str) -> PathBuf {
        self.workspace_tmp_root().join(workspace_id)
    }

    pub(crate) fn workspace_path(&self, workspace_id: &str) -> PathBuf {
        self.workspaces_root().join(workspace_id)
    }

    pub(crate) fn workspace_record_path(&self, workspace_id: &str) -> PathBuf {
        self.workspace_records_root()
            .join(format!("{workspace_id}.json"))
    }
}
