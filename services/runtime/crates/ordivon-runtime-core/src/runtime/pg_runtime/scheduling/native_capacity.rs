//! Native Linux resource observation for PostgreSQL scheduling.
//! Missing controller evidence remains UNKNOWN, never fabricated free capacity.
use super::{RuntimeError, RuntimeErrorCode, RuntimeResult};
use crate::resource_scheduling::ResourceRequest;
use std::{fs, path::Path};

/// Native controller read errors mean UNKNOWN, never an unschedulable verdict.
pub(super) fn native_resource_error(message: impl std::fmt::Display) -> RuntimeError {
    RuntimeError::new(
        RuntimeErrorCode::ToolFailed,
        format!("native scheduling resource observation unavailable: {message}"),
        Some("scheduling.resources"),
        true,
    )
}

/// A *missing unit directory* is an unstarted (or removed) cgroup and thus
/// contributes no observed usage. The committed PG Allocation still reserves
/// its full resource request. An existing unit with missing/corrupt controller
/// files is UNKNOWN and must not be interpreted as zero usage.
///
/// Read each cgroup file directly in the normal path: only an ENOENT triggers
/// an extra directory check, avoiding a per-allocation metadata round trip.
pub(super) fn unspent_native_allocation(
    group: &Path,
    request: &ResourceRequest,
) -> RuntimeResult<(u64, u64)> {
    let read_current = |name: &str| -> RuntimeResult<Option<u64>> {
        let path = group.join(name);
        match fs::read_to_string(&path) {
            Ok(value) => value
                .trim()
                .parse::<u64>()
                .map(Some)
                .map_err(|e| native_resource_error(format!("{}: {e}", path.display()))),
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => {
                match fs::symlink_metadata(group) {
                    Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(None),
                    Ok(_) => Err(native_resource_error(format!(
                        "{} missing from existing cgroup",
                        path.display()
                    ))),
                    Err(e) => Err(native_resource_error(format!("{}: {e}", group.display()))),
                }
            }
            Err(e) => Err(native_resource_error(format!("{}: {e}", path.display()))),
        }
    };
    let Some(memory) = read_current("memory.current")? else {
        return Ok((request.memory_bytes, u64::from(request.pids)));
    };
    let Some(pids) = read_current("pids.current")? else {
        return Ok((request.memory_bytes, u64::from(request.pids)));
    };
    Ok((
        request.memory_bytes.saturating_sub(memory),
        u64::from(request.pids).saturating_sub(pids),
    ))
}
