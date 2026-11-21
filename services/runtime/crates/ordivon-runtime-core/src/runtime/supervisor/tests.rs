//! Physical owner identity and OS recovery behaviors, not source-file shape.
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

#[test]
fn current_identity_recovers_running() {
    assert_eq!(
        classify_supervisor_recovery(&expected(), &running(), TerminationIntent::Natural,).unwrap(),
        SupervisorRecoveryDisposition::Running
    );
}

#[test]
fn identity_reuse_is_orphaned() {
    let mut observation = running();
    observation.invocation_id = Some("replacement".into());
    assert!(matches!(
        classify_supervisor_recovery(&expected(), &observation, TerminationIntent::Natural,)
            .unwrap(),
        SupervisorRecoveryDisposition::Orphaned(_)
    ));
}

#[test]
fn terminal_pid_reuse_does_not_orphan_matching_invocation() {
    let mut observation = running();
    observation.unit_state = SupervisorUnitState::Terminal;
    observation.main_pid = Some(84);
    observation.main_process_start_identity = Some("replacement-process".into());
    observation.recorded_pid_alive = false;
    observation.recorded_pid_start_identity = Some("replacement-process".into());
    observation.result = Some("success".into());
    observation.exec_main_code = Some(1);
    observation.exec_main_status = Some(0);
    assert_eq!(
        classify_supervisor_recovery(&expected(), &observation, TerminationIntent::Natural)
            .unwrap(),
        SupervisorRecoveryDisposition::Terminal(AttemptState::Succeeded)
    );
}

#[test]
fn native_systemd_runtime_max_timeout_is_not_generic_supervisor_failure() {
    // systemd RuntimeMaxSec may kill the unit before Runner writes result.json.
    // Preserve stop/deadline intent precedence while distinguishing a true
    // outer supervisor deadline from an unrelated process failure.
    let mut observation = running();
    observation.unit_state = SupervisorUnitState::Terminal;
    observation.recorded_pid_alive = false;
    observation.result = Some("timeout".into());
    observation.exec_main_code = Some(2);
    observation.exec_main_status = Some(9);
    assert_eq!(
        classify_supervisor_recovery(&expected(), &observation, TerminationIntent::Natural)
            .unwrap(),
        SupervisorRecoveryDisposition::Terminal(AttemptState::TimedOut)
    );
    observation.result = Some("exit-code".into());
    assert_eq!(
        classify_supervisor_recovery(&expected(), &observation, TerminationIntent::Natural)
            .unwrap(),
        SupervisorRecoveryDisposition::Terminal(AttemptState::Failed)
    );
    observation.result = Some("timeout".into());
    assert_eq!(
        classify_supervisor_recovery(&expected(), &observation, TerminationIntent::StopRequested)
            .unwrap(),
        SupervisorRecoveryDisposition::Terminal(AttemptState::Cancelled)
    );
    assert_eq!(
        classify_supervisor_recovery(
            &expected(),
            &observation,
            TerminationIntent::DeadlineExceeded
        )
        .unwrap(),
        SupervisorRecoveryDisposition::Terminal(AttemptState::TimedOut)
    );
}

#[test]
fn missing_unit_after_committed_stop_is_cancelled_when_recorded_pid_is_gone() {
    let mut observation = running();
    observation.unit_state = SupervisorUnitState::NotFound;
    observation.recorded_pid_alive = false;
    observation.recorded_pid_start_identity = None;
    assert_eq!(
        classify_supervisor_recovery(&expected(), &observation, TerminationIntent::StopRequested,)
            .unwrap(),
        SupervisorRecoveryDisposition::Terminal(AttemptState::Cancelled)
    );
}

#[test]
fn missing_unit_after_committed_deadline_is_timed_out_when_recorded_pid_is_gone() {
    let mut observation = running();
    observation.unit_state = SupervisorUnitState::NotFound;
    observation.recorded_pid_alive = false;
    observation.recorded_pid_start_identity = None;
    assert_eq!(
        classify_supervisor_recovery(
            &expected(),
            &observation,
            TerminationIntent::DeadlineExceeded,
        )
        .unwrap(),
        SupervisorRecoveryDisposition::Terminal(AttemptState::TimedOut)
    );
}

#[test]
fn boot_change_is_lost() {
    let mut observation = running();
    observation.boot_id = "boot-b".into();
    assert_eq!(
        classify_supervisor_recovery(&expected(), &observation, TerminationIntent::Natural,)
            .unwrap(),
        SupervisorRecoveryDisposition::Lost
    );
}

#[test]
fn stop_and_deadline_intent_control_terminal_state() {
    assert_eq!(
        classify_terminal_state(
            TerminationIntent::StopRequested,
            Some("timeout"),
            Some(2),
            Some(9)
        ),
        AttemptState::Cancelled
    );
    assert_eq!(
        classify_terminal_state(
            TerminationIntent::DeadlineExceeded,
            Some("timeout"),
            Some(2),
            Some(9)
        ),
        AttemptState::TimedOut
    );
}

fn windows_owner() -> AttemptSupervisorOwner {
    AttemptSupervisorOwner::WindowsLauncherV1 {
        launcher_process_id: 4242,
        launcher_process_creation_time_file_time: 123_456_789,
        launcher_image_digest:
            "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa".to_string(),
        job_name: "Ordivon.attempt-1".to_string(),
        start_evidence_digest:
            "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb".to_string(),
    }
}

#[test]
fn native_windows_launcher_identity_recovers_running() {
    let observed = WindowsLauncherOwnerObservation {
        process_alive: true,
        process_creation_time_file_time: Some(123_456_789),
    };
    assert_eq!(
        classify_windows_launcher_recovery(&windows_owner(), &observed, TerminationIntent::Natural)
            .unwrap(),
        SupervisorRecoveryDisposition::Running
    );
}

#[test]
fn native_windows_launcher_pid_reuse_is_orphaned() {
    let observed = WindowsLauncherOwnerObservation {
        process_alive: true,
        process_creation_time_file_time: Some(987_654_321),
    };
    assert!(matches!(
        classify_windows_launcher_recovery(&windows_owner(), &observed, TerminationIntent::Natural)
            .unwrap(),
        SupervisorRecoveryDisposition::Orphaned(_)
    ));
}

#[test]
fn absent_native_windows_launcher_is_definitively_terminal() {
    let observed = WindowsLauncherOwnerObservation {
        process_alive: false,
        process_creation_time_file_time: None,
    };
    assert_eq!(
        classify_windows_launcher_recovery(&windows_owner(), &observed, TerminationIntent::Natural)
            .unwrap(),
        SupervisorRecoveryDisposition::Terminal(AttemptState::Failed)
    );
    assert_eq!(
        classify_windows_launcher_recovery(
            &windows_owner(),
            &observed,
            TerminationIntent::StopRequested
        )
        .unwrap(),
        SupervisorRecoveryDisposition::Terminal(AttemptState::Cancelled)
    );
}
