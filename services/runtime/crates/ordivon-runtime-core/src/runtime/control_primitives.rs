//! Small mechanical control primitives shared by Runtime operations.
//!
//! These primitives deliberately do not own workflow, domain compensation, or a second durable
//! lifecycle. Operation-specific owners decide when to use them and retain their own state and
//! evidence contracts.

use std::fs::{File, OpenOptions};
#[cfg(unix)]
use std::os::unix::fs::OpenOptionsExt;
use std::path::Path;

use super::{RuntimeError, RuntimeErrorCode, RuntimeResult};

/// Acquire a shared, non-blocking file fence.
///
/// The returned `File` is the lifetime guard: dropping it releases the lock. Callers provide the
/// operation-specific blocked error so this primitive does not invent admission or deployment
/// semantics.
pub(crate) fn acquire_shared_file_fence(
    path: &Path,
    label: &str,
    blocked: RuntimeError,
) -> RuntimeResult<File> {
    let mut options = OpenOptions::new();
    options.read(true).write(true).create(true).truncate(false);
    #[cfg(unix)]
    options.mode(0o600);
    let file = options.open(path).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::RegistryUnavailable,
            format!("cannot open {label} {}: {error}", path.display()),
            None,
            true,
        )
    })?;
    match file.try_lock_shared() {
        Ok(()) => Ok(file),
        Err(std::fs::TryLockError::WouldBlock) => Err(blocked),
        Err(std::fs::TryLockError::Error(error)) => Err(RuntimeError::new(
            RuntimeErrorCode::RegistryUnavailable,
            format!("cannot acquire {label} {}: {error}", path.display()),
            None,
            true,
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    #[test]
    fn shared_file_fence_lifetime_is_guarded_by_returned_file() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-control-fence-{}-{}",
            std::process::id(),
            uuid::Uuid::now_v7()
        ));
        fs::create_dir_all(&root).unwrap();
        let path = root.join("control.lock");

        let first =
            acquire_shared_file_fence(&path, "test fence", RuntimeError::deployment_in_progress())
                .unwrap();
        let second =
            acquire_shared_file_fence(&path, "test fence", RuntimeError::deployment_in_progress())
                .unwrap();

        drop(second);
        drop(first);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn shared_file_fence_preserves_operation_specific_blocked_error() {
        use std::fs::OpenOptions;

        let root = std::env::temp_dir().join(format!(
            "ordivon-control-fence-blocked-{}-{}",
            std::process::id(),
            uuid::Uuid::now_v7()
        ));
        fs::create_dir_all(&root).unwrap();
        let path = root.join("control.lock");
        let exclusive = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(&path)
            .unwrap();
        exclusive.try_lock().unwrap();

        let error =
            acquire_shared_file_fence(&path, "test fence", RuntimeError::deployment_in_progress())
                .unwrap_err();
        assert_eq!(
            error.code,
            super::super::RuntimeErrorCode::DeploymentInProgress
        );
        assert_eq!(
            error.message,
            "Runtime deployment holds the new-admission fence"
        );

        drop(exclusive);
        fs::remove_dir_all(root).unwrap();
    }
}
