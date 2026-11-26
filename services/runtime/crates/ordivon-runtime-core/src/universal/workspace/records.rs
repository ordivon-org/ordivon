// Write a physical-effect intent into the EXISTING Workspace identity record
// before invoking Git. A crash in between is then recoverable without a second
// Registry, a new executor, or trusting an arbitrary unrecorded directory.
#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct OpeningWorkspaceRecord {
    schema_version: u32,
    state: String,
    source_repo: String,
    source_revision: String,
    requested_revision: String,
    created_unix_ms: u128,
}

fn unfinished_open_error(reason: &str) -> UniversalExecError {
    UniversalExecError::new(
        UniversalExecErrorCode::MetadataCorrupt,
        format!("Workspace opening cannot be reconciled safely: {reason}"),
        Some("workspaceId"),
        false,
    )
}

// The persisted intent is necessary but not sufficient. Git must prove the
// exact detached worktree remains registered in the same source and is clean.
fn managed_physical_target(target: &Path) -> Result<PathBuf, UniversalExecError> {
    let parent = target.parent()
        .ok_or_else(|| unfinished_open_error("managed Workspace parent is missing"))?;
    let name = target.file_name()
        .ok_or_else(|| unfinished_open_error("managed Workspace ID is missing"))?;
    Ok(canonical_directory(parent, "workspaceRoot")?.join(name))
}

// The configured store root may be a symbolic alias, but the final Workspace
// directory itself must be a real directory inside the canonical managed root.
fn verified_interrupted_open(
    source: &Path,
    target: &Path,
    revision: &str,
) -> Result<PathBuf, UniversalExecError> {
    let metadata = fs::symlink_metadata(target)
        .map_err(|_| unfinished_open_error("target directory is not observable"))?;
    if private_git_reparse(&metadata) || !metadata.is_dir() {
        return Err(unfinished_open_error("target is not a regular directory"));
    }
    let actual = canonical_directory(target, "workspacePath")?;
    if actual != managed_physical_target(target)? {
        return Err(unfinished_open_error("target escaped its canonical managed path"));
    }
    let entries = git_output_bytes(source, ["worktree", "list", "--porcelain", "-z"])?;
    let mut registered = false;
    for item in entries.split(|b| *b == 0).collect::<Vec<_>>().split(|entry| entry.is_empty()) {
        let mut location = false;
        let mut head = false;
        let mut detached = false;
        let mut unsafe_registration = false;
        for line in item.iter().copied() {
            if let Some(path) = line.strip_prefix(b"worktree ") {
                location = path == actual.as_os_str().as_encoded_bytes();
            } else if let Some(commit) = line.strip_prefix(b"HEAD ") {
                head = commit == revision.as_bytes();
            } else if line == b"detached" {
                detached = true;
            } else if line.starts_with(b"locked") || line.starts_with(b"prunable") {
                unsafe_registration = true;
            }
        }
        if location {
            registered = head && detached && !unsafe_registration;
            break;
        }
    }
    if !registered {
        return Err(unfinished_open_error("Git does not register the expected detached worktree"));
    }
    let actual_head = git_output(&actual, ["rev-parse", "HEAD"])?;
    let actual_common_dir = git_output(&actual, ["rev-parse", "--path-format=absolute", "--git-common-dir"])?;
    let source_common_dir = git_output(source, ["rev-parse", "--path-format=absolute", "--git-common-dir"])?;
    if actual_head.trim() != revision || actual_common_dir.trim() != source_common_dir.trim() {
        return Err(unfinished_open_error("actual Git HEAD or repository binding differs"));
    }
    if !git_output_bytes(
        &actual,
        ["status", "--porcelain=v1", "--untracked-files=all", "--ignored=matching"],
    )?.is_empty() {
        return Err(unfinished_open_error("worktree contains changes or ignored/untracked files"));
    }
    Ok(actual)
}


fn private_git_reparse(meta: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        // Junctions as well as symlinks are namespace substitutions.
        return meta.file_attributes() & 0x400 != 0;
    }
    #[cfg(not(windows))]
    meta.file_type().is_symlink()
}

