//! Materialize existing Runtime private stores and preserve actual Windows native ACL protection.
use super::{io_error, UniversalExecError, UniversalExecutorConfig};
use std::fs;

impl UniversalExecutorConfig {
    pub fn ensure_store(&self) -> Result<(), UniversalExecError> {
        self.validate()?;
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
            fs::create_dir_all(&path).map_err(|error| io_error(&path, "create", error))?;
            #[cfg(windows)]
            crate::windows_security::protect_private_directory(&path)
                .map_err(|error| io_error(&path, "protect with native Windows ACL", error))?;
        }
        Ok(())
    }
}
