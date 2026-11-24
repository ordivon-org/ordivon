//! PostgreSQL Runtime loopback endpoint with local and explicit remote authentication.
#[cfg(target_os = "linux")]
mod access_auth;
#[cfg(target_os = "linux")]
mod pg_auth;

#[cfg(target_os = "linux")]
#[path = "pg_main/config.rs"]
mod config;
#[cfg(target_os = "linux")]
#[path = "pg_main/control.rs"]
mod control;
#[cfg(all(test, target_os = "linux"))]
#[path = "pg_main/headroom_configuration_tests.rs"]
mod headroom_configuration_tests;
#[cfg(target_os = "linux")]
#[path = "pg_main/http_routes.rs"]
mod http_routes;
#[cfg(all(test, target_os = "linux"))]
#[path = "pg_main/ordinary_ingress_profile_configuration_tests.rs"]
mod ordinary_ingress_profile_configuration_tests;
#[cfg(all(test, target_os = "linux"))]
#[path = "pg_main/scheduler_supervision_tests.rs"]
mod scheduler_supervision_tests;
#[cfg(target_os = "linux")]
#[path = "pg_main/server_bind.rs"]
mod server_bind;

#[cfg(all(test, target_os = "linux"))]
use config::{ordinary_contained_only, parse_pg_headroom_pair, require_ordinary_contained_owner};
#[cfg(all(test, target_os = "linux"))]
use control::scheduler_exit_result;
#[cfg(target_os = "linux")]
use control::{finish_pg_control_plane, supervise_pg_service};

#[cfg(target_os = "linux")]
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    use ordivon_runtime_core::PgRuntime;
    let config::PgStartup {
        bind,
        auth,
        contained_ordinary_only,
        isolated_harness,
        config,
        issuer_runtime_config,
    } = config::load_pg_startup()?;
    let runtime = tokio::task::spawn_blocking(move || PgRuntime::new(config)).await??;
    // The issuer view is a second IN-PROCESS port into the same PG and
    // shared native Runner, never a second scheduler, registry or service.
    let harness_runtime = if let Some(config) = issuer_runtime_config {
        Some(tokio::task::spawn_blocking(move || PgRuntime::new(config)).await??)
    } else {
        None
    };
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
    let (server, dedicated_server) = server_bind::bind_pg_runtime_servers(
        runtime,
        harness_runtime,
        contained_ordinary_only,
        &isolated_harness,
    )?;
    let (app, configured_tool_count) =
        http_routes::build_pg_http_routes(server, dedicated_server, auth, isolated_harness)?;
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
