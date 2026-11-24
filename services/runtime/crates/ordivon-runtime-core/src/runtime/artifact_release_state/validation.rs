use super::super::{RuntimeError, RuntimeResult};

pub(super) fn validate_identifier(value: &str, field: &str) -> RuntimeResult<()> {
    if value.trim().is_empty()
        || value.len() > 256
        || value.as_bytes().contains(&0)
        || value.chars().any(char::is_control)
    {
        return Err(RuntimeError::invalid(
            format!("{field} must be non-empty, bounded, and control-free"),
            field,
        ));
    }
    Ok(())
}

pub(super) fn validate_sha256(value: &str, field: &str) -> RuntimeResult<()> {
    let valid = value
        .strip_prefix("sha256:")
        .is_some_and(|hex| hex.len() == 64 && hex.bytes().all(|byte| byte.is_ascii_hexdigit()));
    if !valid {
        return Err(RuntimeError::invalid(
            format!("{field} must be a SHA-256 digest"),
            field,
        ));
    }
    Ok(())
}

pub(super) fn validate_sha256_lowercase(
    value: &str,
    field: &str,
    prefix_message: &str,
    body_message: &str,
) -> RuntimeResult<()> {
    let hex = value
        .strip_prefix("sha256:")
        .ok_or_else(|| RuntimeError::invalid(prefix_message, field))?;
    if !is_lower_hex(hex, 64) {
        return Err(RuntimeError::invalid(body_message, field));
    }
    Ok(())
}

pub(super) fn is_lower_hex(value: &str, len: usize) -> bool {
    value.len() == len
        && value
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
}
