//! Pure native-stop admission classification.
//!
//! systemd/cgroup owns process existence. This function decides only whether
//! an independently observed kernel state is sufficient to record an UNKNOWN
//! execution outcome (the durable status `lost`). It never sends signals,
//! releases capacity directly, or claims an external effect succeeded.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(super) enum NativeStopDecision {
    Hold,
    CommitLost,
}

/// Result-free terminalization is permitted only when the exact attempt has
/// a verified Runner start and its native Unit has no pending systemd job,
/// is not active, and its bound cgroup is observed unpopulated or positively
/// observed removed from the mounted cgroup2 hierarchy.
///
/// `None` alone is unknown and MUST NOT become `Some(false)`. Disappearance is
/// separate positive evidence, never inferred from an I/O or permission error.
pub(super) fn decide_native_stop(
    unit_active: bool,
    unit_pending: bool,
    runner_start_verified: bool,
    cgroup_populated: Option<bool>,
    cgroup_removed: bool,
) -> NativeStopDecision {
    match (
        unit_active,
        unit_pending,
        runner_start_verified,
        cgroup_populated,
        cgroup_removed,
    ) {
        (false, false, true, Some(false), _) | (false, false, true, None, true) => {
            NativeStopDecision::CommitLost
        }
        _ => NativeStopDecision::Hold,
    }
}

#[cfg(kani)]
mod proof {
    use super::{decide_native_stop, NativeStopDecision};

    /// Implementation-refinement witness for all finite decision inputs.
    /// This proves the *pure production classifier*, NOT that systemd, cgroup,
    /// PostgreSQL, or a caller supplied truthful physical observations.
    #[kani::proof]
    fn no_lost_resolution_without_complete_native_evidence() {
        let unit_active: bool = kani::any();
        let unit_pending: bool = kani::any();
        let runner_start_verified: bool = kani::any();
        let known_population: bool = kani::any();
        let populated: bool = kani::any();
        let removed: bool = kani::any();
        let cgroup_populated = if known_population {
            Some(populated)
        } else {
            None
        };

        let observed = decide_native_stop(
            unit_active,
            unit_pending,
            runner_start_verified,
            cgroup_populated,
            removed,
        );
        let spec = !unit_active
            && !unit_pending
            && runner_start_verified
            && ((known_population && !populated) || (!known_population && removed));

        assert_eq!(observed == NativeStopDecision::CommitLost, spec);
        kani::cover!(spec);
        kani::cover!(!known_population && !removed);
        kani::cover!(!known_population && removed);
        kani::cover!(unit_active);
        kani::cover!(unit_pending);
    }
}