/// Each unprivileged Workspace uses its own exact-SourceRevision shallow Git
/// objects/index/refs; the original root-owned linked Worktree stays the
/// physical Runtime source-digest/CAS owner. No alternates or new service.
/// This runs under the existing durable Workspace OPENING identity, before
/// any ordinary Agent can write the Workspace or its separate cache.
#[cfg(any(unix, windows))]
fn create_workspace_private_git_snapshot(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
    source: &Path,
    revision: &str,
    workspace: &Path,
) -> Result<(), UniversalExecError> {
    #[cfg(unix)]
    let (uid, gid) = {
        let (Some(uid), Some(gid)) = (config.workspace_uid, config.workspace_gid) else {
            return Ok(());
        };
        if uid == 0 || gid == 0 {
            return Err(unfinished_open_error("private Git requires a nonroot Workspace identity"));
        }
        (uid, gid)
    };
    // Legacy Windows retains the old linked Worktree behavior. Only the
    // explicit PG presentation root selects this service-owned Git carrier.
    #[cfg(windows)]
    if config.workspace_root.is_none() {
        return Ok(());
    }
    let private = config.workspace_private_git_path(workspace_id);
    let cache = private.parent().ok_or_else(|| unfinished_open_error("private Git parent missing"))?;
    match fs::symlink_metadata(cache) {
        Ok(meta) if meta.is_dir() && !private_git_reparse(&meta) => {}
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            fs::create_dir(cache).map_err(|e| io_error(cache, "create Workspace Git cache", e))?;
        }
        _ => return Err(unfinished_open_error("Workspace Git cache is not a real directory")),
    }
    let run = |label: &str, mut command: Command| -> Result<(), UniversalExecError> {
        let output = command.output().map_err(|e| tool_unavailable("git", e))?;
        if !output.status.success() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                format!("prepare independent Workspace Git {label}: {}", String::from_utf8_lossy(&output.stderr).trim()),
                Some("workspaceId"),
                false,
            ));
        }
        Ok(())
    };
    match fs::symlink_metadata(&private) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            let mut init = workspace_git_command();
            init.args(["init", "--quiet", "--bare"]).arg(&private);
            run("init", init)?;
            let mut fetch = workspace_git_command();
            fetch.arg("--git-dir").arg(&private).args(["fetch", "--no-tags", "--depth=1"])
                .arg(source).arg(revision);
            run("shallow exact revision", fetch)?;
            let mut ref_update = workspace_git_command();
            ref_update.arg("--git-dir").arg(&private)
                .args(["update-ref", "refs/heads/agent-work", revision]);
            run("private ref", ref_update)?;
            let mut head = workspace_git_command();
            head.arg("--git-dir").arg(&private)
                .args(["symbolic-ref", "HEAD", "refs/heads/agent-work"]);
            run("private HEAD", head)?;
            let mut index = workspace_git_command();
            index.arg("--git-dir").arg(&private).arg("--work-tree").arg(workspace)
                .args(["read-tree", "HEAD"]);
            run("private index", index)?;
            if workspace_private_git_has_outputs(&private, revision)? {
                return Err(unfinished_open_error("fresh private Git differs from exact source revision"));
            }
        }
        Ok(meta) if meta.is_dir() && !private_git_reparse(&meta) => {
            // Only a partially completed OPENING can retry. Never fetch
            // after an Agent obtained a normal active Workspace record.
            if workspace_private_git_has_outputs(&private, revision)? {
                return Err(unfinished_open_error("interrupted private Git has unknown output"));
            }
        }
        _ => return Err(unfinished_open_error("private Git is not a real directory")),
    }
    // Only this new cache tree, not the shared source repository, is writable
    // by the ordinary Agent. Existing native ownership traversal is reused.
    #[cfg(unix)]
    transfer_workspace_ownership(&private, uid, gid)?;
    Ok(())
}

