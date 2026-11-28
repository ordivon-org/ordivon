pub(crate) fn workspace_diff(
    config: &UniversalExecutorConfig,
    request: &WorkspaceDiffRequest,
) -> Result<WorkspaceDiffResult, UniversalExecError> {
    request.validate_shape()?;
    let record = load_workspace_record(config, &request.workspace_id)?;
    let workspace = Path::new(&record.workspace_path);
    let mut command = workspace_git_command();
    command
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(workspace)
        .args(["diff", "HEAD", "--no-ext-diff", "--no-color", "--binary"]);
    let (bytes, truncated) =
        bounded_command_stdout(&mut command, request.max_bytes, &[0], "git diff")?;
    let (diff, bytes) = bounded_utf8(bytes, truncated, "git diff output")?;
    let changes = workspace_change_projection_at(workspace)?;
    Ok(WorkspaceDiffResult {
        workspace_id: request.workspace_id.clone(),
        diff,
        digest: sha256_bytes(&bytes),
        byte_length: bytes.len() as u64,
        truncated,
        changed_paths: changes.changed,
        modified_paths: changes.modified,
        added_paths: changes.added,
        deleted_paths: changes.deleted,
        renamed_paths: changes.renamed,
        untracked_paths: changes.untracked,
    })
}

fn workspace_changed_paths(
    workspace: &Path,
) -> Result<WorkspaceChangeProjection, UniversalExecError> {
    let output = workspace_git_command()
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(workspace)
        .args([
            "diff",
            "HEAD",
            "--name-status",
            "-z",
            "--find-renames",
            "--find-copies",
        ])
        .output()
        .map_err(|error| tool_unavailable("git diff --name-status", error))?;
    if !output.status.success() {
        return Err(tool_failed("git diff --name-status", &output.stderr));
    }
    let fields: Vec<&[u8]> = output
        .stdout
        .split(|byte| *byte == 0)
        .filter(|field| !field.is_empty())
        .collect();
    let mut changed = BTreeSet::new();
    let mut modified = BTreeSet::new();
    let mut added = BTreeSet::new();
    let mut deleted = BTreeSet::new();
    let mut renamed = Vec::new();
    let mut index = 0usize;
    while index < fields.len() {
        let status = std::str::from_utf8(fields[index]).map_err(|error| {
            UniversalExecError::new(
                UniversalExecErrorCode::ArtifactNotUtf8,
                format!("git diff status is not UTF-8: {error}"),
                None,
                false,
            )
        })?;
        index += 1;
        let code = status.as_bytes().first().copied().ok_or_else(|| {
            UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                "git diff emitted an empty path status",
                None,
                false,
            )
        })?;
        let path = |raw: &[u8]| -> Result<String, UniversalExecError> {
            String::from_utf8(raw.to_vec()).map_err(|error| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ArtifactNotUtf8,
                    format!("changed Git path is not UTF-8: {error}"),
                    None,
                    false,
                )
            })
        };
        match code {
            b'R' | b'C' => {
                if index + 1 >= fields.len() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::ToolFailed,
                        "git diff rename/copy record is incomplete",
                        None,
                        false,
                    ));
                }
                let from_path = path(fields[index])?;
                let to_path = path(fields[index + 1])?;
                index += 2;
                if code == b'R' {
                    changed.insert(from_path.clone());
                    changed.insert(to_path.clone());
                    renamed.push(WorkspaceRenamedPath { from_path, to_path });
                } else {
                    changed.insert(to_path.clone());
                    added.insert(to_path);
                }
            }
            b'M' | b'T' | b'U' => {
                if index >= fields.len() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::ToolFailed,
                        "git diff path record is incomplete",
                        None,
                        false,
                    ));
                }
                let value = path(fields[index])?;
                index += 1;
                changed.insert(value.clone());
                modified.insert(value);
            }
            b'A' => {
                if index >= fields.len() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::ToolFailed,
                        "git diff added-path record is incomplete",
                        None,
                        false,
                    ));
                }
                let value = path(fields[index])?;
                index += 1;
                changed.insert(value.clone());
                added.insert(value);
            }
            b'D' => {
                if index >= fields.len() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::ToolFailed,
                        "git diff deleted-path record is incomplete",
                        None,
                        false,
                    ));
                }
                let value = path(fields[index])?;
                index += 1;
                changed.insert(value.clone());
                deleted.insert(value);
            }
            _ => {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::ToolFailed,
                    format!("unsupported git diff path status: {status}"),
                    None,
                    false,
                ));
            }
        }
    }
    Ok(WorkspaceChangeProjection {
        changed: changed.into_iter().collect(),
        modified: modified.into_iter().collect(),
        added: added.into_iter().collect(),
        deleted: deleted.into_iter().collect(),
        renamed,
        untracked: Vec::new(),
    })
}

