//! Resource receipt logic: typed metric schema -> strict cgroup parsing -> native file read -> Artifact.
mod counters;
mod cpu;
mod io;
mod memory;
mod snapshot;
mod types;
mod write;

use super::{
    sha256_bytes, write_json_atomic, RunnerRequest, UniversalExecError, UniversalExecErrorCode,
};
use counters::{parse_error, parse_space_counters, required_counter};
pub(crate) use cpu::parse_cgroup_cpu_stat;
pub(crate) use io::parse_cgroup_io_stat;
pub(crate) use memory::parse_cgroup_memory_events;
use snapshot::{read_memory_events, read_optional_u64, read_required_text, read_required_u64};
pub(crate) use types::{
    CgroupCpuUsage, CgroupIoUsage, CgroupMemoryEvents, CgroupMemoryUsage, RunnerResourceReceipt,
    RESOURCE_RECEIPT_FILE, RESOURCE_RECEIPT_PROVIDER_LINUX_CGROUP_V2,
    RESOURCE_RECEIPT_SCHEMA_VERSION, RESOURCE_RECEIPT_SCOPE_ATTEMPT_CGROUP,
};
pub(crate) use write::write_resource_receipt_from_cgroup_root;

#[cfg(test)]
mod tests;
