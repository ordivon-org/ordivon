//! Linux cgroup v2 multi-device IO totals, checked for integer overflow.
use super::{parse_error, required_counter, CgroupIoUsage, UniversalExecError};
use std::collections::BTreeMap;

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
                return Err(parse_error(format!(
                    "io.stat counter {key} is duplicated for {device}"
                )));
            }
        }

        add_counter(
            &mut total.read_bytes,
            required_counter(&counters, "rbytes", "io.stat")?,
            "rbytes",
        )?;
        add_counter(
            &mut total.write_bytes,
            required_counter(&counters, "wbytes", "io.stat")?,
            "wbytes",
        )?;
        add_counter(
            &mut total.read_ops,
            required_counter(&counters, "rios", "io.stat")?,
            "rios",
        )?;
        add_counter(
            &mut total.write_ops,
            required_counter(&counters, "wios", "io.stat")?,
            "wios",
        )?;
        add_counter(
            &mut total.discard_bytes,
            counters.get("dbytes").copied().unwrap_or(0),
            "dbytes",
        )?;
        add_counter(
            &mut total.discard_ops,
            counters.get("dios").copied().unwrap_or(0),
            "dios",
        )?;
    }
    Ok(total)
}
