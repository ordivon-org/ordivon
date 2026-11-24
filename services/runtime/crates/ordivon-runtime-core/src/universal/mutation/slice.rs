//! Stream whole-file SHA/UTF-8 while slicing bounded bytes; separate from file mutation.
use super::super::{
    invalid, io_error, load_workspace_record, resolve_existing_workspace_path, UniversalExecError,
    UniversalExecErrorCode, UniversalExecutorConfig, WorkspaceReadSliceRequest,
    WorkspaceReadSliceResult,
};
use sha2::{Digest, Sha256};
use std::fs::File;
use std::io::Read;

pub(crate) fn read_workspace_slice(
    config: &UniversalExecutorConfig,
    request: &WorkspaceReadSliceRequest,
) -> Result<WorkspaceReadSliceResult, UniversalExecError> {
    const CHUNK_BYTES: usize = 64 * 1024;

    request.validate_shape()?;
    let record = load_workspace_record(config, &request.workspace_id)?;
    let path = resolve_existing_workspace_path(&record, &request.relative_path, false)?;
    let mut file = File::open(&path).map_err(|error| io_error(&path, "open", error))?;
    let before = file
        .metadata()
        .map_err(|error| io_error(&path, "inspect", error))?;
    let file_byte_length = before.len();
    if request.offset > file_byte_length {
        return Err(invalid("offset exceeds file length", "offset"));
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
            .map_err(|error| io_error(&path, "read", error))?;
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
        .map_err(|error| io_error(&path, "inspect after read", error))?;
    if after.len() != before.len() || after.modified().ok() != before.modified().ok() {
        return Err(UniversalExecError::new(
            UniversalExecErrorCode::WorkspaceMutationIncomplete,
            "workspace file changed while reading",
            Some("relativePath"),
            true,
        ));
    }
    let content = String::from_utf8(captured)
        .map_err(|_| invalid("offset and maxBytes must end on UTF-8 boundaries", "offset"))?;
    Ok(WorkspaceReadSliceResult {
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
