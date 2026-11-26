//! Fixed native read operations; no public generic dispatch or effect authority.
use crate::owner_credential::read_fixture_bearer;
use crate::owner_error::{self, QualifiedError};
use rmcp::{
    ClientLifecycleMode, ClientServiceExt,
    model::{CallToolRequestParams, ClientConfig, ProtocolVersion},
    transport::streamable_http_client::{
        StreamableHttpClientTransport, StreamableHttpClientTransportConfig,
    },
};
use serde::Serialize;
use serde_json::{Value, json};
use std::{path::Path, time::Duration};

pub(crate) enum ReadRequest<'a> {
    Describe,
    Resolve { request_id: &'a str },
}

impl ReadRequest<'_> {
    fn tool(&self) -> &'static str {
        match self {
            Self::Describe => "runtime.describe",
            Self::Resolve { .. } => "job.list",
        }
    }
    fn params(self) -> CallToolRequestParams {
        let (name, args) = match self {
            Self::Describe => ("runtime.describe", json!({"schemaVersion":1})),
            Self::Resolve { request_id } => {
                ("job.list", json!({"limit":2,"clientRequestId":request_id}))
            }
        };
        CallToolRequestParams::new(name)
            .with_arguments(args.as_object().expect("literal object").clone())
    }
}

pub(crate) fn fixture_endpoint(endpoint: &str) -> Option<reqwest::Url> {
    let url = reqwest::Url::parse(endpoint).ok()?;
    (url.scheme() == "http"
        && url.host_str() == Some("127.0.0.1")
        && url.port().is_some()
        && url.path() == "/mcp"
        && url.username().is_empty()
        && url.password().is_none()
        && url.query().is_none()
        && url.fragment().is_none())
    .then_some(url)
}

pub(crate) async fn protected_read(
    endpoint: &str,
    credential: &Path,
    budget: Duration,
    legacy: bool,
    request: ReadRequest<'_>,
) -> Result<Value, &'static str> {
    let url = fixture_endpoint(endpoint).ok_or("unqualified_fixture_endpoint")?;
    let token = read_fixture_bearer(credential).map_err(|_| "unqualified_fixture_credential")?;
    read_endpoint(url, budget, legacy, Some(token), request).await
}

#[derive(Debug, Serialize)]
#[serde(tag = "failure", rename_all = "snake_case")]
pub(crate) enum ReadFailure {
    Unobserved { reason: &'static str },
    Tool { evidence: Option<QualifiedError> },
}
impl ReadFailure {
    fn reason(&self) -> &'static str {
        match self {
            Self::Unobserved { reason } => reason,
            Self::Tool { .. } => "owner_tool_error",
        }
    }
}
fn unknown(reason: &'static str) -> ReadFailure {
    ReadFailure::Unobserved { reason }
}

pub(crate) async fn read_endpoint(
    url: reqwest::Url,
    budget: Duration,
    legacy: bool,
    bearer: Option<String>,
    request: ReadRequest<'_>,
) -> Result<Value, &'static str> {
    read_endpoint_typed(url, budget, legacy, bearer, request)
        .await
        .map_err(|e| e.reason())
}

pub(crate) async fn read_endpoint_typed(
    url: reqwest::Url,
    budget: Duration,
    legacy: bool,
    bearer: Option<String>,
    request: ReadRequest<'_>,
) -> Result<Value, ReadFailure> {
    let tool = request.tool();
    let observed = tokio::time::timeout(budget, async {
        let Ok(http) = reqwest::Client::builder()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .retry(reqwest::retry::never())
            .timeout(budget)
            .build()
        else {
            return Err(unknown("client_configuration"));
        };
        let mut config = StreamableHttpClientTransportConfig::with_uri(url.as_str());
        if let Some(token) = bearer {
            config = config.auth_header(token);
        }
        config.max_json_response_size = 1024 * 1024;
        config.max_sse_event_size = 1024 * 1024;
        config.max_error_response_size = 0;
        config.reinit_on_expired_session = false;
        config.max_concurrent_requests = 1;
        let transport = StreamableHttpClientTransport::with_client(http, config);
        let Ok(client) = ClientConfig::default()
            .serve_with_lifecycle(
                transport,
                if legacy {
                    ClientLifecycleMode::Initialize
                } else {
                    ClientLifecycleMode::Auto {
                        preferred_versions: vec![ProtocolVersion::V_2026_07_28],
                        legacy_version: Some(ProtocolVersion::V_2025_11_25),
                    }
                },
            )
            .await
        else {
            return Err(unknown("negotiation_failed"));
        };
        let response = client.call_tool(request.params()).await;
        let outcome = match response {
            Ok(result) if result.is_error == Some(true) => {
                let evidence = serde_json::to_value(&result)
                    .ok()
                    .and_then(|v| owner_error::decode(&v, "runtime.linux", tool));
                Err(ReadFailure::Tool { evidence })
            }
            Ok(result) => result
                .structured_content
                .ok_or_else(|| unknown("structured_result_absent")),
            Err(_) => Err(unknown("protocol_or_transport_failed")),
        };
        let _ = client.cancel().await;
        outcome
    })
    .await;
    observed.unwrap_or_else(|_| Err(unknown("observation_deadline")))
}
