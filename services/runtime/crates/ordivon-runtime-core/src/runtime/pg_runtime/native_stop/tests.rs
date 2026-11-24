//! Original real OS stop proof obligations: correct identity, no unknown->false collapse.
use super::super::platform::CgroupPopulation;
use super::{decide_native_stop, failed_unit_matches_runner, NativeStopDecision};

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

#[test]
fn unresolved_cgroup_never_allows_lost_without_verified_runner_birth() {
    for cgroup in [
        CgroupPopulation::Unpopulated,
        CgroupPopulation::Removed,
        CgroupPopulation::Unknown,
        CgroupPopulation::Populated,
    ] {
        assert_eq!(
            decide_native_stop(false, false, true, true, false, cgroup),
            NativeStopDecision::Hold
        );
    }
}
