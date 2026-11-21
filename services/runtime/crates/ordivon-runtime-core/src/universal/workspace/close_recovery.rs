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
        || !closing.source_state_digest[7..]
            .bytes()
            .all(|b| b.is_ascii_hexdigit())
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
    if !source_repo.is_dir()
        || canonical_directory(source_repo, "sourceRepo")?.to_string_lossy() != record.source_repo
    {
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
        Err(error) => {
            return Err(io_error(
                target,
                "inspect interrupted Workspace close",
                error,
            ));
        }
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
        let common = git_output(
            &actual,
            ["rev-parse", "--path-format=absolute", "--git-common-dir"],
        )?;
        let source_common = git_output(
            source_repo,
            ["rev-parse", "--path-format=absolute", "--git-common-dir"],
        )?;
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

/// Before the ORIGINAL Workspace CAS/close cleans caches, preserve any Git
/// content which exists ONLY in the unprivileged independent Git store.
/// This includes an empty Git commit (outer worktree clean), extra refs, or
/// a staged-only change. An ambiguous private repository is held, not GC'd.
fn require_no_unreceived_private_git_candidate(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<(), UniversalExecError> {
    let private = config.workspace_cache_path(workspace_id).join("agent-git");
    match fs::symlink_metadata(&private) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(error) => return Err(io_error(&private, "inspect private Git", error)),
        Ok(meta) if meta.is_dir() && !meta.file_type().is_symlink() => {}
        Ok(_) => return Err(unfinished_open_error("private Git metadata replaced")),
    }
    let bytes = read_workspace_record_bytes(&config.workspace_record_path(workspace_id))?;
    let record: serde_json::Value = serde_json::from_slice(&bytes)
        .map_err(|_| unfinished_open_error("private Git record authority unavailable"))?;
    let revision = record
        .get("sourceRevision")
        .or_else(|| record.get("record").and_then(|r| r.get("sourceRevision")))
        .and_then(|r| r.as_str())
        .ok_or_else(|| unfinished_open_error("private Git SourceRevision missing"))?;
    if workspace_private_git_has_outputs(&private, revision)? {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceDirty,
            "private Git ref/index contains undelivered candidate; original Workspace must remain HELD",
            Some("workspaceId"),
            false,
        ));
    }
    Ok(())
}

