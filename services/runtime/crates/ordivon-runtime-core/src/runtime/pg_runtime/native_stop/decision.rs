//! Kernel cgroup population is original native evidence, not a source of external effect success.
use super::super::platform::CgroupPopulation;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(in crate::runtime::pg_runtime) enum NativeStopDecision {
    Hold,
    CommitLost,
}

pub(in crate::runtime::pg_runtime) fn decide_native_stop(
    unit_active: bool,
    unit_pending: bool,
    unit_not_found: bool,
    unit_failed_and_bound: bool,
    runner_start_verified: bool,
    population: CgroupPopulation,
) -> NativeStopDecision {
    if unit_active || unit_pending || !runner_start_verified {
        return NativeStopDecision::Hold;
    }
    match population {
        CgroupPopulation::Unpopulated => NativeStopDecision::CommitLost,
        CgroupPopulation::Removed if unit_not_found || unit_failed_and_bound => {
            NativeStopDecision::CommitLost
        }
        CgroupPopulation::Populated | CgroupPopulation::Unknown | CgroupPopulation::Removed => {
            NativeStopDecision::Hold
        }
    }
}
