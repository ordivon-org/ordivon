//! Read actual cgroup files and prefer original local memory event evidence.
use super::{parse_cgroup_memory_events, parse_error, CgroupMemoryEvents, UniversalExecError};
use std::{fs, path::Path};

pub(super) fn read_required_text(path: &Path, context: &str) -> Result<String, UniversalExecError> {
    fs::read_to_string(path).map_err(|error| parse_error(format!("cannot read {context}: {error}")))
}

pub(super) fn read_required_u64(path: &Path, context: &str) -> Result<u64, UniversalExecError> {
    read_required_text(path, context)?
        .trim()
        .parse::<u64>()
        .map_err(|_| parse_error(format!("{context} is not an unsigned integer")))
}

pub(super) fn read_optional_u64(
    path: &Path,
    context: &str,
) -> Result<Option<u64>, UniversalExecError> {
    match fs::read_to_string(path) {
        Ok(value) => value
            .trim()
            .parse::<u64>()
            .map(Some)
            .map_err(|_| parse_error(format!("{context} is not an unsigned integer"))),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(error) => Err(parse_error(format!("cannot read {context}: {error}"))),
    }
}

pub(super) fn read_memory_events(
    cgroup_root: &Path,
) -> Result<CgroupMemoryEvents, UniversalExecError> {
    let local = cgroup_root.join("memory.events.local");
    match fs::read_to_string(&local) {
        Ok(value) => parse_cgroup_memory_events(&value),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => parse_cgroup_memory_events(
            &read_required_text(&cgroup_root.join("memory.events"), "memory.events")?,
        ),
        Err(error) => Err(parse_error(format!(
            "cannot read memory.events.local: {error}"
        ))),
    }
}
