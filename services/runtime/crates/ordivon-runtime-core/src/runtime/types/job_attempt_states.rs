//! Original job attempt states domain wire contract and behavior.
use super::{RuntimeError, RuntimeResult};

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum JobDesiredState {
    Run,
    Cancelled,
}

impl JobDesiredState {
    pub(crate) fn as_db(self) -> &'static str {
        match self {
            Self::Run => "run",
            Self::Cancelled => "cancelled",
        }
    }

    pub(crate) fn parse(value: &str) -> RuntimeResult<Self> {
        match value {
            "run" => Ok(Self::Run),
            "cancelled" => Ok(Self::Cancelled),
            _ => Err(RuntimeError::invalid(
                "unknown desired state",
                "desiredState",
            )),
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum JobResolution {
    Succeeded,
    Failed,
    TimedOut,
    Cancelled,
    Lost,
    Orphaned,
}

impl JobResolution {
    pub(crate) fn as_db(self) -> &'static str {
        match self {
            Self::Succeeded => "succeeded",
            Self::Failed => "failed",
            Self::TimedOut => "timed_out",
            Self::Cancelled => "cancelled",
            Self::Lost => "lost",
            Self::Orphaned => "orphaned",
        }
    }

    pub(crate) fn parse(value: &str) -> RuntimeResult<Self> {
        match value {
            "succeeded" => Ok(Self::Succeeded),
            "failed" => Ok(Self::Failed),
            "timed_out" => Ok(Self::TimedOut),
            "cancelled" => Ok(Self::Cancelled),
            "lost" => Ok(Self::Lost),
            "orphaned" => Ok(Self::Orphaned),
            _ => Err(RuntimeError::invalid(
                "unknown job resolution",
                "resolution",
            )),
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AttemptState {
    Accepted,
    Starting,
    Running,
    Stopping,
    Recovering,
    Succeeded,
    Failed,
    TimedOut,
    Cancelled,
    Lost,
    Orphaned,
}

impl AttemptState {
    pub(crate) fn as_db(self) -> &'static str {
        match self {
            Self::Accepted => "accepted",
            Self::Starting => "starting",
            Self::Running => "running",
            Self::Stopping => "stopping",
            Self::Recovering => "recovering",
            Self::Succeeded => "succeeded",
            Self::Failed => "failed",
            Self::TimedOut => "timed_out",
            Self::Cancelled => "cancelled",
            Self::Lost => "lost",
            Self::Orphaned => "orphaned",
        }
    }

    pub(crate) fn known_db_state(value: &str) -> Option<Self> {
        match value {
            "accepted" => Some(Self::Accepted),
            "starting" => Some(Self::Starting),
            "running" => Some(Self::Running),
            "stopping" => Some(Self::Stopping),
            "recovering" => Some(Self::Recovering),
            "succeeded" => Some(Self::Succeeded),
            "failed" => Some(Self::Failed),
            "timed_out" => Some(Self::TimedOut),
            "cancelled" => Some(Self::Cancelled),
            "lost" => Some(Self::Lost),
            "orphaned" => Some(Self::Orphaned),
            _ => None,
        }
    }

    pub(crate) fn parse(value: &str) -> RuntimeResult<Self> {
        Self::known_db_state(value)
            .ok_or_else(|| RuntimeError::invalid("unknown attempt state", "state"))
    }

    pub fn is_terminal(self) -> bool {
        super::super::job_attempt_state::AttemptLifecycleContract::is_terminal(self)
    }

    pub fn can_transition_to(self, next: Self) -> bool {
        super::super::job_attempt_state::AttemptLifecycleContract::can_transition(self, next)
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AttemptTerminationIntent {
    Natural,
    StopRequested,
    DeadlineExceeded,
}

impl AttemptTerminationIntent {
    pub(crate) fn as_db(self) -> &'static str {
        match self {
            Self::Natural => "natural",
            Self::StopRequested => "stop_requested",
            Self::DeadlineExceeded => "deadline_exceeded",
        }
    }

    pub(crate) fn parse(value: &str) -> RuntimeResult<Self> {
        match value {
            "natural" => Ok(Self::Natural),
            "stop_requested" => Ok(Self::StopRequested),
            "deadline_exceeded" => Ok(Self::DeadlineExceeded),
            _ => Err(RuntimeError::invalid(
                "unknown termination intent",
                "terminationIntent",
            )),
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReservationState {
    Active,
    HeldOrphaned,
    Released,
}

impl ReservationState {
    pub(crate) fn as_db(self) -> &'static str {
        match self {
            Self::Active => "active",
            Self::HeldOrphaned => "held_orphaned",
            Self::Released => "released",
        }
    }

    pub(crate) fn parse(value: &str) -> RuntimeResult<Self> {
        match value {
            "active" => Ok(Self::Active),
            "held_orphaned" => Ok(Self::HeldOrphaned),
            "released" => Ok(Self::Released),
            _ => Err(RuntimeError::invalid(
                "unknown reservation state",
                "reservationState",
            )),
        }
    }
}

#[cfg(test)]
mod db_wire_contract_tests {
    use super::*;

    #[test]
    fn desired_state_db_and_wire_labels_agree() {
        for (state, label) in [
            (JobDesiredState::Run, "run"),
            (JobDesiredState::Cancelled, "cancelled"),
        ] {
            assert_eq!(state.as_db(), label);
            assert_eq!(JobDesiredState::parse(label).unwrap(), state);
            assert_eq!(serde_json::to_value(state).unwrap(), label);
            assert_eq!(
                serde_json::from_value::<JobDesiredState>(label.into()).unwrap(),
                state
            );
        }
        for invalid in ["", "RUN", "cancelled ", "canceled", "unknown"] {
            assert_eq!(
                JobDesiredState::parse(invalid)
                    .unwrap_err()
                    .field
                    .as_deref(),
                Some("desiredState")
            );
            assert!(serde_json::from_value::<JobDesiredState>(invalid.into()).is_err());
        }
    }

    #[test]
    fn resolution_db_and_wire_labels_agree() {
        for (state, label) in [
            (JobResolution::Succeeded, "succeeded"),
            (JobResolution::Failed, "failed"),
            (JobResolution::TimedOut, "timed_out"),
            (JobResolution::Cancelled, "cancelled"),
            (JobResolution::Lost, "lost"),
            (JobResolution::Orphaned, "orphaned"),
        ] {
            assert_eq!(state.as_db(), label);
            assert_eq!(JobResolution::parse(label).unwrap(), state);
            assert_eq!(serde_json::to_value(state).unwrap(), label);
            assert_eq!(
                serde_json::from_value::<JobResolution>(label.into()).unwrap(),
                state
            );
        }
        for invalid in ["", "running", "timedOut", "LOST", "unknown"] {
            assert_eq!(
                JobResolution::parse(invalid).unwrap_err().field.as_deref(),
                Some("resolution")
            );
            assert!(serde_json::from_value::<JobResolution>(invalid.into()).is_err());
        }
    }

    #[test]
    fn termination_intent_db_and_wire_labels_agree() {
        for (state, label) in [
            (AttemptTerminationIntent::Natural, "natural"),
            (AttemptTerminationIntent::StopRequested, "stop_requested"),
            (
                AttemptTerminationIntent::DeadlineExceeded,
                "deadline_exceeded",
            ),
        ] {
            assert_eq!(state.as_db(), label);
            assert_eq!(AttemptTerminationIntent::parse(label).unwrap(), state);
            assert_eq!(serde_json::to_value(state).unwrap(), label);
            assert_eq!(
                serde_json::from_value::<AttemptTerminationIntent>(label.into()).unwrap(),
                state
            );
        }
        for invalid in ["", "cancelled", "stopRequested", "NATURAL", "unknown"] {
            assert_eq!(
                AttemptTerminationIntent::parse(invalid)
                    .unwrap_err()
                    .field
                    .as_deref(),
                Some("terminationIntent")
            );
            assert!(serde_json::from_value::<AttemptTerminationIntent>(invalid.into()).is_err());
        }
    }

    #[test]
    fn reservation_state_db_and_wire_labels_agree() {
        for (state, label) in [
            (ReservationState::Active, "active"),
            (ReservationState::HeldOrphaned, "held_orphaned"),
            (ReservationState::Released, "released"),
        ] {
            assert_eq!(state.as_db(), label);
            assert_eq!(ReservationState::parse(label).unwrap(), state);
            assert_eq!(serde_json::to_value(state).unwrap(), label);
            assert_eq!(
                serde_json::from_value::<ReservationState>(label.into()).unwrap(),
                state
            );
        }
        for invalid in ["", "heldOrphaned", "orphaned", "RELEASED", "unknown"] {
            assert_eq!(
                ReservationState::parse(invalid)
                    .unwrap_err()
                    .field
                    .as_deref(),
                Some("reservationState")
            );
            assert!(serde_json::from_value::<ReservationState>(invalid.into()).is_err());
        }
    }
}
