//! Windows launcher recovery behavior: PID reuse, real native handle owner.
use super::*;

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
