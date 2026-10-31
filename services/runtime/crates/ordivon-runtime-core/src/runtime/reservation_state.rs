use super::{
    job_attempt_state::AttemptLifecycleContract, AttemptState, ReservationState, RuntimeError,
    RuntimeErrorCode, RuntimeResult,
};

pub(crate) struct ReservationContract;

impl ReservationContract {
    pub(crate) fn initial_state() -> ReservationState {
        ReservationState::Active
    }

    #[cfg(any(test, feature = "operator-tools", kani))]
    pub(crate) fn holds_capacity(state: ReservationState) -> bool {
        matches!(
            state,
            ReservationState::Active | ReservationState::HeldOrphaned
        )
    }

    pub(crate) fn capacity_exhausted(active: u32, limit: u32) -> bool {
        active >= limit
    }

    #[cfg(any(test, feature = "operator-tools", kani))]
    pub(crate) fn can_transition(state: ReservationState, next: ReservationState) -> bool {
        match state {
            ReservationState::Active => {
                matches!(
                    next,
                    ReservationState::HeldOrphaned | ReservationState::Released
                )
            }
            ReservationState::HeldOrphaned => {
                matches!(
                    next,
                    ReservationState::HeldOrphaned | ReservationState::Released
                )
            }
            ReservationState::Released => next == ReservationState::Released,
        }
    }

    pub(crate) fn terminal_target(state: AttemptState) -> RuntimeResult<ReservationState> {
        if !AttemptLifecycleContract::is_terminal(state) {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "Attempt is not terminal while repairing terminal reservation",
                Some("attemptId"),
                false,
            ));
        }
        if state == AttemptState::Orphaned {
            Ok(ReservationState::HeldOrphaned)
        } else {
            Ok(ReservationState::Released)
        }
    }

    pub(crate) fn terminal_target_with_evidence(
        state: AttemptState,
        result_digest_present: bool,
        finished_at_present: bool,
        job_resolution: Option<super::JobResolution>,
        current_attempt_present: bool,
    ) -> RuntimeResult<ReservationState> {
        let target = Self::terminal_target(state)?;
        if !AttemptLifecycleContract::terminal_evidence_complete(
            state,
            result_digest_present,
            finished_at_present,
            job_resolution,
            current_attempt_present,
        ) {
            return Err(RuntimeError::new(
                RuntimeErrorCode::ReconciliationRequired,
                "terminal Attempt lacks complete result, Job resolution, or current-Attempt evidence",
                Some("attemptId"),
                false,
            ));
        }
        Ok(target)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::runtime::JobResolution;

    #[test]
    fn active_and_held_orphaned_are_the_only_capacity_holders() {
        assert!(ReservationContract::holds_capacity(
            ReservationState::Active
        ));
        assert!(ReservationContract::holds_capacity(
            ReservationState::HeldOrphaned
        ));
        assert!(!ReservationContract::holds_capacity(
            ReservationState::Released
        ));
    }

    #[test]
    fn initial_reservation_is_active_and_capacity_is_strictly_bounded() {
        assert_eq!(
            ReservationContract::initial_state(),
            ReservationState::Active
        );
        assert!(!ReservationContract::capacity_exhausted(0, 1));
        assert!(ReservationContract::capacity_exhausted(1, 1));
        assert!(ReservationContract::capacity_exhausted(2, 1));
    }

    #[test]
    fn hold_and_release_transitions_preserve_replay_without_reopening_released_capacity() {
        assert!(ReservationContract::can_transition(
            ReservationState::Active,
            ReservationState::HeldOrphaned
        ));
        assert!(ReservationContract::can_transition(
            ReservationState::Active,
            ReservationState::Released
        ));
        assert!(ReservationContract::can_transition(
            ReservationState::HeldOrphaned,
            ReservationState::HeldOrphaned
        ));
        assert!(ReservationContract::can_transition(
            ReservationState::HeldOrphaned,
            ReservationState::Released
        ));
        assert!(ReservationContract::can_transition(
            ReservationState::Released,
            ReservationState::Released
        ));
        assert!(!ReservationContract::can_transition(
            ReservationState::Released,
            ReservationState::Active
        ));
        assert!(!ReservationContract::can_transition(
            ReservationState::Released,
            ReservationState::HeldOrphaned
        ));
    }

    #[test]
    fn terminal_attempts_map_to_held_or_released_capacity_without_queue_semantics() {
        assert_eq!(
            ReservationContract::terminal_target(AttemptState::Orphaned).unwrap(),
            ReservationState::HeldOrphaned
        );
        for state in [
            AttemptState::Succeeded,
            AttemptState::Failed,
            AttemptState::TimedOut,
            AttemptState::Cancelled,
            AttemptState::Lost,
        ] {
            assert_eq!(
                ReservationContract::terminal_target(state).unwrap(),
                ReservationState::Released
            );
        }
        let error = ReservationContract::terminal_target(AttemptState::Running).unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::ReconciliationRequired);
    }

    #[test]
    fn terminal_capacity_target_requires_complete_job_and_attempt_evidence() {
        assert_eq!(
            ReservationContract::terminal_target_with_evidence(
                AttemptState::Succeeded,
                true,
                true,
                Some(JobResolution::Succeeded),
                false,
            )
            .unwrap(),
            ReservationState::Released
        );
        assert_eq!(
            ReservationContract::terminal_target_with_evidence(
                AttemptState::Orphaned,
                true,
                true,
                Some(JobResolution::Orphaned),
                false,
            )
            .unwrap(),
            ReservationState::HeldOrphaned
        );
        for incomplete in [
            (false, true, Some(JobResolution::Succeeded), false),
            (true, false, Some(JobResolution::Succeeded), false),
            (true, true, None, false),
            (true, true, Some(JobResolution::Succeeded), true),
        ] {
            let error = ReservationContract::terminal_target_with_evidence(
                AttemptState::Succeeded,
                incomplete.0,
                incomplete.1,
                incomplete.2,
                incomplete.3,
            )
            .unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::ReconciliationRequired);
        }
    }
}

