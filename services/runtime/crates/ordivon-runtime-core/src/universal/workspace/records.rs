pub(crate) fn create_git_workspace_record(
    config: &UniversalExecutorConfig,
    request: &GitWorkspaceCreateRequest,
) -> Result<WorkspaceRecord, UniversalExecError> {
    config.ensure_store()?;
    request.validate_shape()?;
    let target = config.workspace_path(&request.workspace_id);
    let record_path = config.workspace_record_path(&request.workspace_id);
    if target.exists() || record_path.exists() {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceExists,
            "workspace already exists",
            Some("workspaceId"),
            false,
        ));
    }
    let source_repo = canonical_directory(Path::new(&request.source_repo), "sourceRepo")?;
    let revision = resolve_git_commit(&source_repo, &request.source_revision)?;
    if revision.len() != 40 && revision.len() != 64 {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionNotFound,
            "source revision did not resolve to a commit",
            Some("sourceRevision"),
            false,
        ));
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
    let canonical_target = canonical_directory(&target, "workspacePath")?;
    let actual_revision = git_output(&canonical_target, ["rev-parse", "HEAD"])?;
    if actual_revision.trim() != revision {
        let _ = remove_git_worktree(&source_repo, &canonical_target, true);
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionMismatch,
            "created workspace HEAD does not match requested revision",
            Some("sourceRevision"),
            false,
        ));
    }
    if let (Some(uid), Some(gid)) = (config.workspace_uid, config.workspace_gid) {
        if let Err(error) = transfer_workspace_ownership(&canonical_target, uid, gid) {
            let _ = remove_git_worktree(&source_repo, &canonical_target, true);
            return Err(error);
        }
    }
    let record = WorkspaceRecord {
        schema_version: UNIVERSAL_EXEC_SCHEMA_VERSION,
        workspace_id: request.workspace_id.clone(),
        source_repo: source_repo.to_string_lossy().into_owned(),
        source_revision: revision,
        workspace_path: canonical_target.to_string_lossy().into_owned(),
        created_unix_ms: now_unix_ms()?,
    };
    if let Err(error) = write_json_atomic(&record_path, &record) {
        let _ = remove_git_worktree(&source_repo, &canonical_target, true);
        return Err(error);
    }
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
    let bytes = read_workspace_record_bytes(&path)?;
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
