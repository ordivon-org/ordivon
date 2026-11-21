//! Original pending-batch identity and exclusive durable publication.
use super::super::{
    io_error, sha256_bytes, sync_directory, validate_relative_path, UniversalExecError,
    UniversalExecErrorCode, UniversalExecutorConfig, WorkspaceMutateRequest,
};
use serde::{Deserialize, Serialize};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};

const BATCH_INTENT_FILE: &str = "pending-mutation-v1.json";
pub(super) const MAX_BATCH_INTENT_BYTES: u64 = 64 * 1024 * 1024;

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(super) struct PendingBatch {
    pub(super) schema_version: u32,
    pub(super) workspace_id: String,
    pub(super) request_digest: String,
    pub(super) entries: Vec<PreparedMutation>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(super) struct PreparedMutation {
    pub(super) relative_path: String,
    pub(super) before_content: Option<String>,
    pub(super) before_digest: Option<String>,
    pub(super) after_content: String,
    pub(super) after_digest: String,
}

pub(super) fn incomplete(message: impl Into<String>) -> UniversalExecError {
    UniversalExecError::new(
        UniversalExecErrorCode::WorkspaceMutationIncomplete,
        message,
        Some("mutations"),
        false,
    )
}

fn pending_path(config: &UniversalExecutorConfig, workspace_id: &str) -> std::path::PathBuf {
    config
        .workspace_cache_path(workspace_id)
        .join(BATCH_INTENT_FILE)
}

/// Used within the existing PostgreSQL admission/Workspace-effect fence.
/// A pending batch must never become an implicitly authorized Job or close.
pub(crate) fn ensure_workspace_mutation_quiescent(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<(), UniversalExecError> {
    let path = pending_path(config, workspace_id);
    match fs::symlink_metadata(&path) {
        Ok(_) => Err(incomplete(format!(
            "Workspace has an unfinished file batch at {}; replay the exact workspace.mutate request first",
            path.display()
        ))),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        // A corrupted private-cache parent is not evidence of a batch.
        // Preserve the established IO_ERROR and fail closed before deletion.
        Err(error) if error.kind() == std::io::ErrorKind::NotADirectory => {
            Err(io_error(&path, "inspect Workspace private cache", error))
        }
        Err(error) => Err(incomplete(format!(
            "cannot inspect pending Workspace batch: {error}"
        ))),
    }
}

pub(super) fn publish_pending_exclusive(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
    bytes: &[u8],
) -> Result<(), UniversalExecError> {
    let path = pending_path(config, workspace_id);
    let parent = path.parent().expect("private Workspace cache has a parent");
    fs::create_dir_all(parent).map_err(|e| incomplete(format!("batch intent directory: {e}")))?;
    let stage = parent.join(format!(".pending-mutation-{}", uuid::Uuid::now_v7()));
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&stage)
        .map_err(|e| incomplete(format!("batch intent staging: {e}")))?;
    if let Err(error) = file.write_all(bytes).and_then(|()| file.sync_all()) {
        let _ = fs::remove_file(&stage);
        return Err(incomplete(format!(
            "batch intent staging not durable: {error}"
        )));
    }
    drop(file);
    // Exclusive hard-link publish cannot overwrite a concurrent unfinished
    // batch. POSIX rename with replace_existing=false does not offer this.
    let result = fs::hard_link(&stage, &path);
    let _ = fs::remove_file(&stage);
    match result {
        Ok(()) => sync_directory(parent)
            .map_err(|e| incomplete(format!("batch intent publication durability unknown: {e}"))),
        Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => Err(incomplete(
            "a concurrent Workspace batch already owns the durable intent",
        )),
        Err(error) => Err(incomplete(format!(
            "cannot publish exclusive batch intent: {error}"
        ))),
    }
}

pub(super) fn mutation_request_digest(
    request: &WorkspaceMutateRequest,
) -> Result<String, UniversalExecError> {
    let bytes = serde_json::to_vec(request).map_err(|error| {
        incomplete(format!(
            "cannot encode immutable Workspace mutation request: {error}"
        ))
    })?;
    Ok(sha256_bytes(&bytes))
}

pub(super) fn read_pending(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<Option<PendingBatch>, UniversalExecError> {
    let path = pending_path(config, workspace_id);
    let metadata = match fs::symlink_metadata(&path) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => return Err(incomplete(format!("cannot inspect batch intent: {error}"))),
    };
    if !metadata.file_type().is_file() || metadata.len() > MAX_BATCH_INTENT_BYTES {
        return Err(incomplete("batch intent is not a bounded regular file"));
    }
    let mut bytes = Vec::with_capacity(metadata.len() as usize);
    File::open(&path)
        .and_then(|mut f| f.read_to_end(&mut bytes))
        .map_err(|error| incomplete(format!("cannot read batch intent: {error}")))?;
    let batch: PendingBatch = serde_json::from_slice(&bytes)
        .map_err(|error| incomplete(format!("invalid batch intent: {error}")))?;
    if batch.schema_version != 1
        || batch.workspace_id != workspace_id
        || batch.entries.is_empty()
        || batch.entries.iter().any(|entry| {
            entry.before_digest
                != entry
                    .before_content
                    .as_ref()
                    .map(|c| sha256_bytes(c.as_bytes()))
                || entry.after_digest != sha256_bytes(entry.after_content.as_bytes())
        })
    {
        return Err(incomplete(
            "batch intent identity or content digest mismatch",
        ));
    }
    let mut unique = std::collections::BTreeSet::new();
    for entry in &batch.entries {
        validate_relative_path(&entry.relative_path, "relativePath")?;
        if !unique.insert(&entry.relative_path) {
            return Err(incomplete("batch intent contains duplicate paths"));
        }
    }
    Ok(Some(batch))
}

pub(super) fn finish_pending(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
) -> Result<(), UniversalExecError> {
    let path = pending_path(config, workspace_id);
    fs::remove_file(&path).map_err(|error| {
        incomplete(format!(
            "batch files are reconciled, but intent unlink failed: {error}"
        ))
    })?;
    if let Some(parent) = path.parent() {
        sync_directory(parent).map_err(|error| {
            incomplete(format!(
                "batch intent unlink durability is unknown: {error}"
            ))
        })?;
    }
    Ok(())
}
