//! Detect output retained only in the unprivileged Agent's private Git store.
//!
//! The original worktree SourceStateDigest cannot observe independent refs,
//! empty commits or staged-only index changes. These are deliverables, not a
//! second authorization policy or a caller-supplied acceptance receipt.
use super::{
    io_error, read_workspace_record_bytes, tool_unavailable, unfinished_open_error,
    workspace_git_command, UniversalExecError, UniversalExecErrorCode, UniversalExecutorConfig,
};
use std::{fs, path::Path};

#[cfg(unix)]
pub(super) fn workspace_private_git_has_outputs(
    private: &Path,
    original_sha: &str,
) -> Result<bool, UniversalExecError> {
    let meta =
        fs::symlink_metadata(private).map_err(|e| io_error(private, "inspect private Git", e))?;
    if !meta.is_dir() || meta.file_type().is_symlink() {
        return Ok(true);
    }
    let head = fs::read_to_string(private.join("HEAD"))
        .map_err(|_| unfinished_open_error("private Git HEAD not readable"))?;
    if head.trim() != "ref: refs/heads/agent-work" {
        return Ok(true);
    }
    let ref_path = private.join("refs/heads/agent-work");
    let ref_meta = fs::symlink_metadata(&ref_path)
        .map_err(|_| unfinished_open_error("private Git original ref missing"))?;
    if !ref_meta.is_file() || ref_meta.file_type().is_symlink() {
        return Ok(true);
    }
    let base = fs::read_to_string(&ref_path)
        .map_err(|_| unfinished_open_error("private Git original ref unreadable"))?;
    if base.trim() != original_sha || private.join("packed-refs").exists() {
        return Ok(true);
    }
    for dir in [private.join("refs/heads"), private.join("refs/tags")] {
        for entry in fs::read_dir(&dir).map_err(|e| io_error(&dir, "read private Git refs", e))? {
            let entry = entry.map_err(|e| io_error(&dir, "inspect private Git ref", e))?;
            if dir.ends_with("heads") && entry.file_name() == "agent-work" {
                continue;
            }
            return Ok(true);
        }
    }
    // A staged-only candidate changes this private Git index even if the
    // original root-owned linked Worktree's file digest is unchanged.
    let result = workspace_git_command()
        .arg("--git-dir")
        .arg(private)
        .args([
            "-c",
            "core.fsmonitor=false",
            "diff-index",
            "--cached",
            "--quiet",
            "HEAD",
            "--",
        ])
        .output()
        .map_err(|e| tool_unavailable("git", e))?;
    match result.status.code() {
        Some(0) => Ok(false),
        Some(1) => Ok(true),
        _ => Err(unfinished_open_error(
            "cannot prove private Git index has no unique output",
        )),
    }
}

#[cfg(not(unix))]
pub(super) fn workspace_private_git_has_outputs(
    _private: &Path,
    _original_sha: &str,
) -> Result<bool, UniversalExecError> {
    Ok(false)
}

pub(super) fn require_no_unreceived_private_git_candidate(
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

// Verify delivered-output semantics at the Git boundary rather than asserting
// any Rust source filename, function body, or module layout. These cases also
// prevent a false-green when the root worktree itself remains unmodified.
#[cfg(all(test, unix))]
mod original_private_git_output_behavior_tests {
    use super::*;

    fn git(args: &[&str]) -> String {
        let output = workspace_git_command()
            .args(args)
            .output()
            .expect("native Git must be available");
        assert!(
            output.status.success(),
            "git {:?}: {}",
            args,
            String::from_utf8_lossy(&output.stderr)
        );
        String::from_utf8(output.stdout)
            .expect("Git output must be UTF-8")
            .trim()
            .to_owned()
    }

    fn original_with_private_index() -> (
        tempfile::TempDir,
        std::path::PathBuf,
        std::path::PathBuf,
        String,
    ) {
        let temp = tempfile::tempdir().expect("isolated original Git source");
        let source = temp.path().join("original");
        let private = temp.path().join("agent-git");
        fs::create_dir(&source).unwrap();
        let source_path = source.to_str().unwrap();
        let private_path = private.to_str().unwrap();
        git(&["-C", source_path, "init", "-q"]);
        git(&["-C", source_path, "config", "user.name", "Native Git Test"]);
        git(&[
            "-C",
            source_path,
            "config",
            "user.email",
            "test@example.invalid",
        ]);
        fs::write(source.join("tracked.txt"), b"original bytes").unwrap();
        git(&["-C", source_path, "add", "tracked.txt"]);
        git(&["-C", source_path, "commit", "-qm", "original"]);
        let revision = git(&["-C", source_path, "rev-parse", "HEAD"]);
        git(&["init", "--quiet", "--bare", private_path]);
        git(&[
            "--git-dir",
            private_path,
            "fetch",
            "--no-tags",
            "--depth=1",
            source_path,
            &revision,
        ]);
        git(&[
            "--git-dir",
            private_path,
            "update-ref",
            "refs/heads/agent-work",
            &revision,
        ]);
        git(&[
            "--git-dir",
            private_path,
            "symbolic-ref",
            "HEAD",
            "refs/heads/agent-work",
        ]);
        git(&[
            "--git-dir",
            private_path,
            "--work-tree",
            source_path,
            "read-tree",
            "HEAD",
        ]);
        assert!(
            !workspace_private_git_has_outputs(&private, &revision).unwrap(),
            "an unchanged private snapshot is not a consumer hold"
        );
        (temp, source, private, revision)
    }

    #[test]
    fn private_empty_commit_is_unreceived_even_with_identical_original_source_bytes() {
        let (_tmp, source, private, revision) = original_with_private_index();
        let root = source.to_str().unwrap();
        let git_dir = private.to_str().unwrap();
        git(&[
            "--git-dir",
            git_dir,
            "--work-tree",
            root,
            "-c",
            "user.name=Private Output Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "only private Git has an output",
        ]);
        assert_eq!(
            fs::read(source.join("tracked.txt")).unwrap(),
            b"original bytes"
        );
        assert!(
            workspace_private_git_has_outputs(&private, &revision).unwrap(),
            "a unique private commit must block close until an independent receiver accepts it"
        );
    }

    #[test]
    fn staged_only_private_output_blocks_close_even_after_source_bytes_are_restored() {
        let (_tmp, source, private, revision) = original_with_private_index();
        let root = source.to_str().unwrap();
        let git_dir = private.to_str().unwrap();
        fs::write(source.join("tracked.txt"), b"staged candidate bytes").unwrap();
        git(&[
            "--git-dir",
            git_dir,
            "--work-tree",
            root,
            "add",
            "tracked.txt",
        ]);
        fs::write(source.join("tracked.txt"), b"original bytes").unwrap();
        assert_eq!(
            fs::read(source.join("tracked.txt")).unwrap(),
            b"original bytes"
        );
        assert!(
            workspace_private_git_has_outputs(&private, &revision).unwrap(),
            "the private index is an output consumer even with a clean original worktree"
        );
        git(&[
            "--git-dir",
            git_dir,
            "--work-tree",
            root,
            "reset",
            "-q",
            "HEAD",
            "--",
            "tracked.txt",
        ]);
        assert!(
            !workspace_private_git_has_outputs(&private, &revision).unwrap(),
            "retiring the only private staged candidate must restore normal cleanup eligibility"
        );
    }
}
