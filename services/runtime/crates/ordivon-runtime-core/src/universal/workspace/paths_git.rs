pub(crate) fn resolve_existing_workspace_path(
    record: &WorkspaceRecord,
    relative: &str,
    allow_directory: bool,
) -> Result<PathBuf, UniversalExecError> {
    let relative = validate_relative_path(relative, "relativePath")?;
    let root = canonical_directory(Path::new(&record.workspace_path), "workspacePath")?;
    let candidate = root.join(&relative);
    let metadata = fs::symlink_metadata(&candidate).map_err(|error| {
        if error.kind() == std::io::ErrorKind::NotFound {
            UniversalExecError::new(
                UniversalExecErrorCode::WorkspacePathNotFound,
                format!("workspace path does not exist: {}", relative.display()),
                Some("relativePath"),
                false,
            )
        } else {
            io_error(&candidate, "inspect", error)
        }
    })?;
    if metadata.file_type().is_symlink() {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspacePathDenied,
            "workspace path cannot be a symlink",
            Some("relativePath"),
            false,
        ));
    }
    let canonical = fs::canonicalize(&candidate)
        .map_err(|error| io_error(&candidate, "canonicalize", error))?;
    if !canonical.starts_with(&root) || (!allow_directory && canonical.is_dir()) {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspacePathDenied,
            "workspace path escaped its root",
            Some("relativePath"),
            false,
        ));
    }
    Ok(canonical)
}

#[cfg(feature = "transactional-runtime")]
pub(crate) fn resolve_workspace_cwd(
    record: &WorkspaceRecord,
    relative: &str,
    field: &str,
) -> Result<PathBuf, UniversalExecError> {
    let path = resolve_existing_workspace_path(record, relative, true).map_err(|mut error| {
        if error.field.as_deref() == Some("relativePath") {
            error.field = Some(field.to_string());
        }
        error
    })?;
    if !path.is_dir() {
        return Err(invalid("cwdRelative must resolve to a directory", field));
    }
    Ok(path)
}

pub(crate) fn preflight_workspace_write_path(
    record: &WorkspaceRecord,
    relative: &str,
) -> Result<PathBuf, UniversalExecError> {
    let relative = validate_relative_path(relative, "relativePath")?;
    let root = canonical_directory(Path::new(&record.workspace_path), "workspacePath")?;
    let mut current = root.clone();
    if let Some(parent) = relative.parent() {
        for component in parent.components() {
            let std::path::Component::Normal(name) = component else {
                continue;
            };
            current.push(name);
            if current.exists() {
                let metadata = fs::symlink_metadata(&current)
                    .map_err(|error| io_error(&current, "inspect", error))?;
                if metadata.file_type().is_symlink() || !metadata.is_dir() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::WorkspacePathDenied,
                        "workspace parent must remain a non-symlink directory",
                        Some("relativePath"),
                        false,
                    ));
                }
            }
        }
    }
    let target = root.join(relative);
    if target.exists() {
        let metadata =
            fs::symlink_metadata(&target).map_err(|error| io_error(&target, "inspect", error))?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::WorkspacePathDenied,
                "write target must be a non-symlink regular file",
                Some("relativePath"),
                false,
            ));
        }
    }
    Ok(target)
}

pub(crate) fn remove_workspace_file(
    record: &WorkspaceRecord,
    relative: &str,
) -> Result<(), UniversalExecError> {
    let path = preflight_workspace_write_path(record, relative)?;
    if path.exists() {
        fs::remove_file(&path).map_err(|error| io_error(&path, "remove", error))?;
    }
    Ok(())
}

