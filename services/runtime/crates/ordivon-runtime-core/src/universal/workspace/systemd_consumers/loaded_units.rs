// Loaded/transient systemd Manager consumers, independent of installed unit files.
use super::{external_unit_inspection_error, UniversalExecError, UniversalExecErrorCode};
use std::path::Path;

// Installed file scanning cannot see a loaded manager's transient units or
// already-unlinked unit source. Query the native read-only manager projection;
// this is an additional bounded fence, never a completeness/TOCTOU proof.
#[cfg(target_os = "linux")]
pub(super) fn manager_unit_consumers_at(
    properties: &str,
    workspace_path: &Path,
    expected_names: &[String],
) -> Result<Vec<String>, UniversalExecError> {
    use std::collections::HashSet;
    let expected: HashSet<&str> = expected_names.iter().map(String::as_str).collect();
    let mut seen = HashSet::new();
    let mut hits = Vec::new();
    if !workspace_path.is_absolute() {
        return Err(external_unit_inspection_error(
            "Workspace consumer path is not absolute",
        ));
    }
    let prefix = workspace_path.to_string_lossy().into_owned();
    for unit in properties
        .split("\n\n")
        .filter(|unit| !unit.trim().is_empty())
    {
        let mut name = None;
        let mut state = None;
        let mut consumes = false;
        for line in unit.lines() {
            if let Some(id) = line.strip_prefix("Id=") {
                name = Some(id);
            } else if let Some(value) = line.strip_prefix("LoadState=") {
                state = Some(value);
            } else if [
                "WorkingDirectory=",
                "ExecStart=",
                "ExecStartPre=",
                "ExecStartPost=",
                "ExecCondition=",
                "Environment=",
                "EnvironmentFiles=",
                "RootDirectory=",
                "RootImage=",
            ]
            .iter()
            .any(|field| line.starts_with(field))
            {
                let mut remainder = line;
                while let Some(start) = remainder.find(&prefix) {
                    let suffix = &remainder[start + prefix.len()..];
                    if suffix.chars().next().is_none_or(|next| {
                        !next.is_ascii_alphanumeric() && next != '.' && next != '_' && next != '-'
                    }) {
                        consumes = true;
                        break;
                    }
                    remainder = suffix;
                }
            }
        }
        let name = name.ok_or_else(|| {
            external_unit_inspection_error("manager response lacks unit identity")
        })?;
        // --all also includes retained failed/not-found and masked units.
        // Their normalized properties remain observable, even though there
        // may be no loadable unit file. Do not confuse LoadState with whether
        // the returned manager identity is valid or still has a reference.
        if !expected.contains(name)
            || !seen.insert(name)
            || !matches!(state, Some("loaded" | "not-found" | "masked"))
        {
            return Err(external_unit_inspection_error(
                "manager unit changed state or identity during inspection",
            ));
        }
        if consumes {
            hits.push(name.to_string());
        }
    }
    if seen.len() != expected.len() {
        return Err(external_unit_inspection_error(
            "manager omitted an enumerated unit",
        ));
    }
    Ok(hits)
}

#[cfg(target_os = "linux")]
pub(super) fn manager_read_only_query(args: &[&str]) -> Result<String, UniversalExecError> {
    // Native GNU timeout bounds a hung system bus; no shell or effectful verb.
    let result = std::process::Command::new("/usr/bin/timeout")
        .args(["-k", "1s", "8s", "/usr/bin/systemctl"])
        .args(args)
        .output()
        .map_err(|_| external_unit_inspection_error("native manager CLI unavailable"))?;
    if !result.status.success() || result.stdout.len() > 8 * 1024 * 1024 {
        return Err(external_unit_inspection_error(
            "manager query failed or exceeded bounds",
        ));
    }
    String::from_utf8(result.stdout)
        .map_err(|_| external_unit_inspection_error("manager query output invalid UTF-8"))
}

#[cfg(target_os = "linux")]
pub(super) fn ensure_no_loaded_manager_consumer_at(
    workspace_path: &Path,
) -> Result<(), UniversalExecError> {
    // The system manager does not exist in non-systemd PID1 environments.
    // User manager / arbitrary process readsets remain outside this check.
    if !Path::new("/run/systemd/system").is_dir() {
        return Ok(());
    }
    let list = manager_read_only_query(&[
        "list-units",
        "--all",
        "--plain",
        "--no-legend",
        "--no-pager",
    ])?;
    let mut names = Vec::new();
    for line in list.lines().filter(|line| !line.trim().is_empty()) {
        let mut fields = line.split_whitespace();
        let first = fields.next().unwrap_or("");
        let name = if first == "●" {
            fields.next().unwrap_or("")
        } else {
            first
        };
        if name.is_empty() || !name.contains('.') {
            return Err(external_unit_inspection_error(
                "invalid loaded manager unit name",
            ));
        }
        names.push(name.to_string());
        if names.len() > 4096 {
            return Err(external_unit_inspection_error(
                "loaded unit count exceeds bound",
            ));
        }
    }
    if names.is_empty() {
        return Ok(());
    }
    let mut args = vec![
        "show", "--all", "--no-pager",
        "--property=Id,LoadState,WorkingDirectory,ExecStart,ExecStartPre,ExecStartPost,ExecCondition,Environment,EnvironmentFiles,RootDirectory,RootImage",
        "--", // -.mount is a valid live unit; never reinterpret it as a CLI flag.
    ];
    args.extend(names.iter().map(String::as_str));
    let properties = manager_read_only_query(&args)?;
    let consumers = manager_unit_consumers_at(&properties, workspace_path, &names)?;
    if !consumers.is_empty() {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceStateMismatch,
            format!(
                "loaded systemd manager still consumes Workspace: {}",
                consumers.join(", ")
            ),
            Some("workspaceId"),
            true,
        ));
    }
    Ok(())
}