pub(crate) fn workspace_change_projection_at(
    workspace: &Path,
) -> Result<WorkspaceChangeProjection, UniversalExecError> {
    let workspace = canonical_directory(workspace, "workspacePath")?;
    let mut changes = workspace_changed_paths(&workspace)?;
    let output = workspace_git_command()
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(&workspace)
        .args(["ls-files", "--others", "--exclude-standard", "-z"])
        .output()
        .map_err(|error| tool_unavailable("git ls-files", error))?;
    if !output.status.success() {
        return Err(tool_failed("git ls-files", &output.stderr));
    }
    for raw in output.stdout.split(|byte| *byte == 0) {
        if raw.is_empty() {
            continue;
        }
        changes
            .untracked
            .push(String::from_utf8(raw.to_vec()).map_err(|error| {
                UniversalExecError::new(
                    UniversalExecErrorCode::ArtifactNotUtf8,
                    format!("untracked Git path is not UTF-8: {error}"),
                    None,
                    false,
                )
            })?);
    }
    Ok(changes)
}
// Existing workspace.rs include is a real Rust source consumer, not a test guard.
#[path = "changes/page.rs"]
mod change_page;
#[path = "changes/parse.rs"]
mod change_parse;
#[path = "changes/scan.rs"]
mod change_scan;
pub fn workspace_changes_page(
    config: &UniversalExecutorConfig,
    request: &WorkspaceChangePageRequest,
) -> Result<WorkspaceChangePageResult, UniversalExecError> {
    request.validate_shape()?;
    let record = load_workspace_record(config, &request.workspace_id)?;
    let workspace = Path::new(&record.workspace_path);
    let mut collector = change_page::ChangePageCollector::new(request)?;
    change_scan::scan_tracked_changes(workspace, |entry| collector.observe(entry))?;
    change_scan::scan_untracked_changes(workspace, |entry| collector.observe(entry))?;
    let selection = collector.finish(request.cursor.as_ref())?;

    // A page is one structured change-set observation even though tracked and
    // untracked facts come from separate Git processes. Re-scan only path/kind
    // facts after selection so a concurrent Workspace transition cannot silently
    // splice two realities into one page. This intentionally does not hash file
    // contents; byte-only changes that preserve the same change membership/kind
    // remain valid for this projection.
    let mut verification = change_page::ChangeSetAccumulator::default();
    change_scan::scan_tracked_changes(workspace, |entry| verification.observe_entry(&entry).map(drop))?;
    change_scan::scan_untracked_changes(workspace, |entry| verification.observe_entry(&entry).map(drop))?;
    let verification_digest = verification.digest();
    if verification_digest != selection.change_set_digest {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceMutationIncomplete,
            "workspace change set changed while projecting the page",
            Some("workspaceId"),
            true,
        ));
    }

    Ok(WorkspaceChangePageResult {
        workspace_id: request.workspace_id.clone(),
        change_set_digest: selection.change_set_digest,
        entries: selection.entries,
        entry_bytes: selection.entry_bytes,
        total_entries: selection.total_entries,
        remaining_entries: selection.remaining_entries,
        complete: selection.complete,
        next_cursor: selection.next_cursor,
    })
}