fn resolve_workspace_write_path(
    record: &WorkspaceRecord,
    relative: &str,
) -> Result<PathBuf, UniversalExecError> {
    let relative = validate_relative_path(relative, "relativePath")?;
    let root = canonical_directory(Path::new(&record.workspace_path), "workspacePath")?;
    let file_name = relative
        .file_name()
        .ok_or_else(|| invalid("relativePath has no file name", "relativePath"))?;
    let mut safe_parent = root.clone();
    if let Some(parent) = relative.parent() {
        for component in parent.components() {
            let std::path::Component::Normal(name) = component else {
                continue;
            };
            let next = safe_parent.join(name);
            if next.exists() {
                let metadata = fs::symlink_metadata(&next)
                    .map_err(|error| io_error(&next, "inspect", error))?;
                if metadata.file_type().is_symlink() || !metadata.is_dir() {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::WorkspacePathDenied,
                        "workspace parent must remain a non-symlink directory",
                        Some("relativePath"),
                        false,
                    ));
                }
            } else {
                fs::create_dir(&next).map_err(|error| io_error(&next, "create", error))?;
            }
            safe_parent =
                fs::canonicalize(&next).map_err(|error| io_error(&next, "canonicalize", error))?;
            if !safe_parent.starts_with(&root) {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::WorkspacePathDenied,
                    "workspace write path escaped its root",
                    Some("relativePath"),
                    false,
                ));
            }
        }
    }
    Ok(safe_parent.join(file_name))
}

fn resolve_git_commit(repo: &Path, source_revision: &str) -> Result<String, UniversalExecError> {
    let revision_spec = format!("{source_revision}^{{commit}}");
    let output = Command::new("git")
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(repo)
        .args(["rev-parse", "--verify", "--end-of-options"])
        .arg(&revision_spec)
        .output()
        .map_err(|error| tool_unavailable("git", error))?;
    if !output.status.success() {
        let repository_probe = Command::new("git")
            .arg("--no-optional-locks")
            .arg("-C")
            .arg(repo)
            .args(["rev-parse", "--git-dir"])
            .output()
            .map_err(|error| tool_unavailable("git", error))?;
        if !repository_probe.status.success() {
            let message = String::from_utf8_lossy(&repository_probe.stderr)
                .trim()
                .to_string();
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                format!("source repository is not usable by git: {message}"),
                Some("sourceRepo"),
                false,
            ));
        }
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::RevisionNotFound,
            "source revision does not resolve to a commit",
            Some("sourceRevision"),
            false,
        ));
    }
    String::from_utf8(output.stdout)
        .map(|revision| revision.trim().to_string())
        .map_err(|error| {
            UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                format!("git revision output is not UTF-8: {error}"),
                Some("sourceRevision"),
                false,
            )
        })
}

fn git_output<'a>(
    repo: &Path,
    args: impl IntoIterator<Item = &'a str>,
) -> Result<String, UniversalExecError> {
    let output = Command::new("git")
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(repo)
        .args(args)
        .output()
        .map_err(|error| tool_unavailable("git", error))?;
    if !output.status.success() {
        return Err(tool_failed("git", &output.stderr));
    }
    String::from_utf8(output.stdout).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            format!("git output is not UTF-8: {error}"),
            None,
            false,
        )
    })
}

fn workspace_dirty_paths(workspace: &Path) -> Result<Vec<String>, UniversalExecError> {
    const MAX_DIRTY_PATHS: usize = 20;
    let tracked = git_output_bytes(workspace, ["diff", "--name-only", "-z", "HEAD", "--"])?;
    let untracked = git_output_bytes(
        workspace,
        ["ls-files", "--others", "--exclude-standard", "-z"],
    )?;
    let mut paths = Vec::new();
    for raw in tracked
        .split(|byte| *byte == 0)
        .chain(untracked.split(|byte| *byte == 0))
    {
        if raw.is_empty() {
            continue;
        }
        let path = String::from_utf8_lossy(raw).into_owned();
        if !paths.contains(&path) {
            paths.push(path);
        }
        if paths.len() == MAX_DIRTY_PATHS {
            paths.push("…".to_string());
            break;
        }
    }
    Ok(paths)
}

fn git_output_bytes<'a>(
    repo: &Path,
    args: impl IntoIterator<Item = &'a str>,
) -> Result<Vec<u8>, UniversalExecError> {
    let output = Command::new("git")
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(repo)
        .args(args)
        .output()
        .map_err(|error| tool_unavailable("git", error))?;
    if output.status.success() {
        Ok(output.stdout)
    } else {
        Err(tool_failed("git", &output.stderr))
    }
}

