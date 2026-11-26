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
    }
}