#[cfg(not(any(unix, windows)))]
fn create_workspace_private_git_snapshot(
    _config: &UniversalExecutorConfig, _workspace_id: &str, _source: &Path,
    _revision: &str, _workspace: &Path,
) -> Result<(), UniversalExecError> {
    Ok(())
}

pub(crate) fn create_git_workspace_record(
    config: &UniversalExecutorConfig,
    request: &GitWorkspaceCreateRequest,
) -> Result<WorkspaceRecord, UniversalExecError> {
    config.ensure_store()?;
    request.validate_shape()?;
    let target = config.workspace_path(&request.workspace_id);
    let record_path = config.workspace_record_path(&request.workspace_id);
    let source_repo = canonical_directory(Path::new(&request.source_repo), "sourceRepo")?;
    let resuming_opening = record_path.exists();
    let opening = if resuming_opening {
        let content = read_workspace_record_bytes(&record_path)?;
        let value: serde_json::Value = serde_json::from_slice(&content)
            .map_err(|_| unfinished_open_error("existing identity is unreadable"))?;
        if value.get("state").and_then(serde_json::Value::as_str) != Some("opening") {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::WorkspaceExists,
                "workspace already exists",
                Some("workspaceId"),
                false,
            ));
        }
        let existing: OpeningWorkspaceRecord = serde_json::from_value(value)
            .map_err(|_| unfinished_open_error("opening intent is malformed"))?;
        if existing.schema_version != UNIVERSAL_EXEC_SCHEMA_VERSION
            || existing.source_repo != source_repo.to_string_lossy()
            || existing.requested_revision != request.source_revision
        {
            return Err(unfinished_open_error("request does not match the durable opening intent"));
        }
        existing
    } else {
        if target.exists() {
            return Err(unfinished_open_error("directory exists without a durable opening intent"));
        }
        // Resolve the symbolic ref exactly ONCE, at the original intent.
        // Retrying HEAD after source branches move must recover the recorded
        // physical revision, never rebind an accepted effect to a new source.
        let revision = resolve_git_commit(&source_repo, &request.source_revision)?;
        if revision.len() != 40 && revision.len() != 64 {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::RevisionNotFound,
                "source revision did not resolve to a commit",
                Some("sourceRevision"),
                false,
            ));
        }
        let opening = OpeningWorkspaceRecord {
            schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
            state: "opening".to_string(),
            source_repo: source_repo.to_string_lossy().into_owned(),
            source_revision: revision,
            requested_revision: request.source_revision.clone(),
            created_unix_ms: now_unix_ms()?,
        };
        write_json_atomic(&record_path, &opening)?;
        opening
    };
    let revision = opening.source_revision.clone();
    let canonical_target = if target.exists() {
        if !resuming_opening {
            return Err(unfinished_open_error("unrecorded physical worktree appeared during opening"));
        }
        verified_interrupted_open(&source_repo, &target, &revision)?
    } else {
        // A missing physical directory is safe to create only when Git also
        // has no still-registered, possibly interrupted worktree at that path.
        if resuming_opening {
            let inventory = git_output_bytes(&source_repo, ["worktree", "list", "--porcelain", "-z"])?;
            let physical_target = managed_physical_target(&target)?;
            if inventory.split(|b| *b == 0).any(|line| {
                line.strip_prefix(b"worktree ") == Some(physical_target.as_os_str().as_encoded_bytes())
            }) {
                return Err(unfinished_open_error("Git still registers an absent worktree"));
            }
        }
        let output = workspace_git_command()
            .arg("-C")
            .arg(&source_repo)
            .args(["worktree", "add", "--detach"])
            .arg(&target)
            .arg(&revision)
            .output()
            .map_err(|error| tool_unavailable("git worktree add", error))?;
        if !output.status.success() {
            return Err(tool_failed("git worktree add", &output.stderr));
        }
        // Git itself completed a fresh native add. Keep the normal hot path
        // to the established HEAD check; expensive porcelain/status checks
        // are reserved for a resumed UNKNOWN physical effect.
        let created = canonical_directory(&target, "workspacePath")?;
        if created != managed_physical_target(&target)? {
            return Err(unfinished_open_error("new worktree escaped managed workspace root"));
        }
        if git_output(&created, ["rev-parse", "HEAD"])?.trim() != revision {
            return Err(unfinished_open_error("created worktree HEAD differs from intent"));
        }
        created
    };
    if let (Some(uid), Some(gid)) = (config.workspace_uid, config.workspace_gid) {
        transfer_workspace_ownership(&canonical_target, uid, gid)?;
    }
    create_workspace_private_git_snapshot(
        config, &request.workspace_id, &source_repo, &revision, &canonical_target,
    )?;
    let record = WorkspaceRecord {
        schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
        workspace_id: request.workspace_id.clone(),
        source_repo: opening.source_repo,
        source_revision: opening.source_revision,
        workspace_path: canonical_target.to_string_lossy().into_owned(),
        created_unix_ms: opening.created_unix_ms,
    };
    write_json_atomic(&record_path, &record)?;
    Ok(record)
}

