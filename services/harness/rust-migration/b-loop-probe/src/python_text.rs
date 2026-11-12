//! Narrow source compatibility for Python's existing _text guard.
//! Not a new global string or identity policy.

/// CPython str.strip includes C0 0x1c..0x1f in addition to Unicode
/// White_Space; Rust's default trim does not include those four bytes.
fn python_strip_whitespace(ch: char) -> bool {
    ch.is_whitespace() || ('\u{001c}'..='\u{001f}').contains(&ch)
}

pub(crate) fn valid_trimmed(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && value.trim_matches(python_strip_whitespace) == value
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn python_control_whitespace_is_not_a_valid_identity() {
        for c in '\u{001c}'..='\u{001f}' {
            assert!(!valid_trimmed(&format!("{c}agent"), 300));
        }
        assert!(valid_trimmed("\u{200b}agent", 300));
    }
}
