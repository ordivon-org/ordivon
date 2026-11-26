//! PostgreSQL Runtime loopback endpoint with local and explicit remote authentication.
#[cfg(any(target_os = "linux", windows))]
mod access_auth;
#[cfg(any(target_os = "linux", windows))]
mod pg_auth;

#[cfg(any(target_os = "linux", windows))]
#[path = "pg_main/config.rs"]
mod config;
#[cfg(any(target_os = "linux", windows))]
#[path = "pg_main/control.rs"]
mod control;
#[cfg(all(test, target_os = "linux"))]
#[path = "pg_main/headroom_configuration_tests.rs"]
mod headroom_configuration_tests;
#[cfg(any(target_os = "linux", windows))]
#[path = "pg_main/http_routes.rs"]
mod http_routes;
#[cfg(all(test, target_os = "linux"))]
#[path = "pg_main/ordinary_ingress_profile_configuration_tests.rs"]
mod ordinary_ingress_profile_configuration_tests;
#[cfg(all(test, target_os = "linux"))]
#[path = "pg_main/scheduler_supervision_tests.rs"]
mod scheduler_supervision_tests;
#[cfg(any(target_os = "linux", windows))]
#[path = "pg_main/server_bind.rs"]
mod server_bind;

#[cfg(all(test, target_os = "linux"))]
use config::{ordinary_contained_only, parse_pg_headroom_pair, require_ordinary_contained_owner};
#[cfg(all(test, target_os = "linux"))]
use control::scheduler_exit_result;
#[cfg(any(target_os = "linux", windows))]
use control::{finish_pg_control_plane, supervise_pg_service};

#[cfg(any(target_os = "linux", windows))]
#[cfg(windows)]
mod process_environment;
#[cfg(windows)]
mod windows_service;

#[cfg(any(target_os = "linux", windows))]
fn main() -> Result<(), Box<dyn std::error::Error>> {
    #[cfg(windows)]
    {
        // Load the private env before any Tokio worker or SCM thread exists.
        let args = pg_process_args(std::env::args_os().skip(1))?;
        if let Some(path) = args.env_file.as_deref() {
            for (key, value) in process_environment::read_private_runtime_env_file(path)? {
                std::env::set_var(key, value);
            }
        }
        if args.service {
            windows_service::dispatch()?;
            return Ok(());
        }
    }
    tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()?
        .block_on(run_runtime_server(
            tokio_util::sync::CancellationToken::new(),
            true,
            None,
        ))
}

#[cfg(windows)]
#[derive(Default)]
struct PgProcessArgs {
    env_file: Option<std::path::PathBuf>,
    service: bool,
    reconcile: bool,
}
#[cfg(windows)]
fn pg_process_args(
    args: impl IntoIterator<Item = std::ffi::OsString>,
) -> Result<PgProcessArgs, Box<dyn std::error::Error>> {
    let mut parsed = PgProcessArgs::default();
    let mut args = args.into_iter();
    while let Some(arg) = args.next() {
        if arg == "--windows-service" && !parsed.service {
            parsed.service = true;
        } else if arg == "--env-file" && parsed.env_file.is_none() {
            let p = std::path::PathBuf::from(
                args.next().ok_or("--env-file requires an absolute path")?,
            );
            if !p.is_absolute() {
                return Err("--env-file requires an absolute path".into());
            }
            parsed.env_file = Some(p);
        } else if arg == "--reconcile-cancelled" && !parsed.reconcile {
            parsed.reconcile = true;
        } else {
            return Err("unsupported or duplicate PG Runtime argument".into());
        }
    }
    if parsed.service && (parsed.reconcile || parsed.env_file.is_none()) {
        return Err(
            "SCM PG Runtime requires private env-file and forbids reconcile-only mode".into(),
        );
    }
    Ok(parsed)
}

