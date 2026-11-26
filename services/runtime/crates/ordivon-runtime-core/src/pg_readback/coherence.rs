use super::types::PgJobSnapshot;

impl PgJobSnapshot {
    // A coherent projection is not a proof that the process ran or an external
    // effect happened. It only excludes contradictory durable PG rows.
    pub(super) fn lifecycle_coherent(&self) -> bool {
        if self.job_row_version < 0
            || self.attempt_row_version < 0
            || !matches!(self.desired_state.as_str(), "run" | "cancelled")
            || !matches!(
                self.termination_intent.as_str(),
                "natural" | "stop_requested" | "deadline_exceeded"
            )
        {
            return false;
        }
        match self.resolution.as_deref() {
            None => {
                self.current_attempt_id.as_deref() == Some(self.attempt_id.as_str())
                    && matches!(
                        self.attempt_state.as_str(),
                        "accepted" | "starting" | "running" | "stopping" | "recovering"
                    )
                    && self.reservation_state == "active"
                    && self.result_digest.is_none()
                    && self.finished_at_ms.is_none()
            }
            Some(resolution) => {
                self.current_attempt_id.is_none()
                    && self.attempt_state == resolution
                    && matches!(
                        resolution,
                        "succeeded" | "failed" | "timed_out" | "cancelled" | "lost" | "orphaned"
                    )
                    && self
                        .result_digest
                        .as_deref()
                        .is_some_and(|value| !value.is_empty())
                    && self.finished_at_ms.is_some_and(|value| value >= 0)
                    && self.reservation_state
                        == if resolution == "orphaned" {
                            "held_orphaned"
                        } else {
                            "released"
                        }
            }
        }
    }
}
