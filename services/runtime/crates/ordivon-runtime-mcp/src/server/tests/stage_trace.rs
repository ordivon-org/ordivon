use super::*;
use std::future::Future;
use std::task::Poll;
use std::time::Duration;

fn traced_server(sandbox: &Sandbox) -> (RuntimeServer, PathBuf) {
    let mut server = sandbox.server();
    let path = sandbox.root.join("stage-trace.jsonl");
    Arc::get_mut(&mut server.state).unwrap().trace_path = Some(path.clone());
    (server, path)
}

fn trace_record(path: &PathBuf) -> Value {
    let text = fs::read_to_string(path).unwrap();
    serde_json::from_str(text.lines().last().unwrap()).unwrap()
}

#[test]
fn stage_trace_distinguishes_blocking_wait_from_operation() {
    let sandbox = Sandbox::new("trace-blocking-wait");
    let (server, path) = traced_server(&sandbox);
    let runtime = tokio::runtime::Builder::new_current_thread()
        .enable_time()
        .max_blocking_threads(1)
        .build()
        .unwrap();
    let (started_tx, started_rx) = std::sync::mpsc::channel();
    let (release_tx, release_rx) = std::sync::mpsc::channel();
    runtime.block_on(async {
        let blocker = tokio::task::spawn_blocking(move || {
            started_tx.send(()).unwrap();
            release_rx.recv_timeout(Duration::from_secs(5)).unwrap();
        });
        started_rx.recv_timeout(Duration::from_secs(5)).unwrap();
        let mut pending = Box::pin(server.run_core("test.trace.wait", || {
            std::thread::sleep(Duration::from_millis(30));
            Ok(42_u32)
        }));
        std::future::poll_fn(|cx| {
            assert!(pending.as_mut().poll(cx).is_pending());
            Poll::Ready(())
        })
        .await;
        tokio::time::sleep(Duration::from_millis(40)).await;
        release_tx.send(()).unwrap();
        let outcome = pending.await;
        blocker.await.unwrap();
        assert!(matches!(outcome, ToolOutcome::Success(42)));
    });
    let trace = trace_record(&path);
    let wait = trace["blockingWaitMs"]
        .as_u64()
        .expect("missing blocking wait evidence");
    let operation = trace["operationMs"]
        .as_u64()
        .expect("missing operation evidence");
    let resume = trace["joinResumeMs"]
        .as_u64()
        .expect("missing join/resume evidence");
    assert!(wait >= 30, "{trace}");
    assert!(operation >= 25, "{trace}");
    let sum = wait + operation + resume;
    let core = trace["coreMs"].as_u64().unwrap();
    assert!(sum <= core && core - sum <= 3, "{trace}");
    assert_eq!(trace["ok"], true);
    assert_eq!(trace["tool"], "test.trace.wait");
}

#[test]
fn stage_trace_preserves_tool_error_and_measured_operation() {
    let sandbox = Sandbox::new("trace-tool-error");
    let (server, path) = traced_server(&sandbox);
    let runtime = tokio::runtime::Builder::new_current_thread()
        .build()
        .unwrap();
    let outcome = runtime.block_on(server.run_core::<(), _>("test.trace.error", || {
        Err(ToolError::internal("known operation error".to_string()))
    }));
    match outcome {
        ToolOutcome::Error(error) => {
            assert!(error.message.contains("known operation error"));
            assert!(error.trace_id.is_some());
        }
        ToolOutcome::Success(()) => panic!("operation error became success"),
    }
    let trace = trace_record(&path);
    assert_eq!(trace["ok"], false);
    for field in ["blockingWaitMs", "operationMs", "joinResumeMs"] {
        assert!(trace[field].is_u64(), "missing measured {field}: {trace}");
    }
}

#[test]
fn stage_trace_join_failure_keeps_unreturned_measurements_unknown() {
    let sandbox = Sandbox::new("trace-join-failure");
    let (server, path) = traced_server(&sandbox);
    let runtime = tokio::runtime::Builder::new_current_thread()
        .build()
        .unwrap();
    let outcome = runtime.block_on(server.run_core::<(), _>("test.trace.panic", || {
        panic!("bounded stage-trace panic fixture")
    }));
    assert!(matches!(outcome, ToolOutcome::Error(_)));
    let trace = trace_record(&path);
    assert_eq!(trace["ok"], false);
    for field in ["blockingWaitMs", "operationMs", "joinResumeMs"] {
        assert!(trace.as_object().unwrap().contains_key(field), "{trace}");
        assert!(
            trace[field].is_null(),
            "join failure manufactured {field}: {trace}"
        );
    }
}
