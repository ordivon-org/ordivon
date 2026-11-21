//! Original Linux systemd Unit consumers of a Workspace.
//!
//! This module observes installed and Manager-loaded units. It does not own
//! PostgreSQL Job admission, Harness Claim release, or OS NoFutureSpawn.
//! A query cannot turn an unknown external effect into proof of absence.
use super::{UniversalExecError, UniversalExecErrorCode};
use std::{fs, path::Path};

#[cfg(target_os = "linux")]
fn installed_systemd_workspace_consumers_at(
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

// Installed file scanning cannot see a loaded manager's transient units or
// already-unlinked unit source. Query the native read-only manager projection;
// this is an additional bounded fence, never a completeness/TOCTOU proof.
#[cfg(target_os = "linux")]
fn manager_unit_consumers_at(
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
fn manager_read_only_query(args: &[&str]) -> Result<String, UniversalExecError> {
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
fn ensure_no_loaded_manager_consumer_at(workspace_path: &Path) -> Result<(), UniversalExecError> {
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
        "show",
        "--all",
        "--no-pager",
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

#[cfg(target_os = "linux")]
fn ensure_no_installed_systemd_consumer_at(
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

#[cfg(all(test, target_os = "linux"))]
mod installed_unit_consumer_tests {
    use super::*;

    #[test]
    fn linked_systemd_unit_outside_scanned_roots_is_not_safe_to_ignore() {
        let temp = TestUnitRoot::new();
        let root = temp.path().join("units");
        let external = temp.path().join("external");
        fs::create_dir_all(&root).unwrap();
        fs::create_dir_all(&external).unwrap();
        let source = external.join("remote.service");
        fs::write(
            &source,
            "[Service]\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-linked\n",
        )
        .unwrap();
        let link = root.join("remote.service");
        symlink(&source, &link).unwrap();
        let result = installed_systemd_workspace_consumers("ws-linked", &[&root]);
        assert!(
            result.is_err() || !result.unwrap().is_empty(),
            "CANDIDATE_FALSE_GREEN: systemctl link supports an external service file"
        );
    }

    #[test]
    fn instantiated_systemd_unit_specifier_is_not_safe_to_treat_as_absent() {
        let temp = TestUnitRoot::new();
        let root = temp.path().join("units");
        let wanted = root.join("multi-user.target.wants");
        fs::create_dir_all(&wanted).unwrap();
        let source = root.join("agent@.service");
        fs::write(
            &source,
            "[Service]\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/%i\n",
        )
        .unwrap();
        symlink(&source, wanted.join("agent@ws-instance.service")).unwrap();
        let result = installed_systemd_workspace_consumers("ws-instance", &[&root]);
        assert!(
            result.is_err() || !result.unwrap().is_empty(),
            "CANDIDATE_FALSE_GREEN: systemd template %i can resolve to the live workspace"
        );
    }
    #[test]
    fn unescaped_instance_specifier_is_a_workspace_consumer() {
        let temp = TestUnitRoot::new();
        let root = temp.path().join("units");
        let wants = root.join("multi-user.target.wants");
        fs::create_dir_all(&wants).unwrap();
        let template = root.join("agent@.service");
        fs::write(
            &template,
            "[Service]\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/%I\n",
        )
        .unwrap();
        symlink(&template, wants.join("agent@ws-raw.service")).unwrap();
        let found = installed_systemd_workspace_consumers("ws-raw", &[&root]).unwrap();
        assert_eq!(
            found,
            vec![wants.join("agent@ws-raw.service").display().to_string()]
        );
    }

    use std::os::unix::fs::symlink;
    struct TestUnitRoot(std::path::PathBuf);

    impl TestUnitRoot {
        fn new() -> Self {
            let nonce = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let root = std::env::temp_dir().join(format!(
                "ordivon-systemd-consumer-{}-{nonce}",
                std::process::id()
            ));
            fs::create_dir(&root).unwrap();
            Self(root)
        }

        fn path(&self) -> &Path {
            &self.0
        }
    }

    impl Drop for TestUnitRoot {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    #[test]
    fn installed_consumer_matches_exact_workspace_not_comments_or_prefix_aliases() {
        let temp = TestUnitRoot::new();
        let root = temp.path().join("units");
        fs::create_dir(&root).unwrap();
        let service = root.join("durable.service");
        fs::write(
            &service,
            "# WorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-target\n\
             WorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-target-copy\n",
        )
        .unwrap();
        assert!(installed_systemd_workspace_consumers("ws-target", &[&root])
            .unwrap()
            .is_empty());
        fs::write(
            &service,
            "WorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-target\n",
        )
        .unwrap();
        assert_eq!(
            installed_systemd_workspace_consumers("ws-target", &[&root]).unwrap(),
            vec![service.display().to_string()]
        );
        let err = ensure_no_installed_systemd_consumer("ws-target", &[&root]).unwrap_err();
        assert_eq!(err.code, UniversalExecErrorCode::WorkspaceStateMismatch);
        assert!(err.message.contains("durable.service"));
        assert!(err.retryable);
        fs::remove_file(&service).unwrap();
        ensure_no_installed_systemd_consumer("ws-target", &[&root]).unwrap();
    }

    #[test]
    fn installed_service_dropin_is_consumer_and_symlink_is_not_followed() {
        let temp = TestUnitRoot::new();
        let root = temp.path().join("units");
        let dropin = root.join("durable.service.d");
        fs::create_dir_all(&dropin).unwrap();
        let file = dropin.join("30-override.conf");
        fs::write(
            &file,
            "ExecStartPre=/usr/bin/test -d /var/lib/ordivon/runtime/workspaces/ws-root/.git\n",
        )
        .unwrap();
        let symlink_path = root.join("old.service");
        symlink(&file, &symlink_path).unwrap();
        assert_eq!(
            installed_systemd_workspace_consumers("ws-root", &[&root]).unwrap(),
            vec![file.display().to_string()]
        );
        assert!(installed_systemd_workspace_consumers("ws-other", &[&root])
            .unwrap()
            .is_empty());
    }

    #[test]
    fn unrelated_broken_unit_link_must_not_block_every_workspace_close() {
        // A missing unrelated source cannot currently load a Workspace.
        // Absence in this filesystem readset is not proof of the live manager.
        let temp = TestUnitRoot::new();
        let root = temp.path().join("units");
        fs::create_dir(&root).unwrap();
        let absent = temp.path().join("no-such-unrelated.service");
        symlink(&absent, root.join("unrelated.service")).unwrap();
        assert!(
            ensure_no_installed_systemd_consumer("ws-target", &[&root]).is_ok(),
            "broken unrelated systemd alias globally blocked clean closure",
        );
        // A dangling link to a DIFFERENT workspace whose name has this
        // Workspace as a prefix is not a consumer of this Workspace.
        let different = root.join("similar-name.service");
        symlink(
            "/var/lib/ordivon/runtime/workspaces/ws-target-copy/linked.service",
            &different,
        )
        .unwrap();
        assert!(
            ensure_no_installed_systemd_consumer("ws-target", &[&root]).is_ok(),
            "a different Workspace prefix alias must not block close",
        );
        let link = root.join("target.service");
        symlink(
            "/var/lib/ordivon/runtime/workspaces/ws-target/linked.service",
            &link,
        )
        .unwrap();
        assert!(
            ensure_no_installed_systemd_consumer("ws-target", &[&root]).is_err(),
            "even a broken symlink explicitly pointing to this Workspace is a consumer root",
        );
    }

    #[test]
    fn oversized_or_symlinked_unit_roots_fail_closed() {
        let temp = TestUnitRoot::new();
        let root = temp.path().join("units");
        fs::create_dir(&root).unwrap();
        fs::write(root.join("oversize.service"), vec![b'a'; 1024 * 1024 + 1]).unwrap();
        let err = installed_systemd_workspace_consumers("ws-target", &[&root]).unwrap_err();
        assert_eq!(err.code, UniversalExecErrorCode::WorkspaceStateMismatch);
        assert!(err.message.contains("inspection bound"));
        let alias = temp.path().join("alias");
        symlink(&root, &alias).unwrap();
        let err = installed_systemd_workspace_consumers("ws-target", &[&alias]).unwrap_err();
        assert!(err.message.contains("not a regular directory"));
    }
    #[test]
    fn loaded_transient_unit_retains_workspace_even_without_installed_unit_file() {
        let temp = TestUnitRoot::new();
        let root = temp.path().join("units");
        fs::create_dir(&root).unwrap();
        assert!(installed_systemd_workspace_consumers("ws-live", &[&root])
            .unwrap()
            .is_empty());
        let names = vec!["transient.service".to_string()];
        let show = "Id=transient.service\nLoadState=loaded\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-live\n\n";
        assert_eq!(
            manager_unit_consumers(show, "ws-live", &names).unwrap(),
            names
        );
        assert!(manager_unit_consumers(show, "ws-live-copy", &names)
            .unwrap()
            .is_empty());
    }

    #[test]
    fn changing_or_partial_manager_snapshot_is_not_a_negative_consumer_proof() {
        let names = vec!["one.service".to_string(), "two.scope".to_string()];
        let one = "Id=one.service\nLoadState=loaded\nWorkingDirectory=\n\n";
        assert!(manager_unit_consumers(one, "ws-root", &names).is_err());
        let missing = "Id=one.service\nLoadState=not-found\nWorkingDirectory=\n\n";
        assert!(manager_unit_consumers(missing, "ws-root", &names[..1])
            .unwrap()
            .is_empty());
        let masked = "Id=one.service\nLoadState=masked\nWorkingDirectory=\n\n";
        assert!(manager_unit_consumers(masked, "ws-root", &names[..1])
            .unwrap()
            .is_empty());
        let unknown = "Id=one.service\nLoadState=future-unknown\nWorkingDirectory=\n\n";
        assert!(manager_unit_consumers(unknown, "ws-root", &names[..1]).is_err());
        assert!(manager_unit_consumers(&format!("{one}{one}"), "ws-root", &names[..1]).is_err());
    }

    #[test]
    fn systemd_manager_real_readonly_query_is_not_vacuous_when_booted() {
        if !Path::new("/run/systemd/system").is_dir() {
            return; // Non-systemd CI has no PID1 system manager to query.
        }
        let list = manager_read_only_query(&[
            "list-units",
            "--all",
            "--plain",
            "--no-legend",
            "--no-pager",
        ])
        .expect("real systemd manager unit inventory");
        assert!(!list.trim().is_empty(), "real manager must expose units");
        // The real manager commonly includes a unit named '-.mount';
        // the exact native probe must handle names beginning with a dash.
        ensure_no_loaded_manager_consumer("ws-nonexistent-ordivon-gpt6-probe-20261101")
            .expect("no unrelated loaded manager consumer");
    }

    #[test]
    fn pg_native_workspace_consumer_uses_bound_path_and_exact_instance() {
        let temp = TestUnitRoot::new();
        let root = temp.path().join("units");
        fs::create_dir_all(&root).unwrap();
        let expected = Path::new("/var/lib/ordivon/pg-candidate/workspaces/ws-pg");
        let neighbor = Path::new("/var/lib/ordivon/pg-candidate/workspaces/ws-pg-copy");
        let service = root.join("pg-runner.service");
        fs::write(
            &service,
            format!("[Service]\nWorkingDirectory={neighbor:?}\n"),
        )
        .unwrap();
        assert!(installed_systemd_workspace_consumers_at(expected, &[&root])
            .unwrap()
            .is_empty());
        fs::write(
            &service,
            format!(
                "[Service]\nExecStart=/bin/sh {}/run.sh\n",
                expected.display()
            ),
        )
        .unwrap();
        let hits = installed_systemd_workspace_consumers_at(expected, &[&root]).unwrap();
        assert_eq!(hits, vec![service.display().to_string()]);
        assert!(ensure_no_installed_systemd_consumer_at(expected, &[&root]).is_err());
        let names = vec!["transient-pg.service".to_string()];
        let manager = format!(
            "Id=transient-pg.service\nLoadState=loaded\nWorkingDirectory={}\n\n",
            expected.display()
        );
        assert_eq!(
            manager_unit_consumers_at(&manager, expected, &names).unwrap(),
            names
        );
        assert!(manager_unit_consumers_at(&manager, neighbor, &names)
            .unwrap()
            .is_empty());
        let template = root.join("runner@ws-pg.service");
        fs::write(
            &template,
            "[Service]\nWorkingDirectory=/var/lib/ordivon/pg-candidate/workspaces/%i\n",
        )
        .unwrap();
        assert!(installed_systemd_workspace_consumers_at(expected, &[&root])
            .unwrap()
            .contains(&template.display().to_string()));
    }

    #[test]
    fn loaded_manager_properties_cover_scope_environment_and_exec() {
        let names = vec!["one.scope".to_string(), "two.service".to_string()];
        let show = "Id=one.scope\nLoadState=loaded\nEnvironment=ROOT=/var/lib/ordivon/runtime/workspaces/ws-scope/bin\n\nId=two.service\nLoadState=loaded\nExecStart={ path=/bin/sh ; argv[]=/bin/sh /var/lib/ordivon/runtime/workspaces/ws-scope/job; }\n\n";
        assert_eq!(
            manager_unit_consumers(show, "ws-scope", &names).unwrap(),
            names
        );
        assert!(manager_unit_consumers(show, "ws-other", &names)
            .unwrap()
            .is_empty());
    }
}
