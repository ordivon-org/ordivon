//! Bind the manager's host PID, namespace PID and Linux kernel start identity.

use super::*;

pub(super) fn namespace_pid_from_host_status(status: &str, host_pid: u32) -> Option<u32> {
    if host_pid == 0 {
        return None;
    }
    let mut namespace_pid = None;
    for line in status.lines() {
        let Some(value) = line.strip_prefix("NSpid:") else {
            continue;
        };
        if namespace_pid.is_some() {
            return None;
        }
        let values: Option<Vec<u32>> = value
            .split_whitespace()
            .map(|part| part.parse::<u32>().ok().filter(|pid| *pid != 0))
            .collect();
        let values = values?;
        if values.first().copied() != Some(host_pid) {
            return None;
        }
        namespace_pid = values.last().copied();
    }
    namespace_pid
}

pub(super) fn observed_namespace_pid(host_pid: u32) -> Option<u32> {
    let status = std::fs::read_to_string(format!("/proc/{host_pid}/status")).ok()?;
    namespace_pid_from_host_status(&status, host_pid)
}

/// One native observation binds the Manager's host PID to the Runner's
/// namespace-local PID and the same kernel process starttime. Keep the
/// three dependent facts together rather than accepting free-floating PIDs.
pub(super) struct NativePidReadback<'a> {
    pub(super) host_pid: Option<u32>,
    pub(super) namespace_pid: Option<u32>,
    pub(super) process_start: Option<&'a str>,
}

/// Project RUNNING only from a positively bound Linux Runner plus the
/// kernel supervisor's host PID, the same kernel process starttime, and its
/// namespace-local PID. An issued dispatch, partial stdout, or the mere
/// presence of runner-start.json is insufficient.
pub(super) fn native_running_witness(
    start: &RunnerStartEvidence,
    native: &std::collections::BTreeMap<String, String>,
    job: &str,
    attempt: &str,
    launch_digest: &str,
    observed: NativePidReadback<'_>,
    provider_digest: &str,
) -> bool {
    let expected_unit = format!("ordivon-pg-{attempt}.service");
    start.schema_version == 1
        && start.job_id == job
        && start.attempt_id == attempt
        && start.launch_token_digest == launch_digest
        && start.unit_name == expected_unit
        && start.control_group == format!("/system.slice/{expected_unit}")
        && start.namespace_pid != 0
        && !start.namespace_process_start_identity.is_empty()
        && observed.host_pid.is_some_and(|pid| pid != 0)
        && observed.namespace_pid == Some(start.namespace_pid)
        && observed.process_start == Some(start.namespace_process_start_identity.as_str())
        && start.observed_unix_ms > 0
        && start.runner_executable_digest.as_deref() == Some(provider_digest)
        && native.get("LoadState").map(String::as_str) == Some("loaded")
        && native.get("ActiveState").map(String::as_str) == Some("active")
        && native.get("InvocationID").map(String::as_str) == Some(start.invocation_id.as_str())
        && !start.invocation_id.is_empty()
        && native.get("ControlGroup").map(String::as_str) == Some(start.control_group.as_str())
        && native
            .get("MainPID")
            .and_then(|pid| pid.parse::<u32>().ok())
            == observed.host_pid
}
