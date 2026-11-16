// Workspace continuation is one owner-local deletion precondition. Apply it
// after the path-specific dirty/source diagnostics, but before *every* path
// that can physically remove an open Workspace. A caller assertion is not
// cryptographic proof of release; this guards accidental cleaners only.
fn require_recent_workspace_consumer_release(
    created_unix_ms: u128,
    consumer_released: bool,
) -> Result<(), UniversalExecError> {
    const CONTINUATION_HOLD_MS: u128 = 4 * 60 * 60 * 1000;
    if !consumer_released && now_unix_ms()? < created_unix_ms.saturating_add(CONTINUATION_HOLD_MS) {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceStateMismatch,
            "Workspace is inside the bounded consumer continuation window; explicit consumerReleased is required before close",
            Some("consumerReleased"),
            false,
        ));
    }
    Ok(())
}

#[cfg(target_os = "linux")]
fn installed_systemd_workspace_consumers_at(
    workspace_path: &Path,
    roots: &[&Path],
) -> Result<Vec<String>, UniversalExecError> {
    const MAX_UNIT_BYTES: u64 = 1024 * 1024;
    const MAX_ENTRIES: usize = 65536;
    const MAX_DEPTH: usize = 12;
    if !workspace_path.is_absolute() {
        return Err(external_unit_inspection_error("Workspace consumer path is not absolute"));
    }
    let workspace_id = workspace_path.file_name().and_then(|name| name.to_str())
        .ok_or_else(|| external_unit_inspection_error("Workspace ID is invalid"))?;
    let prefix = workspace_path.to_string_lossy().into_owned();
    let template_parent = workspace_path.parent()
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
                if instance_alias && (
                    line.contains(&template_i) || line.contains(&template_unescaped)
                ) {
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
        return Err(external_unit_inspection_error("Workspace consumer path is not absolute"));
    }
    let prefix = workspace_path.to_string_lossy().into_owned();
    for unit in properties.split("\n\n").filter(|unit| !unit.trim().is_empty()) {
        let mut name = None;
        let mut state = None;
        let mut consumes = false;
        for line in unit.lines() {
            if let Some(id) = line.strip_prefix("Id=") {
                name = Some(id);
            } else if let Some(value) = line.strip_prefix("LoadState=") {
                state = Some(value);
            } else if [
                "WorkingDirectory=", "ExecStart=", "ExecStartPre=",
                "ExecStartPost=", "ExecCondition=", "Environment=",
                "EnvironmentFiles=", "RootDirectory=", "RootImage=",
            ].iter().any(|field| line.starts_with(field)) {
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
        let name = name.ok_or_else(|| external_unit_inspection_error(
            "manager response lacks unit identity",
        ))?;
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
        if consumes { hits.push(name.to_string()); }
    }
    if seen.len() != expected.len() {
        return Err(external_unit_inspection_error("manager omitted an enumerated unit"));
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
        return Err(external_unit_inspection_error("manager query failed or exceeded bounds"));
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
        "list-units", "--all", "--plain", "--no-legend", "--no-pager",
    ])?;
    let mut names = Vec::new();
    for line in list.lines().filter(|line| !line.trim().is_empty()) {
        let mut fields = line.split_whitespace();
        let first = fields.next().unwrap_or("");
        let name = if first == "●" { fields.next().unwrap_or("") } else { first };
        if name.is_empty() || !name.contains('.') {
            return Err(external_unit_inspection_error("invalid loaded manager unit name"));
        }
        names.push(name.to_string());
        if names.len() > 4096 {
            return Err(external_unit_inspection_error("loaded unit count exceeds bound"));
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
            format!("loaded systemd manager still consumes Workspace: {}", consumers.join(", ")),
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
    workspace_id: &str, roots: &[&Path],
) -> Result<Vec<String>, UniversalExecError> {
    installed_systemd_workspace_consumers_at(&legacy_test_workspace(workspace_id), roots)
}

#[cfg(all(test, target_os = "linux"))]
fn manager_unit_consumers(
    properties: &str, workspace_id: &str, expected_names: &[String],
) -> Result<Vec<String>, UniversalExecError> {
    manager_unit_consumers_at(
        properties, &legacy_test_workspace(workspace_id), expected_names
    )
}

#[cfg(all(test, target_os = "linux"))]
fn ensure_no_loaded_manager_consumer(workspace_id: &str) -> Result<(), UniversalExecError> {
    ensure_no_loaded_manager_consumer_at(&legacy_test_workspace(workspace_id))
}

#[cfg(all(test, target_os = "linux"))]
fn ensure_no_installed_systemd_consumer(
    workspace_id: &str, roots: &[&Path],
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

// Never interpret a persisted CLOSING intent as a live Workspace. Its
// immutable source witness is what survives the non-atomic Git/record boundary.
fn decode_closing_workspace_record(
    bytes: &[u8],
) -> Result<Option<ClosingWorkspaceRecord>, UniversalExecError> {
    let value: serde_json::Value = serde_json::from_slice(bytes).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            format!("invalid Workspace identity record: {error}"),
            Some("workspaceId"),
            false,
        )
    })?;
    if value.get("state").and_then(serde_json::Value::as_str) != Some("closing") {
        return Ok(None);
    }
    let closing: ClosingWorkspaceRecord = serde_json::from_value(value).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            format!("invalid durable Workspace closing intent: {error}"),
            Some("workspaceId"),
            false,
        )
    })?;
    if closing.schema_version != UNIVERSAL_EXEC_SCHEMA_VERSION
        || closing.state != "closing"
        || !closing.source_state_digest.starts_with("sha256:")
        || closing.source_state_digest.len() != 71
        || !closing.source_state_digest[7..].bytes().all(|b| b.is_ascii_hexdigit())
        || !matches!(closing.final_head.len(), 40 | 64)
        || !closing.final_head.bytes().all(|b| b.is_ascii_hexdigit())
    {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            "durable Workspace closing intent has invalid identity or source witness",
            Some("workspaceId"),
            false,
        ));
    }
    Ok(Some(closing))
}

