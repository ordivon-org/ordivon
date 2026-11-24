//! Native Windows JobObject launcher identity: stable PID creation and owner receipt.
//! Does not consult or mutate the Linux systemd supervisor.
use super::{SupervisorRecoveryDisposition, TerminationIntent};
use crate::runtime::{AttemptState, RuntimeError, RuntimeErrorCode, RuntimeResult};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", tag = "contract")]
pub(crate) enum AttemptSupervisorOwner {
    #[serde(rename = "windows_launcher_v1")]
    WindowsLauncherV1 {
        launcher_process_id: u32,
        launcher_process_creation_time_file_time: u64,
        launcher_image_digest: String,
        job_name: String,
        start_evidence_digest: String,
    },
}

impl AttemptSupervisorOwner {
    pub(crate) fn start_evidence_digest(&self) -> &str {
        match self {
            AttemptSupervisorOwner::WindowsLauncherV1 {
                start_evidence_digest,
                ..
            } => start_evidence_digest,
        }
    }

    pub(crate) fn contract_name(&self) -> &'static str {
        match self {
            AttemptSupervisorOwner::WindowsLauncherV1 { .. } => "windows_launcher_v1",
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct WindowsLauncherOwnerObservation {
    pub process_alive: bool,
    pub process_creation_time_file_time: Option<u64>,
}

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
