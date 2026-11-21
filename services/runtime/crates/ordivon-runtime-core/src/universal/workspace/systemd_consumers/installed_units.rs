// Installed unit files, symlinks and templates are original OS-level consumers.
use super::{external_unit_inspection_error, UniversalExecError, UniversalExecErrorCode};
use std::{fs, path::Path};

#[cfg(target_os = "linux")]
pub(super) fn installed_systemd_workspace_consumers_at(
    workspace_path: &Path,
    roots: &[&Path],
) -> Result<Vec<String>, UniversalExecError> {
    const MAX_UNIT_BYTES: u64 = 1024 * 1024;
    const MAX_ENTRIES: usize = 65536;
    const MAX_DEPTH: usize = 12;
    if !workspace_path.is_absolute() {
        return Err(external_unit_inspection_error(
            "Workspace consumer path is not absolute",
        ));
    }
    let workspace_id = workspace_path
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| external_unit_inspection_error("Workspace ID is invalid"))?;
    let prefix = workspace_path.to_string_lossy().into_owned();
    let template_parent = workspace_path
        .parent()
        .ok_or_else(|| external_unit_inspection_error("Workspace root is invalid"))?;
    let template_i = format!("{}/%i", template_parent.display());
    let template_unescaped = format!("{}/%I", template_parent.display());
    let mut matches = Vec::new();
    let mut observed_entries = 0_usize;
    let mut pending = Vec::new();
    let mut canonical_roots = Vec::new();
    for root in roots {
        let metadata = match fs::symlink_metadata(root) {
            Ok(metadata) => metadata,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => continue,
            Err(_) => {
                return Err(external_unit_inspection_error(
                    "systemd unit root is unreadable",
                ));
            }
        };
        if !metadata.file_type().is_dir() {
            return Err(external_unit_inspection_error(
                "systemd unit root is not a regular directory",
            ));
        }
        canonical_roots.push(fs::canonicalize(root).map_err(|_| {
            external_unit_inspection_error("systemd unit root cannot be canonicalized")
        })?);
        pending.push(((*root).to_path_buf(), 0_usize));
    }
    while let Some((directory, depth)) = pending.pop() {
        if depth > MAX_DEPTH {
            return Err(external_unit_inspection_error(
                "unit directory depth exceeded limit",
            ));
        }
        let entries = fs::read_dir(&directory).map_err(|_| {
            external_unit_inspection_error("could not enumerate systemd unit directory")
        })?;
        for entry in entries {
            observed_entries += 1;
            if observed_entries > MAX_ENTRIES {
                return Err(external_unit_inspection_error(
                    "systemd unit inventory exceeded bound",
                ));
            }
            let entry = entry.map_err(|_| {
                external_unit_inspection_error("systemd unit inventory was unreadable")
            })?;
            let path = entry.path();
            let file_type = entry.file_type().map_err(|_| {
                external_unit_inspection_error("systemd unit file type was unreadable")
            })?;
            if file_type.is_dir() {
                pending.push((path, depth + 1));
                continue;
            }
            if !file_type.is_file() && !file_type.is_symlink() {
                continue;
            }
            let name = path.file_name().and_then(|s| s.to_str()).unwrap_or("");
            if ![
                ".service",
                ".timer",
                ".socket",
                ".path",
                ".mount",
                ".automount",
                ".conf",
            ]
            .iter()
            .any(|suffix| name.ends_with(suffix))
            {
                continue;
            }
            // A systemctl-linked unit may point outside every scanned unit
            // directory. Do not equate the link's identity with its content.
            let instance_alias = name.contains(&format!("@{workspace_id}."));
            if file_type.is_symlink() {
                let resolved = match fs::canonicalize(&path) {
                    Ok(resolved) => resolved,
                    Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                        // An unrelated dangling link has no loadable source NOW;
                        // it cannot block every Workspace close in the system.
                        // An explicit Workspace link still preserves its root.
                        let target = fs::read_link(&path).map_err(|_| {
                            external_unit_inspection_error("systemd symlink cannot be read")
                        })?;
                        let next = if target.is_absolute() {
                            target
                        } else {
                            path.parent().unwrap_or(&directory).join(target)
                        };
                        // Missing unit files have no loaded bytes to inspect.
                        // Check the exact Workspace path component, not a
                        // substring: ws-target-copy must not retain ws-target.
                        let mut lexical = std::path::PathBuf::new();
                        for component in next.components() {
                            match component {
                                std::path::Component::ParentDir => {
                                    lexical.pop();
                                }
                                std::path::Component::CurDir => {}
                                other => lexical.push(other.as_os_str()),
                            }
                        }
                        if lexical.starts_with(Path::new(&prefix)) {
                            matches.push(path.display().to_string());
                            continue;
                        }
                        if let Ok(metadata) = fs::symlink_metadata(&next) {
                            if metadata.file_type().is_symlink() {
                                return Err(external_unit_inspection_error(
                                    "unresolved nested systemd symlink requires inspection",
                                ));
                            }
                        }
                        continue; // missing unrelated unit: no current file content
                    }
                    Err(_) => {
                        return Err(external_unit_inspection_error(
                            "systemd unit symlink target is not inspectable",
                        ));
                    }
                };
                if resolved == Path::new("/dev/null") {
                    continue; // systemd masked unit: cannot be activated
                }
                if resolved.starts_with(Path::new(&prefix)) {
                    matches.push(path.display().to_string());
                    continue;
                }
                if canonical_roots
                    .iter()
                    .any(|root| resolved.starts_with(root))
                    && !instance_alias
                {
                    // The same ordinary unit file is independently enumerated
                    // in a scanned root; only a named template instance needs
                    // this alias inspected for its %i expansion.
                    continue;
                }
            }
            let metadata = fs::metadata(&path).map_err(|_| {
                external_unit_inspection_error("systemd unit metadata is unreadable")
            })?;
            if !metadata.is_file() {
                return Err(external_unit_inspection_error(
                    "systemd unit alias is not a regular file",
                ));
            }
            if metadata.len() > MAX_UNIT_BYTES {
                return Err(external_unit_inspection_error(
                    "systemd unit file exceeds inspection bound",
                ));
            }
            let content = fs::read_to_string(&path)
                .map_err(|_| external_unit_inspection_error("systemd unit bytes are unreadable"))?;
            let consumes = content.lines().any(|line| {
                let line = line.trim_start();
                if line.is_empty() || line.starts_with('#') || line.starts_with(';') {
                    return false;
                }
                if instance_alias
                    && (line.contains(&template_i) || line.contains(&template_unescaped))
                {
                    // For installed agent@ws-id.service, systemd expands %i
                    // to ws-id; a literal-only source search misses it.
                    return true;
                }
                let mut suffix = line;
                while let Some(offset) = suffix.find(&prefix) {
                    let tail = &suffix[offset + prefix.len()..];
                    if tail.chars().next().is_none_or(|next| {
                        !next.is_ascii_alphanumeric() && next != '.' && next != '_' && next != '-'
                    }) {
                        return true;
                    }
                    suffix = tail;
                }
                false
            });
            if consumes {
                matches.push(path.display().to_string());
            }
        }
    }
    matches.sort();
    matches.dedup();
    Ok(matches)
}

#[cfg(target_os = "linux")]
pub(super) fn ensure_no_installed_systemd_consumer_at(
    workspace_path: &Path,
    roots: &[&Path],
) -> Result<(), UniversalExecError> {
    let matches = installed_systemd_workspace_consumers_at(workspace_path, roots)?;
    if matches.is_empty() {
        return Ok(());
    }
    Err(UniversalExecError::new(
        UniversalExecErrorCode::WorkspaceStateMismatch,
        format!(
            "installed systemd unit still consumes Workspace: {}",
            matches.join(", ")
        ),
        Some("workspaceId"),
        true,
    ))
}
