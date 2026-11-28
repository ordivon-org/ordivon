//! Original typed runner cgroup measurement and exact receipt schema.
use serde::{Deserialize, Serialize};

pub(crate) const RESOURCE_RECEIPT_FILE: &str = "resource-receipt.json";
pub(crate) const RESOURCE_RECEIPT_SCHEMA_VERSION: u32 = 1;
/// Terminal pre-result snapshot of the Attempt cgroup. Includes Runner overhead and descendants
/// observed up to sampling, but not post-sampling result serialization/write or Runner teardown.
pub(crate) const RESOURCE_RECEIPT_SCOPE_ATTEMPT_CGROUP: &str = "attempt_cgroup_including_runner";
pub(crate) const RESOURCE_RECEIPT_PROVIDER_LINUX_CGROUP_V2: &str = "linux_cgroup_v2";

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct CgroupCpuUsage {
    pub usage_usec: u64,
    pub user_usec: u64,
    pub system_usec: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct CgroupMemoryEvents {
    pub low: u64,
    pub high: u64,
    pub max: u64,
    pub oom: u64,
    pub oom_kill: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct CgroupMemoryUsage {
    pub peak_bytes: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub swap_peak_bytes: Option<u64>,
    pub events: CgroupMemoryEvents,
}

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct CgroupIoUsage {
    pub read_bytes: u64,
    pub write_bytes: u64,
    pub read_ops: u64,
    pub write_ops: u64,
    pub discard_bytes: u64,
    pub discard_ops: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct RunnerResourceReceipt {
    pub schema_version: u32,
    pub task_id: String,
    pub job_id: String,
    pub attempt_id: String,
    pub launch_token_digest: String,
    pub observed_unix_ms: u128,
    pub scope: String,
    pub provider: String,
    pub cpu: CgroupCpuUsage,
    pub memory: CgroupMemoryUsage,
    pub io: CgroupIoUsage,
}