// Keep the existing installed + loaded systemd consumer fence on both first
// close and interrupted-close resume: no bypass for a still-present directory.
#[cfg(target_os = "linux")]
fn ensure_no_closing_workspace_systemd_consumer(target: &Path) -> Result<(), UniversalExecError> {
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

fn reconcile_closing_workspace(
    config: &UniversalExecutorConfig,
    request: &WorkspaceCloseRequest,
    record_path: &Path,
    target: &Path,
    closing: ClosingWorkspaceRecord,
) -> Result<WorkspaceCloseResult, UniversalExecError> {
    let workspace_id = &request.workspace_id;
    validate_open_identity(&closing.record, workspace_id)?;
    let record = bind_workspace_record_path(config, workspace_id, closing.record)?;
    if closing.force != request.force || closing.consumer_released != request.consumer_released {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceStateMismatch,
            "Workspace closing reconciliation requires the originally admitted close parameters",
            Some("workspaceId"),
            false,
        ));
    }
    if let Some(expected) = &request.expected_source_state_digest {
        if expected != &closing.source_state_digest {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::RevisionMismatch,
                "interrupted Workspace closing source witness differs from expectedSourceStateDigest",
                Some("expectedSourceStateDigest"),
                false,
            ));
        }
    }
    let source_repo = Path::new(&record.source_repo);
    // The Git source is the sole authority for the original HEAD/rescue ref.
    // If it disappeared too, do not infer that no unique output remains.
    if !source_repo.is_dir() || canonical_directory(source_repo, "sourceRepo")?.to_string_lossy() != record.source_repo {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            "Workspace closing source repository is unavailable or changed identity",
            Some("workspaceId"),
            false,
        ));
    }
    // Same path is not enough if another Git repository was installed at
    // that path after the first physical removal. The original exact HEAD
    // must remain an object of the recorded source repository before
    // reconstructing a CLOSED tombstone from the persisted witness.
    let expected_commit = format!("{}^{{commit}}", closing.final_head);
    let verified_commit = workspace_git_command()
        .arg("-C")
        .arg(source_repo)
        .args(["cat-file", "-e", &expected_commit])
        .output()
        .map_err(|error| tool_unavailable("git cat-file closing HEAD", error))?;
    if !verified_commit.status.success() {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionMismatch,
            "original Workspace closing HEAD is no longer present in its source Git repository",
            Some("workspaceId"),
            false,
        ));
    }
    let target_meta = match fs::symlink_metadata(target) {
        Ok(metadata) => Some(metadata),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => None,
        Err(error) => return Err(io_error(target, "inspect interrupted Workspace close", error)),
    };
    if let Some(metadata) = &target_meta {
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "interrupted Workspace directory is not a regular managed directory",
                Some("workspaceId"),
                false,
            ));
        }
        #[cfg(target_os = "linux")]
        ensure_no_closing_workspace_systemd_consumer(target)?;
        let actual = canonical_directory(target, "workspacePath")?;
        if actual != Path::new(&record.workspace_path) {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "interrupted Workspace path no longer matches original identity",
                Some("workspaceId"),
                false,
            ));
        }
        let current_head = git_output(&actual, ["rev-parse", "HEAD"])?;
        let observed_head = registered_workspace_head(&record)?;
        let current_source = workspace_source_state_digest_at(&actual)?;
        let common = git_output(&actual, ["rev-parse", "--path-format=absolute", "--git-common-dir"])?;
        let source_common = git_output(source_repo, ["rev-parse", "--path-format=absolute", "--git-common-dir"])?;
        if current_head.trim() != closing.final_head
            || observed_head.as_deref() != Some(closing.final_head.as_str())
            || common.trim() != source_common.trim()
            || current_source != closing.source_state_digest
        {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::RevisionMismatch,
                "interrupted Workspace Git identity or original source witness changed",
                Some("workspaceId"),
                false,
            ));
        }
        // The source digest does not include every ignored binary: even a
        // previously authorized FORCE must not erase a new artifact created
        // after CLOSING. Reconciliation of a still-present dirty worktree
        // needs a fresh owner decision; never replay the destructive FORCE.
        if !workspace_dirty_paths(&actual)?.is_empty() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::WorkspaceDirty,
                "interrupted close contains output requiring fresh owner disposition",
                Some("workspaceId"),
                false,
            ));
        }
        if closing.final_head != record.source_revision {
            ensure_rescue_ref(&actual, workspace_id, &closing.final_head)?;
        }
        cleanup_workspace_caches(config, workspace_id)?;
        remove_git_worktree_from_workspace(&actual, request.force)?;
    } else {
        // Git removal completed before the process crashed writing CLOSED.
        // Never silently rewrite an OPEN record if Git still registers a
        // missing worktree: a partially removed Git effect remains UNKNOWN.
        if registered_workspace_head(&record)?.is_some() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::WorkspaceStateMismatch,
                "Git still registers interrupted Workspace despite absent physical directory",
                Some("workspaceId"),
                false,
            ));
        }
        // The original closing intent follows a completed rescue-ref check.
        if closing.final_head != record.source_revision {
            ensure_rescue_ref(source_repo, workspace_id, &closing.final_head)?;
        }
        cleanup_workspace_caches(config, workspace_id)?;
    }
    write_closed_workspace_record(record_path, Some(closing.source_state_digest.clone()))?;
    Ok(WorkspaceCloseResult {
        workspace_id: workspace_id.clone(),
        removed: target_meta.is_some(),
        // Distinguish a physical removal completed by this replay from a
        // prior removal whose missing directory we merely reconciled.
        closure_disposition: if target_meta.is_some() {
            WorkspaceClosureDisposition::Removed
        } else {
            WorkspaceClosureDisposition::RecoveredMissing
        },
        source_state_digest: Some(closing.source_state_digest),
    })
}

