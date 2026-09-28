use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use super::{sha256_bytes, write_json_atomic, RunnerRequest};

use super::{UniversalExecError, UniversalExecErrorCode};

pub(crate) const RESOURCE_RECEIPT_FILE: &str = "resource-receipt.json";
pub(crate) const RESOURCE_RECEIPT_SCHEMA_VERSION: u32 = 1;
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

fn parse_error(message: impl Into<String>) -> UniversalExecError {
    UniversalExecError::new(
        UniversalExecErrorCode::InvalidRequest,
        message,
        Some("resourceReceipt"),
        false,
    )
}

fn parse_space_counters(text: &str, context: &str) -> Result<BTreeMap<String, u64>, UniversalExecError> {
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
            return Err(parse_error(format!("{context} counter {key} has extra fields")));
        }
        let value = raw
            .parse::<u64>()
            .map_err(|_| parse_error(format!("{context} counter {key} is not an unsigned integer")))?;
        if counters.insert(key.to_string(), value).is_some() {
            return Err(parse_error(format!("{context} counter {key} is duplicated")));
        }
    }
    Ok(counters)
}

fn required_counter(
    counters: &BTreeMap<String, u64>,
    key: &str,
    context: &str,
) -> Result<u64, UniversalExecError> {
    counters
        .get(key)
        .copied()
        .ok_or_else(|| parse_error(format!("{context} omitted required counter {key}")))
}

pub(crate) fn parse_cgroup_cpu_stat(text: &str) -> Result<CgroupCpuUsage, UniversalExecError> {
    let counters = parse_space_counters(text, "cpu.stat")?;
    Ok(CgroupCpuUsage {
        usage_usec: required_counter(&counters, "usage_usec", "cpu.stat")?,
        user_usec: required_counter(&counters, "user_usec", "cpu.stat")?,
        system_usec: required_counter(&counters, "system_usec", "cpu.stat")?,
    })
}

pub(crate) fn parse_cgroup_memory_events(
    text: &str,
) -> Result<CgroupMemoryEvents, UniversalExecError> {
    let counters = parse_space_counters(text, "memory.events")?;
    Ok(CgroupMemoryEvents {
        low: required_counter(&counters, "low", "memory.events")?,
        high: required_counter(&counters, "high", "memory.events")?,
        max: required_counter(&counters, "max", "memory.events")?,
        oom: required_counter(&counters, "oom", "memory.events")?,
        oom_kill: required_counter(&counters, "oom_kill", "memory.events")?,
    })
}

fn add_counter(total: &mut u64, value: u64, key: &str) -> Result<(), UniversalExecError> {
    *total = total
        .checked_add(value)
        .ok_or_else(|| parse_error(format!("io.stat aggregate overflowed for {key}")))?;
    Ok(())
}

pub(crate) fn parse_cgroup_io_stat(text: &str) -> Result<CgroupIoUsage, UniversalExecError> {
    let mut total = CgroupIoUsage::default();
    for line in text.lines().filter(|line| !line.trim().is_empty()) {
        let mut parts = line.split_whitespace();
        let device = parts
            .next()
            .ok_or_else(|| parse_error("io.stat contains an empty device line"))?;
        let (major, minor) = device
            .split_once(':')
            .ok_or_else(|| parse_error(format!("io.stat device {device} is malformed")))?;
        if major.parse::<u32>().is_err() || minor.parse::<u32>().is_err() {
            return Err(parse_error(format!("io.stat device {device} is malformed")));
        }

        let mut counters = BTreeMap::new();
        for part in parts {
            let (key, raw) = part
                .split_once('=')
                .ok_or_else(|| parse_error(format!("io.stat field {part} is malformed")))?;
            let value = raw.parse::<u64>().map_err(|_| {
                parse_error(format!("io.stat counter {key} is not an unsigned integer"))
            })?;
            if counters.insert(key.to_string(), value).is_some() {
                return Err(parse_error(format!("io.stat counter {key} is duplicated for {device}")));
            }
        }

        add_counter(&mut total.read_bytes, required_counter(&counters, "rbytes", "io.stat")?, "rbytes")?;
        add_counter(&mut total.write_bytes, required_counter(&counters, "wbytes", "io.stat")?, "wbytes")?;
        add_counter(&mut total.read_ops, required_counter(&counters, "rios", "io.stat")?, "rios")?;
        add_counter(&mut total.write_ops, required_counter(&counters, "wios", "io.stat")?, "wios")?;
        add_counter(&mut total.discard_bytes, counters.get("dbytes").copied().unwrap_or(0), "dbytes")?;
        add_counter(&mut total.discard_ops, counters.get("dios").copied().unwrap_or(0), "dios")?;
    }
    Ok(total)
}

fn read_required_text(path: &Path, context: &str) -> Result<String, UniversalExecError> {
    fs::read_to_string(path).map_err(|error| {
        parse_error(format!("cannot read {context}: {error}"))
    })
}

fn read_required_u64(path: &Path, context: &str) -> Result<u64, UniversalExecError> {
    read_required_text(path, context)?
        .trim()
        .parse::<u64>()
        .map_err(|_| parse_error(format!("{context} is not an unsigned integer")))
}

fn read_optional_u64(path: &Path, context: &str) -> Result<Option<u64>, UniversalExecError> {
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

fn read_memory_events(cgroup_root: &Path) -> Result<CgroupMemoryEvents, UniversalExecError> {
    let local = cgroup_root.join("memory.events.local");
    match fs::read_to_string(&local) {
        Ok(value) => parse_cgroup_memory_events(&value),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            parse_cgroup_memory_events(&read_required_text(
                &cgroup_root.join("memory.events"),
                "memory.events",
            )?)
        }
        Err(error) => Err(parse_error(format!("cannot read memory.events.local: {error}"))),
    }
}

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
