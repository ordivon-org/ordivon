// Native Git commit rescue and broken Worktree recovery; no PostgreSQL/claim authority.
use super::{
    git_output, io_error, remove_git_worktree, tool_failed, tool_unavailable,
    workspace_git_command, UniversalExecError, UniversalExecErrorCode, WorkspaceRecord,
};
use std::{
    fs,
    path::{Path, PathBuf},
};

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

pub(super) fn ensure_rescue_ref(
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

pub(super) fn remove_residual_workspace_directory(target: &Path) -> Result<(), UniversalExecError> {
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

pub(super) fn remove_registered_workspace_with_broken_metadata(
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

pub(super) fn registered_workspace_head(
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

pub(super) fn recover_missing_workspace_head(
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

pub(super) fn remove_git_worktree_from_workspace(
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
