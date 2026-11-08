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
/// Native systemd-run jobs are created as peers in system.slice, not as
/// descendants of the Runtime manager's own service cgroup. Observe their
/// actual shared allocation ancestry (system.slice + the cgroup v2 root).
/// This is an OS controller projection, not a replacement resource manager.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct ResourceBounds {
    cpu_millis: u64,
    memory_total_bytes: u64,
    memory_available_bytes: u64,
    pid_capacity: u64,
    pids_available: u64,
}

fn max_or_number(value: &str) -> Result<Option<u64>, String> {
    match value.trim() {
        "max" => Ok(None),
        raw => raw
            .parse::<u64>()
            .map(Some)
            .map_err(|e| format!("invalid cgroup controller limit: {e}")),
    }
}

impl ResourceBounds {
    /// Take the tightest effective constraint across ancestor cgroups.
    /// A child with "max" cannot override a parent's finite budget.
    fn constrain(
        &mut self,
        cpu_max: &str,
        memory_max: &str,
        memory_current: &str,
        pids_max: &str,
        pids_current: &str,
    ) -> Result<(), String> {
        let cpu = cpu_max.split_whitespace().collect::<Vec<_>>();
        let [quota, period] = cpu.as_slice() else {
            return Err("invalid cgroup cpu.max".into());
        };
        let period: u64 = period
            .parse()
            .map_err(|e| format!("invalid CPU period: {e}"))?;
        if period == 0 {
            return Err("zero CPU period".into());
        }
        if let Some(quota) = max_or_number(quota)? {
            self.cpu_millis = self.cpu_millis.min(quota.saturating_mul(1000) / period);
        }
        if let Some(cap) = max_or_number(memory_max)? {
            let used: u64 = memory_current
                .trim()
                .parse()
                .map_err(|e| format!("invalid memory.current: {e}"))?;
            self.memory_total_bytes = self.memory_total_bytes.min(cap);
            self.memory_available_bytes = self.memory_available_bytes.min(cap.saturating_sub(used));
        }
        let used: u64 = pids_current
            .trim()
            .parse()
            .map_err(|e| format!("invalid pids.current: {e}"))?;
        let cap = max_or_number(pids_max)?.unwrap_or(self.pid_capacity);
        self.pid_capacity = self.pid_capacity.min(cap);
        self.pids_available = self.pids_available.min(cap.saturating_sub(used));
        Ok(())
    }
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
        let cpus = std::thread::available_parallelism()
            .map_err(|e| e.to_string())?
            .get() as u64;
        let kernel_pids = text("/proc/sys/kernel/pid_max")?
            .trim()
            .parse::<u64>()
            .map_err(|e| e.to_string())?;
        let mut bounds = ResourceBounds {
            cpu_millis: cpus.saturating_mul(1000),
            memory_total_bytes: mem("MemTotal:")?,
            memory_available_bytes: mem("MemAvailable:")?,
            pid_capacity: kernel_pids,
            pids_available: kernel_pids,
        };
        // The systemd-run transient units have no --slice override: they
        // execute as siblings of the manager in system.slice. Apply BOTH the
        // slice and root controller constraints, not the manager's narrower
        // and unrelated own service cgroup.
        for scope in ["/sys/fs/cgroup", "/sys/fs/cgroup/system.slice"] {
            let read = |name: &str| text(&format!("{scope}/{name}"));
            bounds.constrain(
                &read("cpu.max")?,
                &read("memory.max")?,
                &read("memory.current")?,
                &read("pids.max")?,
                &read("pids.current")?,
            )?;
        }
        Ok(Self {
            cpu_millis: bounds.cpu_millis,
            memory_total_bytes: bounds.memory_total_bytes,
            memory_available_bytes: bounds.memory_available_bytes,
            pid_capacity: bounds.pid_capacity,
            pids_available: bounds.pids_available,
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

#[cfg(test)]
mod native_allocation_scope_tests {
    use super::{max_or_number, ResourceBounds};

    #[test]
    fn execution_slice_takes_tightest_parent_limits() {
        let mut resources = ResourceBounds {
            cpu_millis: 16_000,
            memory_total_bytes: 16_384,
            memory_available_bytes: 10_000,
            pid_capacity: 1000,
            pids_available: 1000,
        };
        // Kernel-wide root has no quota but still accounts all used PIDs.
        resources
            .constrain("max 100000", "max", "20", "max", "20")
            .unwrap();
        assert_eq!(resources.pids_available, 980);
        // The actual systemd execution slice has a tighter quota.
        resources
            .constrain("150000 100000", "1024", "900", "80", "64")
            .unwrap();
        assert_eq!(resources.cpu_millis, 1500);
        assert_eq!(resources.memory_total_bytes, 1024);
        assert_eq!(resources.memory_available_bytes, 124);
        assert_eq!(resources.pid_capacity, 80);
        assert_eq!(resources.pids_available, 16);
        // An unconstrained ancestor/child cannot override that quota.
        resources
            .constrain("max 100000", "max", "0", "max", "0")
            .unwrap();
        assert_eq!(resources.cpu_millis, 1500);
        assert_eq!(resources.memory_available_bytes, 124);
        assert_eq!(resources.pids_available, 16);
    }

    #[test]
    fn absent_or_malformed_native_limits_are_not_false_free_capacity() {
        assert_eq!(max_or_number("max\n").unwrap(), None);
        assert!(max_or_number("unexpected").is_err());
        let mut resources = ResourceBounds {
            cpu_millis: 1000,
            memory_total_bytes: 100,
            memory_available_bytes: 90,
            pid_capacity: 100,
            pids_available: 90,
        };
        assert!(resources
            .constrain("100 0", "max", "0", "max", "1")
            .is_err());
        assert!(resources
            .constrain("unknown", "max", "0", "max", "1")
            .is_err());
    }
}
