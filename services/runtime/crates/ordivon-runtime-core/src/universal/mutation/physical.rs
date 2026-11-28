//! Original Workspace file effects and exact physical rollback, not a new FS transaction.
use super::super::{
    load_workspace_record, preflight_workspace_write_path, read_workspace_text,
    remove_workspace_file, sha256_bytes, write_workspace_text, UniversalExecError,
    UniversalExecutorConfig, WorkspaceMutateResult, WorkspaceMutationResult, WorkspaceReadRequest,
    WorkspaceWriteRequest, MAX_WORKSPACE_IO_BYTES,
};
use super::intent::{incomplete, PendingBatch};

fn observed_content(
    config: &UniversalExecutorConfig,
    workspace_id: &str,
    relative_path: &str,
) -> Result<Option<String>, UniversalExecError> {
    let record = load_workspace_record(config, workspace_id)?;
    let path = preflight_workspace_write_path(&record, relative_path)?;
    if !path.exists() {
        return Ok(None);
    }
    read_workspace_text(
        config,
        &WorkspaceReadRequest {
            schema_version: 1,
            workspace_id: workspace_id.to_owned(),
            relative_path: relative_path.to_owned(),
            max_bytes: MAX_WORKSPACE_IO_BYTES,
        },
    )
    .map(|read| Some(read.content))
}

pub(super) fn apply_pending(
    config: &UniversalExecutorConfig,
    batch: &PendingBatch,
) -> Result<WorkspaceMutateResult, UniversalExecError> {
    let mut results = Vec::with_capacity(batch.entries.len());
    for entry in &batch.entries {
        let current = observed_content(config, &batch.workspace_id, &entry.relative_path)?;
        let actual_digest = current.as_ref().map(|s| sha256_bytes(s.as_bytes()));
        if actual_digest != Some(entry.after_digest.clone()) {
            if actual_digest != entry.before_digest {
                return Err(incomplete(format!(
                    "batch physical path {} is neither original nor intended; preserve evidence",
                    entry.relative_path
                )));
            }
            let written = write_workspace_text(
                config,
                &WorkspaceWriteRequest {
                    schema_version: 1,
                    workspace_id: batch.workspace_id.clone(),
                    relative_path: entry.relative_path.clone(),
                    content: entry.after_content.clone(),
                    expected_digest: entry.before_digest.clone(),
                },
            )?;
            if written.after_digest != entry.after_digest {
                return Err(incomplete("batch physical digest changed during write"));
            }
        }
        results.push(WorkspaceMutationResult {
            relative_path: entry.relative_path.clone(),
            after_digest: entry.after_digest.clone(),
            byte_length: entry.after_content.len() as u64,
        });
    }
    Ok(WorkspaceMutateResult { mutations: results })
}

pub(super) fn rollback_pending(
    config: &UniversalExecutorConfig,
    batch: &PendingBatch,
) -> Result<(), UniversalExecError> {
    let record = load_workspace_record(config, &batch.workspace_id)?;
    for entry in batch.entries.iter().rev() {
        let current = observed_content(config, &batch.workspace_id, &entry.relative_path)?;
        let actual_digest = current.as_ref().map(|s| sha256_bytes(s.as_bytes()));
        if actual_digest == entry.before_digest {
            continue;
        }
        if actual_digest != Some(entry.after_digest.clone()) {
            return Err(incomplete(format!(
                "batch rollback cannot prove ownership of {}",
                entry.relative_path
            )));
        }
        if let Some(before) = &entry.before_content {
            write_workspace_text(
                config,
                &WorkspaceWriteRequest {
                    schema_version: 1,
                    workspace_id: batch.workspace_id.clone(),
                    relative_path: entry.relative_path.clone(),
                    content: before.clone(),
                    expected_digest: Some(entry.after_digest.clone()),
                },
            )?;
        } else {
            remove_workspace_file(&record, &entry.relative_path)?;
        }
    }
    Ok(())
}
