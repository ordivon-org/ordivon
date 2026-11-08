//! Resource requests, native supply observations and Workspace access contracts.
//! Requests are scheduling estimates; existing ExecutionBudget fields remain hard ceilings.
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::{
    fs,
    path::{Component, Path},
};

#[derive(Clone, Debug, Deserialize, Serialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ResourceRequest {
    pub cpu_millis: u32,
    pub memory_bytes: u64,
    pub pids: u32,
    #[serde(default)]
    pub io_intensive: bool,
}
impl Default for ResourceRequest {
    fn default() -> Self {
        Self {
            cpu_millis: 100,
            memory_bytes: 128 * 1024 * 1024,
            pids: 16,
            io_intensive: false,
        }
    }
}
#[derive(Clone, Debug, Default, Deserialize, Serialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WorkspaceAccess {
    /// Full Workspace read access with no writes. May share with other readers.
    #[serde(default)]
    pub read_only: bool,
    /// Declared relative read sets for scoped mutable jobs; omitted means whole tree.
    #[serde(default)]
    pub read_paths: Vec<String>,
    /// Existing relative directories where writes are permitted. Omitted mutable
    /// access is exclusive. Native read-only mounts protect other Workspace paths.
    #[serde(default)]
    pub write_paths: Vec<String>,
}
#[derive(Clone, Debug, Default, Deserialize, Serialize, JsonSchema, PartialEq, Eq)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ResourceScheduling {
    #[serde(default)]
    pub resources: ResourceRequest,
    #[serde(default)]
    pub workspace_access: WorkspaceAccess,
    /// Trusted operator accounting label, not an authentication identity.
    #[serde(default)]
    pub owner: String,
    #[serde(default)]
    pub priority: i16,
    #[serde(default)]
    pub memory_high_bytes: Option<u64>,
    #[serde(default)]
    pub io_weight: Option<u16>,
}
impl ResourceScheduling {
    pub fn validate(&self) -> Result<(), String> {
        if self.resources.memory_bytes == 0
            || self.resources.memory_bytes > i64::MAX as u64
            || self.resources.pids == 0
            || self.owner.len() > 128
            || self.owner.contains(['\0', '\n'])
        {
            return Err("invalid resource request or accounting owner".into());
        }
        if self.memory_high_bytes == Some(0)
            || self.io_weight.is_some_and(|w| !(1..=10000).contains(&w))
        {
            return Err("invalid soft native resource control".into());
        }
        let a = &self.workspace_access;
        if a.read_only && !a.write_paths.is_empty() {
            return Err("readOnly conflicts with writePaths".into());
        }
        if a.read_paths.len() > 64 || a.write_paths.len() > 64 {
            return Err("too many Workspace access paths".into());
        }
        for path in a.read_paths.iter().chain(&a.write_paths) {
            if path.is_empty()
                || Path::new(path).is_absolute()
                || path.contains(['\0', ':', '\n', ' '])
                || Path::new(path)
                    .components()
                    .any(|p| !matches!(p, Component::Normal(_) | Component::CurDir))
                || path.split('/').any(|p| p == ".git")
            {
                return Err(
                    "Workspace access paths must be contained relative paths outside .git".into(),
                );
            }
        }
        Ok(())
    }
}
fn normalized(path: &str) -> String {
    Path::new(path)
        .components()
        .filter_map(|p| match p {
            Component::Normal(v) => Some(v.to_string_lossy().into_owned()),
            _ => None,
        })
        .collect::<Vec<_>>()
        .join("/")
}
fn overlap(a: &str, b: &str) -> bool {
    let a = normalized(a);
    let b = normalized(b);
    a.is_empty()
        || b.is_empty()
        || a == b
        || a.starts_with(&(b.clone() + "/"))
        || b.starts_with(&(a + "/"))
}
impl WorkspaceAccess {
    pub fn exclusive(&self) -> bool {
        !self.read_only && self.write_paths.is_empty()
    }
    pub fn conflicts(&self, other: &Self) -> bool {
        if self.exclusive() || other.exclusive() {
            return true;
        }
        if self.read_only && other.read_only {
            return false;
        }
        let reads = if self.read_paths.is_empty() {
            vec![".".into()]
        } else {
            self.read_paths.clone()
        };
        let other_reads = if other.read_paths.is_empty() {
            vec![".".into()]
        } else {
            other.read_paths.clone()
        };
        self.write_paths.iter().any(|w| {
            other
                .write_paths
                .iter()
                .chain(&other_reads)
                .any(|p| overlap(w, p))
        }) || other
            .write_paths
            .iter()
            .any(|w| reads.iter().any(|p| overlap(w, p)))
    }
}
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct NodeResources {
    pub cpu_millis: u64,
    pub memory_total_bytes: u64,
    pub memory_available_bytes: u64,
    pub pid_capacity: u64,
    pub pids_available: u64,
    pub cpu_pressure: f64,
    pub memory_pressure: f64,
    pub io_pressure: f64,
}
fn text(path: &str) -> Result<String, String> {
    fs::read_to_string(path).map_err(|e| format!("{path}: {e}"))
}
fn pressure(name: &str, kind: &str) -> Result<f64, String> {
    let raw = text(&format!("/proc/pressure/{name}"))?;
    raw.lines()
        .find(|l| l.starts_with(kind))
        .and_then(|l| l.split_whitespace().find_map(|v| v.strip_prefix("avg10=")))
        .and_then(|v| v.parse().ok())
        .ok_or_else(|| format!("missing {name} PSI"))
}
impl NodeResources {
    pub fn observe() -> Result<Self, String> {
        let info = text("/proc/meminfo")?;
        let mem = |name: &str| -> Result<u64, String> {
            info.lines()
                .find(|l| l.starts_with(name))
                .and_then(|l| l.split_whitespace().nth(1))
                .and_then(|v| v.parse::<u64>().ok())
                .and_then(|v| v.checked_mul(1024))
                .ok_or_else(|| format!("missing {name}"))
        };
        let mut cpu = std::thread::available_parallelism()
            .map_err(|e| e.to_string())?
            .get() as u64
            * 1000;
        let quota = text("/sys/fs/cgroup/cpu.max")?;
        let parts = quota.split_whitespace().collect::<Vec<_>>();
        if let [quota, period] = parts.as_slice() {
            if *quota != "max" {
                let q = quota.parse::<u64>().map_err(|e| e.to_string())?;
                let p = period.parse::<u64>().map_err(|e| e.to_string())?;
                if p == 0 {
                    return Err("invalid CPU period".into());
                }
                cpu = cpu.min(q.saturating_mul(1000) / p);
            }
        }
        let mut total = mem("MemTotal:")?;
        let mut available = mem("MemAvailable:")?;
        let max = text("/sys/fs/cgroup/memory.max")?;
        if let Ok(limit) = max.trim().parse::<u64>() {
            total = total.min(limit);
            let used = text("/sys/fs/cgroup/memory.current")?
                .trim()
                .parse::<u64>()
                .map_err(|e| e.to_string())?;
            available = available.min(limit.saturating_sub(used));
        }
        let kernel_pids = text("/proc/sys/kernel/pid_max")?
            .trim()
            .parse::<u64>()
            .map_err(|e| e.to_string())?;
        let pids_max = text("/sys/fs/cgroup/pids.max")?
            .trim()
            .parse::<u64>()
            .unwrap_or(kernel_pids)
            .min(kernel_pids);
        let pids_current = text("/sys/fs/cgroup/pids.current")?
            .trim()
            .parse::<u64>()
            .map_err(|e| e.to_string())?;
        Ok(Self {
            cpu_millis: cpu,
            memory_total_bytes: total,
            memory_available_bytes: available,
            pid_capacity: pids_max,
            pids_available: pids_max.saturating_sub(pids_current),
            cpu_pressure: pressure("cpu", "some")?,
            memory_pressure: pressure("memory", "full")?,
            io_pressure: pressure("io", "full")?,
        })
    }
    pub fn pressure_allows(&self, r: &ResourceRequest) -> bool {
        self.memory_pressure < 5.0
            && (r.cpu_millis == 0 || self.cpu_pressure < 70.0)
            && (!r.io_intensive || self.io_pressure < 40.0)
    }
}
