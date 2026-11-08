//! Pure, exhaustively checkable native-stop classification.
//!
//! Linux systemd/cgroup owns process existence; this production function
//! classifies verified observations. It never issues signals or claims that
//! opaque external side effects succeeded.

use super::platform::CgroupPopulation;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) enum NativeStopDecision {
    Hold,
    CommitLost,
}

/// The cgroup v2 kernel allows removal of a cgroup only after it has become
/// empty. With verified Runner start, a collected/not-found systemd transient
/// unit AND its removed cgroup are a native terminal witness, distinct from
/// an unavailable cgroup.events read. A still-loaded unit requires an observed
/// recursive `populated=0` state instead.
///
/// This does not infer external effect success or allow a replacement Attempt.
pub(super) fn decide_native_stop(
    unit_active: bool,
    unit_pending: bool,
    unit_not_found: bool,
    runner_start_verified: bool,
    population: CgroupPopulation,
) -> NativeStopDecision {
    if unit_active || unit_pending || !runner_start_verified {
        return NativeStopDecision::Hold;
    }
    match population {
        CgroupPopulation::Unpopulated => NativeStopDecision::CommitLost,
        CgroupPopulation::Removed if unit_not_found => NativeStopDecision::CommitLost,
        CgroupPopulation::Populated | CgroupPopulation::Unknown | CgroupPopulation::Removed => {
            NativeStopDecision::Hold
        }
    }
}

#[cfg(kani)]
mod proof {
    use super::{decide_native_stop, CgroupPopulation, NativeStopDecision};

    /// Exhaustively checks the actual source decision against an independent
    /// propositional specification. Native observation truth/PG effect still
    /// require their own physical acceptance and do not follow from this proof.
    #[kani::proof]
    fn native_stop_releases_only_with_qualified_os_evidence() {
        let unit_active: bool = kani::any();
        let unit_pending: bool = kani::any();
        let unit_not_found: bool = kani::any();
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
            runner_start_verified,
            cgroup_population,
        );
        let spec = !unit_active
            && !unit_pending
            && runner_start_verified
            && (tag == 1 || (tag == 2 && unit_not_found));
        assert_eq!(actual == NativeStopDecision::CommitLost, spec);
        kani::cover!(spec && tag == 1);
        kani::cover!(spec && tag == 2);
        kani::cover!(tag == 3);
        kani::cover!(unit_active);
        kani::cover!(unit_pending);
        kani::cover!(!runner_start_verified);
    }
}