pub(crate) fn remove_git_workspace(
    config: &UniversalExecutorConfig,
    request: &WorkspaceCloseRequest,
) -> Result<WorkspaceCloseResult, UniversalExecError> {
    request.validate_shape()?;
    config.ensure_store()?;
    // Do not unlink the only durable recovery intent while a batch is partial.
    ensure_workspace_mutation_quiescent(config, &request.workspace_id)?;
    let record_path = config.workspace_record_path(&request.workspace_id);
    let target = config.workspace_path(&request.workspace_id);

    if !record_path.exists() {
        if target.exists() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "workspace directory exists without an identity record",
                Some("workspaceId"),
                false,
            ));
        }
        cleanup_workspace_caches(config, &request.workspace_id)?;
        if request.expected_source_state_digest.is_some() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::RevisionMismatch,
                "cannot prove the requested Workspace source state after identity loss",
                Some("expectedSourceStateDigest"),
                false,
            ));
        }
        return Ok(WorkspaceCloseResult {
            workspace_id: request.workspace_id.clone(),
            removed: false,
            closure_disposition: WorkspaceClosureDisposition::AlreadyAbsent,
            source_state_digest: None,
        });
    }

    let bytes = read_workspace_record_bytes(&record_path)?;
    if let Some(closed) = decode_closed_workspace_record(&bytes)? {
        validate_closed_identity(&closed, &request.workspace_id)?;
        if let Some(expected) = &request.expected_source_state_digest {
            if closed.source_state_digest.as_deref() != Some(expected.as_str()) {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::RevisionMismatch,
                    "closed Workspace source state differs from expectedSourceStateDigest",
                    Some("expectedSourceStateDigest"),
                    false,
                ));
            }
        }
        cleanup_workspace_caches(config, &request.workspace_id)?;
        return Ok(WorkspaceCloseResult {
            workspace_id: request.workspace_id.clone(),
            removed: false,
            closure_disposition: WorkspaceClosureDisposition::AlreadyClosed,
            source_state_digest: closed.source_state_digest,
        });
    }
    if let Some(closing) = decode_closing_workspace_record(&bytes)? {
        return reconcile_closing_workspace(config, request, &record_path, &target, closing);
    }
    let record = bind_workspace_record_path(
        config,
        &request.workspace_id,
        decode_open_workspace_record(&bytes, &request.workspace_id)?,
    )?;

    #[cfg(target_os = "linux")]
    ensure_no_closing_workspace_systemd_consumer(&target)?;

    if !target.exists() {
        if !workspace_record_path_matches_identity(
            config,
            &request.workspace_id,
            &record.workspace_path,
        ) {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "workspace record path mismatch",
                Some("workspacePath"),
                false,
            ));
        }
        let final_head = recover_missing_workspace_head(&record)?;
        if let Some(head) = final_head
            .as_deref()
            .filter(|head| *head != record.source_revision)
        {
            let source_repo = Path::new(&record.source_repo);
            if source_repo.is_dir() {
                ensure_rescue_ref(source_repo, &request.workspace_id, head)?;
            }
        }
        if request.expected_source_state_digest.is_some() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::RevisionMismatch,
                "cannot prove expectedSourceStateDigest after Workspace directory loss",
                Some("expectedSourceStateDigest"),
                false,
            ));
        }
        cleanup_workspace_caches(config, &request.workspace_id)?;
        write_closed_workspace_record(&record_path, None)?;
        return Ok(WorkspaceCloseResult {
            workspace_id: request.workspace_id.clone(),
            removed: false,
            closure_disposition: WorkspaceClosureDisposition::RecoveredMissing,
            source_state_digest: None,
        });
    }

    let expected = canonical_directory(&target, "workspacePath")?;
    let recorded = canonical_directory(Path::new(&record.workspace_path), "workspacePath")?;
    if expected != recorded {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            "workspace record path mismatch",
            Some("workspacePath"),
            false,
        ));
    }

    if workspace_git_common_dir_at(&recorded).is_err() {
        let registered_head = registered_workspace_head(&record)?;
        if request.expected_source_state_digest.is_some() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::RevisionMismatch,
                "cannot prove expectedSourceStateDigest after Workspace Git metadata loss",
                Some("expectedSourceStateDigest"),
                false,
            ));
        }
        if !request.force {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::WorkspaceDirty,
                "cannot prove Workspace clean after Git worktree metadata loss; retry with force=true to recover the residual directory",
                Some("workspaceId"),
                false,
            ));
        }

        require_recent_workspace_consumer_release(
            record.created_unix_ms,
            request.consumer_released,
        )?;

        let final_head = recover_missing_workspace_head(&record)?;
        if let Some(head) = final_head
            .as_deref()
            .filter(|head| *head != record.source_revision)
        {
            let source_repo = Path::new(&record.source_repo);
            if source_repo.is_dir() {
                ensure_rescue_ref(source_repo, &request.workspace_id, head)?;
            }
        }

        cleanup_workspace_caches(config, &request.workspace_id)?;
        if registered_head.is_some() {
            remove_registered_workspace_with_broken_metadata(&record, &target, &recorded)?;
        } else {
            remove_residual_workspace_directory(&target)?;
        }
        write_closed_workspace_record(&record_path, None)?;
        return Ok(WorkspaceCloseResult {
            workspace_id: request.workspace_id.clone(),
            removed: true,
            closure_disposition: WorkspaceClosureDisposition::RecoveredMissing,
            source_state_digest: None,
        });
    }

    let source_state_digest = match workspace_source_state_digest_at(&recorded) {
        Ok(digest) => digest,
        Err(error) => {
            // A registered Git worktree with an unborn HEAD has no source
            // commit for the normal diff/digest path. Do not disguise this as
            // a verified clean state or manufacture a zero-OID rescue ref.
            let unborn_head = registered_workspace_head(&record)?.is_some_and(|head| {
                (head.len() == 40 || head.len() == 64) && head.bytes().all(|byte| byte == b'0')
            });
            if !unborn_head {
                return Err(error);
            }
            if request.expected_source_state_digest.is_some() {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::RevisionMismatch,
                    "unborn Workspace HEAD cannot prove expectedSourceStateDigest",
                    Some("expectedSourceStateDigest"),
                    false,
                ));
            }
            if !request.force {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::WorkspaceDirty,
                    "unborn Workspace HEAD cannot prove a clean source state; force=true is required",
                    Some("workspaceId"),
                    false,
                ));
            }
            require_recent_workspace_consumer_release(
                record.created_unix_ms,
                request.consumer_released,
            )?;
            cleanup_workspace_caches(config, &request.workspace_id)?;
            remove_git_worktree_from_workspace(&recorded, true)?;
            write_closed_workspace_record(&record_path, None)?;
            return Ok(WorkspaceCloseResult {
                workspace_id: request.workspace_id.clone(),
                removed: true,
                closure_disposition: WorkspaceClosureDisposition::RecoveredMissing,
                source_state_digest: None,
            });
        }
    };
    if let Some(expected) = &request.expected_source_state_digest {
        if expected != &source_state_digest {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::RevisionMismatch,
                "Workspace source state differs from expectedSourceStateDigest",
                Some("expectedSourceStateDigest"),
                false,
            ));
        }
    }
    if !request.force {
        let dirty = workspace_dirty_paths(&recorded)?;
        if !dirty.is_empty() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::WorkspaceDirty,
                format!(
                    "workspace contains uncommitted or untracked paths: {}",
                    dirty.join(", ")
                ),
                Some("workspaceId"),
                false,
            ));
        }
    }

    require_recent_workspace_consumer_release(record.created_unix_ms, request.consumer_released)?;

    let final_head = git_output(&recorded, ["rev-parse", "HEAD"])?
        .trim()
        .to_string();
    if final_head != record.source_revision {
        ensure_rescue_ref(&recorded, &request.workspace_id, &final_head)?;
    }
    // Before any irreversible cache/Git effects, persist the exact validated
    // OPEN identity and source-state CAS witness in the existing record.
    // This is a native file-side intent, not a second registry or PG transaction.
    let closing = ClosingWorkspaceRecord {
        schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
        state: "closing".to_string(),
        record: record.clone(),
        source_state_digest: source_state_digest.clone(),
        final_head,
        force: request.force,
        consumer_released: request.consumer_released,
    };
    write_json_atomic(&record_path, &closing)?;
    cleanup_workspace_caches(config, &request.workspace_id)?;
    remove_git_worktree_from_workspace(&recorded, request.force)?;
    write_closed_workspace_record(&record_path, Some(source_state_digest.clone()))?;
    Ok(WorkspaceCloseResult {
        workspace_id: request.workspace_id.clone(),
        removed: true,
        closure_disposition: WorkspaceClosureDisposition::Removed,
        source_state_digest: Some(source_state_digest),
    })
}

