//! PostgreSQL Runtime loopback endpoint with local and explicit remote authentication.
#[cfg(target_os = "linux")]
mod access_auth;
#[cfg(target_os = "linux")]
mod pg_auth;
/// A running MCP listener without a running scheduler is not a healthy Runtime.
/// Allow normal shutdown, but fail the process on an unexpected scheduler exit
/// so the existing systemd Restart=always policy can restore the control plane.
#[cfg(target_os = "linux")]
fn scheduler_exit_result(
    shutdown_requested: bool,
    result: Result<(), tokio::task::JoinError>,
) -> Result<(), Box<dyn std::error::Error>> {
    match result {
        Err(error) => Err(format!("PG scheduling controller crashed: {error}").into()),
        Ok(()) if !shutdown_requested => {
            Err("PG scheduling controller exited without shutdown".into())
        }
        Ok(()) => Ok(()),
    }
}

/// Supervise the native scheduler and the MCP listener as one availability
/// unit. Losing either side without an operator shutdown is a service failure.
#[cfg(target_os = "linux")]
async fn supervise_pg_service<F>(
    shutdown: std::sync::Arc<std::sync::atomic::AtomicBool>,
    mut scheduler_task: tokio::task::JoinHandle<()>,
    server: F,
) -> Result<(), Box<dyn std::error::Error>>
where
    F: std::future::Future<Output = std::io::Result<()>>,
{
    use std::sync::atomic::Ordering;
    tokio::pin!(server);
    tokio::select! {
        scheduler_result = &mut scheduler_task => {
            scheduler_exit_result(shutdown.load(Ordering::Acquire), scheduler_result)?;
            server.await?;
        }
        server_result = &mut server => {
            let requested = shutdown.load(Ordering::Acquire);
            shutdown.store(true, Ordering::Release);
            server_result?;
            if !requested {
                return Err("PG MCP listener exited without shutdown".into());
            }
            scheduler_exit_result(true, scheduler_task.await)?;
        }
    }
    Ok(())
}

/// An unexpected loss of the HTTP listener must fail the entire service even
/// if a synchronous scheduler call never unblocks. Tokio waits indefinitely
/// for started spawn_blocking tasks on Runtime drop, so simply propagating the
/// error out of #[tokio::main] cannot guarantee systemd will see process exit.
/// The existing PG Journal/Runner owns durable native effects; this controller
/// must stop and let systemd restart rather than impersonate a live service.
#[cfg(target_os = "linux")]
fn finish_pg_control_plane(
    result: Result<(), Box<dyn std::error::Error>>,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Err(error) = &result {
        eprintln!("PG Runtime control plane failed; exiting for systemd restart: {error}");
        std::process::exit(1);
    }
    result
}

