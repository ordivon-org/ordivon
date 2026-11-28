//! Exact physical store canonicalization and short Unix TMPDIR presentation locator.
use super::{
    invalid, io_error, sha256_bytes, UniversalExecError, UniversalExecErrorCode,
    UniversalExecutorConfig,
};
use std::{
    fs,
    path::{Path, PathBuf},
};

impl UniversalExecutorConfig {
    pub(crate) fn canonical_store_root(&self) -> Result<PathBuf, UniversalExecError> {
        fs::canonicalize(&self.store_root)
            .map_err(|error| io_error(&self.store_root, "canonicalize Runtime store root", error))
    }

    pub(crate) fn workspace_tmp_presentation_path(
        &self,
        workspace_id: &str,
    ) -> Result<PathBuf, UniversalExecError> {
        // Trusted-local tools can derive Unix-domain sockets below TMPDIR. Keep the
        // child-visible pathname bounded independently of store_root/workspace-id length
        // while retaining all bytes in the Workspace-owned backing under cache/tmp.
        // Workspace IDs are store-local. Canonicalize the already-materialized store root
        // before hashing so equivalent absolute spellings or symlink aliases of one physical
        // Runtime store converge on one presentation namespace. The digest is only a locator;
        // exact symlink-target verification remains the authority check.
        let canonical_store = self.canonical_store_root()?;
        let mut identity = canonical_store.as_os_str().as_encoded_bytes().to_vec();
        identity.push(0);
        identity.extend_from_slice(workspace_id.as_bytes());
        let digest = sha256_bytes(&identity);
        let hex = digest.strip_prefix("sha256:").unwrap_or(&digest);
        Ok(PathBuf::from("/tmp/ordivon-t").join(&hex[..20]))
    }

    pub(crate) fn canonical_workspace_tmp_path(
        &self,
        workspace_id: &str,
    ) -> Result<PathBuf, UniversalExecError> {
        Ok(self
            .canonical_store_root()?
            .join("cache")
            .join("tmp")
            .join(workspace_id))
    }
}
pub(crate) fn canonical_directory(path: &Path, field: &str) -> Result<PathBuf, UniversalExecError> {
    let canonical = fs::canonicalize(path).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::IoError,
            format!("cannot canonicalize {}: {error}", path.display()),
            Some(field),
            false,
        )
    })?;
    if !canonical.is_dir() {
        return Err(invalid(format!("{field} must be a directory"), field));
    }
    Ok(canonical)
}
