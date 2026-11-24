//! Real scheduler supervision tests.rs behavioral tests.
use super::{finish_pg_control_plane, scheduler_exit_result, supervise_pg_service};
use std::sync::{atomic::AtomicBool, Arc};

#[tokio::test]
async fn silent_scheduler_exit_is_a_process_failure() {
    let result = tokio::task::spawn_blocking(|| ()).await;
    assert!(scheduler_exit_result(false, result).is_err());
}

#[tokio::test]
async fn expected_scheduler_shutdown_is_not_an_error() {
    let result = tokio::task::spawn_blocking(|| ()).await;
    assert!(scheduler_exit_result(true, result).is_ok());
}

#[tokio::test]
async fn supervisor_fails_fast_even_if_the_listener_would_never_finish() {
    let shutdown = Arc::new(AtomicBool::new(false));
    let scheduler = tokio::task::spawn_blocking(|| ());
    let still_listening = std::future::pending::<std::io::Result<()>>();
    let result = tokio::time::timeout(
        std::time::Duration::from_secs(2),
        supervise_pg_service(shutdown, scheduler, still_listening),
    )
    .await
    .expect("scheduler death must not leave HTTP serving indefinitely");
    assert!(result.is_err());
}

#[tokio::test]
async fn supervisor_allows_normal_listener_and_scheduler_shutdown() {
    let shutdown = Arc::new(AtomicBool::new(true));
    let scheduler = tokio::task::spawn_blocking(|| ());
    let listener = std::future::ready(Ok(()));
    assert!(supervise_pg_service(shutdown, scheduler, listener)
        .await
        .is_ok());
}

#[tokio::test]
async fn supervisor_rejects_listener_termination_without_shutdown() {
    let shutdown = Arc::new(AtomicBool::new(false));
    let scheduler = tokio::task::spawn_blocking(|| ());
    let listener = std::future::ready(Ok(()));
    assert!(supervise_pg_service(shutdown, scheduler, listener)
        .await
        .is_err());
}

#[test]
fn fatal_control_plane_exit_does_not_wait_for_stuck_blocking_scheduler() {
    use std::process::{Command, Stdio};
    use std::time::{Duration, Instant};

    const ENV: &str = "ORDIVON_TEST_FATAL_PG_CONTROL_EXIT";
    if let Ok(mode) = std::env::var(ENV) {
        let runtime = tokio::runtime::Builder::new_multi_thread()
            .enable_all()
            .build()
            .unwrap();
        let result = runtime.block_on(async {
            let (started_tx, started_rx) = std::sync::mpsc::channel();
            // The blocking task has actually started and intentionally does
            // not finish. The child process is always reaped by its parent.
            tokio::task::spawn_blocking(move || {
                let _ = started_tx.send(());
                loop {
                    std::thread::park();
                }
            });
            started_rx.recv_timeout(Duration::from_secs(2)).unwrap();
            let error: Box<dyn std::error::Error> = "synthetic listener failure".into();
            if mode == "fatal" {
                finish_pg_control_plane(Err(error))
            } else {
                Err(error)
            }
        });
        let _ = result;
        drop(runtime); // The uncorrected control path waits forever here.
        return;
    }
    // Discover this executable test's real module identity, rather than
    // pinning its old source-file/module placement. A 0-test subprocess
    // is never valid evidence of fatal systemd supervision behavior.
    let current_module = module_path!()
        .split_once("::")
        .map(|(_, module)| module)
        .unwrap_or(module_path!());
    let test_identity = format!(
        "{current_module}::fatal_control_plane_exit_does_not_wait_for_stuck_blocking_scheduler"
    );
    let run = |mode: &str| {
        Command::new(std::env::current_exe().unwrap())
            .args(["--exact", &test_identity, "--nocapture"])
            .env(ENV, mode)
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .unwrap()
    };
    let mut uncorrected = run("return");
    std::thread::sleep(Duration::from_millis(400));
    assert!(
        uncorrected.try_wait().unwrap().is_none(),
        "returning Err from tokio::main alone is not an exit"
    );
    uncorrected.kill().unwrap();
    uncorrected.wait().unwrap();

    let mut corrected = run("fatal");
    let deadline = Instant::now() + Duration::from_secs(3);
    loop {
        if let Some(status) = corrected.try_wait().unwrap() {
            assert_eq!(
                status.code(),
                Some(1),
                "fatal supervision must exit nonzero"
            );
            break;
        }
        if Instant::now() > deadline {
            corrected.kill().unwrap();
            corrected.wait().unwrap();
            panic!("fatal supervisor did not exit while scheduler was blocked");
        }
        std::thread::sleep(Duration::from_millis(20));
    }
}

#[tokio::test]
async fn scheduler_panic_is_not_hidden_by_shutdown() {
    let result = tokio::task::spawn_blocking(|| panic!("synthetic scheduler panic")).await;
    assert!(scheduler_exit_result(true, result).is_err());
}
