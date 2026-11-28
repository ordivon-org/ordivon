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
    for state in OL_ALL_ATTEMPT_STATES {
        let (runner, supervisor) = match state {
            AttemptState::Starting | AttemptState::Recovering => {
                (Some(AttemptState::Running), Some(AttemptState::Running))
            }
            AttemptState::Stopping => (None, Some(AttemptState::Stopping)),
            _ => (None, None),
        };
        assert_eq!(
            AttemptLifecycleContract::runner_identity_bound_state(state),
            runner
        );
        assert_eq!(
            AttemptLifecycleContract::supervisor_owner_bound_state(state),
            supervisor
        );
    }
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
        assert!(state.is_terminal());
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
        assert!(!state.is_terminal());
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

const OL_ALL_ATTEMPT_STATES: [AttemptState; 11] = [
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
];

fn ol_observation_class(state: AttemptState) -> u8 {
    match state {
        AttemptState::Accepted => 0,
        AttemptState::Starting | AttemptState::Recovering => 1,
        AttemptState::Running => 2,
        AttemptState::Stopping => 3,
        AttemptState::Succeeded => 4,
        AttemptState::Failed => 5,
        AttemptState::TimedOut => 6,
        AttemptState::Cancelled => 7,
        AttemptState::Lost => 8,
        AttemptState::Orphaned => 9,
    }
}

fn ol_push_unique(pairs: &mut Vec<(u8, u8)>, pair: (u8, u8)) {
    if !pairs.contains(&pair) {
        pairs.push(pair);
    }
}

fn ol_projected_relation(target: AttemptState) -> Vec<(u8, u8)> {
    let mut relation = Vec::new();
    for source in OL_ALL_ATTEMPT_STATES {
        if AttemptLifecycleContract::can_transition(source, target) {
            ol_push_unique(
                &mut relation,
                (ol_observation_class(source), ol_observation_class(target)),
            );
        }
    }
    relation
}

fn ol_projected_concrete_composition(first: AttemptState, second: AttemptState) -> Vec<(u8, u8)> {
    let mut relation = Vec::new();
    if AttemptLifecycleContract::can_transition(first, second) {
        for source in OL_ALL_ATTEMPT_STATES {
            if AttemptLifecycleContract::can_transition(source, first) {
                ol_push_unique(
                    &mut relation,
                    (ol_observation_class(source), ol_observation_class(second)),
                );
            }
        }
    }
    relation
}

fn ol_compose(left: &[(u8, u8)], right: &[(u8, u8)]) -> Vec<(u8, u8)> {
    let mut relation = Vec::new();
    for &(source, middle_left) in left {
        for &(middle_right, target) in right {
            if middle_left == middle_right {
                ol_push_unique(&mut relation, (source, target));
            }
        }
    }
    relation
}

#[test]
fn all_declared_attempt_states_are_reachable_in_the_unguarded_transition_graph() {
    let mut reached = vec![AttemptState::Accepted];
    loop {
        let mut changed = false;
        let snapshot = reached.clone();
        for source in snapshot {
            for target in OL_ALL_ATTEMPT_STATES {
                if AttemptLifecycleContract::can_transition(source, target)
                    && !reached.contains(&target)
                {
                    reached.push(target);
                    changed = true;
                }
            }
        }
        if !changed {
            break;
        }
    }

    assert_eq!(
        reached.len(),
        OL_ALL_ATTEMPT_STATES.len(),
        "graph reachability alone does not justify deleting an Attempt state"
    );
}

#[test]
fn dispatched_stop_kernel_is_shared_without_collapsing_accepted_cancel_semantics() {
    for state in OL_ALL_ATTEMPT_STATES {
        assert_eq!(
            AttemptLifecycleContract::deadline_request_is_admissible(state),
            AttemptLifecycleContract::stopping_target_state(state).is_some(),
            "deadline admissibility is exactly the dispatched-stop consumer"
        );
    }

    assert_eq!(
        AttemptLifecycleContract::stopping_target_state(AttemptState::Accepted),
        None
    );
    assert_eq!(
        AttemptLifecycleContract::cancel_target_state(AttemptState::Accepted),
        Some(AttemptState::Cancelled),
        "legacy accepted cancellation has an additional terminal edge"
    );

    for state in [
        AttemptState::Starting,
        AttemptState::Running,
        AttemptState::Recovering,
        AttemptState::Stopping,
    ] {
        assert_eq!(
            AttemptLifecycleContract::stopping_target_state(state),
            Some(AttemptState::Stopping)
        );
        assert_eq!(
            AttemptLifecycleContract::cancel_target_state(state),
            Some(AttemptState::Stopping)
        );
    }
}

#[test]
fn starting_and_recovering_are_locally_similar_but_transition_observably_distinct() {
    fn local_observation(
        state: AttemptState,
    ) -> (
        bool,
        Option<JobResolution>,
        Option<AttemptState>,
        bool,
        Option<AttemptState>,
        Option<AttemptState>,
    ) {
        (
            AttemptLifecycleContract::is_terminal(state),
            AttemptLifecycleContract::resolution(state),
            AttemptLifecycleContract::cancel_target_state(state),
            AttemptLifecycleContract::deadline_request_is_admissible(state),
            AttemptLifecycleContract::runner_identity_bound_state(state),
            AttemptLifecycleContract::supervisor_owner_bound_state(state),
        )
    }

    assert_eq!(
        local_observation(AttemptState::Starting),
        local_observation(AttemptState::Recovering),
        "the named local consumers alone do not distinguish these states"
    );

    assert!(AttemptLifecycleContract::can_transition(
        AttemptState::Starting,
        AttemptState::Recovering
    ));
    assert!(!AttemptLifecycleContract::can_transition(
        AttemptState::Recovering,
        AttemptState::Recovering
    ));
    assert!(AttemptLifecycleContract::can_transition(
        AttemptState::Recovering,
        AttemptState::Starting
    ));
    assert!(!AttemptLifecycleContract::can_transition(
        AttemptState::Starting,
        AttemptState::Starting
    ));
}

#[test]
fn merging_starting_and_recovering_is_sound_but_not_exact_under_labelled_composition() {
    let mut sound_pairs = 0usize;
    let mut exact_pairs = 0usize;
    let mut non_exact = Vec::new();

    for first in OL_ALL_ATTEMPT_STATES {
        for second in OL_ALL_ATTEMPT_STATES {
            let concrete = ol_projected_concrete_composition(first, second);
            let abstract_composed = ol_compose(
                &ol_projected_relation(first),
                &ol_projected_relation(second),
            );

            assert!(
                concrete.iter().all(|pair| abstract_composed.contains(pair)),
                "the quotient must at least over-approximate concrete two-step behavior"
            );
            sound_pairs += 1;

            let exact = concrete.len() == abstract_composed.len()
                && abstract_composed.iter().all(|pair| concrete.contains(pair));
            if exact {
                exact_pairs += 1;
            } else {
                non_exact.push((first, second));
            }
        }
    }

    assert_eq!(sound_pairs, 121);
    assert_eq!(exact_pairs, 119);
    assert_eq!(
        non_exact,
        vec![
            (AttemptState::Starting, AttemptState::Starting),
            (AttemptState::Recovering, AttemptState::Recovering),
        ],
        "consumer-local equality is not a congruence for exact labelled composition"
    );
}
