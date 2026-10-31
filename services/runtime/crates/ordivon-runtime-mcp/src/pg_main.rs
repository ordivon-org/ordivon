//! Separate opt-in loopback endpoint. No installed service or Registry is changed.
#[cfg(target_os = "linux")]
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    use ordivon_runtime_core::{PgRuntime, PgRuntimeConfig, UniversalExecutorConfig};
    use ordivon_runtime_mcp::server::{ExecutionContext, PgRuntimeServer};
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
    let config = PgRuntimeConfig {
        dsn: required("ORDIVON_PG_DSN")?,
        schema: required("ORDIVON_PG_SCHEMA")?,
        source_sha256: required("ORDIVON_PG_SOURCE_SHA256")?,
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
    let server = PgRuntimeServer::new(
        runtime,
        ExecutionContext {
            principal: required("ORDIVON_PG_PRINCIPAL")?,
            global_limit: 4,
        },
    );
    let service: StreamableHttpService<PgRuntimeServer, LocalSessionManager> =
        StreamableHttpService::new(
            move || Ok(server.clone()),
            Default::default(),
            StreamableHttpServerConfig::default(),
        );
    let expected = format!("Bearer {token}");
    let app = axum::Router::new()
        .nest_service("/mcp", service)
        .layer(axum::middleware::from_fn(
            move |request: axum::extract::Request, next: axum::middleware::Next| {
                let authorized = request
                    .headers()
                    .get(axum::http::header::AUTHORIZATION)
                    .and_then(|v| v.to_str().ok())
                    .is_some_and(|v| v == expected);
                async move {
                    if authorized {
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
        PgRuntimeServer::catalog().len()
    );
    axum::serve(listener, app)
        .with_graceful_shutdown(async {
            let _ = tokio::signal::ctrl_c().await;
        })
        .await?;
    Ok(())
}
#[cfg(not(target_os = "linux"))]
fn main() {
    eprintln!("The scoped PG execution vertical currently requires Linux");
    std::process::exit(64);
}
