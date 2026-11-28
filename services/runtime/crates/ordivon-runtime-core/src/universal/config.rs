//! Universal native executor config: stable schema, validation, store, paths, and canonical namespace.
use super::{invalid, io_error, sha256_bytes, UniversalExecError, UniversalExecErrorCode};
use std::path::PathBuf;

pub const UNIVERSAL_EXEC_SCHEMA_VERSION: u32 = 1;
pub const MAX_WORKSPACE_IO_BYTES: u64 = 4 * 1024 * 1024;

#[derive(Clone, Debug)]
pub struct UniversalExecutorConfig {
    pub store_root: PathBuf,
    pub workspace_root: Option<PathBuf>,
    pub workspace_uid: Option<u32>,
    pub workspace_gid: Option<u32>,
    pub runner_path: Option<PathBuf>,
    pub allowed_executable_roots: Vec<PathBuf>,
    pub max_runtime_ms: u64,
    pub max_output_bytes: u64,
}

mod namespace;
mod paths;
mod store;
#[cfg(test)]
mod tests;
mod validation;
pub(crate) use namespace::canonical_directory;
