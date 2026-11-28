//! Shared original Runtime private env-file parser and native ACL validation.
#[cfg(unix)]
use std::os::unix::fs::PermissionsExt;
use std::{collections::BTreeMap, fs, path::Path};
const MAX_RUNTIME_ENV_FILE_BYTES: u64 = 64 * 1024;

pub(crate) fn read_private_runtime_env_file(
    path: &Path,
) -> Result<BTreeMap<String, String>, Box<dyn std::error::Error>> {
    if !path.is_absolute() {
        return Err("Runtime env file path must be absolute".into());
    }
    let metadata = fs::symlink_metadata(path)?;
    if !metadata.file_type().is_file() {
        return Err("Runtime env file path must be a regular file".into());
    }
    validate_private_runtime_file_permissions(path, &metadata, "Runtime env file")?;
    if metadata.len() > MAX_RUNTIME_ENV_FILE_BYTES {
        return Err("Runtime env file exceeds the configured bound".into());
    }
    let text = fs::read_to_string(path)?;
    parse_runtime_env_text(&text)
}

pub(crate) fn parse_runtime_env_text(
    text: &str,
) -> Result<BTreeMap<String, String>, Box<dyn std::error::Error>> {
    let mut values = BTreeMap::new();
    for (index, raw_line) in text.lines().enumerate() {
        let line = raw_line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let (name, value) = line
            .split_once('=')
            .ok_or_else(|| format!("Runtime env line {} must use NAME=VALUE", index + 1))?;
        let name = name.trim();
        let value = value.trim();
        let valid_name = !name.is_empty()
            && name
                .chars()
                .all(|ch| ch == '_' || ch.is_ascii_uppercase() || ch.is_ascii_digit())
            && !name.as_bytes()[0].is_ascii_digit();
        if !valid_name || (name != "RUST_LOG" && !name.starts_with("ORDIVON_")) {
            return Err(format!("Runtime env line {} uses an unsupported key", index + 1).into());
        }
        if matches!(
            name,
            "ORDIVON_BEARER_TOKEN" | "ORDIVON_REMOTE_BEARER_TOKEN" | "ORDIVON_PG_TOKEN"
        ) {
            return Err(format!(
                "Runtime env line {} embeds a bearer secret; use the corresponding *_FILE key",
                index + 1
            )
            .into());
        }
        if value.as_bytes().contains(&0) {
            return Err(format!("Runtime env line {} contains NUL", index + 1).into());
        }
        if values.insert(name.to_string(), value.to_string()).is_some() {
            return Err(format!("Runtime env line {} duplicates key {name}", index + 1).into());
        }
    }
    Ok(values)
}

#[cfg(unix)]
fn validate_private_runtime_file_permissions(
    _path: &Path,
    metadata: &fs::Metadata,
    label: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    if metadata.permissions().mode() & 0o077 != 0 {
        return Err(format!("{label} must not be accessible by group or others").into());
    }
    Ok(())
}

#[cfg(windows)]
fn validate_private_runtime_file_permissions(
    path: &Path,
    _metadata: &fs::Metadata,
    label: &str,
) -> Result<(), Box<dyn std::error::Error>> {
    ordivon_runtime_core::validate_windows_private_readonly_file_acl(path).map_err(|error| {
        format!("{label} does not satisfy the native Windows read-only ACL contract: {error}")
            .into()
    })
}
