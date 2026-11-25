mod logic;
mod matching;
mod native_discovery;
mod owner_observation;
use logic::{
    DescriptionInput, parse_execution_ref, system_describe, valid_status_envelope,
    valid_target_inventory,
};
use rmcp::{
    ErrorData, RoleServer, ServerHandler,
    model::{
        CacheScope, CallToolRequestParams, CallToolResponse, CallToolResult, Implementation,
        ListToolsResult, PaginatedRequestParams, ProtocolVersion, ServerCapabilities, ServerConfig,
        Tool,
    },
    service::RequestContext,
    transport::streamable_http_server::{
        StreamableHttpServerConfig, StreamableHttpService, session::local::LocalSessionManager,
    },
};
use serde::Deserialize;
use serde_json::{Value, json};
use std::{
    borrow::Cow,
    io::{self, BufRead},
    sync::Arc,
};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Fixture {
    description: DescriptionInput,
    tool: Tool,
}

#[derive(Clone)]
struct Probe {
    fixture: Arc<Fixture>,
    result: Arc<Value>,
}

impl ServerHandler for Probe {
    fn get_info(&self) -> ServerConfig {
        ServerConfig::new(ServerCapabilities::builder().enable_tools().build()).with_server_info(
            Implementation::new("ordivon-gateway-read-only-probe", env!("CARGO_PKG_VERSION")),
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
        Ok(
            ListToolsResult::with_all_items(vec![self.fixture.tool.clone()])
                .with_ttl_ms(0)
                .with_cache_scope(CacheScope::Private),
        )
    }
    fn get_tool(&self, name: &str) -> Option<Tool> {
        (name == "system.describe").then(|| self.fixture.tool.clone())
    }
    async fn call_tool(
        &self,
        request: CallToolRequestParams,
        _: RequestContext<RoleServer>,
    ) -> Result<CallToolResponse, ErrorData> {
        if request.name != "system.describe"
            || request.arguments.as_ref().is_some_and(|a| !a.is_empty())
        {
            return Err(ErrorData::invalid_params(
                "probe accepts only empty system.describe",
                None,
            ));
        }
        Ok(CallToolResponse::Complete(CallToolResult::structured(
            (*self.result).clone(),
        )))
    }
}

fn eval(v: Value) -> Value {
    let input = &v["input"];
    match v["operation"].as_str() {
        Some("fold") => json!(input.as_str().map(matching::fold)),
        Some("search") => match serde_json::from_value::<matching::SearchInput>(input.clone()) {
            Ok(input) => json!(matching::search(input)),
            Err(_) => json!({"error": "invalid search fixture"}),
        },
        Some("search_batch") => match serde_json::from_value::<matching::BatchInput>(input.clone())
        {
            Ok(input) => match matching::search_batch(input) {
                Ok(results) => json!(results),
                Err(error) => json!({"error": error}),
            },
            Err(_) => json!({"error": "invalid search batch fixture"}),
        },
        Some("status") => json!(valid_status_envelope(input)),
        Some("inventory") => json!(valid_target_inventory(input)),
        Some("reference") => json!(input.as_str().and_then(parse_execution_ref)),
        Some("describe") => match serde_json::from_value::<DescriptionInput>(input.clone()) {
            Ok(fixture) => match system_describe(&fixture) {
                Ok(v) => json!(v),
                Err(e) => json!({"error": e}),
            },
            Err(_) => json!({"error": "invalid fixture"}),
        },
        _ => json!({"error": "unknown operation"}),
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    match args.next().as_deref() {
        Some("casefold-digest") => println!("{}", matching::scalar_fold_digest()),
        Some("eval") => {
            for line in io::stdin().lock().lines() {
                let v: Value = serde_json::from_str(&line?)?;
                println!("{}", eval(v));
            }
        }
        Some("observe-runtime-fixture") => {
            let endpoint = args.next().ok_or("fixture endpoint required")?;
            let node = args.next().ok_or("expected fixture node required")?;
            let legacy = match args.next().as_deref() {
                None | Some("auto") => false,
                Some("legacy") => true,
                _ => return Err("unexpected fixture mode".into()),
            };
            if args.next().is_some() {
                return Err("unexpected arguments".into());
            }
            let observation = owner_observation::observe_runtime(
                &endpoint, &node, std::time::Duration::from_secs(3), legacy,
            ).await;
            println!("{}", serde_json::to_string(&observation)?);
        }
        Some("discover-runtime-fixture") => {
            let path = args.next().ok_or("fixture path required")?;
            let endpoint = args.next().ok_or("fixture endpoint required")?;
            let node = args.next().ok_or("fixture node required")?;
            if args.next().is_some() { return Err("unexpected arguments".into()); }
            let fixture = serde_json::from_slice(&std::fs::read(path)?)?;
            let discovery = native_discovery::discover_runtime_fixture(fixture, &endpoint, &node).await?;
            println!("{}", serde_json::to_string(&discovery)?);
        }
        Some("serve") => {
            let path = args.next().ok_or("fixture path required")?;
            let fixture: Fixture = serde_json::from_slice(&std::fs::read(path)?)?;
            if fixture.tool.name != "system.describe" {
                return Err("unexpected tool".into());
            }
            let result = serde_json::to_value(system_describe(&fixture.description)?)?;
            let probe = Probe {
                fixture: Arc::new(fixture),
                result: Arc::new(result),
            };
            let config = StreamableHttpServerConfig::default()
                .with_legacy_session_mode(false)
                .with_json_response(true);
            let service: StreamableHttpService<Probe, LocalSessionManager> =
                StreamableHttpService::new(move || Ok(probe.clone()), Default::default(), config);
            let app = axum::Router::new()
                .nest_service("/mcp", service)
                .layer(tower_http::limit::RequestBodyLimitLayer::new(1024 * 1024));
            let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await?;
            println!("{}", listener.local_addr()?);
            axum::serve(listener, app).await?;
        }
        _ => return Err("expected eval, casefold-digest, observe-runtime-fixture <endpoint> <node>, or serve <fixture>".into()),
    }
    Ok(())
}
