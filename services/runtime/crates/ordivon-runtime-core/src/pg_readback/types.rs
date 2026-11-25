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
    /// Durable Runner binding observation, not a native process start clock.
    pub started_at_ms: Option<i64>,
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
    pub(crate) inspection: Option<PgInspectionMetadata>,
}

pub(crate) struct PgObservedArtifact {
    pub(crate) attempt_id: String,
    pub(crate) registration: crate::pg_admission::PgArtifactRegistration,
}

/// Bounded inspection metadata from the same qualified database cut.
pub(crate) struct PgInspectionMetadata {
    pub(crate) client_request_id: String,
    pub(crate) created_at_ms: u64,
    pub(crate) has_other_attempts: bool,
    pub(crate) events: Vec<PgInspectionEvent>,
}
pub(crate) struct PgInspectionEvent {
    pub(crate) sequence: u64,
    pub(crate) attempt_id: Option<String>,
    pub(crate) event_type: String,
    pub(crate) origin: String,
    pub(crate) previous_state: Option<String>,
    pub(crate) new_state: Option<String>,
    pub(crate) reason_code: String,
    pub(crate) observed_at_ms: u64,
}