fn remove_git_worktree(
    source_repo: &Path,
    workspace: &Path,
    force: bool,
) -> Result<(), UniversalExecError> {
    let mut command = Command::new("git");
    command
        .arg("-C")
        .arg(source_repo)
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

fn tool_unavailable(operation: &str, error: impl std::fmt::Display) -> UniversalExecError {
    UniversalExecError::new(
        UniversalExecErrorCode::ToolUnavailable,
        format!("cannot execute {operation}: {error}"),
        None,
        false,
    )
}

fn tool_failed(operation: &str, stderr: &[u8]) -> UniversalExecError {
    let message = String::from_utf8_lossy(stderr).trim().to_string();
    let code =
        if message.contains("No space left on device") || message.contains("Disk quota exceeded") {
            UniversalExecErrorCode::WorkspaceCapacityExceeded
        } else {
            UniversalExecErrorCode::ToolFailed
        };
    UniversalExecError::new(code, format!("{operation} failed: {message}"), None, false)
}

#[cfg(unix)]
fn transfer_workspace_ownership(root: &Path, uid: u32, gid: u32) -> Result<(), UniversalExecError> {
    fn chown_nofollow(path: &Path, uid: u32, gid: u32) -> Result<(), UniversalExecError> {
        let c_path = std::ffi::CString::new(path.as_os_str().as_encoded_bytes()).map_err(|_| {
            UniversalExecError::new(
                UniversalExecErrorCode::WorkspacePathDenied,
                "workspace ownership path contains NUL",
                Some("workspacePath"),
                false,
            )
        })?;
        let result = unsafe { libc::lchown(c_path.as_ptr(), uid, gid) };
        if result != 0 {
            return Err(io_error(
                path,
                "change workspace ownership",
                std::io::Error::last_os_error(),
            ));
        }
        Ok(())
    }

    fn visit(path: &Path, uid: u32, gid: u32) -> Result<(), UniversalExecError> {
        let metadata = fs::symlink_metadata(path)
            .map_err(|error| io_error(path, "inspect ownership target", error))?;
        if metadata.is_dir() {
            chown_nofollow(path, 0, gid)?;
            fs::set_permissions(path, fs::Permissions::from_mode(0o770))
                .map_err(|error| io_error(path, "set workspace directory mode", error))?;
            for entry in fs::read_dir(path)
                .map_err(|error| io_error(path, "read ownership directory", error))?
            {
                let entry = entry.map_err(|error| io_error(path, "read ownership entry", error))?;
                visit(&entry.path(), uid, gid)?;
            }
        } else if path.file_name().is_some_and(|name| name == ".git") {
            chown_nofollow(path, 0, 0)?;
            if metadata.is_file() {
                fs::set_permissions(path, fs::Permissions::from_mode(0o400))
                    .map_err(|error| io_error(path, "protect Git worktree identity", error))?;
            }
        } else {
            chown_nofollow(path, uid, gid)?;
        }
        Ok(())
    }

    visit(root, uid, gid)?;
    let metadata =
        fs::metadata(root).map_err(|error| io_error(root, "verify workspace ownership", error))?;
    if metadata.uid() != 0
        || metadata.gid() != gid
        || metadata.permissions().mode() & 0o7777 != 0o770
    {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspacePathDenied,
            "workspace trust-root ownership did not persist",
            Some("workspacePath"),
            false,
        ));
    }
    Ok(())
}

#[cfg(not(unix))]
fn transfer_workspace_ownership(
    _root: &Path,
    _uid: u32,
    _gid: u32,
) -> Result<(), UniversalExecError> {
    Err(UniversalExecError::new(
        UniversalExecErrorCode::ToolUnavailable,
        "native workspace ownership transfer is not implemented for this platform",
        Some("workspacePath"),
        false,
    ))
}