fn cleanup_workspace_caches(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<(), UniversalExecError> {
    let tmp_backing = config.workspace_tmp_path(workspace_id);
    let canonical_tmp_backing = config.canonical_workspace_tmp_path(workspace_id)?;
    let tmp_presentation = config.workspace_tmp_presentation_path(workspace_id)?;
    match fs::symlink_metadata(&tmp_presentation) {
        Ok(metadata) => {
            if !metadata.file_type().is_symlink() {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::MetadataCorrupt,
                    format!(
                        "Workspace temporary presentation {} is not a symlink",
                        tmp_presentation.display()
                    ),
                    Some("workspaceId"),
                    false,
                ));
            }
            let target = fs::read_link(&tmp_presentation).map_err(|error| {
                io_error(
                    &tmp_presentation,
                    "read Workspace temporary presentation",
                    error,
                )
            })?;
            if target != canonical_tmp_backing {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::MetadataCorrupt,
                    format!(
                        "Workspace temporary presentation {} points at {}, expected {}",
                        tmp_presentation.display(),
                        target.display(),
                        canonical_tmp_backing.display()
                    ),
                    Some("workspaceId"),
                    false,
                ));
            }
            fs::remove_file(&tmp_presentation).map_err(|error| {
                io_error(
                    &tmp_presentation,
                    "remove Workspace temporary presentation",
                    error,
                )
            })?;
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
        Err(error) => {
            return Err(io_error(
                &tmp_presentation,
                "inspect Workspace temporary presentation",
                error,
            ));
        }
    }
    for path in [
        config.workspace_cache_path(workspace_id),
        config.workspace_build_cache_path(workspace_id),
        tmp_backing,
    ] {
        match fs::remove_dir_all(&path) {
            Ok(()) => {}
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(error) => return Err(io_error(&path, "remove Workspace cache", error)),
        }
    }
    Ok(())
}

fn write_closed_workspace_record(
    record_path: &Path,
    source_state_digest: Option<String>,
) -> Result<(), UniversalExecError> {
    let closed = ClosedWorkspaceRecord {
        schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
        state: "closed".to_string(),
        legacy_workspace_id: String::new(),
        _legacy_source_repo: None,
        _legacy_source_revision: None,
        _legacy_final_head: None,
        source_state_digest,
        _legacy_closed_unix_ms: None,
        _legacy_removal_result: None,
    };
    write_json_atomic(record_path, &closed)
}

// A rescue ref is a durable, immutable Workspace identity. Checking first
// and then updating unconditionally is a TOCTOU overwrite under concurrent
// closures. Git's expected-absent old oid is the atomic authority; the empty
// string also works in SHA-256 repositories without hardcoding the hash width.
fn try_create_rescue_ref_if_absent(
    git_root: &Path,
    reference: &str,
    final_head: &str,
) -> Result<std::process::Output, UniversalExecError> {
    workspace_git_command()
        .arg("-C")
        .arg(git_root)
        .args(["update-ref", reference, final_head, ""])
        .output()
        .map_err(|error| tool_unavailable("git update-ref", error))
}

fn ensure_rescue_ref(
    git_root: &Path,
    workspace_id: &str,
    final_head: &str,
) -> Result<(), UniversalExecError> {
    let reference = format!("refs/ordivon/closed/{workspace_id}");
    let created = try_create_rescue_ref_if_absent(git_root, &reference, final_head)?;
    if created.status.success() {
        return Ok(());
    }
    // A simultaneous closure may have won the creation transaction. Accept
    // only the exact same immutable HEAD; never turn a losing CAS into a write.
    let existing = workspace_git_command()
        .arg("-C")
        .arg(git_root)
        .args(["rev-parse", "--verify", "--quiet", &reference])
        .output()
        .map_err(|error| tool_unavailable("git rev-parse rescue ref", error))?;
    if !existing.status.success() {
        return Err(tool_failed("git update-ref", &created.stderr));
    }
    let observed = String::from_utf8(existing.stdout).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            format!("git rescue ref output is not UTF-8: {error}"),
            None,
            false,
        )
    })?;
    if observed.trim() == final_head {
        return Ok(());
    }
    Err(UniversalExecError::new(
        UniversalExecErrorCode::RevisionMismatch,
        "workspace rescue ref already points to a different commit",
        Some("workspaceId"),
        false,
    ))
}

