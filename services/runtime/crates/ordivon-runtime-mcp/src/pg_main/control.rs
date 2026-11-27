//! One failure boundary for PostgreSQL scheduler and MCP listener.
//! Physical Runner/PG effects remain owned by the original Runtime.

/// A running MCP listener without a running scheduler is not a healthy Runtime.
/// Allow normal shutdown, but fail the process on an unexpected scheduler exit
/// so the existing systemd Restart=always policy can restore the control plane.
pub(super) fn scheduler_exit_result(
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
pub(super) async fn supervise_pg_service<F>(
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
pub(super) fn finish_pg_control_plane(
    result: Result<(), Box<dyn std::error::Error>>,
) -> Result<(), Box<dyn std::error::Error>> {
    if let Err(error) = &result {
        eprintln!(
            "PG Runtime control plane failed; exiting for native service-manager restart: {error}"
        );
        std::process::exit(1);
    }
    result
}
