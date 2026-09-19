pub fn remove_git_workspace(
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
        write_closed_workspace_record(&record_path, &record, final_head, None, "already_missing")?;
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
    let source_state_digest = workspace_source_state_digest_at(&recorded)?;
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
    write_closed_workspace_record(
        &record_path,
        &record,
        Some(final_head),
        Some(source_state_digest.clone()),
        "removed",
    )?;
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
    open: &WorkspaceRecord,
    final_head: Option<String>,
    source_state_digest: Option<String>,
    removal_result: &str,
) -> Result<(), UniversalExecError> {
    let closed = ClosedWorkspaceRecord {
        schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
        state: "closed".to_string(),
        workspace_id: open.workspace_id.clone(),
        source_repo: Some(open.source_repo.clone()),
        source_revision: Some(open.source_revision.clone()),
        final_head,
        source_state_digest,
        closed_unix_ms: now_unix_ms()?,
        removal_result: removal_result.to_string(),
    };
    write_json_atomic(record_path, &closed)
}

fn ensure_rescue_ref(
    git_root: &Path,
    workspace_id: &str,
    final_head: &str,
) -> Result<(), UniversalExecError> {
    let reference = format!("refs/ordivon/closed/{workspace_id}");
    let existing = Command::new("git")
        .arg("-C")
        .arg(git_root)
        .args(["rev-parse", "--verify", "--quiet", &reference])
        .output()
        .map_err(|error| tool_unavailable("git rev-parse rescue ref", error))?;
    if existing.status.success() {
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
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionMismatch,
            "workspace rescue ref already points to a different commit",
            Some("workspaceId"),
            false,
        ));
    }
    let output = Command::new("git")
        .arg("-C")
        .arg(git_root)
        .args(["update-ref", &reference, final_head])
        .output()
        .map_err(|error| tool_unavailable("git update-ref", error))?;
    if output.status.success() {
        Ok(())
    } else {
        Err(tool_failed("git update-ref", &output.stderr))
    }
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
