pub(crate) fn workspace_head_and_dirty_at(
    workspace: &Path,
) -> Result<(String, bool), UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let output = Command::new("git")
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(&workspace)
        .args([
            "status",
            "--porcelain=v2",
            "--branch",
            "-z",
            "--untracked-files=normal",
            "--ignore-submodules=none",
        ])
        .output()
        .map_err(|error| tool_unavailable("git status", error))?;
    if !output.status.success() {
        return Err(tool_failed("git status", &output.stderr));
    }
    let mut head_revision = None;
    let mut dirty = false;
    for raw in output
        .stdout
        .split(|byte| *byte == 0)
        .filter(|raw| !raw.is_empty())
    {
        if let Some(value) = raw.strip_prefix(b"# branch.oid ") {
            let value = String::from_utf8(value.to_vec()).map_err(|error| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ArtifactNotUtf8,
                    format!("Git branch OID is not UTF-8: {error}"),
                    None,
                    false,
                )
            })?;
            head_revision = Some(value);
        } else if !raw.starts_with(b"# ") {
            dirty = true;
        }
    }
    let head_revision = head_revision.ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::RevisionNotFound,
            "git status omitted branch.oid",
            Some("workspaceId"),
            false,
        )
    })?;
    if head_revision.len() != 40 && head_revision.len() != 64 {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionNotFound,
            "workspace HEAD did not resolve to a commit",
            Some("workspaceId"),
            false,
        ));
    }
    Ok((head_revision, dirty))
}

#[cfg(any(feature = "transactional-runtime", test))]
pub fn workspace_head_revision(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<String, UniversalExecError> {
    let record = load_workspace_record(config, workspace_id)?;
    workspace_head_revision_at(Path::new(&record.workspace_path))
}

pub(crate) fn workspace_head_revision_at(workspace: &Path) -> Result<String, UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let revision = git_output(&workspace, ["rev-parse", "HEAD"])?
        .trim()
        .to_string();
    if revision.len() != 40 && revision.len() != 64 {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionNotFound,
            "workspace HEAD did not resolve to a commit",
            Some("workspaceId"),
            false,
        ));
    }
    Ok(revision)
}

pub fn workspace_source_state_digest(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<String, UniversalExecError> {
    let record = load_workspace_record(config, workspace_id)?;
    workspace_source_state_digest_at(Path::new(&record.workspace_path))
}

pub(crate) fn workspace_git_common_dir_at(workspace: &Path) -> Result<PathBuf, UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let common_dir = git_output(
        &workspace,
        ["rev-parse", "--path-format=absolute", "--git-common-dir"],
    )?;
    canonical_directory(Path::new(common_dir.trim()), "workspaceGitCommonDir")
}

pub(crate) fn workspace_source_state_digest_at(
    workspace: &Path,
) -> Result<String, UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let head_revision = workspace_head_revision_at(&workspace)?;
    let staged_index = git_output_bytes(&workspace, ["ls-files", "--stage", "-z"])?;
    let index_flags = git_output_bytes(&workspace, ["ls-files", "-v", "-z"])?;
    let index_digest = sha256_bytes(
        format!(
            "workspace-index-v1\0{}\0{}",
            sha256_bytes(&staged_index),
            sha256_bytes(&index_flags)
        )
        .as_bytes(),
    );
    let tracked_paths = parse_tracked_index_paths(&staged_index)?;
    let mut tracked = Vec::with_capacity(tracked_paths.len());
    for (relative, index_mode) in tracked_paths {
        tracked.push(workspace_source_entry(
            &workspace,
            &relative,
            Some(&index_mode),
        )?);
    }

    let untracked_raw = git_output_bytes(
        &workspace,
        ["ls-files", "--others", "--exclude-standard", "-z"],
    )?;
    let mut untracked_paths = parse_nul_paths(&untracked_raw, "untracked Git path")?;
    untracked_paths.sort();
    let mut untracked = Vec::with_capacity(untracked_paths.len());
    for relative in untracked_paths {
        untracked.push(workspace_source_entry(&workspace, &relative, None)?);
    }

    let state = WorkspaceSourceState {
        schema_version: 2,
        head_revision,
        index_digest,
        tracked,
        untracked,
    };
    let bytes = serde_json::to_vec(&state).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::MetadataCorrupt,
            format!("cannot serialize Workspace source state: {error}"),
            None,
            false,
        )
    })?;
    Ok(sha256_bytes(&bytes))
}

