mod artifact_chunk;
mod artifact_descriptor;
mod artifact_inventory;
mod logic;
mod matching;
mod native_discovery;
mod owner_credential;
mod owner_error;
mod owner_observation;
mod owner_receipt;
mod owner_resolution;
mod owner_transport;
mod principal_binding;
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
    io::{self, BufRead, Write},
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
        Some("principal_namespace") => {
            let coords = input.as_array().filter(|v| v.len() == 4).and_then(|v| {
                Some([
                    v[0].as_str()?,
                    v[1].as_str()?,
                    v[2].as_str()?,
                    v[3].as_str()?,
                ])
            });
            json!(coords.map(|v| principal_binding::namespace(v[0], v[1], v[2], v[3])))
        }
        Some("owner_receipt") => json!(owner_receipt::project(
            input["operationRef"].as_str().unwrap_or_default(),
            &input["observation"],
            &input["inspection"]
        )),
        Some("owner_error") => json!(owner_error::decode(
            &input["result"],
            input["owner"].as_str().unwrap_or_default(),
            input["tool"].as_str().unwrap_or_default()
        )),
        Some("artifact_chunk") => json!(artifact_chunk::qualify(
            input["operationRef"].as_str().unwrap_or_default(),
            &input["descriptor"],
            &input["request"],
            &input["response"]
        )),
        Some("artifact_descriptor") => json!(artifact_descriptor::qualify(
            &input["payload"],
            &input["count"]
        )),
        Some("artifact_inventory") => json!(artifact_inventory::project(
            &input["payload"],
            &input["count"]
        )),
        Some("resolve_page") => json!(owner_resolution::project(
            &input["page"],
            input["requestId"].as_str().unwrap_or_default()
        )),
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
        Some("observe-runtime-error-fixture") => {
            let endpoint=args.next().ok_or("fixture endpoint required")?;
            let legacy=match args.next().as_deref(){Some("auto")=>false,Some("legacy")=>true,_=>return Err("unexpected fixture mode".into())};
            if args.next().is_some(){return Err("unexpected arguments".into());}
            let url=owner_transport::fixture_endpoint(&endpoint).ok_or("unqualified fixture endpoint")?;
            let result=owner_transport::read_endpoint_typed(url,std::time::Duration::from_secs(3),legacy,None,owner_transport::ReadRequest::Describe).await;
            match result {Ok(_)=>println!("{}",json!({"standing":"reported"})),Err(e)=>println!("{}",serde_json::to_string(&e)?),}
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
        Some("observe-protected-runtime-sequence-fixture") => {
            let endpoint = args.next().ok_or("fixture endpoint required")?;
            let node = args.next().ok_or("expected fixture node required")?;
            let credential = args.next().ok_or("fixture credential path required")?;
            let legacy = match args.next().as_deref() {
                Some("auto") => false,
                Some("legacy") => true,
                _ => return Err("unexpected fixture mode".into()),
            };
            if args.next().is_some() {
                return Err("unexpected arguments".into());
            }
            // Qualification-only carrier: one process, sequential independent reads.
            // The command stream cannot select endpoints, tools, or credentials.
            for (i, line) in io::stdin().lock().lines().enumerate() {
                if i >= 256 || line? != "observe" {
                    return Err("invalid bounded fixture sequence".into());
                }
                let result = owner_observation::observe_protected_runtime(
                    &endpoint, &node, std::path::Path::new(&credential),
                    std::time::Duration::from_secs(3), legacy,
                ).await;
                println!("{}", serde_json::to_string(&result)?);
                io::stdout().flush()?;
            }
        }
        Some("qualify-principal-runtime-fixture") => {
            let endpoint=args.next().ok_or("fixture endpoint required")?;
            let credential=args.next().ok_or("fixture credential path required")?;
            let legacy=match args.next().as_deref(){
                Some("auto")=>false,Some("legacy")=>true,
                _=>return Err("unexpected fixture mode".into()),
            };
            if args.next().is_some(){return Err("unexpected arguments".into());}
            // Operator-only synthetic identity, bounded input, not HTTP ingress.
            use std::io::Read;
            let mut bytes=Vec::new();
            io::stdin().take(65537).read_to_end(&mut bytes)?;
            if bytes.len()>65536 {return Err("fixture exceeds input budget".into());}
            let input:principal_binding::BindingFixture=serde_json::from_slice(&bytes)?;
            let result=principal_binding::qualify_fixture(input,&endpoint,std::path::Path::new(&credential),legacy).await;
            println!("{}",serde_json::to_string(&result)?);
        }
        Some("resolve-protected-runtime-fixture") => {
            let endpoint=args.next().ok_or("fixture endpoint required")?;
            let credential=args.next().ok_or("fixture credential path required")?;
            let request_id=args.next().ok_or("fixture request identity required")?;
            let legacy=match args.next().as_deref(){
                None|Some("auto")=>false,
                Some("legacy")=>true,
                _=>return Err("unexpected fixture mode".into()),
            };
            if args.next().is_some(){return Err("unexpected arguments".into());}
            let result=owner_resolution::resolve_protected_fixture(&endpoint,std::path::Path::new(&credential),&request_id,legacy).await;
            println!("{}",serde_json::to_string(&result)?);
        }
        Some("observe-protected-runtime-fixture") => {
            let endpoint = args.next().ok_or("fixture endpoint required")?;
            let node = args.next().ok_or("expected fixture node required")?;
            let credential = args.next().ok_or("fixture credential path required")?;
            let legacy = match args.next().as_deref() {
                None | Some("auto") => false,
                Some("legacy") => true,
                _ => return Err("unexpected fixture mode".into()),
            };
            if args.next().is_some() {
                return Err("unexpected arguments".into());
            }
            let observation = owner_observation::observe_protected_runtime(
                &endpoint, &node, std::path::Path::new(&credential),
                std::time::Duration::from_secs(3), legacy,
            ).await;
            println!("{}", serde_json::to_string(&observation)?);
        }
        Some(mode @ ("discover-runtime-fixture" | "discover-protected-runtime-fixture")) => {
            let path = args.next().ok_or("fixture path required")?;
            let endpoint = args.next().ok_or("fixture endpoint required")?;
            let node = args.next().ok_or("fixture node required")?;
            let credential = if mode == "discover-protected-runtime-fixture" {
                Some(args.next().ok_or("fixture credential path required")?)
            } else {
                None
            };
            if args.next().is_some() { return Err("unexpected arguments".into()); }
            let fixture = serde_json::from_slice(&std::fs::read(path)?)?;
            let discovery = native_discovery::discover_runtime_fixture(
                fixture, &endpoint, &node, credential.as_deref().map(std::path::Path::new),
            ).await?;
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
        _ => return Err("expected eval, casefold-digest, observe-runtime-fixture, observe-protected-runtime-fixture, discover-runtime-fixture, discover-protected-runtime-fixture, or serve <fixture>".into()),
    }
    Ok(())
}