// Formal verification of the REAL Runtime reservation/Attempt composition.
// This binds the production ReservationContract to the same AttemptLifecycleContract
// already used by Registry recovery. It does not prove SQL transaction atomicity,
// global capacity accounting, installed binaries, provider liveness, or fairness.
#[cfg(kani)]
mod kani_reservation_contract_proofs {
    use super::{AttemptLifecycleContract, AttemptState, ReservationContract, ReservationState};
    use crate::runtime::JobResolution;

    fn attempt_state_from_id(id: u8) -> AttemptState {
        match id {
            0 => AttemptState::Accepted,
            1 => AttemptState::Starting,
            2 => AttemptState::Running,
            3 => AttemptState::Stopping,
            4 => AttemptState::Recovering,
            5 => AttemptState::Succeeded,
            6 => AttemptState::Failed,
            7 => AttemptState::TimedOut,
            8 => AttemptState::Cancelled,
            9 => AttemptState::Lost,
            10 => AttemptState::Orphaned,
            _ => unreachable!(),
        }
    }

    fn resolution_from_id(id: u8) -> JobResolution {
        match id {
            0 => JobResolution::Succeeded,
            1 => JobResolution::Failed,
            2 => JobResolution::TimedOut,
            3 => JobResolution::Cancelled,
            4 => JobResolution::Lost,
            5 => JobResolution::Orphaned,
            _ => unreachable!(),
        }
    }

    #[kani::proof]
    fn proof_actual_terminal_reservation_target_preserves_held_orphan_fence() {
        let state_id: u8 = kani::any();
        kani::assume(state_id < 11);
        let state = attempt_state_from_id(state_id);
        let result = ReservationContract::terminal_target_with_evidence(
            state,
            true,
            true,
            AttemptLifecycleContract::resolution(state),
            false,
        );

        if AttemptLifecycleContract::is_terminal(state) {
            let target = result.expect("complete terminal evidence must yield a capacity target");
            assert_eq!(
                target == ReservationState::HeldOrphaned,
                state == AttemptState::Orphaned
            );
            assert_eq!(
                ReservationContract::holds_capacity(target),
                state == AttemptState::Orphaned
            );
            assert!(ReservationContract::can_transition(
                ReservationState::Active,
                target
            ));
            assert!(ReservationContract::can_transition(
                ReservationState::HeldOrphaned,
                target
            ));
            if target == ReservationState::HeldOrphaned {
                assert!(!ReservationContract::can_transition(
                    ReservationState::Released,
                    target
                ));
            }
        } else {
            assert!(result.is_err());
        }
    }

    #[kani::proof]
    fn proof_actual_terminal_reservation_target_fails_closed_on_incomplete_evidence() {
        let state_id: u8 = kani::any();
        let has_result: bool = kani::any();
        let has_finished_at: bool = kani::any();
        let current_attempt_present: bool = kani::any();
        kani::assume(state_id < 11);
        let state = attempt_state_from_id(state_id);
        let expected_resolution = AttemptLifecycleContract::resolution(state);
        let result = ReservationContract::terminal_target_with_evidence(
            state,
            has_result,
            has_finished_at,
            expected_resolution,
            current_attempt_present,
        );
        let evidence_complete = AttemptLifecycleContract::is_terminal(state)
            && has_result
            && has_finished_at
            && !current_attempt_present;
        assert_eq!(result.is_ok(), evidence_complete);
    }

    #[kani::proof]
    fn proof_actual_terminal_reservation_target_rejects_mismatched_job_resolution() {
        let state_id: u8 = kani::any();
        let resolution_id: u8 = kani::any();
        kani::assume(state_id < 11 && resolution_id < 6);
        let state = attempt_state_from_id(state_id);
        let supplied = Some(resolution_from_id(resolution_id));
        let expected = AttemptLifecycleContract::resolution(state);
        kani::assume(AttemptLifecycleContract::is_terminal(state));
        kani::assume(supplied != expected);
        assert!(ReservationContract::terminal_target_with_evidence(
            state, true, true, supplied, false
        )
        .is_err());
    }
}
