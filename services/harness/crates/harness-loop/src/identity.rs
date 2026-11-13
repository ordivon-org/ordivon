//! Rust-native identity and field-text validation.

/// Reject the four C0 separator controls in addition to Unicode whitespace.
fn identity_whitespace(ch: char) -> bool {
    ch.is_whitespace() || ('\u{001c}'..='\u{001f}').contains(&ch)
}

pub(crate) fn valid_trimmed(value: &str, max_bytes: usize) -> bool {
    !value.is_empty()
        && value.len() <= max_bytes
        && value.trim_matches(identity_whitespace) == value
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn c0_control_whitespace_is_not_a_valid_identity() {
        for c in '\u{001c}'..='\u{001f}' {
            assert!(!valid_trimmed(&format!("{c}agent"), 300));
        }
        assert!(valid_trimmed("\u{200b}agent", 300));
    }
}
