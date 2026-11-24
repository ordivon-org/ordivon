//! Behavioral Supervisor recovery tests; no assertion about where Rust functions reside.
use super::*;
use crate::runtime::AttemptState;

fn expected() -> SupervisorIdentity {
    SupervisorIdentity {
        boot_id: "boot-a".into(),
        unit_name: "ordivon-job-01.service".into(),
        invocation_id: "invocation-a".into(),
        control_group: "/system.slice/ordivon-job-01.service".into(),
        main_pid: 42,
        main_process_start_identity: "9001".into(),
    }
}

fn running() -> SupervisorObservation {
    SupervisorObservation {
        boot_id: "boot-a".into(),
        unit_state: SupervisorUnitState::Running,
        invocation_id: Some("invocation-a".into()),
        control_group: Some("/system.slice/ordivon-job-01.service".into()),
        main_pid: Some(42),
        main_process_start_identity: Some("9001".into()),
        recorded_pid_alive: true,
        recorded_pid_start_identity: Some("9001".into()),
        result: None,
        exec_main_code: None,
        exec_main_status: None,
    }
}

mod linux;
mod windows;