pub(crate) fn remove_git_workspace(
    config: &UniversalExecutorConfig,
    request: &WorkspaceCloseRequest,
) -> Result<WorkspaceCloseResult, UniversalExecError> {
    request.validate_shape()?;
    config.ensure_store()?;
    // Never inspect the private Git candidate before the existing lifecycle
    // quiescence fence; an already-running nonroot task could still commit
    // after an early read and before the physical cache is deleted.
    ensure_workspace_mutation_quiescent(config, &request.workspace_id)?;
    require_no_unreceived_private_git_candidate(config, &request.workspace_id)?;
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
    ) -> (
        tempfile::TempDir,
        UniversalExecutorConfig,
        WorkspaceRecord,
        String,
    ) {
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
    fn record_only_closing_is_discoverable_without_auto_release_and_resumable_by_exact_request() {
        let (_temp, config, record, digest) = source_workspace("ws-close-record-only-inventory");
        let request = closing_fixture(&config, &record, &digest);
        remove_git_worktree_from_workspace(Path::new(&record.workspace_path), false)
            .expect("simulate Git physical removal before CLOSED tombstone");
        assert!(!Path::new(&record.workspace_path).exists());
        assert!(config.workspace_record_path(&record.workspace_id).exists());
        let inventory = list_open_workspace_record_inventory(&config)
            .expect("native inventory must enumerate durable record-only closing");
        assert!(
            inventory.records.is_empty(),
            "CLOSING is not an OPEN worktree"
        );
        let issue = inventory
            .issues
            .iter()
            .find(|issue| issue.workspace_id == record.workspace_id)
            .expect("record-only CLOSING must be diagnosable without the Git directory");
        assert_eq!(
            issue.error.code,
            UniversalExecErrorCode::WorkspaceStateMismatch,
            "{}",
            issue.error.message
        );
        assert!(issue.error.message.contains("CLOSING"));

        let unauthorized = WorkspaceCloseRequest {
            schema_version: 1,
            workspace_id: record.workspace_id.clone(),
            force: false,
            consumer_released: false,
            expected_source_state_digest: Some(digest.clone()),
        };
        let denied = remove_git_workspace(&config, &unauthorized)
            .expect_err("inventory cannot confer missing original release authority");
        assert_eq!(denied.code, UniversalExecErrorCode::WorkspaceStateMismatch);
        assert!(config.workspace_record_path(&record.workspace_id).exists());

        let recovered = remove_git_workspace(&config, &request)
            .expect("only original exact request can finish native reconciliation");
        assert_eq!(
            recovered.closure_disposition,
            WorkspaceClosureDisposition::RecoveredMissing
        );
        let after = list_open_workspace_record_inventory(&config)
            .expect("closed tombstone no longer needs recovery");
        assert!(after.records.is_empty());
        assert!(
            after.issues.is_empty(),
            "CLOSED tombstone is not a pending CLOSING"
        );
    }

    #[test]
    fn corrupt_record_only_closing_is_reported_not_silently_dropped() {
        let (_temp, config, record, digest) = source_workspace("ws-close-record-corrupt");
        closing_fixture(&config, &record, &digest);
        remove_git_worktree_from_workspace(Path::new(&record.workspace_path), false)
            .expect("disposable Git removal");
        fs::write(
            config.workspace_record_path(&record.workspace_id),
            b"{not-json",
        )
        .expect("simulate corrupt native record after crash");
        let inventory = list_open_workspace_record_inventory(&config).unwrap();
        assert!(inventory.records.is_empty());
        assert_eq!(inventory.issues.len(), 1);
        assert_eq!(inventory.issues[0].workspace_id, record.workspace_id);
        assert_eq!(
            inventory.issues[0].error.code,
            UniversalExecErrorCode::MetadataCorrupt
        );
    }

    #[cfg(unix)]
    #[test]
    fn record_only_symlink_cannot_import_foreign_record_authority() {
        let (temp, config, record, digest) = source_workspace("ws-close-record-symlink");
        closing_fixture(&config, &record, &digest);
        remove_git_worktree_from_workspace(Path::new(&record.workspace_path), false)
            .expect("disposable Git removal");
        let path = config.workspace_record_path(&record.workspace_id);
        let foreign = temp.path().join("foreign-record.json");
        fs::rename(&path, &foreign).expect("move only disposable fixture record");
        std::os::unix::fs::symlink(&foreign, &path)
            .expect("simulate record file substituted with symlink");
        let inventory = list_open_workspace_record_inventory(&config).unwrap();
        assert!(inventory.records.is_empty());
        assert_eq!(inventory.issues.len(), 1);
        assert_eq!(inventory.issues[0].workspace_id, record.workspace_id);
        assert_eq!(
            inventory.issues[0].error.code,
            UniversalExecErrorCode::MetadataCorrupt
        );
        assert!(
            foreign.exists(),
            "inventory must not consume or delete external record"
        );
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
        assert_eq!(
            recovered.closure_disposition,
            WorkspaceClosureDisposition::RecoveredMissing
        );
        assert!(!recovered.removed);
        assert_eq!(
            recovered.source_state_digest.as_deref(),
            Some(digest.as_str())
        );
        let repeat = remove_git_workspace(&config, &request)
            .expect("closed tombstone remains idempotent with exact original digest");
        assert_eq!(
            repeat.closure_disposition,
            WorkspaceClosureDisposition::AlreadyClosed
        );
        assert_eq!(repeat.source_state_digest.as_deref(), Some(digest.as_str()));
    }

    #[test]
    fn crash_before_git_removal_replays_only_unchanged_original_source() {
        let (_temp, config, record, digest) = source_workspace("ws-close-crash-before-git");
        let request = closing_fixture(&config, &record, &digest);
        let completed = remove_git_workspace(&config, &request)
            .expect("idempotent exact replay of authorized physical Git close");
        assert_eq!(
            completed.closure_disposition,
            WorkspaceClosureDisposition::Removed
        );
        assert!(completed.removed);
        assert_eq!(
            completed.source_state_digest.as_deref(),
            Some(digest.as_str())
        );
        assert!(!Path::new(&record.workspace_path).exists());
    }

    #[test]
    fn altered_source_or_changed_release_assertion_cannot_resume_closing() {
        let (_temp, config, record, digest) = source_workspace("ws-close-crash-mutated");
        let request = closing_fixture(&config, &record, &digest);
        let weaker = WorkspaceCloseRequest {
            consumer_released: false,
            ..request.clone()
        };
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
        fs::write(
            Path::new(&record.workspace_path).join("tracked.txt"),
            "modified after intent",
        )
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
        let mut closing =
            decode_closing_workspace_record(&fs::read(&record_path).expect("closing intent bytes"))
                .expect("read durable record")
                .expect("state is closing");
        closing.force = true;
        write_json_atomic(&record_path, &closing)
            .expect("simulate original authorized forced close");
        let ignored = Path::new(&record.workspace_path).join("delivery.bin");
        fs::write(&ignored, b"unique unshipped binary").expect("new ignored output");
        git(
            Path::new(&record.workspace_path),
            &["config", "core.excludesfile", "/dev/null"],
        );
        // Exact Git ignored status rather than a filename guess.
        fs::write(
            Path::new(&record.workspace_path).join(".gitignore"),
            b"delivery.bin\n",
        )
        .expect("mark the binary as ignored");
        let candidate = WorkspaceCloseRequest {
            force: true,
            ..request
        };
        let denied = remove_git_workspace(&config, &candidate)
            .expect_err("forced crash replay cannot delete unexpected ignored output");
        assert!(
            matches!(
                denied.code,
                UniversalExecErrorCode::WorkspaceDirty | UniversalExecErrorCode::RevisionMismatch
            ),
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
            decode_closing_workspace_record(
                &fs::read(config.workspace_record_path(&record.workspace_id)).unwrap()
            )
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
        git(
            source,
            &["config", "user.email", "replacement@example.invalid"],
        );
        fs::write(
            source.join("unrelated.txt"),
            b"different Git source content",
        )
        .expect("replacement repository commit payload");
        git(source, &["add", "unrelated.txt"]);
        git(source, &["commit", "-qm", "unrelated replacement"]);
        assert_ne!(git(source, &["rev-parse", "HEAD"]), record.source_revision);
        let denied = remove_git_workspace(&config, &request)
            .expect_err("a new Git repository at the old path is not the original source");
        assert_eq!(denied.code, UniversalExecErrorCode::RevisionMismatch);
        assert!(
            decode_closing_workspace_record(
                &fs::read(config.workspace_record_path(&record.workspace_id)).unwrap()
            )
            .unwrap()
            .is_some(),
            "the durable closing intent must survive a source authority mismatch"
        );
    }

    #[test]
    fn closing_unrelated_workspace_must_not_block_dependent_scan_globally() {
        let (_temp, config, record, _digest) = source_workspace("ws-close-independent-a");
        let peer = create_git_workspace_record(
            &config,
            &GitWorkspaceCreateRequest {
                schema_version: 1,
                workspace_id: "ws-close-independent-b".to_string(),
                source_repo: record.source_repo.clone(),
                source_revision: record.source_revision.clone(),
            },
        )
        .expect("independent second native Git worktree");
        let peer_digest =
            workspace_source_state_digest_at(Path::new(&peer.workspace_path)).unwrap();
        closing_fixture(&config, &peer, &peer_digest);
        assert!(
            workspace_cleanup_dependents(&config, &record.workspace_id)
                .expect("CLOSING of another worktree must not globally block safe close")
                .is_empty(),
            "independent worktree closure is not a Git dependent"
        );
    }

    #[test]
    fn closing_peer_still_blocks_removal_of_its_actual_git_source_parent() {
        let (_temp, config, parent, _digest) = source_workspace("ws-close-dependent-parent");
        // A real independent source repository lives INSIDE this parent
        // worktree. Removing parent would destroy the peer Git authority.
        let nested_source = Path::new(&parent.workspace_path).join("nested-source-repository");
        fs::create_dir_all(&nested_source).unwrap();
        git(&nested_source, &["init", "-q"]);
        git(&nested_source, &["config", "user.name", "Dependent Peer"]);
        git(
            &nested_source,
            &["config", "user.email", "dependent@example.invalid"],
        );
        fs::write(
            nested_source.join("source.txt"),
            b"peer owns a nested Git repository",
        )
        .unwrap();
        git(&nested_source, &["add", "source.txt"]);
        git(&nested_source, &["commit", "-qm", "peer original source"]);
        let peer = create_git_workspace_record(
            &config,
            &GitWorkspaceCreateRequest {
                schema_version: 1,
                workspace_id: "ws-close-dependent-peer".to_string(),
                source_repo: nested_source.to_string_lossy().into_owned(),
                source_revision: git(&nested_source, &["rev-parse", "HEAD"]),
            },
        )
        .expect("native peer Git worktree within same Runtime store");
        let before = workspace_cleanup_dependents(&config, &parent.workspace_id).unwrap();
        assert!(before.contains(&peer.workspace_id));
        let peer_digest =
            workspace_source_state_digest_at(Path::new(&peer.workspace_path)).unwrap();
        closing_fixture(&config, &peer, &peer_digest);
        let after = workspace_cleanup_dependents(&config, &parent.workspace_id)
            .expect("CLOSING peer must still count as a real source dependency");
        assert_eq!(after, before);
        assert!(after.contains(&peer.workspace_id));
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
        let closed = remove_git_workspace(&config, &request).expect("normal native worktree close");
        assert!(closed.removed);
        assert_eq!(
            closed.closure_disposition,
            WorkspaceClosureDisposition::Removed
        );
        let again = remove_git_workspace(&config, &request)
            .expect("closed exact digest remains recoverable");
        assert_eq!(
            again.closure_disposition,
            WorkspaceClosureDisposition::AlreadyClosed
        );
        assert_eq!(again.source_state_digest.as_deref(), Some(digest.as_str()));
    }
}
