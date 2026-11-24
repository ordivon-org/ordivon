//! Native Runner resource receipt writes original immutable bytes atomically.
//! This is an observation Artifact, never a capacity authorization or release decision.
use super::{
    parse_cgroup_cpu_stat, parse_cgroup_io_stat, parse_error, read_memory_events,
    read_optional_u64, read_required_text, read_required_u64, sha256_bytes, write_json_atomic,
    CgroupMemoryUsage, RunnerRequest, RunnerResourceReceipt, UniversalExecError,
    RESOURCE_RECEIPT_FILE, RESOURCE_RECEIPT_PROVIDER_LINUX_CGROUP_V2,
    RESOURCE_RECEIPT_SCHEMA_VERSION, RESOURCE_RECEIPT_SCOPE_ATTEMPT_CGROUP,
};
use std::path::Path;

pub(crate) fn write_resource_receipt_from_cgroup_root(
    task_dir: &Path,
    request: &RunnerRequest,
    cgroup_root: &Path,
    observed_unix_ms: u128,
) -> Result<(), UniversalExecError> {
    let job_id = request
        .job_id
        .as_ref()
        .ok_or_else(|| parse_error("resource receipt requires jobId"))?;
    let attempt_id = request
        .attempt_id
        .as_ref()
        .ok_or_else(|| parse_error("resource receipt requires attemptId"))?;
    let launch_token = request
        .launch_token
        .as_ref()
        .ok_or_else(|| parse_error("resource receipt requires launchToken"))?;

    let cpu = parse_cgroup_cpu_stat(&read_required_text(
        &cgroup_root.join("cpu.stat"),
        "cpu.stat",
    )?)?;
    let memory = CgroupMemoryUsage {
        peak_bytes: read_required_u64(&cgroup_root.join("memory.peak"), "memory.peak")?,
        swap_peak_bytes: read_optional_u64(
            &cgroup_root.join("memory.swap.peak"),
            "memory.swap.peak",
        )?,
        events: read_memory_events(cgroup_root)?,
    };
    let io = parse_cgroup_io_stat(&read_required_text(
        &cgroup_root.join("io.stat"),
        "io.stat",
    )?)?;
    let receipt = RunnerResourceReceipt {
        schema_version: RESOURCE_RECEIPT_SCHEMA_VERSION,
        task_id: request.task_id.clone(),
        job_id: job_id.clone(),
        attempt_id: attempt_id.clone(),
        launch_token_digest: sha256_bytes(launch_token.as_bytes()),
        observed_unix_ms,
        scope: RESOURCE_RECEIPT_SCOPE_ATTEMPT_CGROUP.to_string(),
        provider: RESOURCE_RECEIPT_PROVIDER_LINUX_CGROUP_V2.to_string(),
        cpu,
        memory,
        io,
    };
    write_json_atomic(&task_dir.join(RESOURCE_RECEIPT_FILE), &receipt)
}
