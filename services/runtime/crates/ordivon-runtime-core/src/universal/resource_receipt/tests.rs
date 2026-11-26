//! Original cgroup v2 observable behavior, not source layout or file path assertions.
use super::{
    parse_cgroup_cpu_stat, parse_cgroup_io_stat, parse_cgroup_memory_events, UniversalExecErrorCode,
};

#[test]
fn io_multiple_devices_sum_without_dropping_operations_or_discards() {
    let value = parse_cgroup_io_stat(
        "8:0 rbytes=13 wbytes=4 rios=2 wios=1 dbytes=7 dios=3\n\
         8:1 rbytes=2 wbytes=9 rios=4 wios=5 dbytes=8 dios=6",
    )
    .expect("two actual cgroup device rows");
    assert_eq!(value.read_bytes, 15);
    assert_eq!(value.write_bytes, 13);
    assert_eq!(value.read_ops, 6);
    assert_eq!(value.write_ops, 6);
    assert_eq!(value.discard_bytes, 15);
    assert_eq!(value.discard_ops, 9);
}

#[test]
fn duplicate_cgroup_cpu_counters_are_rejected_not_silently_overwritten() {
    let invalid = "usage_usec 7\nuser_usec 3\nsystem_usec 4\nusage_usec 0\n";
    let error = parse_cgroup_cpu_stat(invalid).expect_err("duplicate usage must be rejected");
    assert_eq!(error.code, UniversalExecErrorCode::InvalidRequest);
    assert!(error.message.contains("duplicated"));
}

#[test]
fn missing_memory_oom_kill_is_inconclusive_not_zero() {
    let invalid = "low 1\nhigh 2\nmax 3\noom 4\n";
    let error = parse_cgroup_memory_events(invalid).expect_err("missing key is unknown");
    assert_eq!(error.code, UniversalExecErrorCode::InvalidRequest);
    assert!(error.message.contains("oom_kill"));
}

#[test]
fn io_device_aggregation_overflow_is_rejected() {
    let invalid = format!(
        "8:0 rbytes={} wbytes=0 rios=0 wios=0\n8:1 rbytes=1 wbytes=0 rios=0 wios=0",
        u64::MAX
    );
    let error = parse_cgroup_io_stat(&invalid).expect_err("sum must not wrap");
    assert_eq!(error.code, UniversalExecErrorCode::InvalidRequest);
    assert!(error.message.contains("overflowed"));
}

#[test]
fn valid_cpu_and_memory_counters_keep_exact_kernel_values() {
    let cpu = parse_cgroup_cpu_stat("usage_usec 20\nuser_usec 14\nsystem_usec 6\n")
        .expect("complete cpu.stat");
    assert_eq!(cpu.usage_usec, 20);
    assert_eq!(cpu.user_usec, 14);
    assert_eq!(cpu.system_usec, 6);
    let mem = parse_cgroup_memory_events("low 1\nhigh 2\nmax 3\noom 4\noom_kill 5\n")
        .expect("complete memory.events");
    assert_eq!(mem.oom_kill, 5);
    assert_eq!(mem.max, 3);
}
