//! Typed durable PostgreSQL readback states, not OS effects.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PgJobSnapshot {
    pub job_id: String,
    pub desired_state: String,
    pub resolution: Option<String>,
    pub current_attempt_id: Option<String>,
    pub attempt_id: String,
    pub attempt_state: String,
    pub termination_intent: String,
    pub reservation_state: String,
    pub result_digest: Option<String>,
    pub finished_at_ms: Option<i64>,
    pub job_row_version: i64,
    pub attempt_row_version: i64,
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgJobReadback {
    Observed(Box<PgJobSnapshot>),
    Inconclusive,
}

/// Internal readback carrier. Every metadata item belongs to the same PG
/// repeatable-read cut; historical registrations retain their actual origin.
pub(crate) struct PgProjectionReadback {
    pub(crate) snapshot: Box<PgJobSnapshot>,
    pub(crate) artifacts: Vec<PgObservedArtifact>,
    pub(crate) exit_code: Option<i32>,
}

pub(crate) struct PgObservedArtifact {
    pub(crate) attempt_id: String,
    pub(crate) registration: crate::pg_admission::PgArtifactRegistration,
}
