//! Preserve real consumer behavior; test placement is not a production contract.
use super::*;

#[test]
fn nonterminal_native_transition_requires_reconciliation() {
    for state in [
        AttemptState::Starting,
        AttemptState::Stopping,
        AttemptState::Recovering,
    ] {
        assert!(needs_recovery_observation(state, false));
        assert!(!needs_recovery_observation(state, true));
    }
    for state in [
        AttemptState::Accepted,
        AttemptState::Running,
        AttemptState::Succeeded,
        AttemptState::Failed,
        AttemptState::TimedOut,
        AttemptState::Cancelled,
        AttemptState::Lost,
        AttemptState::Orphaned,
    ] {
        assert!(!needs_recovery_observation(state, false));
        assert!(!needs_recovery_observation(state, true));
    }
}

// The list projection must retain the behavior of its former string
// predicate when decoding row-local unknown or absent Attempt states.
#[test]
fn recovery_projection_contract_matches_existing_list_semantics() {
    for raw in [
        None,
        Some("accepted"),
        Some("starting"),
        Some("running"),
        Some("stopping"),
        Some("recovering"),
        Some("succeeded"),
        Some("failed"),
        Some("timed_out"),
        Some("cancelled"),
        Some("lost"),
        Some("orphaned"),
        Some("unknown"),
    ] {
        for finished in [false, true] {
            let expected = !finished
                && raw.is_some_and(|state| matches!(state, "starting" | "stopping" | "recovering"));
            let actual = raw
                .and_then(AttemptState::known_db_state)
                .is_some_and(|state| needs_recovery_observation(state, finished));
            assert_eq!(actual, expected, "state={raw:?}, finished={finished}");
        }
    }
}
