//! Linux systemd unit/process ownership, PID-reuse and final-state classification.
use super::types::{
    SupervisorIdentity, SupervisorObservation, SupervisorRecoveryDisposition, SupervisorUnitState,
    TerminationIntent,
};
use crate::runtime::{AttemptState, RuntimeError, RuntimeErrorCode, RuntimeResult};

pub(crate) fn classify_supervisor_recovery(
    expected: &SupervisorIdentity,
    observation: &SupervisorObservation,
    termination_intent: TerminationIntent,
) -> RuntimeResult<SupervisorRecoveryDisposition> {
    validate_identity(expected)?;
    if observation.boot_id != expected.boot_id {
        return Ok(SupervisorRecoveryDisposition::Lost);
    }
    match observation.unit_state {
        SupervisorUnitState::Running => match running_identity_mismatch(expected, observation) {
            Some(reason) => Ok(SupervisorRecoveryDisposition::Orphaned(reason)),
            None => Ok(SupervisorRecoveryDisposition::Running),
        },
        SupervisorUnitState::Terminal => match terminal_identity_mismatch(expected, observation) {
            Some(reason) => Ok(SupervisorRecoveryDisposition::Orphaned(reason)),
            None => Ok(SupervisorRecoveryDisposition::Terminal(
                classify_terminal_state(
                    termination_intent,
                    observation.result.as_deref(),
                    observation.exec_main_code,
                    observation.exec_main_status,
                ),
            )),
        },
        SupervisorUnitState::NotFound => {
            if observation.recorded_pid_alive
                && observation.recorded_pid_start_identity.as_deref()
                    == Some(expected.main_process_start_identity.as_str())
            {
                return Ok(SupervisorRecoveryDisposition::Orphaned(
                    "recorded process identity is alive but supervisor unit is missing".to_string(),
                ));
            }
            Ok(match termination_intent {
                TerminationIntent::StopRequested => {
                    SupervisorRecoveryDisposition::Terminal(AttemptState::Cancelled)
                }
                TerminationIntent::DeadlineExceeded => {
                    SupervisorRecoveryDisposition::Terminal(AttemptState::TimedOut)
                }
                TerminationIntent::Natural => SupervisorRecoveryDisposition::Lost,
            })
        }
    }
}

pub(super) fn classify_terminal_state(
    intent: TerminationIntent,
    result: Option<&str>,
    exec_main_code: Option<i32>,
    exec_main_status: Option<i32>,
) -> AttemptState {
    match intent {
        TerminationIntent::StopRequested => AttemptState::Cancelled,
        TerminationIntent::DeadlineExceeded => AttemptState::TimedOut,
        TerminationIntent::Natural => {
            if result == Some("timeout") {
                // systemd RuntimeMaxSec is the outer deadline, including when
                // Runner cannot persist its result before the unit is killed.
                AttemptState::TimedOut
            } else if matches!(result, Some("success"))
                || (exec_main_code == Some(1) && exec_main_status == Some(0))
            {
                AttemptState::Succeeded
            } else {
                AttemptState::Failed
            }
        }
    }
}

fn validate_identity(identity: &SupervisorIdentity) -> RuntimeResult<()> {
    if identity.boot_id.is_empty()
        || identity.invocation_id.is_empty()
        || identity.main_process_start_identity.is_empty()
        || identity.main_pid == 0
        || !identity.unit_name.ends_with(".service")
        || !identity.control_group.starts_with('/')
    {
        return Err(RuntimeError::new(
            RuntimeErrorCode::RegistryCorrupt,
            "persisted supervisor identity is incomplete",
            Some("supervisorIdentity"),
            false,
        ));
    }
    Ok(())
}

fn terminal_identity_mismatch(
    expected: &SupervisorIdentity,
    observed: &SupervisorObservation,
) -> Option<String> {
    if observed.invocation_id.as_deref() != Some(expected.invocation_id.as_str()) {
        return Some("invocationId does not match persisted supervisor identity".to_string());
    }
    if observed
        .control_group
        .as_deref()
        .is_some_and(|actual| actual != expected.control_group)
    {
        return Some("controlGroup does not match persisted supervisor identity".to_string());
    }
    None
}

fn running_identity_mismatch(
    expected: &SupervisorIdentity,
    observed: &SupervisorObservation,
) -> Option<String> {
    for (field, actual, expected_value) in [
        (
            "invocationId",
            observed.invocation_id.as_deref(),
            expected.invocation_id.as_str(),
        ),
        (
            "controlGroup",
            observed.control_group.as_deref(),
            expected.control_group.as_str(),
        ),
        (
            "mainProcessStartIdentity",
            observed.main_process_start_identity.as_deref(),
            expected.main_process_start_identity.as_str(),
        ),
    ] {
        if actual != Some(expected_value) {
            return Some(format!(
                "{field} does not match persisted supervisor identity"
            ));
        }
    }
    if observed.main_pid != Some(expected.main_pid) {
        return Some("mainPid does not match persisted supervisor identity".to_string());
    }
    None
}
