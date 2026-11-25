//! Read-only native recipient refinement. No effect, credential or Owner authority.
//! The fixture endpoint is operator-selected, never a public tool argument.

use crate::logic::{valid_status_envelope, valid_target_inventory};
use crate::owner_credential::read_fixture_bearer;
use rmcp::{
    ClientLifecycleMode, ClientServiceExt,
    model::{CallToolRequestParams, CallToolResult, ClientConfig, ProtocolVersion},
    transport::streamable_http_client::{
        StreamableHttpClientTransport, StreamableHttpClientTransportConfig,
    },
};
use serde::Serialize;
use serde_json::json;
use std::{path::Path, time::Duration};

#[derive(Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "standing", rename_all = "snake_case")]
pub enum Observation {
    // This is a syntactically qualified Owner report, not physical readiness.
    Reported { configured: bool, available: bool },
    Unobserved { reason: &'static str },
}

fn unknown(reason: &'static str) -> Observation {
    Observation::Unobserved { reason }
}

fn fixture_endpoint(endpoint: &str) -> Option<reqwest::Url> {
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

fn project(result: CallToolResult, expected_node: &str) -> Observation {
    if result.is_error == Some(true) {
        return unknown("owner_tool_error");
    }
    let Some(value) = result.structured_content else {
        return unknown("structured_result_absent");
    };
    if !valid_status_envelope(&value) {
        return unknown("invalid_status_envelope");
    }
    let node = &value["node"];
    if expected_node.is_empty()
        || node["nodeId"].as_str() != Some(expected_node)
        || node["platform"].as_str() != Some("linux")
        || node["native"].as_bool() != Some(true)
    {
        return unknown("unqualified_node");
    }
    if !valid_target_inventory(&value["targets"]) {
        return unknown("invalid_target_inventory");
    }
    let Some(target) = value["targets"]
        .as_array()
        .and_then(|rows| rows.iter().find(|row| row["target"] == "local_linux"))
    else {
        return unknown("target_not_observed");
    };
    // B03 selected target's explicitly supplied execution context inventory
    // is list-valued; absent remains compatible with older Owner reports.
    if target
        .get("executionProfiles")
        .is_some_and(|v| !v.is_array())
    {
        return unknown("invalid_execution_context_inventory");
    }
    Observation::Reported {
        configured: target["configured"].as_bool().expect("qualified inventory"),
        available: target["available"].as_bool().expect("qualified inventory"),
    }
}

pub async fn observe_runtime(
    endpoint: &str,
    expected_node: &str,
    budget: Duration,
    legacy: bool,
) -> Observation {
    let Some(url) = fixture_endpoint(endpoint) else {
        return unknown("unqualified_fixture_endpoint");
    };
    observe_endpoint(url, expected_node, budget, legacy, None).await
}

pub async fn observe_protected_runtime(
    endpoint: &str,
    expected_node: &str,
    credential: &Path,
    budget: Duration,
    legacy: bool,
) -> Observation {
    // Qualify route before opening a secret. No anonymous fallback.
    let Some(url) = fixture_endpoint(endpoint) else {
        return unknown("unqualified_fixture_endpoint");
    };
    let Ok(token) = read_fixture_bearer(credential) else {
        return unknown("unqualified_fixture_credential");
    };
    observe_endpoint(url, expected_node, budget, legacy, Some(token)).await
}

async fn observe_endpoint(
    url: reqwest::Url,
    expected_node: &str,
    budget: Duration,
    legacy: bool,
    bearer: Option<String>,
) -> Observation {
    let observed = tokio::time::timeout(budget, async {
        let Ok(http) = reqwest::Client::builder()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .retry(reqwest::retry::never())
            .timeout(budget)
            .build()
        else {
            return unknown("client_configuration");
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
            return unknown("negotiation_failed");
        };
        // No generic tool dispatch or automatic MRTR. Read exactly one tool.
        let arguments = json!({"schemaVersion": 1});
        let response = client
            .call_tool(
                CallToolRequestParams::new("runtime.describe")
                    .with_arguments(arguments.as_object().expect("literal object").clone()),
            )
            .await;
        let observation = match response {
            Ok(result) => project(result, expected_node),
            Err(_) => unknown("protocol_or_transport_failed"),
        };
        let _ = client.cancel().await;
        observation
    })
    .await;
    observed.unwrap_or_else(|_| unknown("observation_deadline"))
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use rmcp::model::CallToolResult;
    use serde_json::Value;

    fn fixture() -> Value {
        json!({
            "schemaVersion":1,
            "node":{"nodeId":"fixture-linux","platform":"linux","native":true},
            "targets":[{"target":"local_linux","configured":true,"available":false}]
        })
    }

    #[test]
    fn distinct_reported_false_and_unknown() {
        let v = fixture();
        assert_eq!(
            project(CallToolResult::structured(v.clone()), "fixture-linux"),
            Observation::Reported {
                configured: true,
                available: false
            }
        );
        for bad in [
            json!(null),
            json!({"schemaVersion":true}),
            json!({"schemaVersion":1,"node":v["node"],"targets":[{"target":"local_linux","configured":false,"available":true}]}),
            json!({"schemaVersion":1,"node":v["node"],"targets":[v["targets"][0],v["targets"][0]]}),
            json!({"schemaVersion":1,"node":v["node"],"targets":[]}),
        ] {
            assert!(matches!(
                project(CallToolResult::structured(bad), "fixture-linux"),
                Observation::Unobserved { .. }
            ));
        }
        assert_eq!(
            project(CallToolResult::structured(v), "other"),
            unknown("unqualified_node")
        );
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(256))]
        #[test]
        fn explicit_context_container_qualification(
            context in prop_oneof![
                Just(Value::Null), any::<bool>().prop_map(|v|json!(v)),
                any::<i64>().prop_map(|v|json!(v)),
                "[a-z]{0,12}".prop_map(|v|json!(v)),
                Just(json!({})), prop::collection::vec("[a-z]{0,8}",0..8).prop_map(|v|json!(v)),
            ],
            available in any::<bool>(),
        ) {
            let mut v=fixture();
            v["targets"][0]["available"]=json!(available);
            let expected=if context.is_array() {
                Observation::Reported {configured:true,available}
            } else {
                unknown("invalid_execution_context_inventory")
            };
            v["targets"][0]["executionProfiles"]=context;
            prop_assert_eq!(project(CallToolResult::structured(v),"fixture-linux"),expected);
        }
    }

    #[test]
    fn operator_fixture_endpoint_has_no_arbitrary_egress() {
        assert!(fixture_endpoint("http://127.0.0.1:9999/mcp").is_some());
        for bad in [
            "https://127.0.0.1:9999/mcp",
            "http://localhost:9999/mcp",
            "http://127.0.0.1:9999/mcp?x=1",
            "http://127.0.0.1:9999/mcp#x",
            "http://user@127.0.0.1:9999/mcp",
            "http://127.0.0.1/mcp",
            "http://127.0.0.1:9999/other",
            "http://192.0.2.1:9999/mcp",
        ] {
            assert!(fixture_endpoint(bad).is_none(), "{bad}");
        }
    }
}
