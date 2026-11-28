//! Kani symbolic checks of original pure Rust reservation transitions.
use super::super::{
    job_attempt_state::AttemptLifecycleContract, AttemptState, JobResolution, ReservationState,
};
use super::ReservationContract;

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
    assert!(
        ReservationContract::terminal_target_with_evidence(state, true, true, supplied, false)
            .is_err()
    );
}
