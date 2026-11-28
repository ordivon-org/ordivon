//! Request shape, original content/CAS and bounded batch preparation.
use super::super::{
    load_workspace_record, preflight_workspace_write_path, read_workspace_text, sha256_bytes,
    UniversalExecError, UniversalExecErrorCode, UniversalExecutorConfig, WorkspaceMutateRequest,
    WorkspaceMutateResult, WorkspaceMutationMode, WorkspaceReadRequest, MAX_WORKSPACE_IO_BYTES,
};
use super::intent::{
    finish_pending, incomplete, mutation_request_digest, publish_pending_exclusive, read_pending,
    PendingBatch, PreparedMutation, MAX_BATCH_INTENT_BYTES,
};
use super::physical::{apply_pending, rollback_pending};

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
