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
/// an unavailable cgroup.events read. A failed-but-loaded unit with the
/// *same verified Runner invocation*, no main PID and a removed cgroup is
/// also terminal: CollectMode=inactive deliberately preserves failed units
/// until after PostgreSQL commits the terminal result. Other loaded units
/// still require an observed recursive `populated=0` state.
///
/// This does not infer external effect success or allow a replacement Attempt.
pub(super) fn failed_unit_matches_runner(
    load_state: Option<&str>,
    active_state: Option<&str>,
    invocation_id: Option<&str>,
    expected_invocation_id: &str,
    main_pid: Option<&str>,
) -> bool {
    !expected_invocation_id.is_empty()
        && load_state == Some("loaded")
        && active_state == Some("failed")
        && invocation_id == Some(expected_invocation_id)
        && main_pid == Some("0")
}

pub(super) fn decide_native_stop(
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

#[cfg(test)]
mod tests {
    use super::{
        decide_native_stop, failed_unit_matches_runner, CgroupPopulation, NativeStopDecision,
    };

    #[test]
    fn failed_retained_transient_requires_exact_positive_runner_identity() {
        assert!(failed_unit_matches_runner(
            Some("loaded"),
            Some("failed"),
            Some("invocation-a"),
            "invocation-a",
            Some("0"),
        ));
        for (load, active, observed, expected, main_pid) in [
            (
                Some("loaded"),
                Some("failed"),
                None,
                "invocation-a",
                Some("0"),
            ),
            (
                Some("loaded"),
                Some("failed"),
                Some("invocation-b"),
                "invocation-a",
                Some("0"),
            ),
            (
                Some("loaded"),
                Some("failed"),
                Some("invocation-a"),
                "",
                Some("0"),
            ),
            (
                Some("loaded"),
                Some("failed"),
                Some("invocation-a"),
                "invocation-a",
                Some("42"),
            ),
            (
                Some("loaded"),
                Some("inactive"),
                Some("invocation-a"),
                "invocation-a",
                Some("0"),
            ),
            (
                Some("not-found"),
                Some("failed"),
                Some("invocation-a"),
                "invocation-a",
                Some("0"),
            ),
        ] {
            assert!(!failed_unit_matches_runner(
                load, active, observed, expected, main_pid
            ));
        }
    }

    #[test]
    fn removed_failed_bound_cgroup_converges_without_resetting_systemd_before_pg_commit() {
        let lost = NativeStopDecision::CommitLost;
        let hold = NativeStopDecision::Hold;
        assert_eq!(
            decide_native_stop(false, false, false, true, true, CgroupPopulation::Removed),
            lost
        );
        assert_eq!(
            decide_native_stop(false, false, false, false, true, CgroupPopulation::Removed),
            hold
        );
        assert_eq!(
            decide_native_stop(false, false, true, false, true, CgroupPopulation::Removed),
            lost
        );
        assert_eq!(
            decide_native_stop(
                false,
                false,
                false,
                true,
                true,
                CgroupPopulation::Unpopulated
            ),
            lost
        );
        for populated in [CgroupPopulation::Populated, CgroupPopulation::Unknown] {
            assert_eq!(
                decide_native_stop(false, false, false, true, true, populated),
                hold
            );
        }
        assert_eq!(
            decide_native_stop(true, false, false, true, true, CgroupPopulation::Removed),
            hold
        );
        assert_eq!(
            decide_native_stop(false, true, false, true, true, CgroupPopulation::Removed),
            hold
        );
        assert_eq!(
            decide_native_stop(false, false, false, true, false, CgroupPopulation::Removed),
            hold
        );
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
}