fn remove_residual_workspace_directory(target: &Path) -> Result<(), UniversalExecError> {
    let metadata = fs::symlink_metadata(target)
        .map_err(|error| io_error(target, "inspect residual Workspace directory", error))?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            "residual Workspace path must remain a non-symlink directory",
            Some("workspaceId"),
            false,
        ));
    }
    fs::remove_dir_all(target)
        .map_err(|error| io_error(target, "remove residual Workspace directory", error))
}

fn remove_registered_workspace_with_broken_metadata(
    record: &WorkspaceRecord,
    target: &Path,
    recorded: &Path,
) -> Result<(), UniversalExecError> {
    let source_repo = Path::new(&record.source_repo);
    if remove_git_worktree(source_repo, recorded, true).is_ok() {
        return Ok(());
    }

    let git_marker = target.join(".git");
    match fs::symlink_metadata(&git_marker) {
        Ok(metadata) if metadata.is_file() || metadata.file_type().is_symlink() => {
            fs::remove_file(&git_marker).map_err(|error| {
                io_error(&git_marker, "remove invalid Workspace .git marker", error)
            })?;
        }
        Ok(_) => {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "broken registered Workspace has a non-file .git marker",
                Some("workspaceId"),
                false,
            ));
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
        Err(error) => {
            return Err(io_error(
                &git_marker,
                "inspect invalid Workspace .git marker",
                error,
            ));
        }
    }

    let output = workspace_git_command()
        .arg("-C")
        .arg(source_repo)
        .args(["worktree", "prune", "--expire", "now"])
        .output()
        .map_err(|error| tool_unavailable("git worktree prune", error))?;
    if !output.status.success() {
        return Err(tool_failed("git worktree prune", &output.stderr));
    }
    if registered_workspace_head(record)?.is_some() {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git worktree prune did not release the broken registered Workspace",
            Some("workspaceId"),
            false,
        ));
    }
    remove_residual_workspace_directory(target)
}

fn registered_workspace_head(
    record: &WorkspaceRecord,
) -> Result<Option<String>, UniversalExecError> {
    let source_repo = Path::new(&record.source_repo);
    if !source_repo.is_dir() {
        return Ok(None);
    }
    let output = workspace_git_command()
        .arg("-C")
        .arg(source_repo)
        .args(["worktree", "list", "--porcelain"])
        .output()
        .map_err(|error| tool_unavailable("git worktree list", error))?;
    if !output.status.success() {
        return Err(tool_failed("git worktree list", &output.stderr));
    }
    let wanted = Path::new(&record.workspace_path);
    let text = String::from_utf8(output.stdout).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            format!("git worktree list output is not UTF-8: {error}"),
            None,
            false,
        )
    })?;
    let mut matched = false;
    for line in text.lines() {
        if let Some(path) = line.strip_prefix("worktree ") {
            matched = Path::new(path) == wanted;
        } else if matched {
            if let Some(head) = line.strip_prefix("HEAD ") {
                return Ok(Some(head.to_string()));
            }
            if line.is_empty() {
                matched = false;
            }
        }
    }
    Ok(None)
}

fn recover_missing_workspace_head(
    record: &WorkspaceRecord,
) -> Result<Option<String>, UniversalExecError> {
    let source_repo = Path::new(&record.source_repo);
    if !source_repo.is_dir() {
        return Ok(None);
    }
    let rescue_ref = format!("refs/ordivon/closed/{}", record.workspace_id);
    let rescued = workspace_git_command()
        .arg("-C")
        .arg(source_repo)
        .args(["rev-parse", "--verify", "--quiet", &rescue_ref])
        .output()
        .map_err(|error| tool_unavailable("git rev-parse rescue ref", error))?;
    if rescued.status.success() {
        return String::from_utf8(rescued.stdout)
            .map(|value| Some(value.trim().to_string()))
            .map_err(|error| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ToolFailed,
                    format!("git rescue ref output is not UTF-8: {error}"),
                    None,
                    false,
                )
            });
    }
    let output = workspace_git_command()
        .arg("-C")
        .arg(source_repo)
        .args(["worktree", "list", "--porcelain"])
        .output()
        .map_err(|error| tool_unavailable("git worktree list", error))?;
    if !output.status.success() {
        return Err(tool_failed("git worktree list", &output.stderr));
    }
    let wanted = Path::new(&record.workspace_path);
    let text = String::from_utf8(output.stdout).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            format!("git worktree list output is not UTF-8: {error}"),
            None,
            false,
        )
    })?;
    let mut matched = false;
    for line in text.lines() {
        if let Some(path) = line.strip_prefix("worktree ") {
            matched = Path::new(path) == wanted;
        } else if matched {
            if let Some(head) = line.strip_prefix("HEAD ") {
                return Ok(Some(head.to_string()));
            }
            if line.is_empty() {
                matched = false;
            }
        }
    }
    Ok(None)
}

fn remove_git_worktree_from_workspace(
    workspace: &Path,
    force: bool,
) -> Result<(), UniversalExecError> {
    let common_dir = git_output(
        workspace,
        ["rev-parse", "--path-format=absolute", "--git-common-dir"],
    )?;
    let common_dir = PathBuf::from(common_dir.trim());
    let mut command = workspace_git_command();
    command
        .arg("--git-dir")
        .arg(common_dir)
        .args(["worktree", "remove"]);
    if force {
        command.arg("--force");
    }
    let output = command
        .arg(workspace)
        .output()
        .map_err(|error| tool_unavailable("git worktree remove", error))?;
    if output.status.success() {
        Ok(())
    } else {
        Err(tool_failed("git worktree remove", &output.stderr))
    }
}

#[cfg(test)]
mod rescue_ref_atomicity_tests {
    use super::*;

