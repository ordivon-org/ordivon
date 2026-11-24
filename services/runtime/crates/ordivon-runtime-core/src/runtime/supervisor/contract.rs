//! Original OS-independent Supervisor observation, identity and terminal intent values.
use crate::runtime::AttemptState;

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
