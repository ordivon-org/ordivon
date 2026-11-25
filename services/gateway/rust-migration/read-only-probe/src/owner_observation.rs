//! Read-only native recipient refinement. No effect, credential or Owner authority.
//! The fixture endpoint is operator-selected, never a public tool argument.

use crate::logic::{valid_status_envelope, valid_target_inventory};
use crate::owner_transport::{ReadRequest, fixture_endpoint, protected_read, read_endpoint};
use serde::Serialize;
use serde_json::Value;
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

fn project(value: Value, expected_node: &str) -> Observation {
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
    match read_endpoint(url, budget, legacy, None, ReadRequest::Describe).await {
        Ok(value) => project(value, expected_node),
        Err(reason) => unknown(reason),
    }
}

pub async fn observe_protected_runtime(
    endpoint: &str,
    expected_node: &str,
    credential: &Path,
    budget: Duration,
    legacy: bool,
) -> Observation {
    match protected_read(endpoint, credential, budget, legacy, ReadRequest::Describe).await {
        Ok(value) => project(value, expected_node),
        Err(reason) => unknown(reason),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use serde_json::json;

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
            project(v.clone(), "fixture-linux"),
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
                project(bad, "fixture-linux"),
                Observation::Unobserved { .. }
            ));
        }
        assert_eq!(project(v, "other"), unknown("unqualified_node"));
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
            prop_assert_eq!(project(v,"fixture-linux"),expected);
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