    fn git(root: &Path, args: &[&str]) -> String {
        let output = workspace_git_command()
            .arg("-C")
            .arg(root)
            .args(args)
            .output()
            .expect("native Git must run");
        assert!(
            output.status.success(),
            "Git {:?} failed: {}",
            args,
            String::from_utf8_lossy(&output.stderr)
        );
        String::from_utf8(output.stdout)
            .expect("Git output is UTF-8")
            .trim()
            .to_string()
    }

    #[test]
    fn rescue_ref_create_if_absent_does_not_overwrite_interleaved_commit() {
        // The Git ref transaction, not an Agent-side preflight read,
        // atomically decides whether the immutable rescue slot is free.
        for algorithm in ["sha1", "sha256"] {
            let path = std::env::temp_dir().join(format!(
                "ordivon-rescue-cas-{}-{algorithm}-{}",
                std::process::id(),
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .expect("clock")
                    .as_nanos()
            ));
            std::fs::create_dir(&path).expect("create test repository");
            git(
                &path,
                &[
                    "init",
                    "-q",
                    "-b",
                    "main",
                    &format!("--object-format={algorithm}"),
                ],
            );
            git(&path, &["config", "user.name", "Ordivon Test"]);
            git(&path, &["config", "user.email", "test@example.invalid"]);
            std::fs::write(path.join("state"), b"first").expect("first source");
            git(&path, &["add", "."]);
            git(&path, &["commit", "-qm", "first"]);
            let first_head = git(&path, &["rev-parse", "HEAD"]);
            std::fs::write(path.join("state"), b"second").expect("second source");
            git(&path, &["add", "."]);
            git(&path, &["commit", "-qm", "second"]);
            let second_head = git(&path, &["rev-parse", "HEAD"]);
            let reference = "refs/ordivon/closed/one-slot";
            let first = try_create_rescue_ref_if_absent(&path, reference, &first_head)
                .expect("atomic Git transaction");
            assert!(first.status.success());
            let collision = try_create_rescue_ref_if_absent(&path, reference, &second_head)
                .expect("atomic Git transaction");
            assert!(
                !collision.status.success(),
                "an occupied slot must never be replaced"
            );
            assert_eq!(git(&path, &["rev-parse", reference]), first_head);
            ensure_rescue_ref(&path, "one-slot", &first_head).expect("same HEAD is idempotent");
            let mismatch = ensure_rescue_ref(&path, "one-slot", &second_head)
                .expect_err("a different HEAD must fail closed");
            assert_eq!(mismatch.code, UniversalExecErrorCode::RevisionMismatch);
            assert_eq!(git(&path, &["rev-parse", reference]), first_head);
            std::fs::remove_dir_all(path).expect("remove temporary test repository");
        }
    }
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
        fs::write(&template,
            "[Service]\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/%I\n"
        ).unwrap();
        symlink(&template, wants.join("agent@ws-raw.service")).unwrap();
        let found = installed_systemd_workspace_consumers("ws-raw", &[&root]).unwrap();
        assert_eq!(found, vec![wants.join("agent@ws-raw.service").display().to_string()]);
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
        assert!(
            installed_systemd_workspace_consumers("ws-target", &[&root])
                .unwrap()
                .is_empty()
        );
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
        assert!(
            installed_systemd_workspace_consumers("ws-other", &[&root])
                .unwrap()
                .is_empty()
        );
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
        ).unwrap();
        assert!(
            ensure_no_installed_systemd_consumer("ws-target", &[&root]).is_ok(),
            "a different Workspace prefix alias must not block close",
        );
        let link = root.join("target.service");
        symlink(
            "/var/lib/ordivon/runtime/workspaces/ws-target/linked.service",
            &link,
        ).unwrap();
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
            .unwrap().is_empty());
        let names = vec!["transient.service".to_string()];
        let show = "Id=transient.service\nLoadState=loaded\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-live\n\n";
        assert_eq!(manager_unit_consumers(show, "ws-live", &names).unwrap(), names);
        assert!(manager_unit_consumers(show, "ws-live-copy", &names).unwrap().is_empty());
    }

    #[test]
    fn changing_or_partial_manager_snapshot_is_not_a_negative_consumer_proof() {
        let names = vec!["one.service".to_string(), "two.scope".to_string()];
        let one = "Id=one.service\nLoadState=loaded\nWorkingDirectory=\n\n";
        assert!(manager_unit_consumers(one, "ws-root", &names).is_err());
        let missing = "Id=one.service\nLoadState=not-found\nWorkingDirectory=\n\n";
        assert!(manager_unit_consumers(missing, "ws-root", &names[..1]).unwrap().is_empty());
        let masked = "Id=one.service\nLoadState=masked\nWorkingDirectory=\n\n";
        assert!(manager_unit_consumers(masked, "ws-root", &names[..1]).unwrap().is_empty());
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
            "list-units", "--all", "--plain", "--no-legend", "--no-pager",
        ]).expect("real systemd manager unit inventory");
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
        ).unwrap();
        assert!(installed_systemd_workspace_consumers_at(expected, &[&root]).unwrap().is_empty());
        fs::write(
            &service,
            format!("[Service]\nExecStart=/bin/sh {}/run.sh\n", expected.display()),
        ).unwrap();
        let hits = installed_systemd_workspace_consumers_at(expected, &[&root]).unwrap();
        assert_eq!(hits, vec![service.display().to_string()]);
        assert!(ensure_no_installed_systemd_consumer_at(expected, &[&root]).is_err());
        let names = vec!["transient-pg.service".to_string()];
        let manager = format!(
            "Id=transient-pg.service\nLoadState=loaded\nWorkingDirectory={}\n\n",
            expected.display()
        );
        assert_eq!(manager_unit_consumers_at(&manager, expected, &names).unwrap(), names);
        assert!(manager_unit_consumers_at(&manager, neighbor, &names).unwrap().is_empty());
        let template = root.join("runner@ws-pg.service");
        fs::write(&template,
            "[Service]\nWorkingDirectory=/var/lib/ordivon/pg-candidate/workspaces/%i\n"
        ).unwrap();
        assert!(installed_systemd_workspace_consumers_at(expected, &[&root])
            .unwrap().contains(&template.display().to_string()));
    }

    #[test]
    fn loaded_manager_properties_cover_scope_environment_and_exec() {
        let names = vec!["one.scope".to_string(), "two.service".to_string()];
        let show = "Id=one.scope\nLoadState=loaded\nEnvironment=ROOT=/var/lib/ordivon/runtime/workspaces/ws-scope/bin\n\nId=two.service\nLoadState=loaded\nExecStart={ path=/bin/sh ; argv[]=/bin/sh /var/lib/ordivon/runtime/workspaces/ws-scope/job; }\n\n";
        assert_eq!(manager_unit_consumers(show, "ws-scope", &names).unwrap(), names);
        assert!(manager_unit_consumers(show, "ws-other", &names).unwrap().is_empty());
    }

}


