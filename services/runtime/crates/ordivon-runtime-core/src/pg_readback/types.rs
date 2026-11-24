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
