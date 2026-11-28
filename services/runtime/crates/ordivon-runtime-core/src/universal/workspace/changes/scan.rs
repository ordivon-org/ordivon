//! Stream original tracked and untracked Git entries to their consumer.
use super::change_parse::{read_nul_field, tracked_change_entry, utf8_change_path};
use super::BufReader;
use super::{
    drain_reader_bounded, finish_stream_child, tool_unavailable, workspace_git_command,
    UniversalExecError, UniversalExecErrorCode, WorkspaceChangeEntry, WorkspaceChangeKind,
};
use std::path::Path;
use std::process::Stdio;
pub(super) fn scan_tracked_changes(
    workspace: &Path,
    mut observe: impl FnMut(WorkspaceChangeEntry) -> Result<(), UniversalExecError>,
) -> Result<(), UniversalExecError> {
    let mut command = workspace_git_command();
    command
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(workspace)
        .args([
            "diff",
            "HEAD",
            "--name-status",
            "-z",
            "--no-renames",
            "--no-ext-diff",
            "--no-textconv",
        ])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = command
        .spawn()
        .map_err(|error| tool_unavailable("git diff --name-status", error))?;
    let stdout = child.stdout.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git diff --name-status stdout pipe is unavailable",
            None,
            false,
        )
    })?;
    let stderr = drain_reader_bounded(child.stderr.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git diff --name-status stderr pipe is unavailable",
            None,
            false,
        )
    })?);
    let mut reader = BufReader::new(stdout);
    loop {
        let candidate = match tracked_change_entry(&mut reader) {
            Ok(candidate) => candidate,
            Err(error) => {
                let _ = finish_stream_child(child, stderr, "git diff --name-status", true);
                return Err(error);
            }
        };
        let Some(candidate) = candidate else {
            finish_stream_child(child, stderr, "git diff --name-status", false)?;
            return Ok(());
        };
        if let Err(error) = observe(candidate) {
            let _ = finish_stream_child(child, stderr, "git diff --name-status", true);
            return Err(error);
        }
    }
}

pub(super) fn scan_untracked_changes(
    workspace: &Path,
    mut observe: impl FnMut(WorkspaceChangeEntry) -> Result<(), UniversalExecError>,
) -> Result<(), UniversalExecError> {
    let mut command = workspace_git_command();
    command
        .arg("--no-optional-locks")
        .arg("-C")
        .arg(workspace)
        .args(["ls-files", "--others", "--exclude-standard", "-z"])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let mut child = command
        .spawn()
        .map_err(|error| tool_unavailable("git ls-files", error))?;
    let stdout = child.stdout.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git ls-files stdout pipe is unavailable",
            None,
            false,
        )
    })?;
    let stderr = drain_reader_bounded(child.stderr.take().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git ls-files stderr pipe is unavailable",
            None,
            false,
        )
    })?);
    let mut reader = BufReader::new(stdout);
    loop {
        let raw = match read_nul_field(&mut reader, "git ls-files") {
            Ok(raw) => raw,
            Err(error) => {
                let _ = finish_stream_child(child, stderr, "git ls-files", true);
                return Err(error);
            }
        };
        let Some(raw) = raw else {
            finish_stream_child(child, stderr, "git ls-files", false)?;
            return Ok(());
        };
        let entry = WorkspaceChangeEntry {
            kind: WorkspaceChangeKind::Untracked,
            path: utf8_change_path(raw, "untracked Git path")?,
        };
        if let Err(error) = observe(entry) {
            let _ = finish_stream_child(child, stderr, "git ls-files", true);
            return Err(error);
        }
    }
}
