//! UTF-8 byte cursor pagination that cannot return zero progress inside a character.
use super::{io, RuntimeError, RuntimeResult};

pub(super) fn artifact_utf8_window(
    text: &str,
    offset: u64,
    max_bytes: u64,
) -> RuntimeResult<(usize, usize)> {
    let begin = usize::try_from(offset).map_err(io)?;
    if begin > text.len() || !text.is_char_boundary(begin) {
        return Err(RuntimeError::invalid("invalid UTF-8 offset", "offset"));
    }
    let mut end = begin.saturating_add(max_bytes as usize).min(text.len());
    while !text.is_char_boundary(end) {
        end -= 1;
    }
    if end == begin && begin < text.len() {
        return Err(RuntimeError::invalid(
            "maxBytes is too small for the next UTF-8 character; use at least 4 bytes",
            "maxBytes",
        ));
    }
    Ok((begin, end))
}
