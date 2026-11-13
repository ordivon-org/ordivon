//! Crash-recoverable Workspace file batches using the existing private Workspace cache.
//! This is a durable physical intent, not a second Workspace/Job authority.
//! The existing PG Workspace effect lock serializes entry points; individual
//! files are still atomically replaced, never misrepresented as a filesystem transaction.
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use super::{
    io_error, load_workspace_record, preflight_workspace_write_path, read_workspace_text,
    remove_workspace_file, sha256_bytes, sync_directory, write_workspace_text, UniversalExecError,
    UniversalExecErrorCode, UniversalExecutorConfig, WorkspaceMutateRequest, WorkspaceMutateResult,
    WorkspaceMutationMode, WorkspaceMutationResult, WorkspaceReadRequest, WorkspaceWriteRequest,
    MAX_WORKSPACE_IO_BYTES,
};

const BATCH_INTENT_FILE: &str = "pending-mutation-v1.json";
const MAX_BATCH_INTENT_BYTES: u64 = 64 * 1024 * 1024;

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct PendingBatch {
    schema_version: u32,
    workspace_id: String,
    request_digest: String,
    entries: Vec<PreparedMutation>,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct PreparedMutation {
    relative_path: String,
    before_content: Option<String>,
    before_digest: Option<String>,
    after_content: String,
    after_digest: String,
}

fn incomplete(message: impl Into<String>) -> UniversalExecError {
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

fn publish_pending_exclusive(
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

fn mutation_request_digest(request: &WorkspaceMutateRequest) -> Result<String, UniversalExecError> {
    let bytes = serde_json::to_vec(request).map_err(|error| {
        incomplete(format!(
            "cannot encode immutable Workspace mutation request: {error}"
        ))
    })?;
    Ok(sha256_bytes(&bytes))
}

fn read_pending(
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
        super::validate_relative_path(&entry.relative_path, "relativePath")?;
        if !unique.insert(&entry.relative_path) {
            return Err(incomplete("batch intent contains duplicate paths"));
        }
    }
    Ok(Some(batch))
}

fn finish_pending(
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

fn apply_pending(
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

fn rollback_pending(
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

pub fn mutate_workspace(
    config: &UniversalExecutorConfig,
    request: &WorkspaceMutateRequest,
) -> Result<WorkspaceMutateResult, UniversalExecError> {
    request.validate_shape()?;
    let request_digest = mutation_request_digest(request)?;
    if let Some(pending) = read_pending(config, &request.workspace_id)? {
        if pending.request_digest != request_digest {
            return Err(incomplete(
                "a different Workspace batch remains unfinished; only the exact original request may reconcile it",
            ));
        }
        let result = apply_pending(config, &pending)?;
        finish_pending(config, &request.workspace_id)?;
        return Ok(result);
    }

    let record = load_workspace_record(config, &request.workspace_id)?;
    let mut prepared = Vec::with_capacity(request.mutations.len());
    for (mutation_index, mutation) in request.mutations.iter().enumerate() {
        let path = preflight_workspace_write_path(&record, &mutation.relative_path)?;
        let existing = if path.exists() {
            let read = read_workspace_text(
                config,
                &WorkspaceReadRequest {
                    schema_version: request.schema_version,
                    workspace_id: request.workspace_id.clone(),
                    relative_path: mutation.relative_path.clone(),
                    max_bytes: MAX_WORKSPACE_IO_BYTES,
                },
            )?;
            Some((read.content, read.digest))
        } else {
            None
        };
        let before_digest = existing.as_ref().map(|(_, digest)| digest.clone());
        if mutation.expected_digest.is_none() && before_digest.is_some() {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::RevisionMismatch,
                format!(
                    "workspace file {} already exists; expectedDigest is required",
                    mutation.relative_path
                ),
                Some(&format!("mutations[{mutation_index}].expectedDigest")),
                false,
            ));
        }
        if mutation.expected_digest != before_digest
            && (mutation.expected_digest.is_some() || before_digest.is_some())
        {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::RevisionMismatch,
                format!(
                    "workspace file {} does not match expectedDigest",
                    mutation.relative_path
                ),
                Some(&format!("mutations[{mutation_index}].expectedDigest")),
                false,
            ));
        }
        let before_content = existing.map(|(content, _)| content);
        let after_content = match mutation.mode {
            WorkspaceMutationMode::Write => mutation.content.clone(),
            WorkspaceMutationMode::Append => {
                let mut content = before_content.clone().unwrap_or_default();
                content.push_str(&mutation.content);
                content
            }
            WorkspaceMutationMode::ReplaceExact => {
                let content = before_content.as_ref().ok_or_else(|| {
                    UniversalExecError::new(
                        UniversalExecErrorCode::WorkspacePathNotFound,
                        format!(
                            "REPLACE_EXACT target does not exist: {}",
                            mutation.relative_path
                        ),
                        Some(&format!("mutations[{mutation_index}].relativePath")),
                        false,
                    )
                })?;
                let expected = mutation.expected_text.as_ref().expect("validated");
                let occurrences = content.matches(expected).count();
                if occurrences != 1 {
                    return Err(UniversalExecError::new(
                        UniversalExecErrorCode::RevisionMismatch,
                        format!(
                            "REPLACE_EXACT expected one match in {}, found {occurrences}",
                            mutation.relative_path
                        ),
                        Some(&format!("mutations[{mutation_index}].expectedText")),
                        false,
                    ));
                }
                content.replacen(expected, &mutation.content, 1)
            }
        };
        if after_content.len() as u64 > MAX_WORKSPACE_IO_BYTES {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::OutputLimitExceeded,
                "mutated file exceeds the workspace limit",
                Some(&format!("mutations[{mutation_index}].content")),
                false,
            ));
        }
        prepared.push(PreparedMutation {
            relative_path: mutation.relative_path.clone(),
            before_content,
            before_digest,
            after_digest: sha256_bytes(after_content.as_bytes()),
            after_content,
        });
    }
    let batch = PendingBatch {
        schema_version: 1,
        workspace_id: request.workspace_id.clone(),
        request_digest,
        entries: prepared,
    };
    let serialized = serde_json::to_vec(&batch)
        .map_err(|error| incomplete(format!("cannot encode durable batch intent: {error}")))?;
    if serialized.len() as u64 > MAX_BATCH_INTENT_BYTES {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::OutputLimitExceeded,
            "batch intent exceeds 64 MiB private Workspace budget",
            Some("mutations"),
            false,
        ));
    }
    // Durable before ANY physical file replacement. No extra PG table or Job ID.
    publish_pending_exclusive(config, &request.workspace_id, &serialized)?;
    match apply_pending(config, &batch) {
        Ok(result) => {
            finish_pending(config, &request.workspace_id)?;
            Ok(result)
        }
        Err(error) => {
            // Preserve the original caught-error rollback contract. If the
            // physical state is ambiguous, retain the journal for exact replay.
            rollback_pending(config, &batch).map_err(|recovery| {
                incomplete(format!(
                    "batch write failed ({error}) and physical rollback is incomplete ({recovery})"
                ))
            })?;
            finish_pending(config, &request.workspace_id)?;
            Err(error)
        }
    }
}

