//! Reuse native RMCP StreamableHTTP and the existing original bearer verifiers.
use super::pg_auth;
use ordivon_runtime_mcp::server::PgRuntimeServer;
use rmcp::transport::streamable_http_server::{
    session::local::LocalSessionManager, StreamableHttpServerConfig, StreamableHttpService,
};

fn is_protected_harness_path(path: &str) -> bool {
    path == "/harness/mcp" || path.starts_with("/harness/mcp/")
}

pub(super) fn build_pg_http_routes(
    server: PgRuntimeServer,
    dedicated_server: Option<PgRuntimeServer>,
    auth: pg_auth::PgAuth,
    isolated_harness: Option<(pg_auth::PgAuth, String, Option<String>)>,
) -> Result<(axum::Router, usize), Box<dyn std::error::Error>> {
    let mut transport = StreamableHttpServerConfig::default();
    if let Some(hosts) = pg_auth::optional_env("ORDIVON_PG_ALLOWED_HOSTS_JSON")? {
        transport
            .allowed_hosts
            .extend(serde_json::from_str::<Vec<String>>(&hosts)?);
    }
    let configured_tool_count = server.configured_tool_count();
    let service: StreamableHttpService<PgRuntimeServer, LocalSessionManager> =
        StreamableHttpService::new(
            move || Ok(server.clone()),
            Default::default(),
            transport.clone(),
        );
    let mut app = axum::Router::new().nest_service("/mcp", service);
    if let Some(harness_server) = dedicated_server {
        let harness_service: StreamableHttpService<PgRuntimeServer, LocalSessionManager> =
            StreamableHttpService::new(
                move || Ok(harness_server.clone()),
                Default::default(),
                transport.clone(),
            );
        app = app.nest_service("/harness/mcp", harness_service);
    }
    let harness_auth = isolated_harness.map(|(auth, _, _)| auth);
    let app = app
        .layer(axum::middleware::from_fn(
            move |request: axum::extract::Request, next: axum::middleware::Next| {
                let auth = auth.clone();
                let harness_auth = harness_auth.clone();
                async move {
                    let path = request.uri().path();
                    let protected = is_protected_harness_path(path);
                    let admitted = if protected {
                        match harness_auth {
                            Some(harness) => harness.authorized(request.headers()).await,
                            None => false,
                        }
                    } else {
                        auth.authorized(request.headers()).await
                    };
                    if admitted {
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
    Ok((app, configured_tool_count))
}

#[cfg(test)]
mod tests {
    use super::is_protected_harness_path;

    #[test]
    fn only_the_original_harness_path_and_descendants_use_harness_authentication() {
        assert!(is_protected_harness_path("/harness/mcp"));
        assert!(is_protected_harness_path("/harness/mcp/"));
        assert!(is_protected_harness_path("/harness/mcp/child"));
        for unrelated in [
            "/mcp",
            "/mcp/",
            "/harness",
            "/harness/mcpx",
            "/harness/mcp-old",
            "/harness/MCP",
            "/harnessx/mcp",
        ] {
            assert!(!is_protected_harness_path(unrelated), "{unrelated}");
        }
    }
}
