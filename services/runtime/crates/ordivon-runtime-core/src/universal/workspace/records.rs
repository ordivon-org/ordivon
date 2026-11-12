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
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
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
        let output = Command::new("git")
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
