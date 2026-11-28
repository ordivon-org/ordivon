use super::types::PgJobSnapshot;
use crate::runtime::{
    AttemptLifecycleContract, AttemptState, AttemptTerminationIntent, JobDesiredState,
    JobResolution, ReservationState,
};

impl PgJobSnapshot {
    // A coherent projection is not a proof that the process ran or an external
    // effect happened. It only excludes contradictory durable PG rows.
    pub(super) fn lifecycle_coherent(&self) -> bool {
        let Some(state) = AttemptState::known_db_state(&self.attempt_state) else {
            return false;
        };
        if self.job_row_version < 0
            || self.attempt_row_version < 0
            || JobDesiredState::parse(&self.desired_state).is_err()
            || AttemptTerminationIntent::parse(&self.termination_intent).is_err()
        {
            return false;
        }
        match self.resolution.as_deref() {
            None => {
                self.current_attempt_id.as_deref() == Some(self.attempt_id.as_str())
                    && !state.is_terminal()
                    && self.reservation_state == ReservationState::Active.as_db()
                    && self.result_digest.is_none()
                    && self.finished_at_ms.is_none()
            }
            Some(resolution) => {
                let Ok(resolution) = JobResolution::parse(resolution) else {
                    return false;
                };
                AttemptLifecycleContract::terminal_evidence_complete(
                    state,
                    self.result_digest
                        .as_deref()
                        .is_some_and(|value| !value.is_empty()),
                    self.finished_at_ms.is_some_and(|value| value >= 0),
                    Some(resolution),
                    self.current_attempt_id.is_some(),
                ) && self.reservation_state
                    == if resolution == JobResolution::Orphaned {
                        ReservationState::HeldOrphaned.as_db()
                    } else {
                        ReservationState::Released.as_db()
                    }
            }
        }
    }
}
