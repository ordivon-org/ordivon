//! Linux cgroup v2 CPU usage, no derived approximate units.
use super::{parse_space_counters, required_counter, CgroupCpuUsage, UniversalExecError};

pub(crate) fn parse_cgroup_cpu_stat(text: &str) -> Result<CgroupCpuUsage, UniversalExecError> {
    let counters = parse_space_counters(text, "cpu.stat")?;
    Ok(CgroupCpuUsage {
        usage_usec: required_counter(&counters, "usage_usec", "cpu.stat")?,
        user_usec: required_counter(&counters, "user_usec", "cpu.stat")?,
        system_usec: required_counter(&counters, "system_usec", "cpu.stat")?,
    })
}
