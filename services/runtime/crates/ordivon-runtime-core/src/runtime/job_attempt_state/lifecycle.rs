//! Attempt transition, physical owner replay and terminal-evidence qualification.
use super::super::{
    AttemptState, AttemptTerminationIntent, JobResolution, RuntimeError, RuntimeResult,
};

pub(crate) struct AttemptLifecycleContract;

impl AttemptLifecycleContract {
    pub(crate) const INITIAL_ATTEMPT_NUMBER: u32 = 1;

    pub(crate) fn initial_state() -> AttemptState {
        AttemptState::Accepted
    }

    pub(crate) fn initial_termination_intent() -> AttemptTerminationIntent {
        AttemptTerminationIntent::Natural
    }

    pub(crate) fn is_terminal(state: AttemptState) -> bool {
        Self::resolution(state).is_some()
    }

    pub(crate) fn can_transition(state: AttemptState, next: AttemptState) -> bool {
        // Every dispatched nonterminal state can settle to any terminal
        // resolution. Accepted has fewer edges: no successful or timed-out
        // physical execution can be inferred before dispatch.
        match state {
            AttemptState::Accepted => matches!(
                next,
                AttemptState::Starting
                    | AttemptState::Cancelled
                    | AttemptState::Failed
                    | AttemptState::Lost
                    | AttemptState::Orphaned
            ),
            AttemptState::Starting => {
                Self::is_terminal(next)
                    || matches!(
                        next,
                        AttemptState::Running | AttemptState::Stopping | AttemptState::Recovering
                    )
            }
            AttemptState::Running => {
                Self::is_terminal(next)
                    || matches!(next, AttemptState::Stopping | AttemptState::Recovering)
            }
            AttemptState::Stopping => Self::is_terminal(next) || next == AttemptState::Recovering,
            AttemptState::Recovering => {
                Self::is_terminal(next)
                    || matches!(
                        next,
                        AttemptState::Starting | AttemptState::Running | AttemptState::Stopping
                    )
            }
            AttemptState::Succeeded
            | AttemptState::Failed
            | AttemptState::TimedOut
            | AttemptState::Cancelled
            | AttemptState::Lost
            | AttemptState::Orphaned => false,
        }
    }

    pub(crate) fn deadline_request_is_replay(
        state: AttemptState,
        termination_intent: AttemptTerminationIntent,
    ) -> bool {
        Self::is_terminal(state) || termination_intent != AttemptTerminationIntent::Natural
    }

    /// Shared dispatched-stop kernel. This is deliberately smaller than
    /// cancellation: an accepted Attempt may have a durable cancel intent
    /// without proving that physical dispatch happened.
    pub(crate) fn stopping_target_state(state: AttemptState) -> Option<AttemptState> {
        match state {
            AttemptState::Starting
            | AttemptState::Running
            | AttemptState::Recovering
            | AttemptState::Stopping => Some(AttemptState::Stopping),
            AttemptState::Accepted
            | AttemptState::Succeeded
            | AttemptState::Failed
            | AttemptState::TimedOut
            | AttemptState::Cancelled
            | AttemptState::Lost
            | AttemptState::Orphaned => None,
        }
    }

    pub(crate) fn deadline_request_is_admissible(state: AttemptState) -> bool {
        Self::stopping_target_state(state).is_some()
    }

    pub(crate) fn cancel_target_state(state: AttemptState) -> Option<AttemptState> {
        match state {
            AttemptState::Accepted => Some(AttemptState::Cancelled),
            _ => Self::stopping_target_state(state),
        }
    }

    pub(crate) fn runner_identity_bound_state(state: AttemptState) -> Option<AttemptState> {
        match state {
            AttemptState::Starting | AttemptState::Recovering => Some(AttemptState::Running),
            _ => None,
        }
    }

    pub(crate) fn supervisor_owner_bound_state(state: AttemptState) -> Option<AttemptState> {
        if state == AttemptState::Stopping {
            Some(state)
        } else {
            Self::runner_identity_bound_state(state)
        }
    }

    pub(crate) fn physical_owner_replay_matches(
        state: AttemptState,
        existing_owner_digest: &str,
        requested_owner_digest: &str,
        stored_start_digest: Option<&str>,
        requested_start_digest: &str,
    ) -> bool {
        existing_owner_digest == requested_owner_digest
            && matches!(state, AttemptState::Running | AttemptState::Stopping)
            && stored_start_digest == Some(requested_start_digest)
    }

    pub(crate) fn resolution(state: AttemptState) -> Option<JobResolution> {
        match state {
            AttemptState::Succeeded => Some(JobResolution::Succeeded),
            AttemptState::Failed => Some(JobResolution::Failed),
            AttemptState::TimedOut => Some(JobResolution::TimedOut),
            AttemptState::Cancelled => Some(JobResolution::Cancelled),
            AttemptState::Lost => Some(JobResolution::Lost),
            AttemptState::Orphaned => Some(JobResolution::Orphaned),
            AttemptState::Accepted
            | AttemptState::Starting
            | AttemptState::Running
            | AttemptState::Stopping
            | AttemptState::Recovering => None,
        }
    }

    pub(crate) fn require_terminal_resolution(state: AttemptState) -> RuntimeResult<JobResolution> {
        Self::resolution(state)
            .ok_or_else(|| RuntimeError::invalid("Attempt state is not terminal", "state"))
    }

    pub(crate) fn terminal_evidence_complete(
        state: AttemptState,
        result_digest_present: bool,
        finished_at_present: bool,
        job_resolution: Option<JobResolution>,
        current_attempt_present: bool,
    ) -> bool {
        let resolution = Self::resolution(state);
        resolution.is_some()
            && result_digest_present
            && finished_at_present
            && job_resolution == resolution
            && !current_attempt_present
    }
}