#[cfg(test)]
mod durable_closing_intent_tests {
    use super::*;

    fn git(root: &Path, args: &[&str]) -> String {
        let output = workspace_git_command()
            .arg("-C")
            .arg(root)
            .args(args)
            .output()
            .expect("Git must execute in isolated disposable repo");
        assert!(
            output.status.success(),
            "{:?}: {}",
            args,
            String::from_utf8_lossy(&output.stderr)
        );
        String::from_utf8(output.stdout)
            .expect("test Git output")
            .trim()
            .to_string()
    }

    fn source_workspace(
        id: &str,
    ) -> (tempfile::TempDir, UniversalExecutorConfig, WorkspaceRecord, String) {
        let tmp = tempfile::tempdir().expect("disposable native store");
        let source = tmp.path().join("repository");
        fs::create_dir(&source).expect("source directory");
        git(&source, &["init", "-q"]);
        git(&source, &["config", "user.name", "Workspace Crash Test"]);
        git(&source, &["config", "user.email", "test@example.invalid"]);
        fs::write(source.join("tracked.txt"), b"durable tracked payload")
            .expect("write repository fixture");
        git(&source, &["add", "tracked.txt"]);
        git(&source, &["commit", "-qm", "initial"]);
        let head = git(&source, &["rev-parse", "HEAD"]);
        let cfg = UniversalExecutorConfig {
            store_root: tmp.path().join("runtime-store"),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: Some(PathBuf::from("/usr/bin/true")),
            allowed_executable_roots: vec![PathBuf::from("/usr/bin")],
            max_runtime_ms: 10000,
            max_output_bytes: 1024 * 1024,
        };
        let request = GitWorkspaceCreateRequest {
            schema_version: 1,
            workspace_id: id.to_string(),
            source_repo: source.to_string_lossy().into_owned(),
            source_revision: head.clone(),
        };
        let record = create_git_workspace_record(&cfg, &request)
            .expect("native workspace opening under durable record");
        let digest = workspace_source_state_digest_at(Path::new(&record.workspace_path))
            .expect("exact physical source witness");
        (tmp, cfg, record, digest)
    }

    fn closing_fixture(
        config: &UniversalExecutorConfig,
        record: &WorkspaceRecord,
        source_digest: &str,
    ) -> WorkspaceCloseRequest {
        let closing = ClosingWorkspaceRecord {
            schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
            state: "closing".to_string(),
            record: record.clone(),
            source_state_digest: source_digest.to_string(),
            final_head: git(Path::new(&record.workspace_path), &["rev-parse", "HEAD"]),
            force: false,
            consumer_released: true,
        };
        write_json_atomic(
            &config.workspace_record_path(&record.workspace_id),
            &closing,
        )
        .expect("durably recorded first-class close intent");
        WorkspaceCloseRequest {
            schema_version: 1,
            workspace_id: record.workspace_id.clone(),
            force: false,
            consumer_released: true,
            expected_source_state_digest: Some(source_digest.to_string()),
        }
    }

    #[test]
    fn crash_after_git_removal_retains_original_digest_and_closed_tombstone() {
        let (_temp, config, record, digest) = source_workspace("ws-close-crash-after-git");
        let request = closing_fixture(&config, &record, &digest);
        let interim = load_workspace_record(&config, &record.workspace_id)
            .expect_err("CLOSING must not be visible as OPEN to any new Job or Agent");
        assert_eq!(interim.code, UniversalExecErrorCode::WorkspaceStateMismatch);
        remove_git_worktree_from_workspace(Path::new(&record.workspace_path), false)
            .expect("simulate process crash after physical Git effect");
        let recovered = remove_git_workspace(&config, &request)
            .expect("exact expected digest survives physical path loss");
        assert_eq!(recovered.closure_disposition, WorkspaceClosureDisposition::RecoveredMissing);
        assert!(!recovered.removed);
        assert_eq!(recovered.source_state_digest.as_deref(), Some(digest.as_str()));
        let repeat = remove_git_workspace(&config, &request)
            .expect("closed tombstone remains idempotent with exact original digest");
        assert_eq!(repeat.closure_disposition, WorkspaceClosureDisposition::AlreadyClosed);
        assert_eq!(repeat.source_state_digest.as_deref(), Some(digest.as_str()));
    }

    #[test]
    fn crash_before_git_removal_replays_only_unchanged_original_source() {
        let (_temp, config, record, digest) = source_workspace("ws-close-crash-before-git");
        let request = closing_fixture(&config, &record, &digest);
        let completed = remove_git_workspace(&config, &request)
            .expect("idempotent exact replay of authorized physical Git close");
        assert_eq!(completed.closure_disposition, WorkspaceClosureDisposition::Removed);
        assert!(completed.removed);
        assert_eq!(completed.source_state_digest.as_deref(), Some(digest.as_str()));
        assert!(!Path::new(&record.workspace_path).exists());
    }

