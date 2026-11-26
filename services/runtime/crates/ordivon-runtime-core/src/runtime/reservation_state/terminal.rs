//! Convert qualified *physical terminal evidence* to release or held-orphaned capacity.
use super::super::{
    job_attempt_state::AttemptLifecycleContract, AttemptState, JobResolution, ReservationState,
    RuntimeError, RuntimeErrorCode, RuntimeResult,
};
use super::ReservationContract;

impl ReservationContract {
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
        job_resolution: Option<JobResolution>,
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
