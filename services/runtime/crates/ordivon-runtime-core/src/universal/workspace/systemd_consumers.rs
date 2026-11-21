// Physical Linux systemd consumers of a Workspace.
// This is a native observation capability, not a new claim/authorization layer.
use super::{UniversalExecError, UniversalExecErrorCode};
#[cfg(test)]
use std::fs;
use std::path::Path;

mod installed_units;
mod loaded_units;
use installed_units::ensure_no_installed_systemd_consumer_at;
#[cfg(test)]
use installed_units::installed_systemd_workspace_consumers_at;
use loaded_units::ensure_no_loaded_manager_consumer_at;
#[cfg(test)]
use loaded_units::{manager_read_only_query, manager_unit_consumers_at};

#[cfg(test)]
mod installed_unit_consumer_tests;

#[cfg(all(test, target_os = "linux"))]
fn legacy_test_workspace(workspace_id: &str) -> std::path::PathBuf {
    Path::new("/var/lib/ordivon/runtime/workspaces").join(workspace_id)
}

#[cfg(all(test, target_os = "linux"))]
fn installed_systemd_workspace_consumers(
    workspace_id: &str,
    roots: &[&Path],
) -> Result<Vec<String>, UniversalExecError> {
    installed_systemd_workspace_consumers_at(&legacy_test_workspace(workspace_id), roots)
}

#[cfg(all(test, target_os = "linux"))]
fn manager_unit_consumers(
    properties: &str,
    workspace_id: &str,
    expected_names: &[String],
) -> Result<Vec<String>, UniversalExecError> {
    manager_unit_consumers_at(
        properties,
        &legacy_test_workspace(workspace_id),
        expected_names,
    )
}

#[cfg(all(test, target_os = "linux"))]
fn ensure_no_loaded_manager_consumer(workspace_id: &str) -> Result<(), UniversalExecError> {
    ensure_no_loaded_manager_consumer_at(&legacy_test_workspace(workspace_id))
}

#[cfg(all(test, target_os = "linux"))]
fn ensure_no_installed_systemd_consumer(
    workspace_id: &str,
    roots: &[&Path],
) -> Result<(), UniversalExecError> {
    ensure_no_installed_systemd_consumer_at(&legacy_test_workspace(workspace_id), roots)
}

#[cfg(target_os = "linux")]
fn external_unit_inspection_error(reason: &str) -> UniversalExecError {
    UniversalExecError::new(
        UniversalExecErrorCode::WorkspaceStateMismatch,
        format!("cannot prove installed systemd consumer absence: {reason}"),
        Some("workspaceId"),
        true,
    )
}

// Keep the existing installed + loaded systemd consumer fence on both first
// close and interrupted-close resume: no bypass for a still-present directory.
#[cfg(target_os = "linux")]
pub(super) fn ensure_no_closing_workspace_systemd_consumer(
    target: &Path,
) -> Result<(), UniversalExecError> {
    if target.exists() {
        ensure_no_installed_systemd_consumer_at(
            target,
            &[
                Path::new("/etc/systemd/system.control"),
                Path::new("/run/systemd/system.control"),
                Path::new("/run/systemd/transient"),
                Path::new("/run/systemd/generator.early"),
                Path::new("/etc/systemd/system"),
                Path::new("/etc/systemd/system.attached"),
                Path::new("/run/systemd/system"),
                Path::new("/run/systemd/system.attached"),
                Path::new("/run/systemd/generator"),
                Path::new("/usr/local/lib/systemd/system"),
                Path::new("/usr/lib/systemd/system"),
                Path::new("/run/systemd/generator.late"),
            ],
        )?;
        if target.starts_with(Path::new("/var/lib/ordivon")) {
            ensure_no_loaded_manager_consumer_at(target)?;
        }
    }
    Ok(())
}