    #[test]
    fn altered_source_or_changed_release_assertion_cannot_resume_closing() {
        let (_temp, config, record, digest) = source_workspace("ws-close-crash-mutated");
        let request = closing_fixture(&config, &record, &digest);
        let weaker = WorkspaceCloseRequest { consumer_released: false, ..request.clone() };
        let err = remove_git_workspace(&config, &weaker)
            .expect_err("resume must preserve original caller assertion");
        assert_eq!(err.code, UniversalExecErrorCode::WorkspaceStateMismatch);
        let wrong_digest = WorkspaceCloseRequest {
            expected_source_state_digest: Some(format!("sha256:{}", "0".repeat(64))),
            ..request.clone()
        };
        let err = remove_git_workspace(&config, &wrong_digest)
            .expect_err("resume must preserve original immutable physical CAS");
        assert_eq!(err.code, UniversalExecErrorCode::RevisionMismatch);
        fs::write(Path::new(&record.workspace_path).join("tracked.txt"), "modified after intent")
            .expect("introduce new tracked data after interruption");
        let err = remove_git_workspace(&config, &request)
            .expect_err("reconciliation may not overwrite later changed payload");
        assert_eq!(err.code, UniversalExecErrorCode::RevisionMismatch);
        assert!(Path::new(&record.workspace_path).exists());
    }

    #[test]
    fn force_replay_does_not_destroy_new_ignored_binary_after_original_intent() {
        let (_temp, config, record, digest) = source_workspace("ws-close-crash-ignored");
        let request = closing_fixture(&config, &record, &digest);
        let record_path = config.workspace_record_path(&record.workspace_id);
        let mut closing = decode_closing_workspace_record(
            &fs::read(&record_path).expect("closing intent bytes"),
        )
        .expect("read durable record")
        .expect("state is closing");
        closing.force = true;
        write_json_atomic(&record_path, &closing).expect("simulate original authorized forced close");
        let ignored = Path::new(&record.workspace_path).join("delivery.bin");
        fs::write(&ignored, b"unique unshipped binary").expect("new ignored output");
        git(Path::new(&record.workspace_path), &["config", "core.excludesfile", "/dev/null"]);
        // Exact Git ignored status rather than a filename guess.
        fs::write(Path::new(&record.workspace_path).join(".gitignore"), b"delivery.bin\n")
            .expect("mark the binary as ignored");
        let candidate = WorkspaceCloseRequest { force: true, ..request };
        let denied = remove_git_workspace(&config, &candidate)
            .expect_err("forced crash replay cannot delete unexpected ignored output");
        assert!(
            matches!(denied.code, UniversalExecErrorCode::WorkspaceDirty | UniversalExecErrorCode::RevisionMismatch),
            "the new data must block automatic destructive reconciliation"
        );
        assert_eq!(fs::read(&ignored).unwrap(), b"unique unshipped binary");
    }

    #[test]
    fn missing_directory_still_registered_in_git_is_not_a_proven_closed_effect() {
        let (_temp, config, record, digest) = source_workspace("ws-close-crash-registered");
        let request = closing_fixture(&config, &record, &digest);
        let original = create_git_workspace_record(
            &config,
            &GitWorkspaceCreateRequest {
                schema_version: 1,
                workspace_id: record.workspace_id.clone(),
                source_repo: record.source_repo.clone(),
                source_revision: record.source_revision.clone(),
            },
        )
        .expect_err("same WorkspaceId cannot be reopened while closing");
        assert_eq!(original.code, UniversalExecErrorCode::WorkspaceExists);
        // Simulate a crash/foreign filesystem loss without the Git native
        // worktree deregistration side effect having completed.
        fs::remove_dir_all(&record.workspace_path)
            .expect("remove only self-owned disposable test worktree directory");
        assert!(registered_workspace_head(&record).unwrap().is_some());
        let denied = remove_git_workspace(&config, &request)
            .expect_err("missing physical tree is not sufficient to mark closed");
        assert_eq!(denied.code, UniversalExecErrorCode::WorkspaceStateMismatch);
        assert!(
            decode_closing_workspace_record(&fs::read(config.workspace_record_path(&record.workspace_id)).unwrap())
                .unwrap()
                .is_some(),
            "unfinished close intent remains for operator reconciliation"
        );
    }

    #[test]
    fn replaced_source_git_repository_cannot_validate_missing_worktree_recovery() {
        let (_temp, config, record, digest) = source_workspace("ws-close-replaced-source");
        let request = closing_fixture(&config, &record, &digest);
        remove_git_worktree_from_workspace(Path::new(&record.workspace_path), false)
            .expect("simulate completed Git removal and crash before CLOSED record");
        let source = Path::new(&record.source_repo);
        fs::remove_dir_all(source.join(".git"))
            .expect("only disposable test repository Git metadata may be replaced");
        git(source, &["init", "-q"]);
        git(source, &["config", "user.name", "Replacement Repository"]);
        git(source, &["config", "user.email", "replacement@example.invalid"]);
        fs::write(source.join("unrelated.txt"), b"different Git source content")
            .expect("replacement repository commit payload");
        git(source, &["add", "unrelated.txt"]);
        git(source, &["commit", "-qm", "unrelated replacement"]);
        assert_ne!(git(source, &["rev-parse", "HEAD"]), record.source_revision);
        let denied = remove_git_workspace(&config, &request)
            .expect_err("a new Git repository at the old path is not the original source");
        assert_eq!(denied.code, UniversalExecErrorCode::RevisionMismatch);
        assert!(
            decode_closing_workspace_record(&fs::read(config.workspace_record_path(&record.workspace_id)).unwrap())
                .unwrap()
                .is_some(),
            "the durable closing intent must survive a source authority mismatch"
        );
    }

    #[test]
    fn normal_close_produces_exact_closed_record_not_intermediate_closing() {
        let (_temp, config, record, digest) = source_workspace("ws-close-uninterrupted");
        let request = WorkspaceCloseRequest {
            schema_version: 1,
            workspace_id: record.workspace_id.clone(),
            force: false,
            consumer_released: true,
            expected_source_state_digest: Some(digest.clone()),
        };
        let closed = remove_git_workspace(&config, &request)
            .expect("normal native worktree close");
        assert!(closed.removed);
        assert_eq!(closed.closure_disposition, WorkspaceClosureDisposition::Removed);
        let again = remove_git_workspace(&config, &request)
            .expect("closed exact digest remains recoverable");
        assert_eq!(again.closure_disposition, WorkspaceClosureDisposition::AlreadyClosed);
        assert_eq!(again.source_state_digest.as_deref(), Some(digest.as_str()));
    }
}
