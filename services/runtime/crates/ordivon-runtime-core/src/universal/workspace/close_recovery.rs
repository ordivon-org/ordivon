// Installed systemd units are durable consumers outside Runtime's Job Registry.
// Do not delete a live Workspace whose exact path is still bound into a
// persistent deployment. This is a bounded, host-local witness, not a proof
// of all external consumers or atomic coordination with systemd installers.
#[cfg(target_os = "linux")]
fn installed_systemd_workspace_consumers(
    workspace_id: &str,
    roots: &[&Path],
) -> Result<Vec<String>, UniversalExecError> {
    const MAX_UNIT_BYTES: u64 = 1024 * 1024;
    const MAX_ENTRIES: usize = 65536;
    const MAX_DEPTH: usize = 12;
    let prefix = format!("/var/lib/ordivon/runtime/workspaces/{workspace_id}");
    let mut matches = Vec::new();
    let mut observed_entries = 0_usize;
    let mut pending = Vec::new();
    for root in roots {
        let metadata = match fs::symlink_metadata(root) {
            Ok(metadata) => metadata,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => continue,
            Err(_) => return Err(external_unit_inspection_error("systemd unit root is unreadable")),
        };
        if !metadata.file_type().is_dir() {
            return Err(external_unit_inspection_error("systemd unit root is not a regular directory"));
        }
        pending.push(((*root).to_path_buf(), 0_usize));
    }
    while let Some((directory, depth)) = pending.pop() {
        if depth > MAX_DEPTH {
            return Err(external_unit_inspection_error("unit directory depth exceeded limit"));
        }
        let entries = fs::read_dir(&directory)
            .map_err(|_| external_unit_inspection_error("could not enumerate systemd unit directory"))?;
        for entry in entries {
            observed_entries += 1;
            if observed_entries > MAX_ENTRIES {
                return Err(external_unit_inspection_error("systemd unit inventory exceeded bound"));
            }
            let entry = entry
                .map_err(|_| external_unit_inspection_error("systemd unit inventory was unreadable"))?;
            let path = entry.path();
            let file_type = entry
                .file_type()
                .map_err(|_| external_unit_inspection_error("systemd unit file type was unreadable"))?;
            if file_type.is_symlink() {
                continue;
            }
            if file_type.is_dir() {
                pending.push((path, depth + 1));
                continue;
            }
            if !file_type.is_file() {
                continue;
            }
            let name = path.file_name().and_then(|s| s.to_str()).unwrap_or("");
            if ![".service", ".timer", ".socket", ".path", ".mount", ".automount", ".conf"]
                .iter()
                .any(|suffix| name.ends_with(suffix))
            {
                continue;
            }
            let metadata = fs::metadata(&path)
                .map_err(|_| external_unit_inspection_error("systemd unit metadata is unreadable"))?;
            if metadata.len() > MAX_UNIT_BYTES {
                return Err(external_unit_inspection_error("systemd unit file exceeds inspection bound"));
            }
            let content = fs::read_to_string(&path)
                .map_err(|_| external_unit_inspection_error("systemd unit bytes are unreadable"))?;
            let consumes = content.lines().any(|line| {
                let line = line.trim_start();
                if line.is_empty() || line.starts_with('#') || line.starts_with(';') {
                    return false;
                }
                let mut suffix = line;
                while let Some(offset) = suffix.find(&prefix) {
                    let tail = &suffix[offset + prefix.len()..];
                    if tail.chars().next().is_none_or(|next|
                        !next.is_ascii_alphanumeric() && next != '.' && next != '_' && next != '-'
                    ) {
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
fn external_unit_inspection_error(reason: &str) -> UniversalExecError {
    UniversalExecError::new(
        UniversalExecErrorCode::WorkspaceStateMismatch,
        format!("cannot prove installed systemd consumer absence: {reason}"),
        Some("workspaceId"),
        true,
    )
}

#[cfg(target_os = "linux")]
fn ensure_no_installed_systemd_consumer(
    workspace_id: &str,
    roots: &[&Path],
) -> Result<(), UniversalExecError> {
    let matches = installed_systemd_workspace_consumers(workspace_id, roots)?;
    if matches.is_empty() {
        return Ok(());
    }
    Err(UniversalExecError::new(
        UniversalExecErrorCode::WorkspaceStateMismatch,
        format!("installed systemd unit still consumes Workspace: {}", matches.join(", ")),
        Some("workspaceId"),
        true,
    ))
}

pub(crate) fn remove_git_workspace(
    config: &UniversalExecutorConfig,
    request: &WorkspaceCloseRequest,
) -> Result<WorkspaceCloseResult, UniversalExecError> {
    request.validate_shape()?;
    config.ensure_store()?;
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
    let record = bind_workspace_record_path(
        config,
        &request.workspace_id,
        decode_open_workspace_record(&bytes, &request.workspace_id)?,
    )?;

    #[cfg(target_os = "linux")]
    if target.exists() {
        ensure_no_installed_systemd_consumer(
            &request.workspace_id,
            &[
                Path::new("/etc/systemd/system"),
                Path::new("/run/systemd/system"),
                Path::new("/usr/lib/systemd/system"),
            ],
        )?;
    }

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
                (head.len() == 40 || head.len() == 64)
                    && head.bytes().all(|byte| byte == b'0')
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

    let final_head = git_output(&recorded, ["rev-parse", "HEAD"])?
        .trim()
        .to_string();
    if final_head != record.source_revision {
        ensure_rescue_ref(&recorded, &request.workspace_id, &final_head)?;
    }
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
    Command::new("git")
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
    let existing = Command::new("git")
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
            fs::remove_file(&git_marker)
                .map_err(|error| io_error(&git_marker, "remove invalid Workspace .git marker", error))?;
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

    let output = Command::new("git")
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
    let output = Command::new("git")
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
    let rescued = Command::new("git")
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
    let output = Command::new("git")
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
    let mut command = Command::new("git");
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
        let output = Command::new("git")
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
            git(&path, &["init", "-q", "-b", "main", &format!("--object-format={algorithm}")]);
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
            assert!(!collision.status.success(), "an occupied slot must never be replaced");
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
        ).unwrap();
        assert!(installed_systemd_workspace_consumers("ws-target", &[&root])
            .unwrap()
            .is_empty());
        fs::write(
            &service,
            "WorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-target\n",
        ).unwrap();
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
        ).unwrap();
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
}
