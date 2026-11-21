//! Windows JobObject launcher identity and physical process-owner recovery.
use super::types::{
    AttemptSupervisorOwner, SupervisorRecoveryDisposition, TerminationIntent,
    WindowsLauncherOwnerObservation,
};
use crate::runtime::{AttemptState, RuntimeError, RuntimeErrorCode, RuntimeResult};

pub(crate) fn validate_attempt_supervisor_owner(
    owner: &AttemptSupervisorOwner,
) -> RuntimeResult<()> {
    match owner {
        AttemptSupervisorOwner::WindowsLauncherV1 {
            launcher_process_id,
            launcher_process_creation_time_file_time,
            launcher_image_digest,
            job_name,
            start_evidence_digest,
        } => {
            if *launcher_process_id == 0
                || *launcher_process_creation_time_file_time == 0
                || job_name.is_empty()
                || !job_name.starts_with("Ordivon.")
                || !is_sha256_digest(launcher_image_digest)
                || !is_sha256_digest(start_evidence_digest)
            {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    "persisted Windows launcher owner identity is incomplete",
                    Some("attemptSupervisorOwner"),
                    false,
                ));
            }
        }
    }
    Ok(())
}

pub(crate) fn classify_windows_launcher_recovery(
    expected: &AttemptSupervisorOwner,
    observation: &WindowsLauncherOwnerObservation,
    termination_intent: TerminationIntent,
) -> RuntimeResult<SupervisorRecoveryDisposition> {
    validate_attempt_supervisor_owner(expected)?;
    let AttemptSupervisorOwner::WindowsLauncherV1 {
        launcher_process_creation_time_file_time,
        launcher_image_digest,
        ..
    } = expected;
    if observation.process_alive {
        if observation.process_creation_time_file_time
            != Some(*launcher_process_creation_time_file_time)
        {
            return Ok(SupervisorRecoveryDisposition::Orphaned(
                "launcher process creation identity does not match persisted owner".to_string(),
            ));
        }
        let _ = launcher_image_digest;
        return Ok(SupervisorRecoveryDisposition::Running);
    }
    Ok(SupervisorRecoveryDisposition::Terminal(
        match termination_intent {
            TerminationIntent::StopRequested => AttemptState::Cancelled,
            TerminationIntent::DeadlineExceeded => AttemptState::TimedOut,
            // The Windows launcher is the sole owner of the KILL_ON_JOB_CLOSE handle. If that
            // process identity is gone and no result evidence was observed by the caller, the
            // native process tree cannot still be executing under this Attempt.
            TerminationIntent::Natural => AttemptState::Failed,
        },
    ))
}

fn is_sha256_digest(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..].bytes().all(|byte| byte.is_ascii_hexdigit())
}