#[cfg(any(target_os = "linux", windows))]
pub(crate) async fn run_runtime_server(
    cancellation: tokio_util::sync::CancellationToken,
    install_ctrl_c: bool,
    ready_hook: Option<fn(std::net::SocketAddr)>,
) -> Result<(), Box<dyn std::error::Error>> {
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
    #[cfg(windows)]
    let reconcile = pg_process_args(std::env::args_os().skip(1))?.reconcile;
    #[cfg(not(windows))]
    let reconcile = {
        let arguments: Vec<String> = std::env::args().skip(1).collect();
        if !arguments.is_empty() && arguments != ["--reconcile-cancelled"] {
            return Err("unsupported PG Runtime arguments".into());
        }
        arguments == ["--reconcile-cancelled"]
    };
    if reconcile {
        let report =
            tokio::task::spawn_blocking(move || runtime.reconcile_cancelled_jobs(100)).await??;
        println!("{report}");
        return Ok(());
    }
    let shutdown = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let (server, dedicated_server) = server_bind::bind_pg_runtime_servers(
        runtime.clone(),
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
    let worker_shutdown = shutdown.clone();
    let scheduler = runtime.clone();
    let scheduler_task =
        tokio::task::spawn_blocking(move || scheduler.serve_scheduler(worker_shutdown));
    if let Some(ready) = ready_hook {
        ready(listener.local_addr()?);
    }
    // Do not detach the scheduler: a panic/early exit must terminate this
    // apparently healthy MCP process, allowing systemd to restart it.
    // SIGINT is used by the installed systemd unit; also handle SIGTERM.
    use std::future::IntoFuture;
    use std::sync::atomic::Ordering;
    let signal_shutdown = shutdown.clone();
    let server = axum::serve(listener, app)
        .with_graceful_shutdown(async move {
            #[cfg(unix)]
            if install_ctrl_c {
                let mut term = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
                    .expect("failed to install SIGTERM handler");
                tokio::select! { _ = tokio::signal::ctrl_c() => {}, _ = term.recv() => {}, _ = cancellation.cancelled() => {} }
            } else { cancellation.cancelled().await; }
            #[cfg(windows)]
            if install_ctrl_c {
                tokio::select! { _ = tokio::signal::ctrl_c() => {}, _ = cancellation.cancelled() => {} }
            } else { cancellation.cancelled().await; }
            signal_shutdown.store(true, Ordering::Release);
        })
        .into_future();
    finish_pg_control_plane(supervise_pg_service(shutdown, scheduler_task, server).await)
}
#[cfg(not(any(target_os = "linux", windows)))]
fn main() {
    eprintln!("The scoped PG execution vertical requires a supported native Linux or Windows host");
    std::process::exit(64);
}

#[cfg(all(test, windows))]
mod windows_pg_service_bootstrap_tests {
    use super::*;
    use std::ffi::OsString;

    fn args<'a>(values: &'a [&'a str]) -> impl Iterator<Item = OsString> + 'a {
        values.iter().map(OsString::from)
    }
    #[test]
    fn scm_requires_private_env_and_disallows_admin_command() {
        assert!(pg_process_args(args(&["--windows-service"])).is_err());
        assert!(
            pg_process_args(args(&["--windows-service", "--env-file", "relative.env"])).is_err()
        );
        assert!(pg_process_args(args(&[
            "--windows-service",
            "--env-file",
            r"C:\private\pg.env",
            "--reconcile-cancelled"
        ]))
        .is_err());
        assert!(pg_process_args(args(&[
            "--env-file",
            r"C:\private\pg.env",
            "--env-file",
            r"C:\other.env"
        ]))
        .is_err());
        let v = pg_process_args(args(&[
            "--windows-service",
            "--env-file",
            r"C:\private\pg.env",
        ]))
        .unwrap();
        assert!(v.service && !v.reconcile && v.env_file.unwrap().is_absolute());
        assert!(
            pg_process_args(args(&["--reconcile-cancelled"]))
                .unwrap()
                .reconcile
        );
    }

    #[test]
    fn private_env_parser_rejects_inline_pg_bearer_and_legacy_secret() {
        use crate::process_environment::parse_runtime_env_text;
        for k in [
            "ORDIVON_PG_TOKEN",
            "ORDIVON_BEARER_TOKEN",
            "ORDIVON_REMOTE_BEARER_TOKEN",
        ] {
            assert!(parse_runtime_env_text(&format!("{k}=fixture")).is_err());
        }
        let p = parse_runtime_env_text(
            r"ORDIVON_PG_DSN=host=localhost dbname=pg
ORDIVON_BEARER_TOKEN_FILE=C:\private\token.txt
",
        )
        .unwrap();
        assert_eq!(p["ORDIVON_PG_DSN"], "host=localhost dbname=pg");
        assert!(parse_runtime_env_text(
            "ORDIVON_PG_SCHEMA=a
ORDIVON_PG_SCHEMA=b"
        )
        .is_err());
    }
}
