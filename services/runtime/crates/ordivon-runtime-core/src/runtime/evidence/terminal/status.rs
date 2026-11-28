use super::super::super::{AttemptRecord, AttemptState, AttemptTerminationIntent};
use crate::universal::{RunnerResult, RunnerTerminalStatus};

pub(super) fn terminal_state(
    current: &AttemptRecord,
    result: &RunnerResult,
) -> (AttemptState, &'static str) {
    match result.status {
        RunnerTerminalStatus::Completed
            if current.state == AttemptState::Stopping
                || current.termination_intent == AttemptTerminationIntent::StopRequested =>
        {
            (
                AttemptState::Succeeded,
                "PROCESS_COMPLETED_BEFORE_STOP_EFFECTIVE",
            )
        }
        RunnerTerminalStatus::Completed => (AttemptState::Succeeded, "PROCESS_EXIT_ZERO"),
        RunnerTerminalStatus::Failed if result.timed_out => {
            (AttemptState::TimedOut, "DEADLINE_EXCEEDED")
        }
        RunnerTerminalStatus::Failed
            if result.infrastructure_error_code.as_deref() == Some("WORKSPACE_STATE_MISMATCH") =>
        {
            (AttemptState::Failed, "WORKSPACE_SOURCE_PRECONDITION_DRIFT")
        }
        RunnerTerminalStatus::Failed
            if result.infrastructure_error_code.as_deref() == Some("INPUT_STATE_MISMATCH") =>
        {
            (AttemptState::Failed, "INPUT_PRECONDITION_DRIFT")
        }
        RunnerTerminalStatus::Failed
            if result.infrastructure_error_code.as_deref()
                == Some("HOST_DEPENDENCY_RUNTIME_DRIFT") =>
        {
            (AttemptState::Failed, "HOST_DEPENDENCY_RUNTIME_DRIFT")
        }
        RunnerTerminalStatus::Failed
            if result.infrastructure_error_code.as_deref() == Some("EXECUTABLE_RUNTIME_DRIFT") =>
        {
            (AttemptState::Failed, "EXECUTABLE_RUNTIME_DRIFT")
        }
        RunnerTerminalStatus::Failed if result.infrastructure_error_code.is_some() => {
            (AttemptState::Failed, "RUNNER_INFRASTRUCTURE_FAILURE")
        }
        RunnerTerminalStatus::Failed => (AttemptState::Failed, "PROCESS_EXIT_NONZERO"),
        RunnerTerminalStatus::Cancelled => (AttemptState::Cancelled, "STOP_REQUESTED"),
    }
}
