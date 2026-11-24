//! Original Kani proof for native stop decision, not substitute for OS/PG testing.
use super::super::platform::CgroupPopulation;
use super::{decide_native_stop, NativeStopDecision};

/// Exhaustively checks the actual source decision against an independent
/// propositional specification. Native observation truth/PG effect still
/// require their own physical acceptance and do not follow from this proof.
#[kani::proof]
fn native_stop_releases_only_with_qualified_os_evidence() {
    let unit_active: bool = kani::any();
    let unit_pending: bool = kani::any();
    let unit_not_found: bool = kani::any();
    let unit_failed_and_bound: bool = kani::any();
    let runner_start_verified: bool = kani::any();
    let tag: u8 = kani::any();
    kani::assume(tag < 4);
    let cgroup_population = match tag {
        0 => CgroupPopulation::Populated,
        1 => CgroupPopulation::Unpopulated,
        2 => CgroupPopulation::Removed,
        _ => CgroupPopulation::Unknown,
    };
    let actual = decide_native_stop(
        unit_active,
        unit_pending,
        unit_not_found,
        unit_failed_and_bound,
        runner_start_verified,
        cgroup_population,
    );
    let spec = !unit_active
        && !unit_pending
        && runner_start_verified
        && (tag == 1 || (tag == 2 && (unit_not_found || unit_failed_and_bound)));
    assert_eq!(actual == NativeStopDecision::CommitLost, spec);
    kani::cover!(spec && tag == 1);
    kani::cover!(spec && tag == 2 && !unit_not_found && unit_failed_and_bound);
    kani::cover!(spec && tag == 2 && unit_not_found);
    kani::cover!(tag == 3);
    kani::cover!(unit_active);
    kani::cover!(unit_pending);
    kani::cover!(!runner_start_verified);
}
