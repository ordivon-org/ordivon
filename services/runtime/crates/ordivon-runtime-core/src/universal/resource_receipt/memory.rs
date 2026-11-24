//! Linux cgroup v2 memory.events, mandatory fields and no silent defaults.
use super::{parse_space_counters, required_counter, CgroupMemoryEvents, UniversalExecError};

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