pub(crate) fn load_workspace_record(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<WorkspaceRecord, UniversalExecError> {
    let mut record = load_workspace_record_metadata(config, workspace_id)?;
    let expected = canonical_directory(&config.workspace_path(workspace_id), "workspacePath")?;
    record.workspace_path = expected.to_string_lossy().into_owned();
    Ok(record)
}

fn load_workspace_record_metadata(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<WorkspaceRecord, UniversalExecError> {
    super::validate_id(workspace_id, "workspaceId")?;
    let path = config.workspace_record_path(workspace_id);
    // Keep the healthy list/get path to one record read: consult the physical
    // Workspace directory only after a missing identity record, not on every
    // item in a potentially large Workspace inventory.
    let bytes = read_workspace_record_bytes(&path).map_err(|error| {
        if error.code == UniversalExecErrorCode::WorkspaceNotFound
            && !path.exists()
            && config.workspace_path(workspace_id).exists()
        {
            return UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "workspace directory exists without an identity record",
                Some("workspaceId"),
                false,
            );
        }
        error
    })?;
    if let Some(closed) = decode_closed_workspace_record(&bytes)? {
        validate_closed_identity(&closed, workspace_id)?;
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceNotFound,
            "workspace is closed",
            Some("workspaceId"),
            false,
        ));
    }
    let record = decode_open_workspace_record(&bytes, workspace_id)?;
    bind_workspace_record_path(config, workspace_id, record)
}

fn bind_workspace_record_path(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
    mut record: WorkspaceRecord,
) -> Result<WorkspaceRecord, UniversalExecError> {
    let legacy_path = record.workspace_path.clone();
    if !legacy_path.is_empty()
        && !workspace_record_path_matches_identity(config, workspace_id, &legacy_path)
    {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            "workspace record path does not match its identity",
            Some("workspacePath"),
            false,
        ));
    }
    let expected = config.workspace_path(workspace_id);
    let derived = if expected.exists() {
        canonical_directory(&expected, "workspacePath")?
    } else {
        expected
    };
    record.workspace_path = derived.to_string_lossy().into_owned();
    Ok(record)
}

fn workspace_record_path_matches_identity(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
    recorded_path: &str,
) -> bool {
    let expected = config.workspace_path(workspace_id);
    let recorded = Path::new(recorded_path);
    if recorded == expected {
        return true;
    }
    if let (Ok(expected), Ok(recorded)) = (
        canonical_directory(&expected, "workspacePath"),
        canonical_directory(recorded, "workspacePath"),
    ) {
        return expected == recorded;
    }
    if expected.exists() || recorded.exists() {
        return false;
    }
    if recorded.file_name() != expected.file_name() {
        return false;
    }
    let (Some(expected_parent), Some(recorded_parent)) = (expected.parent(), recorded.parent())
    else {
        return false;
    };
    match (
        canonical_directory(expected_parent, "workspaceRoot"),
        canonical_directory(recorded_parent, "workspaceRoot"),
    ) {
        (Ok(expected_parent), Ok(recorded_parent)) => expected_parent == recorded_parent,
        _ => false,
    }
}