fn parse_tracked_index_paths(
    staged_index: &[u8],
) -> Result<BTreeMap<String, String>, UniversalExecError> {
    let mut paths = BTreeMap::new();
    for raw in staged_index
        .split(|byte| *byte == 0)
        .filter(|raw| !raw.is_empty())
    {
        let record = String::from_utf8(raw.to_vec()).map_err(|error| {
            UniversalExecError::new(
                UniversalExecErrorCode::ArtifactNotUtf8,
                format!("tracked Git index record is not UTF-8: {error}"),
                None,
                false,
            )
        })?;
        let (metadata, relative) = record.split_once('\t').ok_or_else(|| {
            UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "tracked Git index record has no path separator",
                None,
                false,
            )
        })?;
        let index_mode = metadata.split_whitespace().next().ok_or_else(|| {
            UniversalExecError::new(
                UniversalExecErrorCode::MetadataCorrupt,
                "tracked Git index record has no mode",
                None,
                false,
            )
        })?;
        validate_relative_path(relative, "trackedPath")?;
        paths.insert(relative.to_string(), index_mode.to_string());
    }
    Ok(paths)
}

fn parse_nul_paths(bytes: &[u8], label: &str) -> Result<Vec<String>, UniversalExecError> {
    bytes
        .split(|byte| *byte == 0)
        .filter(|raw| !raw.is_empty())
        .map(|raw| {
            String::from_utf8(raw.to_vec()).map_err(|error| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ArtifactNotUtf8,
                    format!("{label} is not UTF-8: {error}"),
                    None,
                    false,
                )
            })
        })
        .collect()
}

#[cfg(unix)]
fn workspace_source_entry(
    workspace: &Path,
    relative: &str,
    index_mode: Option<&str>,
) -> Result<WorkspaceSourceEntry, UniversalExecError> {
    let relative_path = validate_relative_path(relative, "sourcePath")?;
    let path = workspace.join(&relative_path);
    let before = match fs::symlink_metadata(&path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            return Ok(WorkspaceSourceEntry {
                path: relative.to_string(),
                kind: if index_mode == Some("160000") {
                    "gitlink-uninitialized".to_string()
                } else {
                    "missing".to_string()
                },
                mode: 0,
                byte_length: 0,
                digest: sha256_bytes(b"missing"),
            });
        }
        Err(error) => return Err(io_error(&path, "inspect source state", error)),
    };
    let mode = before.permissions().mode() & 0o7777;
    let (kind, byte_length, digest) = if before.file_type().is_symlink() {
        let target =
            fs::read_link(&path).map_err(|error| io_error(&path, "read source symlink", error))?;
        let bytes = target.as_os_str().as_bytes();
        (
            "symlink".to_string(),
            bytes.len() as u64,
            sha256_bytes(bytes),
        )
    } else if before.is_file() {
        ("file".to_string(), before.len(), sha256_file(&path)?)
    } else if before.is_dir() && index_mode == Some("160000") {
        if is_git_worktree(&path)? {
            (
                "git-worktree".to_string(),
                0,
                workspace_source_state_digest_at(&path)?,
            )
        } else {
            (
                "gitlink-uninitialized".to_string(),
                0,
                sha256_bytes(b"gitlink-uninitialized"),
            )
        }
    } else {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspacePathDenied,
            format!("source path is not a regular file, symlink, or Git worktree: {relative}"),
            Some("workspaceId"),
            false,
        ));
    };
    let after = fs::symlink_metadata(&path)
        .map_err(|error| io_error(&path, "reinspect source state", error))?;
    if !same_source_metadata(&before, &after) {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceMutationIncomplete,
            format!("source path changed while its commitment was computed: {relative}"),
            Some("workspaceId"),
            true,
        ));
    }
    Ok(WorkspaceSourceEntry {
        path: relative.to_string(),
        kind,
        mode,
        byte_length,
        digest,
    })
}

#[cfg(not(unix))]
fn workspace_source_entry(
    _workspace: &Path,
    _relative: &str,
    _index_mode: Option<&str>,
) -> Result<WorkspaceSourceEntry, UniversalExecError> {
    Err(UniversalExecError::new(
        UniversalExecErrorCode::ToolUnavailable,
        "native workspace source-state identity is not implemented for this platform",
        Some("workspaceId"),
        false,
    ))
}

#[cfg(unix)]
fn is_git_worktree(path: &Path) -> Result<bool, UniversalExecError> {
    let output = Command::new("git")
        .arg("-C")
        .arg(path)
        .args(["rev-parse", "--is-inside-work-tree"])
        .output()
        .map_err(|error| tool_unavailable("git rev-parse worktree", error))?;
    Ok(output.status.success() && output.stdout == b"true\n")
}

#[cfg(unix)]
fn same_source_metadata(left: &fs::Metadata, right: &fs::Metadata) -> bool {
    left.dev() == right.dev()
        && left.ino() == right.ino()
        && left.mode() == right.mode()
        && left.size() == right.size()
        && left.mtime() == right.mtime()
        && left.mtime_nsec() == right.mtime_nsec()
        && left.ctime() == right.ctime()
        && left.ctime_nsec() == right.ctime_nsec()
}
