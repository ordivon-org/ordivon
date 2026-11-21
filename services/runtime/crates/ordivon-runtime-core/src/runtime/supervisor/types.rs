//! Original supervisor identity, observation and terminal ownership types.
use crate::runtime::AttemptState;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct SupervisorIdentity {
    pub boot_id: String,
    pub unit_name: String,
    pub invocation_id: String,
    pub control_group: String,
    pub main_pid: u32,
    pub main_process_start_identity: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum SupervisorUnitState {
    Running,
    Terminal,
    NotFound,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct SupervisorObservation {
    pub boot_id: String,
    pub unit_state: SupervisorUnitState,
    pub invocation_id: Option<String>,
    pub control_group: Option<String>,
    pub main_pid: Option<u32>,
    pub main_process_start_identity: Option<String>,
    pub recorded_pid_alive: bool,
    pub recorded_pid_start_identity: Option<String>,
    pub result: Option<String>,
    pub exec_main_code: Option<i32>,
    pub exec_main_status: Option<i32>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum SupervisorRecoveryDisposition {
    Running,
    Terminal(AttemptState),
    Lost,
    Orphaned(String),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum TerminationIntent {
    Natural,
    StopRequested,
    DeadlineExceeded,
}

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