pub(crate) fn read_workspace_slice(
    config: &UniversalExecutorConfig,
    request: &super::WorkspaceReadSliceRequest,
) -> Result<super::WorkspaceReadSliceResult, UniversalExecError> {
    const CHUNK_BYTES: usize = 64 * 1024;

    request.validate_shape()?;
    let record = load_workspace_record(config, &request.workspace_id)?;
    let path = super::resolve_existing_workspace_path(&record, &request.relative_path, false)?;
    let mut file = File::open(&path).map_err(|error| super::io_error(&path, "open", error))?;
    let before = file
        .metadata()
        .map_err(|error| super::io_error(&path, "inspect", error))?;
    let file_byte_length = before.len();
    if request.offset > file_byte_length {
        return Err(super::invalid("offset exceeds file length", "offset"));
    }
    let slice_end = request
        .offset
        .saturating_add(request.max_bytes)
        .min(file_byte_length);
    let mut digest = Sha256::new();
    let mut carry = Vec::with_capacity(4);
    let mut chunk = vec![0_u8; CHUNK_BYTES];
    let mut captured =
        Vec::with_capacity(usize::try_from(slice_end.saturating_sub(request.offset)).unwrap_or(0));
    let mut position = 0_u64;
    while position < file_byte_length {
        let remaining = file_byte_length - position;
        let wanted = usize::try_from(remaining.min(CHUNK_BYTES as u64)).unwrap_or(CHUNK_BYTES);
        let read = file
            .read(&mut chunk[..wanted])
            .map_err(|error| super::io_error(&path, "read", error))?;
        if read == 0 {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::WorkspaceMutationIncomplete,
                "workspace file changed while reading",
                Some("relativePath"),
                true,
            ));
        }
        let bytes = &chunk[..read];
        digest.update(bytes);

        let mut validation = Vec::with_capacity(carry.len() + read);
        validation.extend_from_slice(&carry);
        validation.extend_from_slice(bytes);
        match std::str::from_utf8(&validation) {
            Ok(_) => carry.clear(),
            Err(error) if error.error_len().is_none() => {
                let valid = error.valid_up_to();
                carry.clear();
                carry.extend_from_slice(&validation[valid..]);
                debug_assert!(carry.len() <= 3);
            }
            Err(error) => {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::ArtifactNotUtf8,
                    format!("workspace file is not UTF-8: {error}"),
                    Some("relativePath"),
                    false,
                ));
            }
        }

        let chunk_end = position.saturating_add(read as u64);
        let capture_start = request.offset.max(position);
        let capture_end = slice_end.min(chunk_end);
        if capture_start < capture_end {
            let local_start = usize::try_from(capture_start - position).unwrap_or(0);
            let local_end = usize::try_from(capture_end - position).unwrap_or(read);
            captured.extend_from_slice(&bytes[local_start..local_end]);
        }
        position = chunk_end;
    }
    if !carry.is_empty() {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::ArtifactNotUtf8,
            "workspace file ends with an incomplete UTF-8 sequence",
            Some("relativePath"),
            false,
        ));
    }
    let after = file
        .metadata()
        .map_err(|error| super::io_error(&path, "inspect after read", error))?;
    if after.len() != before.len() || after.modified().ok() != before.modified().ok() {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceMutationIncomplete,
            "workspace file changed while reading",
            Some("relativePath"),
            true,
        ));
    }
    let content = String::from_utf8(captured).map_err(|_| {
        super::invalid("offset and maxBytes must end on UTF-8 boundaries", "offset")
    })?;
    Ok(super::WorkspaceReadSliceResult {
        workspace_id: request.workspace_id.clone(),
        relative_path: request.relative_path.clone(),
        content,
        offset: request.offset,
        next_offset: slice_end,
        eof: slice_end == file_byte_length,
        file_digest: format!("sha256:{}", hex::encode(digest.finalize())),
        file_byte_length,
    })
}
