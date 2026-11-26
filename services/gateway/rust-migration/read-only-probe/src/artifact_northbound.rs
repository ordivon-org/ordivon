//! Loopback-only northbound fixture. Fixed test principal, never production OAuth.
use crate::{artifact_provenance, owner_credential::read_fixture_bearer};
use axum::{
    extract::Request,
    http::{StatusCode, header},
    middleware::{self, Next},
    response::Response,
};
use rmcp::{
    ErrorData, RoleServer, ServerHandler,
    model::{
        CallToolRequestParams, CallToolResponse, CallToolResult, ContentBlock, Implementation,
        ListToolsResult, PaginatedRequestParams, ProtocolVersion, ServerCapabilities, ServerConfig,
        Tool,
    },
    service::RequestContext,
    transport::streamable_http_server::{
        StreamableHttpServerConfig, StreamableHttpService, session::local::LocalSessionManager,
    },
};
use serde::Deserialize;
use serde_json::Value;
use std::{
    borrow::Cow,
    path::{Path, PathBuf},
    sync::Arc,
};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Config {
    owner_endpoint: String,
    owner_credential: PathBuf,
    ingress_credential: PathBuf,
    issuer: String,
    principal: String,
    tool: Tool,
}
#[derive(Clone)]
struct Probe(Arc<Config>);
impl ServerHandler for Probe {
    fn get_info(&self) -> ServerConfig {
        ServerConfig::new(ServerCapabilities::builder().enable_tools().build()).with_server_info(
            Implementation::new(
                "ordivon-gateway-artifact-fixture",
                env!("CARGO_PKG_VERSION"),
            ),
        )
    }
    fn supported_protocol_versions(&self) -> Cow<'static, [ProtocolVersion]> {
        Cow::Borrowed(&[ProtocolVersion::V_2026_07_28, ProtocolVersion::V_2025_11_25])
    }
    async fn list_tools(
        &self,
        _: Option<PaginatedRequestParams>,
        _: RequestContext<RoleServer>,
    ) -> Result<ListToolsResult, ErrorData> {
        Ok(ListToolsResult::with_all_items(vec![self.0.tool.clone()]))
    }
    fn get_tool(&self, name: &str) -> Option<Tool> {
        (name == "artifact.read").then(|| self.0.tool.clone())
    }
    async fn call_tool(
        &self,
        request: CallToolRequestParams,
        _: RequestContext<RoleServer>,
    ) -> Result<CallToolResponse, ErrorData> {
        if request.name != "artifact.read" {
            return Err(ErrorData::invalid_params("unsupported fixture tool", None));
        }
        let args = Value::Object(request.arguments.unwrap_or_default());
        let Ok(args) = serde_json::from_value::<artifact_provenance::Request>(args) else {
            return Err(ErrorData::invalid_params("invalid fixture arguments", None));
        };
        let result = artifact_provenance::read(
            &self.0.owner_endpoint,
            &self.0.owner_credential,
            &self.0.issuer,
            &self.0.principal,
            false,
            args,
        )
        .await;
        if result["standing"] == "qualified" {
            Ok(CallToolResponse::Complete(CallToolResult::structured(
                result["chunk"].clone(),
            )))
        } else {
            // Fixed error only; no owner private details, and never success-shaped null.
            Ok(CallToolResponse::Complete(CallToolResult::error(vec![
                ContentBlock::text("artifact evidence unqualified"),
            ])))
        }
    }
}
pub(crate) async fn serve(path: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let bytes = std::fs::read(path)?;
    if bytes.len() > 65536 {
        return Err("fixture config too large".into());
    }
    let cfg: Config = serde_json::from_slice(&bytes)?;
    if cfg.tool.name != "artifact.read"
        || cfg.issuer.trim().is_empty()
        || cfg.principal.trim().is_empty()
        || crate::owner_transport::fixture_endpoint(&cfg.owner_endpoint).is_none()
    {
        return Err("invalid fixture config".into());
    }
    let north = read_fixture_bearer(&cfg.ingress_credential)
        .map_err(|_| "invalid fixture ingress credential")?;
    let south = read_fixture_bearer(&cfg.owner_credential)
        .map_err(|_| "invalid fixture owner credential")?;
    if north == south || north.len() < 32 {
        return Err("fixture credentials must be distinct".into());
    }
    let expected = Arc::new(format!("Bearer {north}"));
    let probe = Probe(Arc::new(cfg));
    let config = StreamableHttpServerConfig::default()
        .with_legacy_session_mode(false)
        .with_json_response(true);
    let service: StreamableHttpService<Probe, LocalSessionManager> =
        StreamableHttpService::new(move || Ok(probe.clone()), Default::default(), config);
    // Test-only fixed bearer, checked for every HTTP request (including legacy session messages).
    // A real deployment MUST use Security's verified issuer/subject/audience adapter.
    let app = axum::Router::new()
        .nest_service("/mcp", service)
        .layer(tower_http::limit::RequestBodyLimitLayer::new(1024 * 1024))
        .layer(middleware::from_fn(move |req: Request, next: Next| {
            let expected = expected.clone();
            async move {
                let mut values = req.headers().get_all(header::AUTHORIZATION).iter();
                if values.next().and_then(|v| v.to_str().ok()) != Some(expected.as_str())
                    || values.next().is_some()
                {
                    return Response::builder()
                        .status(StatusCode::UNAUTHORIZED)
                        .body(axum::body::Body::empty())
                        .expect("fixed response");
                }
                next.run(req).await
            }
        }));
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await?;
    println!("{}", listener.local_addr()?);
    axum::serve(listener, app).await?;
    Ok(())
}
