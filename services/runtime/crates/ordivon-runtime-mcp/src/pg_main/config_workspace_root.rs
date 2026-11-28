//! Existing PG executor's physical Workspace root must not expose its private
//! journal, credentials, Attempt evidence or cache directory to Session 1.
use std::path::{Path, PathBuf};

pub(super) fn windows_workspace_root(store: &Path, workspace: &Path) -> std::io::Result<PathBuf> {
    use std::io::{Error, ErrorKind};
    if !store.is_absolute() || !workspace.is_absolute() {
        return Err(Error::new(
            ErrorKind::InvalidInput,
            "Windows PG store and Workspace roots must be absolute",
        ));
    }
    // Provisioned by the operator before startup. Never implicitly create a
    // directory or accept a lexical alias as a different physical root.
    let store = store.canonicalize()?;
    let workspace = workspace.canonicalize()?;
    if !store.is_dir() || !workspace.is_dir() {
        return Err(Error::new(
            ErrorKind::InvalidInput,
            "Windows PG roots must be existing directories",
        ));
    }
    // Canonicalize resolves junctions/symlinks; compare each complete path
    // component conservatively case-insensitively on Windows as well.
    fn within(path: &Path, root: &Path) -> bool {
        let mut parts = path.components();
        root.components().all(|parent| {
            parts.next().is_some_and(|child| {
                child.as_os_str().to_string_lossy().to_lowercase()
                    == parent.as_os_str().to_string_lossy().to_lowercase()
            })
        })
    }
    if within(&workspace, &store) || within(&store, &workspace) {
        return Err(Error::new(
            ErrorKind::InvalidInput,
            "Windows PG Workspace root must be physically disjoint from private store",
        ));
    }
    Ok(workspace)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn windows_pg_workspace_root_requires_disjoint_existing_physical_directory() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-winpg-root-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&root).unwrap();
        struct Cleanup(PathBuf);
        impl Drop for Cleanup {
            fn drop(&mut self) {
                let _ = std::fs::remove_dir_all(&self.0);
            }
        }
        let _cleanup = Cleanup(root.clone());
        let store = root.join("private");
        let workspace = root.join("workspace");
        let nested = store.join("nested");
        for path in [&store, &workspace, &nested] {
            std::fs::create_dir(path).unwrap();
        }
        assert_eq!(
            windows_workspace_root(&store, &workspace).unwrap(),
            workspace.canonicalize().unwrap()
        );
        assert!(windows_workspace_root(&store, &store).is_err());
        assert!(windows_workspace_root(&store, &nested).is_err());
        assert!(windows_workspace_root(&store, &root).is_err());
        assert!(windows_workspace_root(&store, &root.join("missing")).is_err());
        assert!(windows_workspace_root(&store, Path::new("relative")).is_err());
        let alias = store.join("..").join("private");
        assert!(windows_workspace_root(&store, &alias).is_err());
    }

    #[cfg(windows)]
    #[test]
    fn windows_pg_workspace_root_rejects_physical_junction_alias() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-winpg-junction-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&root).unwrap();
        struct Cleanup(PathBuf);
        impl Drop for Cleanup {
            fn drop(&mut self) {
                let _ = std::fs::remove_dir_all(&self.0);
            }
        }
        let _cleanup = Cleanup(root.clone());
        let store = root.join("private");
        let alias = root.join("alias");
        std::fs::create_dir(&store).unwrap();
        let cmd = std::path::PathBuf::from(std::env::var_os("SystemRoot").unwrap())
            .join("System32")
            .join("cmd.exe");
        let status = std::process::Command::new(cmd)
            .args(["/d", "/c", "mklink", "/J"])
            .arg(&alias)
            .arg(&store)
            .status()
            .unwrap();
        assert!(status.success(), "native junction fixture creation failed");
        assert!(windows_workspace_root(&store, &alias).is_err());
        std::fs::remove_dir(&alias).unwrap();
    }
}