fn read_workspace_record_bytes(path: &Path) -> Result<Vec<u8>, UniversalExecError> {
    fs::read(path).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceNotFound,
            format!("cannot read workspace record: {error}"),
            Some("workspaceId"),
            false,
        )
    })
}

fn decode_closed_workspace_record(
    bytes: &[u8],
) -> Result<Option<ClosedWorkspaceRecord>, UniversalExecError> {
    let value: serde_json::Value = serde_json::from_slice(bytes).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            format!("invalid workspace record: {error}"),
            Some("workspaceId"),
            false,
        )
    })?;
    if value.get("state").and_then(serde_json::Value::as_str) != Some("closed") {
        return Ok(None);
    }
    serde_json::from_value(value).map(Some).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            format!("invalid closed workspace record: {error}"),
            Some("workspaceId"),
            false,
        )
    })
}

fn decode_open_workspace_record(
    bytes: &[u8],
    workspace_id: &str,
) -> Result<WorkspaceRecord, UniversalExecError> {
    let mut record: WorkspaceRecord = serde_json::from_slice(bytes).map_err(|error| {
        if serde_json::from_slice::<serde_json::Value>(bytes)
            .ok()
            .and_then(|value| value.get("state").and_then(|state| state.as_str()).map(str::to_owned))
            .as_deref() == Some("opening")
        {
            return unfinished_open_error("durable opening is unfinished; retry exact original workspace.open with the same workspaceId");
        }
        // A crash during native Git removal must not expose the worktree to
        // a new Job/Run while the durable close intent awaits reconciliation.
        if serde_json::from_slice::<serde_json::Value>(bytes)
            .ok()
            .and_then(|value| value.get("state").and_then(|state| state.as_str()).map(str::to_owned))
            .as_deref() == Some("closing")
        {
            return UniversalExecError::new(
                UniversalExecErrorCode::WorkspaceStateMismatch,
                "Workspace close is pending native Git reconciliation",
                Some("workspaceId"),
                true,
            );
        }
        UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            format!("invalid workspace record: {error}"),
            Some("workspaceId"),
            false,
        )
    })?;
    validate_open_identity(&record, workspace_id)?;
    record.workspace_id = workspace_id.to_string();
    Ok(record)
}

fn validate_open_identity(
    record: &WorkspaceRecord,
    workspace_id: &str,
) -> Result<(), UniversalExecError> {
    if record.schema_version != UNIVERSAL_EXEC_SCHEMA_VERSION
        || (!record.workspace_id.is_empty() && record.workspace_id != workspace_id)
    {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            "workspace record identity mismatch",
            Some("workspaceId"),
            false,
        ));
    }
    Ok(())
}

fn validate_closed_identity(
    record: &ClosedWorkspaceRecord,
    workspace_id: &str,
) -> Result<(), UniversalExecError> {
    if record.schema_version != UNIVERSAL_EXEC_SCHEMA_VERSION
        || record.state != "closed"
        || (!record.legacy_workspace_id.is_empty()
            && record.legacy_workspace_id != workspace_id)
    {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            "closed workspace record identity mismatch",
            Some("workspaceId"),
            false,
        ));
    }
    Ok(())
}

#[derive(Debug)]
pub(crate) struct WorkspaceRecordInventoryIssue {
    pub workspace_id: String,
    pub error: UniversalExecError,
}

#[derive(Debug)]
pub(crate) struct WorkspaceRecordInventory {
    pub records: Vec<WorkspaceRecord>,
    pub issues: Vec<WorkspaceRecordInventoryIssue>,
}

