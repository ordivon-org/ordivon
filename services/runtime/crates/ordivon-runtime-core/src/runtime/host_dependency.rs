//! Single native Host Dependency validation and pre-dispatch authority.
//! Shared by the original Runtime engine and the fresh PostgreSQL Runtime.

use super::error::map_universal_error;
use super::{
    ExecutionProfile, ExecutionTarget, HostDependencyBinding, RuntimeError, RuntimeErrorCode,
    RuntimeResult,
};
use crate::universal::sha256_file;
use std::{fs, path::Path};

pub(super) fn validate_bindings(
    requested: &[HostDependencyBinding],
    target: ExecutionTarget,
    profile: ExecutionProfile,
) -> RuntimeResult<Vec<HostDependencyBinding>> {
    if requested.is_empty() {
        return Ok(Vec::new());
    }
    if target != ExecutionTarget::LocalLinux || profile != ExecutionProfile::TrustedLocal {
        return Err(RuntimeError::invalid(
            "Host Dependencies require trusted_local local_linux execution",
            "execution.hostDependencies",
        ));
    }
    let mut bindings = requested.to_vec();
    bindings.sort_by(|left, right| left.path.cmp(&right.path));
    let mut previous: Option<&str> = None;
    for (index, binding) in bindings.iter().enumerate() {
        let path = Path::new(&binding.path);
        if !path.is_absolute() || binding.path.as_bytes().contains(&0) {
            return Err(RuntimeError::invalid(
                "Host Dependency path must be absolute and NUL-free",
                &format!("execution.hostDependencies[{index}].path"),
            ));
        }
        if previous == Some(binding.path.as_str()) {
            return Err(RuntimeError::invalid(
                "Host Dependency paths must be unique",
                "execution.hostDependencies",
            ));
        }
        previous = Some(&binding.path);
        let expected = binding
            .expected_digest
            .strip_prefix("sha256:")
            .ok_or_else(|| {
                RuntimeError::invalid(
                    "Host Dependency expectedDigest must use sha256",
                    &format!("execution.hostDependencies[{index}].expectedDigest"),
                )
            })?;
        if expected.len() != 64
            || !expected
                .bytes()
                .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
        {
            return Err(RuntimeError::invalid(
                "Host Dependency expectedDigest must contain 64 lowercase hexadecimal characters",
                &format!("execution.hostDependencies[{index}].expectedDigest"),
            ));
        }
        let metadata = fs::symlink_metadata(path).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                format!("Host Dependency {} is unavailable: {error}", binding.path),
                Some("execution.hostDependencies"),
                false,
            )
        })?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(RuntimeError::invalid(
                "Host Dependency must be a regular non-symlink file",
                &format!("execution.hostDependencies[{index}].path"),
            ));
        }
        let observed = sha256_file(path).map_err(map_universal_error)?;
        if observed != binding.expected_digest {
            return Err(RuntimeError::new(
                RuntimeErrorCode::InvalidRequest,
                format!(
                    "Host Dependency {} does not match expected digest: expected {}, observed {}",
                    binding.path, binding.expected_digest, observed
                ),
                Some("execution.hostDependencies"),
                false,
            ));
        }
    }
    Ok(bindings)
}

pub(super) fn verify_committed_bindings(bindings: &[HostDependencyBinding]) -> RuntimeResult<()> {
    for binding in bindings.iter() {
        let path = Path::new(&binding.path);
        let metadata = fs::symlink_metadata(path).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                format!(
                    "committed Host Dependency {} is unavailable before dispatch: {error}",
                    binding.path
                ),
                Some("hostDependencies"),
                false,
            )
        })?;
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::WorkspaceStateMismatch,
                format!(
                    "committed Host Dependency {} is not a regular non-symlink file",
                    binding.path
                ),
                Some("hostDependencies"),
                false,
            ));
        }
        let observed = sha256_file(path).map_err(map_universal_error)?;
        if observed != binding.expected_digest {
            return Err(RuntimeError::new(
                    RuntimeErrorCode::WorkspaceStateMismatch,
                    format!(
                        "committed Host Dependency {} changed after admission: expected {}, observed {}",
                        binding.path, binding.expected_digest, observed
                    ),
                    Some("hostDependencies"),
                    false,
                ));
        }
    }
    Ok(())
}
