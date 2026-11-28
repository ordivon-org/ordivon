//! Symbolic checks target actual Rust transitions; physical PG/OS proof is separate.
use super::AttemptLifecycleContract;
use crate::{AttemptState, JobResolution};

// Map a symbolic, bounded identifier to every declared AttemptState
// variant. Every ID in 0..11 denotes exactly one existing state.
fn state_from_id(id: u8) -> AttemptState {
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

#[kani::proof]
fn proof_actual_attempt_terminal_absorbing_and_resolution_equivalence() {
    let current_id: u8 = kani::any();
    let next_id: u8 = kani::any();
    kani::assume(current_id < 11 && next_id < 11);
    let current = state_from_id(current_id);
    let next = state_from_id(next_id);
    let terminal = AttemptLifecycleContract::is_terminal(current);
    // Both functions are the actual Rust implementation, not a copied
    // abstract state machine. All 121 state pairs are symbolically covered.
    assert_eq!(
        terminal,
        AttemptLifecycleContract::resolution(current).is_some()
    );
    if terminal {
        assert!(!AttemptLifecycleContract::can_transition(current, next));
        assert!(AttemptLifecycleContract::cancel_target_state(current).is_none());
        assert!(!AttemptLifecycleContract::deadline_request_is_admissible(
            current
        ));
    }
    if AttemptLifecycleContract::can_transition(current, next) {
        assert!(!terminal);
    }
    assert_eq!(
        AttemptLifecycleContract::deadline_request_is_admissible(current),
        AttemptLifecycleContract::stopping_target_state(current).is_some()
    );
    if let Some(target) = AttemptLifecycleContract::stopping_target_state(current) {
        assert_eq!(target, AttemptState::Stopping);
    }
}

#[kani::proof]
fn proof_actual_attempt_cancel_is_transition_or_stopping_replay() {
    let current_id: u8 = kani::any();
    kani::assume(current_id < 11);
    let current = state_from_id(current_id);
    if let Some(target) = AttemptLifecycleContract::cancel_target_state(current) {
        if current == AttemptState::Stopping {
            // Idempotent cancel intent is a replay, not a state transition.
            assert_eq!(target, AttemptState::Stopping);
            assert!(!AttemptLifecycleContract::can_transition(current, target));
        } else {
            assert!(AttemptLifecycleContract::can_transition(current, target));
        }
    } else {
        assert!(AttemptLifecycleContract::is_terminal(current));
    }
}

fn resolution_from_id(id: u8) -> Option<JobResolution> {
    match id {
        0 => None,
        1 => Some(JobResolution::Succeeded),
        2 => Some(JobResolution::Failed),
        3 => Some(JobResolution::TimedOut),
        4 => Some(JobResolution::Cancelled),
        5 => Some(JobResolution::Lost),
        6 => Some(JobResolution::Orphaned),
        _ => unreachable!(),
    }
}

#[kani::proof]
fn proof_terminal_evidence_is_exact_conjunction() {
    let state_id: u8 = kani::any();
    let resolution_id: u8 = kani::any();
    let result_digest_present: bool = kani::any();
    let finished_at_present: bool = kani::any();
    let current_attempt_present: bool = kani::any();
    kani::assume(state_id < 11 && resolution_id < 7);

    let state = state_from_id(state_id);
    let resolution = resolution_from_id(resolution_id);
    let expected = AttemptLifecycleContract::is_terminal(state)
        && result_digest_present
        && finished_at_present
        && resolution == AttemptLifecycleContract::resolution(state)
        && !current_attempt_present;

    assert_eq!(
        AttemptLifecycleContract::terminal_evidence_complete(
            state,
            result_digest_present,
            finished_at_present,
            resolution,
            current_attempt_present,
        ),
        expected
    );
}
