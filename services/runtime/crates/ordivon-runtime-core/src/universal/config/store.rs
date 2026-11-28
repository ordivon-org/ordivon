//! Materialize existing Runtime private stores and preserve actual Windows native ACL protection.
use super::{io_error, UniversalExecError, UniversalExecutorConfig};
use std::fs;

impl UniversalExecutorConfig {
    pub fn ensure_store(&self) -> Result<(), UniversalExecError> {
        self.validate()?;
        // The Windows SCM materializer owns the separate interactive
        // presentation root and its non-inheriting desktop identity ACE.
        // Re-protecting it here on every open/close erases that exact ACE.
        #[cfg(windows)]
        self.require_existing_windows_presentation_root()?;
        for path in [
            self.store_root.clone(),
            self.workspaces_root(),
            self.workspace_records_root(),
            self.workspace_caches_root(),
            self.build_caches_root(),
            self.source_build_caches_root(),
            self.workspace_tmp_root(),
            self.shared_caches_root(),
            self.input_materializations_root(),
            self.job_inputs_root(),
            self.credential_materializations_root(),
            self.job_credentials_root(),
        ] {
            #[cfg(windows)]
            if self.workspace_root.as_ref() == Some(&path) {
                // Already qualified above; the private store still receives
                // its original exact native DACL on every ensure_store.
                continue;
            }
            fs::create_dir_all(&path).map_err(|error| io_error(&path, "create", error))?;
            #[cfg(windows)]
            crate::windows_security::protect_private_directory(&path)
                .map_err(|error| io_error(&path, "protect with native Windows ACL", error))?;
        }
        Ok(())
    }

    #[cfg(windows)]
    fn require_existing_windows_presentation_root(&self) -> Result<(), UniversalExecError> {
        use super::invalid;
        use std::path::Path;
        let Some(root) = self.workspace_root.as_ref() else {
            return Ok(()); // legacy private workspace remains unchanged
        };
        // Both roots are pre-provisioned by the disabled SCM stage. Native
        // nofollow rejects a replaced final component before any store effect.
        let _root = super::super::fsutil::open_directory_nofollow(root)
            .map_err(|e| io_error(root, "open operator Workspace presentation root", e))?;
        let _store = super::super::fsutil::open_directory_nofollow(&self.store_root)
            .map_err(|e| io_error(&self.store_root, "open private store root", e))?;
        let physical =
            |path: &Path| fs::canonicalize(path).map_err(|e| io_error(path, "resolve root", e));
        let store = physical(&self.store_root)?;
        let workspace = physical(root)?;
        let within = |path: &Path, parent: &Path| {
            let mut parts = path.components();
            parent.components().all(|p| {
                parts.next().is_some_and(|c| {
                    c.as_os_str().to_string_lossy().to_lowercase()
                        == p.as_os_str().to_string_lossy().to_lowercase()
                })
            })
        };
        if within(&workspace, &store) || within(&store, &workspace) {
            return Err(invalid(
                "Workspace presentation and private store must be physically disjoint",
                "workspaceRoot",
            ));
        }
        Ok(())
    }
}
