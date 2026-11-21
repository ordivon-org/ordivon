//! Detect output retained only in the unprivileged Agent's private Git store.
//!
//! The original worktree SourceStateDigest cannot observe independent refs,
//! empty commits or staged-only index changes. These are deliverables, not a
//! second authorization policy or a caller-supplied acceptance receipt.
use super::{
    io_error, tool_unavailable, unfinished_open_error, workspace_git_command, UniversalExecError,
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

#[cfg(all(test, unix))]
mod original_private_git_output_behavior_tests;