pub(crate) fn list_open_workspace_record_inventory(
    config: &UniversalExecutorConfig,
) -> Result<WorkspaceRecordInventory, UniversalExecError> {
    let workspaces_root = config.workspaces_root();
    let mut records = Vec::new();
    let mut issues = Vec::new();
    for entry in
        fs::read_dir(&workspaces_root).map_err(|error| io_error(&workspaces_root, "list", error))?
    {
        let entry =
            entry.map_err(|error| io_error(&workspaces_root, "read directory entry", error))?;
        let workspace_id = entry.file_name().to_string_lossy().into_owned();
        if let Err(error) = super::validate_id(&workspace_id, "workspaceId") {
            issues.push(WorkspaceRecordInventoryIssue {
                workspace_id,
                error,
            });
            continue;
        }
        let file_type = entry
            .file_type()
            .map_err(|error| io_error(&entry.path(), "inspect", error))?;
        if !file_type.is_dir() || file_type.is_symlink() {
            issues.push(WorkspaceRecordInventoryIssue {
                workspace_id,
                error: UniversalExecError::new(
                    UniversalExecErrorCode::MetadataCorrupt,
                    "workspace target must be a non-symlink directory",
                    Some("workspaceId"),
                    false,
                ),
            });
            continue;
        }
        let record = match load_workspace_record_metadata(config, &workspace_id) {
            Ok(record) => record,
            Err(error) => {
                issues.push(WorkspaceRecordInventoryIssue {
                    workspace_id,
                    error,
                });
                continue;
            }
        };
        if !workspace_record_path_matches_identity(config, &workspace_id, &record.workspace_path) {
            issues.push(WorkspaceRecordInventoryIssue {
                workspace_id,
                error: UniversalExecError::new(
                    UniversalExecErrorCode::MetadataCorrupt,
                    "workspace record path does not match its identity",
                    Some("workspaceId"),
                    false,
                ),
            });
            continue;
        }
        records.push(record);
    }
    // A crash after native Git removal may leave only the durable CLOSING
    // record. Scanning workspaces_root alone would make this incomplete close
    // invisible to workspace.list and to its natural lifecycle consumer.
    // This is an observation, NOT permission to replay close or release a Run.
    let records_root = config.workspace_records_root();
    for entry in
        fs::read_dir(&records_root).map_err(|error| io_error(&records_root, "list", error))?
    {
        let entry =
            entry.map_err(|error| io_error(&records_root, "read directory entry", error))?;
        let path = entry.path();
        if path.extension().and_then(|value| value.to_str()) != Some("json") {
            continue;
        }
        let Some(workspace_id) = path.file_stem().and_then(|value| value.to_str()) else {
            continue;
        };
        if let Err(error) = super::validate_id(workspace_id, "workspaceId") {
            issues.push(WorkspaceRecordInventoryIssue {
                workspace_id: workspace_id.to_string(),
                error,
            });
            continue;
        }
        // The physical first pass already reported this identity, including
        // corrupt/closing records. A record-only entry is a separate exception.
        if config.workspace_path(workspace_id).exists() {
            continue;
        }
        let error = match entry.file_type() {
            Ok(file_type) if file_type.is_file() && !file_type.is_symlink() => {
                match read_workspace_record_bytes(&path) {
                    Ok(bytes) => match decode_closed_workspace_record(&bytes) {
                        Ok(Some(closed)) => {
                            // Valid CLOSED tombstones are intentional and must
                            // not be returned as unfinished physical work.
                            validate_closed_identity(&closed, workspace_id).err()
                        }
                        Ok(None) => match decode_closing_workspace_record(&bytes) {
                            Ok(Some(closing)) => {
                                if let Err(error) =
                                    validate_open_identity(&closing.record, workspace_id)
                                {
                                    Some(error)
                                } else if let Err(error) =
                                    bind_workspace_record_path(config, workspace_id, closing.record)
                                {
                                    // Use the SAME legacy/modern source-path binder
                                    // as exact native close reconciliation.
                                    Some(error)
                                } else {
                                    Some(UniversalExecError::new(
                                        UniversalExecErrorCode::WorkspaceStateMismatch,
                                        "record-only CLOSING needs the original close request and native/PG owner reconciliation; do not auto-release or delete",
                                        Some("workspaceId"),
                                        true,
                                    ))
                                }
                            }
                            // Preserve historical OPEN/OPENING inventory semantics;
                            // this repair only makes durable CLOSING visible.
                            // The existing NativeClose protocol remains the sole
                            // authority for recovering other record states.
                            Ok(None) => None,
                            Err(error) => Some(error),
                        },
                        Err(error) => Some(error),
                    },
                    Err(error) => Some(error),
                }
            }
            Ok(_) => Some(UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "record-only Workspace identity is not a regular non-symlink JSON file",
                Some("workspaceId"),
                false,
            )),
            Err(error) => Some(io_error(&path, "inspect record-only Workspace", error)),
        };
        if let Some(error) = error {
            issues.push(WorkspaceRecordInventoryIssue {
                workspace_id: workspace_id.to_string(),
                error,
            });
        }
    }

    records.sort_by(|left, right| {
        right
            .created_unix_ms
            .cmp(&left.created_unix_ms)
            .then_with(|| left.workspace_id.cmp(&right.workspace_id))
    });
    issues.sort_by(|left, right| left.workspace_id.cmp(&right.workspace_id));
    Ok(WorkspaceRecordInventory { records, issues })
}

