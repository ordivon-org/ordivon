//! Shared cgroup stat parser: duplicate and malformed counters fail, never default.
use super::{UniversalExecError, UniversalExecErrorCode};
use std::collections::BTreeMap;

pub(super) fn parse_error(message: impl Into<String>) -> UniversalExecError {
    UniversalExecError::new(
        UniversalExecErrorCode::InvalidRequest,
        message,
        Some("resourceReceipt"),
        false,
    )
}

pub(super) fn parse_space_counters(
    text: &str,
    context: &str,
) -> Result<BTreeMap<String, u64>, UniversalExecError> {
    let mut counters = BTreeMap::new();
    for line in text.lines().filter(|line| !line.trim().is_empty()) {
        let mut parts = line.split_whitespace();
        let key = parts
            .next()
            .ok_or_else(|| parse_error(format!("{context} contains an empty counter line")))?;
        let raw = parts
            .next()
            .ok_or_else(|| parse_error(format!("{context} counter {key} omitted its value")))?;
        if parts.next().is_some() {
            return Err(parse_error(format!(
                "{context} counter {key} has extra fields"
            )));
        }
        let value = raw.parse::<u64>().map_err(|_| {
            parse_error(format!(
                "{context} counter {key} is not an unsigned integer"
            ))
        })?;
        if counters.insert(key.to_string(), value).is_some() {
            return Err(parse_error(format!(
                "{context} counter {key} is duplicated"
            )));
        }
    }
    Ok(counters)
}

pub(super) fn required_counter(
    counters: &BTreeMap<String, u64>,
    key: &str,
    context: &str,
) -> Result<u64, UniversalExecError> {
    counters
        .get(key)
        .copied()
        .ok_or_else(|| parse_error(format!("{context} omitted required counter {key}")))
}
