//! Behavior tests exercise real Attempt-state contracts, not historic source file layout.
use super::super::{AttemptState, AttemptTerminationIntent, JobResolution, RuntimeErrorCode};
use super::AttemptLifecycleContract;

#[test]
fn initial_attempt_generation_and_default_intent_are_stable() {
    assert_eq!(AttemptLifecycleContract::INITIAL_ATTEMPT_NUMBER, 1);
    assert_eq!(
        AttemptLifecycleContract::initial_state(),
        AttemptState::Accepted
    );
    assert_eq!(
        AttemptLifecycleContract::initial_termination_intent(),
        AttemptTerminationIntent::Natural
    );
}

#[test]
fn state_transition_matrix_preserves_terminal_absorption_and_recovery_paths() {
    assert!(AttemptLifecycleContract::can_transition(
        AttemptState::Accepted,
        AttemptState::Starting
    ));
    assert!(AttemptLifecycleContract::can_transition(
        AttemptState::Running,
        AttemptState::Stopping
    ));
    assert!(AttemptLifecycleContract::can_transition(
        AttemptState::Recovering,
        AttemptState::Running
    ));
    assert!(!AttemptLifecycleContract::can_transition(
        AttemptState::Accepted,
        AttemptState::Running
    ));
    for terminal in [
        AttemptState::Succeeded,
        AttemptState::Failed,
        AttemptState::TimedOut,
        AttemptState::Cancelled,
        AttemptState::Lost,
        AttemptState::Orphaned,
    ] {
        assert!(AttemptLifecycleContract::is_terminal(terminal));
        assert!(!AttemptLifecycleContract::can_transition(
            terminal,
            AttemptState::Running
        ));
    }
}

#[test]
fn durable_cancel_and_deadline_edges_are_present_in_attempt_transition_graph() {
    // Registry commits these controls while Starting; the formal graph
    // must recognize their target without assuming Running happened.
    for state in [
        AttemptState::Accepted,
        AttemptState::Starting,
        AttemptState::Running,
        AttemptState::Stopping,
        AttemptState::Recovering,
        AttemptState::Succeeded,
        AttemptState::Failed,
        AttemptState::TimedOut,
        AttemptState::Cancelled,
        AttemptState::Lost,
        AttemptState::Orphaned,
    ] {
        if let Some(target) = AttemptLifecycleContract::cancel_target_state(state) {
            if target != state {
                assert!(
                    AttemptLifecycleContract::can_transition(state, target),
                    "durable cancellation edge {state:?} -> {target:?} rejected"
                );
            }
        }
        if AttemptLifecycleContract::deadline_request_is_admissible(state)
            && state != AttemptState::Stopping
        {
            assert!(
                AttemptLifecycleContract::can_transition(state, AttemptState::Stopping),
                "durable deadline edge {state:?} -> Stopping rejected"
            );
        }
    }
}

#[test]
fn termination_intent_and_control_targets_preserve_first_committed_control_intent() {
    assert!(AttemptLifecycleContract::deadline_request_is_replay(
        AttemptState::Running,
        AttemptTerminationIntent::StopRequested
    ));
    assert!(AttemptLifecycleContract::deadline_request_is_replay(
        AttemptState::Running,
        AttemptTerminationIntent::DeadlineExceeded
    ));
    assert!(!AttemptLifecycleContract::deadline_request_is_replay(
        AttemptState::Running,
        AttemptTerminationIntent::Natural
    ));
    assert!(AttemptLifecycleContract::deadline_request_is_admissible(
        AttemptState::Stopping
    ));
    assert!(!AttemptLifecycleContract::deadline_request_is_admissible(
        AttemptState::Accepted
    ));
    assert_eq!(
        AttemptLifecycleContract::cancel_target_state(AttemptState::Accepted),
        Some(AttemptState::Cancelled)
    );
    assert_eq!(
        AttemptLifecycleContract::cancel_target_state(AttemptState::Running),
        Some(AttemptState::Stopping)
    );
    assert_eq!(
        AttemptLifecycleContract::cancel_target_state(AttemptState::Stopping),
        Some(AttemptState::Stopping)
    );
}

#[test]
fn physical_owner_binding_preserves_stopping_and_replay_identity() {
    assert_eq!(
        AttemptLifecycleContract::runner_identity_bound_state(AttemptState::Starting),
        Some(AttemptState::Running)
    );
    assert_eq!(
        AttemptLifecycleContract::runner_identity_bound_state(AttemptState::Stopping),
        None
    );
    assert_eq!(
        AttemptLifecycleContract::supervisor_owner_bound_state(AttemptState::Stopping),
        Some(AttemptState::Stopping)
    );
    assert!(AttemptLifecycleContract::physical_owner_replay_matches(
        AttemptState::Running,
        "sha256:owner",
        "sha256:owner",
        Some("sha256:start"),
        "sha256:start",
    ));
    assert!(!AttemptLifecycleContract::physical_owner_replay_matches(
        AttemptState::Running,
        "sha256:owner-a",
        "sha256:owner-b",
        Some("sha256:start"),
        "sha256:start",
    ));
}

#[test]
fn terminal_resolution_is_total_only_for_terminal_attempt_states() {
    let mappings = [
        (AttemptState::Succeeded, JobResolution::Succeeded),
        (AttemptState::Failed, JobResolution::Failed),
        (AttemptState::TimedOut, JobResolution::TimedOut),
        (AttemptState::Cancelled, JobResolution::Cancelled),
        (AttemptState::Lost, JobResolution::Lost),
        (AttemptState::Orphaned, JobResolution::Orphaned),
    ];
    for (state, resolution) in mappings {
        assert_eq!(
            AttemptLifecycleContract::resolution(state),
            Some(resolution)
        );
        assert_eq!(
            AttemptLifecycleContract::require_terminal_resolution(state).unwrap(),
            resolution
        );
    }
    for state in [
        AttemptState::Accepted,
        AttemptState::Starting,
        AttemptState::Running,
        AttemptState::Stopping,
        AttemptState::Recovering,
    ] {
        assert_eq!(AttemptLifecycleContract::resolution(state), None);
        let error = AttemptLifecycleContract::require_terminal_resolution(state).unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
        assert_eq!(error.field.as_deref(), Some("state"));
    }
}

#[test]
fn terminal_evidence_requires_result_finish_matching_resolution_and_no_current_attempt() {
    assert!(AttemptLifecycleContract::terminal_evidence_complete(
        AttemptState::Succeeded,
        true,
        true,
        Some(JobResolution::Succeeded),
        false,
    ));
    assert!(AttemptLifecycleContract::terminal_evidence_complete(
        AttemptState::Orphaned,
        true,
        true,
        Some(JobResolution::Orphaned),
        false,
    ));

    for complete in [
        AttemptLifecycleContract::terminal_evidence_complete(
            AttemptState::Running,
            true,
            true,
            None,
            false,
        ),
        AttemptLifecycleContract::terminal_evidence_complete(
            AttemptState::Succeeded,
            false,
            true,
            Some(JobResolution::Succeeded),
            false,
        ),
        AttemptLifecycleContract::terminal_evidence_complete(
            AttemptState::Succeeded,
            true,
            false,
            Some(JobResolution::Succeeded),
            false,
        ),
        AttemptLifecycleContract::terminal_evidence_complete(
            AttemptState::Succeeded,
            true,
            true,
            Some(JobResolution::Failed),
            false,
        ),
        AttemptLifecycleContract::terminal_evidence_complete(
            AttemptState::Succeeded,
            true,
            true,
            Some(JobResolution::Succeeded),
            true,
        ),
    ] {
        assert!(!complete);
    }
}
