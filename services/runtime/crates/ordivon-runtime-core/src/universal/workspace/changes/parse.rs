//! NUL framed Git status and bounded path reader.
use super::super::MAX_WORKSPACE_IO_BYTES;
use super::{
    BufRead, UniversalExecError, UniversalExecErrorCode, WorkspaceChangeEntry, WorkspaceChangeKind,
};
pub(super) fn read_nul_field<R: BufRead>(
    reader: &mut R,
    context: &str,
) -> Result<Option<Vec<u8>>, UniversalExecError> {
    let max_bytes = usize::try_from(MAX_WORKSPACE_IO_BYTES).unwrap_or(usize::MAX);
    let mut field = Vec::new();
    loop {
        let available = reader.fill_buf().map_err(|error| {
            UniversalExecError::new(
                UniversalExecErrorCode::IoError,
                format!("read {context}: {error}"),
                None,
                true,
            )
        })?;
        if available.is_empty() {
            if field.is_empty() {
                return Ok(None);
            }
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                format!("{context} ended before NUL terminator"),
                None,
                false,
            ));
        }
        if let Some(index) = available.iter().position(|byte| *byte == 0) {
            if field.len().saturating_add(index) > max_bytes {
                return Err(UniversalExecError::new(
                    UniversalExecErrorCode::OutputLimitExceeded,
                    format!("{context} field exceeds {max_bytes} bytes"),
                    Some("maxBytes"),
                    false,
                ));
            }
            field.extend_from_slice(&available[..index]);
            reader.consume(index + 1);
            return Ok(Some(field));
        }
        if field.len().saturating_add(available.len()) > max_bytes {
            return Err(UniversalExecError::new(
                UniversalExecErrorCode::OutputLimitExceeded,
                format!("{context} field exceeds {max_bytes} bytes"),
                Some("maxBytes"),
                false,
            ));
        }
        let consumed = available.len();
        field.extend_from_slice(available);
        reader.consume(consumed);
    }
}

pub(super) fn utf8_change_path(raw: Vec<u8>, context: &str) -> Result<String, UniversalExecError> {
    String::from_utf8(raw).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ArtifactNotUtf8,
            format!("{context} is not UTF-8: {error}"),
            None,
            false,
        )
    })
}

pub(super) fn tracked_change_entry<R: BufRead>(
    reader: &mut R,
) -> Result<Option<WorkspaceChangeEntry>, UniversalExecError> {
    let Some(status) = read_nul_field(reader, "git diff --name-status")? else {
        return Ok(None);
    };
    let status = std::str::from_utf8(&status).map_err(|error| {
        UniversalExecError::new(
            UniversalExecErrorCode::ArtifactNotUtf8,
            format!("git diff status is not UTF-8: {error}"),
            None,
            false,
        )
    })?;
    let code = status.as_bytes().first().copied().ok_or_else(|| {
        UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            "git diff emitted an empty path status",
            None,
            false,
        )
    })?;
    let one_path = |reader: &mut R, kind: WorkspaceChangeKind| {
        let raw = read_nul_field(reader, "git diff path")?.ok_or_else(|| {
            UniversalExecError::new(
                UniversalExecErrorCode::ToolFailed,
                "git diff path record is incomplete",
                None,
                false,
            )
        })?;
        Ok(WorkspaceChangeEntry {
            kind,
            path: utf8_change_path(raw, "changed Git path")?,
        })
    };
    match code {
        b'M' | b'T' | b'U' => one_path(reader, WorkspaceChangeKind::Modified).map(Some),
        b'A' => one_path(reader, WorkspaceChangeKind::Added).map(Some),
        b'D' => one_path(reader, WorkspaceChangeKind::Deleted).map(Some),
        _ => Err(UniversalExecError::new(
            UniversalExecErrorCode::ToolFailed,
            format!("unsupported git diff path status: {status}"),
            None,
            false,
        )),
    }
}
