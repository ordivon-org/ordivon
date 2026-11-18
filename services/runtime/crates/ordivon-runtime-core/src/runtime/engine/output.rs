//! UTF-8 output and Artifact range projections; no Job admission or persistence authority.

use std::fs::{self, File};
use std::io::{Read, Seek, SeekFrom};
use std::path::Path;

use super::{io_error, RuntimeError, RuntimeResult};

#[derive(Debug)]
pub(super) struct OutputView {
    pub(super) content: String,
    pub(super) offset: Option<u64>,
    pub(super) next_offset: Option<u64>,
    pub(super) available_bytes: Option<u64>,
    pub(super) eof: Option<bool>,
}

impl OutputView {
    pub(super) fn empty(offset: Option<u64>, terminal: bool) -> Self {
        Self {
            content: String::new(),
            offset,
            next_offset: offset,
            available_bytes: offset.map(|_| 0),
            eof: offset.map(|value| terminal && value == 0),
        }
    }
}

#[derive(Debug)]
pub(super) struct TextRange {
    pub(super) content: String,
    pub(super) next_offset: u64,
}

#[derive(Clone, Copy)]
pub(super) struct RangeFields<'a> {
    pub(super) offset: &'a str,
    pub(super) max_bytes: &'a str,
}

pub(super) fn read_utf8_range(
    path: &Path,
    offset: u64,
    max_bytes: u64,
    available: u64,
    terminal: bool,
    fields: RangeFields<'_>,
    context: &str,
) -> RuntimeResult<TextRange> {
    let mut file =
        File::open(path).map_err(|error| io_error(&format!("open {context} range"), error))?;
    read_utf8_range_from_reader(
        &mut file, offset, max_bytes, available, terminal, fields, context,
    )
}

// Use this same UTF-8 boundary contract for regular output files and for a
// digest-verified Artifact byte snapshot. A fresh pathname open after hashing
// is not a valid Artifact identity bridge.
fn read_utf8_range_from_reader<R: Read + Seek>(
    reader: &mut R,
    offset: u64,
    max_bytes: u64,
    available: u64,
    terminal: bool,
    fields: RangeFields<'_>,
    context: &str,
) -> RuntimeResult<TextRange> {
    if offset > available {
        return Err(RuntimeError::invalid(
            format!("{} exceeds retained byte length {available}", fields.offset),
            fields.offset,
        ));
    }
    if max_bytes == 0 || offset == available {
        return Ok(TextRange {
            content: String::new(),
            next_offset: offset,
        });
    }
    let read_limit = max_bytes.min(available.saturating_sub(offset));
    reader
        .seek(SeekFrom::Start(offset))
        .map_err(|error| io_error(&format!("seek {context} range"), error))?;
    let mut bytes = vec![0_u8; usize::try_from(read_limit).unwrap_or(usize::MAX)];
    let read = reader
        .read(&mut bytes)
        .map_err(|error| io_error(&format!("read {context} range"), error))?;
    bytes.truncate(read);
    decode_utf8_range_bytes(bytes, offset, available, terminal, fields)
}

pub(super) fn decode_utf8_range_bytes(
    mut bytes: Vec<u8>,
    offset: u64,
    available: u64,
    terminal: bool,
    fields: RangeFields<'_>,
) -> RuntimeResult<TextRange> {
    if offset > 0 && bytes.first().is_some_and(|byte| byte & 0xc0 == 0x80) {
        return Err(RuntimeError::invalid(
            format!("{} must point to a UTF-8 character boundary", fields.offset),
            fields.offset,
        ));
    }
    let safe_len = match std::str::from_utf8(&bytes) {
        Ok(_) => bytes.len(),
        Err(error) if error.error_len().is_none() => error.valid_up_to(),
        Err(_) => bytes.len(),
    };
    if safe_len == 0 && !bytes.is_empty() {
        if !terminal && offset.saturating_add(bytes.len() as u64) >= available {
            return Ok(TextRange {
                content: String::new(),
                next_offset: offset,
            });
        }
        return Err(RuntimeError::invalid(
            format!(
                "{} is too small for the next UTF-8 character; use at least 4 bytes",
                fields.max_bytes
            ),
            fields.max_bytes,
        ));
    }
    bytes.truncate(safe_len);
    Ok(TextRange {
        content: String::from_utf8_lossy(&bytes).into_owned(),
        next_offset: offset.saturating_add(safe_len as u64),
    })
}

pub(super) fn read_output_text(
    path: &Path,
    offset: Option<u64>,
    max_bytes: u64,
    terminal: bool,
    offset_field: &str,
    max_bytes_field: &str,
) -> RuntimeResult<OutputView> {
    let Some(offset) = offset else {
        return Ok(OutputView {
            content: read_tail_text(path, max_bytes)?,
            offset: None,
            next_offset: None,
            available_bytes: None,
            eof: None,
        });
    };
    let available = if path.exists() {
        fs::metadata(path)
            .map_err(|error| io_error("inspect output range", error))?
            .len()
    } else {
        0
    };
    if offset > available {
        return Err(RuntimeError::invalid(
            format!("{offset_field} exceeds retained output length {available}"),
            offset_field,
        ));
    }
    if max_bytes == 0 || !path.exists() {
        return Ok(OutputView {
            content: String::new(),
            offset: Some(offset),
            next_offset: Some(offset),
            available_bytes: Some(available),
            eof: Some(terminal && offset >= available),
        });
    }
    let range = read_utf8_range(
        path,
        offset,
        max_bytes,
        available,
        terminal,
        RangeFields {
            offset: offset_field,
            max_bytes: max_bytes_field,
        },
        "output",
    )?;
    Ok(OutputView {
        content: range.content,
        offset: Some(offset),
        next_offset: Some(range.next_offset),
        available_bytes: Some(available),
        eof: Some(terminal && range.next_offset >= available),
    })
}

pub(super) fn read_tail_text(path: &Path, max_bytes: u64) -> RuntimeResult<String> {
    if max_bytes == 0 || !path.exists() {
        return Ok(String::new());
    }
    let mut file = File::open(path).map_err(|error| io_error("open output tail", error))?;
    let length = file
        .metadata()
        .map_err(|error| io_error("inspect output tail", error))?
        .len();
    let offset = length.saturating_sub(max_bytes);
    file.seek(SeekFrom::Start(offset))
        .map_err(|error| io_error("seek output tail", error))?;
    let mut bytes = Vec::with_capacity(usize::try_from(max_bytes.min(length)).unwrap_or(0));
    file.take(max_bytes)
        .read_to_end(&mut bytes)
        .map_err(|error| io_error("read output tail", error))?;
    Ok(String::from_utf8_lossy(&bytes).into_owned())
}