pub(crate) fn workspace_cleanup_dependents(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<Vec<String>, UniversalExecError> {
    super::validate_id(workspace_id, "workspaceId")?;
    config.ensure_store()?;
    let destructive_roots = [
        config.workspace_path(workspace_id),
        config.workspace_cache_path(workspace_id),
        config.workspace_private_git_path(workspace_id),
        config.workspace_build_cache_path(workspace_id),
        config.workspace_tmp_path(workspace_id),
    ]
    .into_iter()
    .filter(|root| root.exists())
    .map(|root| canonical_directory(&root, "workspaceCleanupRoot"))
    .collect::<Result<Vec<_>, _>>()?;
    let records_root = config.workspace_records_root();
    let mut dependents = Vec::new();
    for entry in
        fs::read_dir(&records_root).map_err(|error| io_error(&records_root, "list", error))?
    {
        let entry =
            entry.map_err(|error| io_error(&records_root, "read directory entry", error))?;
        let path = entry.path();
        if path.extension().and_then(|value| value.to_str()) != Some("json") {
            continue;
        }
        let Some(candidate_id) = path.file_stem().and_then(|value| value.to_str()) else {
            continue;
        };
        if candidate_id == workspace_id {
            continue;
        }
        let record = match load_workspace_record_metadata(config, candidate_id) {
            Ok(record) => record,
            Err(error) if error.code == UniversalExecErrorCode::WorkspaceNotFound => continue,
            Err(error) if error.code == UniversalExecErrorCode::WorkspaceStateMismatch => {
                // A peer with a durable CLOSING intent is not an OPEN worktree,
                // but it can still own a dependency of the directory being
                // removed. Inspect its ORIGINAL source identity instead of
                // globally blocking every unrelated Workspace close.
                let bytes = read_workspace_record_bytes(&path)?;
                let Some(closing) = decode_closing_workspace_record(&bytes)? else {
                    return Err(error);
                };
                validate_open_identity(&closing.record, candidate_id)?;
                let mut original =
                    bind_workspace_record_path(config, candidate_id, closing.record)?;
                original.workspace_id = candidate_id.to_string();
                original
            }
            Err(error) => return Err(error),
        };
        let workspace_path = Path::new(&record.workspace_path);
        let authority = workspace_git_common_dir_at(workspace_path)
            .unwrap_or_else(|_| PathBuf::from(&record.source_repo));
        if destructive_roots
            .iter()
            .any(|root| authority.starts_with(root))
        {
            dependents.push(record.workspace_id);
        }
    }
    dependents.sort();
    dependents.dedup();
    Ok(dependents)
}

#[cfg(all(test, windows))]
mod windows_pg_private_git_tests {
    use super::*;
    fn git(cwd: &Path, args: &[&str]) -> String {
        let output=workspace_git_command().arg("-C").arg(cwd).args(args).output().unwrap();
        assert!(output.status.success(), "{}", String::from_utf8_lossy(&output.stderr));
        String::from_utf8(output.stdout).unwrap().trim().to_string()
    }
    #[test]
    fn windows_pg_private_git_snapshot_holds_unreceived_candidate_and_cleans_exact_leaf() {
        let temp=tempfile::tempdir().unwrap();
        let src=temp.path().join("source");
        let presentation=temp.path().join("presentation");
        fs::create_dir(&src).unwrap();
        fs::create_dir(&presentation).unwrap();
        git(&src,&["init","-q"]);
        git(&src,&["config","user.name","Workspace witness"]);
        git(&src,&["config","user.email","workspace@example.invalid"]);
        fs::write(src.join("marker"),"source").unwrap();
        git(&src,&["add","marker"]);
        git(&src,&["commit","-qm","source"]);
        let rev=git(&src,&["rev-parse","HEAD"]);
        let config=UniversalExecutorConfig {
            store_root:temp.path().join("private-store"),
            workspace_root:Some(presentation.clone()),workspace_uid:None,workspace_gid:None,
            runner_path:None,allowed_executable_roots:vec![temp.path().to_path_buf()],
            max_runtime_ms:60000,max_output_bytes:1048576,
        };
        fs::create_dir(&config.store_root).unwrap();
        let id="winpg-private-git";
        let target=config.workspace_path(id);
        let output=workspace_git_command().arg("-C").arg(&src).args(["worktree","add","--detach"]).arg(&target).arg(&rev).output().unwrap();
        assert!(output.status.success(), "{}",String::from_utf8_lossy(&output.stderr));
        create_workspace_private_git_snapshot(&config,id,&src,&rev,&target).unwrap();
        let private=config.workspace_private_git_path(id);
        assert_eq!(private,presentation.join(".winpg-private-git.agent-git"));
        assert!(!private.join("objects/info/alternates").exists());
        assert!(!workspace_private_git_has_outputs(&private,&rev).unwrap());
        // A private-only empty commit is undelivered even though worktree bytes
        // are clean and the original source is still at the opening revision.
        let output=workspace_git_command().arg("--git-dir").arg(&private).arg("--work-tree").arg(&target)
            .args(["-c","user.name=Workspace witness","-c","user.email=workspace@example.invalid","commit","--allow-empty","-qm","private-only"]).output().unwrap();
        assert!(output.status.success(), "{}",String::from_utf8_lossy(&output.stderr));
        assert!(workspace_private_git_has_outputs(&private,&rev).unwrap());
        assert_eq!(git(&src,&["rev-parse","HEAD"]),rev);
        assert_eq!(git(&target,&["rev-parse","HEAD"]),rev);
        let candidate=workspace_git_command().arg("--git-dir").arg(&private).args(["rev-parse","HEAD"]).output().unwrap();
        assert!(candidate.status.success());
        assert_ne!(String::from_utf8(candidate.stdout).unwrap().trim(),rev);
        // Returning to the admitted base permits cleanup; do not mutate shared Git.
        let output=workspace_git_command().arg("--git-dir").arg(&private).args(["update-ref","refs/heads/agent-work",&rev]).output().unwrap();
        assert!(output.status.success());
        assert!(!workspace_private_git_has_outputs(&private,&rev).unwrap());
        // Isolated sibling must remain untouched by private leaf cleanup.
        let sibling=presentation.join("foreign");
        fs::create_dir(&sibling).unwrap();
        fs::write(sibling.join("marker"),"foreign").unwrap();
        cleanup_workspace_caches(&config,id).unwrap();
        assert!(!private.exists());
        assert_eq!(fs::read_to_string(sibling.join("marker")).unwrap(),"foreign");
        assert!(target.exists());
        assert_eq!(git(&src,&["rev-parse","HEAD"]),rev);
    }
}
