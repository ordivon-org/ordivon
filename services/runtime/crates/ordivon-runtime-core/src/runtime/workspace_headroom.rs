//! Storage-neutral Workspace carrier capacity contract for legacy and PG.
use super::{RuntimeError, RuntimeErrorCode, RuntimeResult};
use std::path::{Path, PathBuf};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct WorkspaceHeadroomConfig {
    pub path: PathBuf,
    pub minimum_free_bytes: u64,
}

fn io_error(context: &str, cause: std::io::Error) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::IoError,
        format!("{context}: {cause}"),
        None,
        false,
    )
}

#[cfg(unix)]
fn filesystem_available_bytes(path: &Path) -> RuntimeResult<u64> {
    use std::ffi::CString;
    use std::os::unix::ffi::OsStrExt;
    let encoded = CString::new(path.as_os_str().as_bytes()).map_err(|_| {
        RuntimeError::invalid(
            "workspace headroom path must not contain NUL",
            "workspaceHeadroom.path",
        )
    })?;
    let mut stats: libc::statvfs = unsafe { std::mem::zeroed() };
    if unsafe { libc::statvfs(encoded.as_ptr(), &mut stats) } != 0 {
        return Err(io_error(
            "inspect workspace carrier free space",
            std::io::Error::last_os_error(),
        ));
    }
    let fragment_size = if stats.f_frsize == 0 {
        stats.f_bsize
    } else {
        stats.f_frsize
    } as u64;
    Ok((stats.f_bavail as u64).saturating_mul(fragment_size))
}

#[cfg(windows)]
fn filesystem_available_bytes(path: &Path) -> RuntimeResult<u64> {
    use std::os::windows::ffi::OsStrExt;
    use windows_sys::Win32::Storage::FileSystem::GetDiskFreeSpaceExW;
    let mut encoded = path.as_os_str().encode_wide().collect::<Vec<_>>();
    encoded.push(0);
    let mut available = 0_u64;
    let result = unsafe {
        GetDiskFreeSpaceExW(
            encoded.as_ptr(),
            &mut available,
            std::ptr::null_mut(),
            std::ptr::null_mut(),
        )
    };
    if result == 0 {
        return Err(io_error(
            "inspect workspace carrier free space",
            std::io::Error::last_os_error(),
        ));
    }
    Ok(available)
}

#[cfg(not(any(unix, windows)))]
fn filesystem_available_bytes(_path: &Path) -> RuntimeResult<u64> {
    Err(RuntimeError::new(
        RuntimeErrorCode::ToolUnavailable,
        "workspace carrier free-space observation is unavailable on this platform",
        Some("workspaceHeadroom.path"),
        false,
    ))
}

pub(super) fn validate_workspace_headroom(
    headrooms: &[WorkspaceHeadroomConfig],
) -> RuntimeResult<()> {
    for headroom in headrooms {
        if !headroom.path.is_absolute() {
            return Err(RuntimeError::invalid(
                "workspace headroom path must be absolute",
                "workspaceHeadroom.path",
            ));
        }
        if headroom.minimum_free_bytes == 0 {
            return Err(RuntimeError::invalid(
                "workspace minimum free bytes must be positive",
                "workspaceHeadroom.minimumFreeBytes",
            ));
        }
    }
    Ok(())
}

/// Shared physical capacity gate for legacy and current PG Workspace.open.
pub(super) fn ensure_workspace_headroom(
    headrooms: &[WorkspaceHeadroomConfig],
) -> RuntimeResult<()> {
    ensure_workspace_headroom_with_commitment(headrooms, 0)
}

/// A conservative upper bound for declared Job commitments. The full
/// committed peak is retained until release; without attributable native
/// usage, no already-materialized bytes are credited back to the budget.
pub(super) fn ensure_workspace_headroom_with_commitment(
    headrooms: &[WorkspaceHeadroomConfig],
    committed_bytes: u64,
) -> RuntimeResult<()> {
    if committed_bytes != 0 && headrooms.is_empty() {
        return Err(RuntimeError::new(
            RuntimeErrorCode::WorkspaceCapacityExceeded,
            "storage commitment has no configured carrier observation",
            Some("workspaceHeadroom"),
            true,
        ));
    }
    for headroom in headrooms {
        let available = filesystem_available_bytes(&headroom.path)?;
        if !crate::resource_fit::storage_fits(
            available,
            headroom.minimum_free_bytes,
            committed_bytes,
        ) {
            let mut error = RuntimeError::new(
                RuntimeErrorCode::WorkspaceCapacityExceeded,
                format!(
                    "workspace carrier headroom below configured minimum: path={} availableBytes={} minimumFreeBytes={}",
                    headroom.path.display(),
                    available,
                    headroom.minimum_free_bytes
                ),
                Some("workspaceHeadroom"),
                true,
            );
            if committed_bytes != 0 {
                error
                    .message
                    .push_str(&format!(" committedBytes={committed_bytes}"));
            }
            error.retry_after_ms = Some(60_000);
            return Err(error);
        }
    }
    Ok(())
}

#[cfg(test)]
mod commitment_tests {
    use super::*;

    #[test]
    fn configured_headroom_is_required_for_a_nonzero_commitment() {
        assert!(ensure_workspace_headroom(&[]).is_ok());
        assert_eq!(
            ensure_workspace_headroom_with_commitment(&[], 1)
                .unwrap_err()
                .code,
            RuntimeErrorCode::WorkspaceCapacityExceeded
        );
    }

    #[test]
    fn native_carrier_rejects_an_overflowing_commitment_without_writing() {
        let path = std::env::temp_dir();
        let carrier = WorkspaceHeadroomConfig {
            path,
            minimum_free_bytes: 1,
        };
        assert_eq!(
            ensure_workspace_headroom_with_commitment(&[carrier], u64::MAX)
                .unwrap_err()
                .code,
            RuntimeErrorCode::WorkspaceCapacityExceeded
        );
    }
}
