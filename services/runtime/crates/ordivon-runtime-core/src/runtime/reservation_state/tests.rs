//! Original capacity state and real attempt-resolution semantics, no source-file assertions.
use super::super::{AttemptState, JobResolution, ReservationState, RuntimeErrorCode};
use super::ReservationContract;

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