#[cfg(target_os = "linux")]
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    use ordivon_runtime_core::{PgRuntime, PgRuntimeConfig, UniversalExecutorConfig};
    use ordivon_runtime_mcp::server::{ExecutionContext, PgReleaseOperatorConfig, PgRuntimeServer};
    use rmcp::transport::streamable_http_server::{
        session::local::LocalSessionManager, StreamableHttpServerConfig, StreamableHttpService,
    };
    use std::{net::SocketAddr, path::PathBuf};
    let required = |key: &str| {
        std::env::var(key).map_err(|_| std::io::Error::other(format!("{key} required")))
    };
    let bind: SocketAddr = required("ORDIVON_PG_BIND")?.parse()?;
    if !bind.ip().is_loopback() {
        return Err("PG vertical requires an explicit loopback bind".into());
    }
    let token = required("ORDIVON_PG_TOKEN")?;
    if token.len() < 32 {
        return Err("ORDIVON_PG_TOKEN requires at least 32 characters".into());
    }
    let auth = pg_auth::PgAuth::from_env(&token)?;
    let config = PgRuntimeConfig {
        dsn: required("ORDIVON_PG_DSN")?,
        schema: required("ORDIVON_PG_SCHEMA")?,
        source_sha256: required("ORDIVON_PG_SOURCE_SHA256")?,
        harness_issuer_schema: std::env::var("ORDIVON_PG_HARNESS_ISSUER_SCHEMA")
            .ok()
            .filter(|s| !s.is_empty()),
        executor: UniversalExecutorConfig {
            store_root: PathBuf::from(required("ORDIVON_PG_STORE_ROOT")?),
            workspace_root: None,
            workspace_uid: None,
            workspace_gid: None,
            runner_path: Some(PathBuf::from(required("ORDIVON_PG_RUNNER")?)),
            allowed_executable_roots: serde_json::from_str(&required(
                "ORDIVON_PG_EXECUTABLE_ROOTS_JSON",
            )?)?,
            max_runtime_ms: 30 * 60 * 1000,
            max_output_bytes: 4 * 1024 * 1024,
        },
    };
    let runtime = tokio::task::spawn_blocking(move || PgRuntime::new(config)).await??;
    // Native administration runs independently of ordinary execution admission.
    // The CLI can repair exact committed cancellations even when all slots are held.
    let arguments: Vec<String> = std::env::args().skip(1).collect();
    if arguments == ["--reconcile-cancelled"] {
        let report =
            tokio::task::spawn_blocking(move || runtime.reconcile_cancelled_jobs(100)).await??;
        println!("{report}");
        return Ok(());
    }
    if !arguments.is_empty() {
        return Err("unsupported PG Runtime arguments".into());
    }
    let shutdown = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let worker_shutdown = shutdown.clone();
    let scheduler = runtime.clone();
    let scheduler_task =
        tokio::task::spawn_blocking(move || scheduler.serve_scheduler(worker_shutdown));
    // The release interface remains absent unless the separate native
    // operator is explicitly installed/configured. PgRuntimeServer also
    // verifies actual live timer and independently qualified PG release stage.
    let release = std::env::var("ORDIVON_PG_RELEASE_SOURCE_REPO")
        .ok()
        .map(|source_repo| {
            Ok::<_, std::io::Error>(PgReleaseOperatorConfig {
                source_repo: PathBuf::from(source_repo),
                operator_executable: PathBuf::from(required("ORDIVON_PG_RELEASE_OPERATOR_BIN")?),
                receipt_root: PathBuf::from(required("ORDIVON_PG_RELEASE_RECEIPT_ROOT")?),
                dispatcher_timer: required("ORDIVON_PG_RELEASE_DISPATCH_TIMER")?,
            })
        })
        .transpose()?;
    let server = PgRuntimeServer::with_release(
        runtime,
        ExecutionContext {
            principal: required("ORDIVON_PG_PRINCIPAL")?,
            global_limit: 0,
        },
        release,
    );
    let mut transport = StreamableHttpServerConfig::default();
    if let Some(hosts) = pg_auth::optional_env("ORDIVON_PG_ALLOWED_HOSTS_JSON")? {
        transport
            .allowed_hosts
            .extend(serde_json::from_str::<Vec<String>>(&hosts)?);
    }
    let configured_tool_count = server.configured_tool_count();
    let service: StreamableHttpService<PgRuntimeServer, LocalSessionManager> =
        StreamableHttpService::new(move || Ok(server.clone()), Default::default(), transport);
    let app = axum::Router::new()
        .nest_service("/mcp", service)
        .layer(axum::middleware::from_fn(
            move |request: axum::extract::Request, next: axum::middleware::Next| {
                let auth = auth.clone();
                async move {
                    if auth.authorized(request.headers()).await {
                        next.run(request).await
                    } else {
                        axum::response::Response::builder()
                            .status(401)
                            .body(axum::body::Body::empty())
                            .unwrap()
                    }
                }
            },
        ))
        .layer(tower_http::limit::RequestBodyLimitLayer::new(1024 * 1024));
    let listener = tokio::net::TcpListener::bind(bind).await?;
    eprintln!(
        "fresh PG Runtime MCP: http://{}/mcp ({} tools)",
        listener.local_addr()?,
        configured_tool_count
    );
    // Do not detach the scheduler: a panic/early exit must terminate this
    // apparently healthy MCP process, allowing systemd to restart it.
    // SIGINT is used by the installed systemd unit; also handle SIGTERM.
    use std::future::IntoFuture;
    use std::sync::atomic::Ordering;
    let signal_shutdown = shutdown.clone();
    let server = axum::serve(listener, app)
        .with_graceful_shutdown(async move {
            let mut term =
                tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
                    .expect("failed to install SIGTERM handler");
            tokio::select! {
                signal = tokio::signal::ctrl_c() => {
                    if let Err(error) = signal {
                        eprintln!("PG Runtime SIGINT handler failed: {error}");
                    }
                }
                _ = term.recv() => {}
            }
            signal_shutdown.store(true, Ordering::Release);
        })
        .into_future();
    finish_pg_control_plane(supervise_pg_service(shutdown, scheduler_task, server).await)
}
#[cfg(not(target_os = "linux"))]
fn main() {
    eprintln!("The scoped PG execution vertical currently requires Linux");
    std::process::exit(64);
}

#[cfg(all(test, target_os = "linux"))]
mod scheduler_supervision_tests {
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
        let run = |mode: &str| {
            Command::new(std::env::current_exe().unwrap())
                .args([
                    "--exact",
                    "scheduler_supervision_tests::fatal_control_plane_exit_does_not_wait_for_stuck_blocking_scheduler",
                    "--nocapture",
                ])
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
}
