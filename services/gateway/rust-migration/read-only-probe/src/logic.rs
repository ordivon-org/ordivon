use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Route {
    capability: String,
    owner_id: String,
    category: String,
    owner_tool: Option<String>,
    context_mode: String,
    truth_boundary: String,
    description: String,
    tags: Vec<String>,
    execution_target: Option<String>,
    default_context: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DescriptionInput {
    pub gateway_version: String,
    pub routes: BTreeMap<String, Route>,
    pub configured: BTreeMap<String, bool>,
    pub host_read_route: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct OwnerDescription {
    owner_id: &'static str,
    role: &'static str,
    configured: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct SystemDescription {
    schema_version: u8,
    kind: &'static str,
    gateway_version: String,
    route_digest: String,
    truth_role: &'static str,
    owners: Vec<OwnerDescription>,
    capabilities: Vec<String>,
}

pub fn valid_status_envelope(v: &Value) -> bool {
    v.get("schemaVersion").and_then(Value::as_i64) == Some(1)
}

pub fn valid_target_inventory(v: &Value) -> bool {
    let Some(items) = v.as_array() else {
        return false;
    };
    let mut names = BTreeSet::new();
    items.iter().all(|item| {
        let (Some(name), Some(configured), Some(available)) = (
            item.get("target").and_then(Value::as_str),
            item.get("configured").and_then(Value::as_bool),
            item.get("available").and_then(Value::as_bool),
        ) else {
            return false;
        };
        // Python str.strip also recognizes the four C0 information separators.
        !name
            .trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
            .is_empty()
            && (!available || configured)
            && names.insert(name)
    })
}

pub fn parse_execution_ref(value: &str) -> Option<(&str, &str)> {
    let (owner, native) = value.strip_prefix("ordivon-exec:v1:")?.rsplit_once(':')?;
    if native.is_empty()
        || !matches!(
            owner,
            "runtime.linux" | "runtime.windows" | "runtime.harness"
        )
    {
        return None;
    }
    Some((owner, native))
}

pub fn system_describe(fixture: &DescriptionInput) -> Result<SystemDescription, String> {
    if fixture
        .routes
        .iter()
        .any(|(key, route)| key != &route.capability)
    {
        return Err("route identity mismatch".into());
    }
    let roles = [
        ("runtime.linux", "physical execution owner"),
        ("runtime.windows", "physical execution owner"),
        (
            "runtime.harness",
            "issuer-fenced execution profile of the Linux Runtime owner",
        ),
        ("host", "external semantic continuity owner"),
        (
            "skills",
            "procedural Skill discovery and exact binding owner",
        ),
        (
            "research.composition",
            "non-authoritative Research composition metadata",
        ),
    ];
    let configured = |name: &str| fixture.configured.get(name).copied().unwrap_or(false);
    let owners = roles.map(|(owner, role)| {
        let state = match owner {
            "research.composition" => true,
            "host" => configured("host") || (fixture.host_read_route && configured("host.read")),
            _ => configured(owner),
        };
        OwnerDescription {
            owner_id: owner,
            role,
            configured: state,
        }
    });
    // Value maps use sorted keys with serde_json's default map; the source
    // route payload contains only strings/null/arrays, not float numbers.
    let routes: Vec<Value> = fixture
        .routes
        .values()
        .map(|r| serde_json::to_value(r).expect("route"))
        .collect();
    let bytes = serde_json::to_vec(&routes).map_err(|e| e.to_string())?;
    let digest = Sha256::digest(bytes);
    let hex: String = digest.iter().map(|b| format!("{b:02x}")).collect();
    Ok(SystemDescription {
        schema_version: 1,
        kind: "ordivon.gateway-system-description",
        gateway_version: fixture.gateway_version.clone(),
        route_digest: format!("sha256:{hex}"),
        truth_role: "non-authoritative-routing-projection",
        owners: owners.into(),
        capabilities: fixture.routes.keys().cloned().collect(),
    })
}

#[cfg(test)]
mod property_tests {
    use super::*;
    use proptest::prelude::*;
    use serde_json::json;

    // The oracle is constructed from the input domain, not from the validator.
    fn malformed_boolean() -> impl Strategy<Value = Value> {
        prop_oneof![
            Just(Value::Null),
            any::<i32>().prop_map(|v| json!(v)),
            "[a-z]{0,12}".prop_map(|v| json!(v)),
            Just(json!([])),
            Just(json!({}))
        ]
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(256))]

        #[test]
        fn status_version_is_exact_integer(v in prop_oneof![
            any::<i64>().prop_map(|v| (json!(v),v==1)),
            Just((json!(1),true)), Just((json!(1.0),false)),
            any::<bool>().prop_map(|v| (json!(v),false)),
            "[0-9]{0,10}".prop_map(|v| (json!(v),false)),
            Just((Value::Null,false))
        ]) {
            prop_assert_eq!(valid_status_envelope(&json!({"schemaVersion":v.0})),v.1);
        }

        #[test]
        fn inventory_permutation_and_duplicate_invariants(
            rows in prop::collection::vec((any::<bool>(),any::<bool>()), 1..64),
            selected in any::<usize>(),
        ) {
            let mut inventory:Vec<Value> = rows.iter().enumerate()
                .map(|(i,(configured,requested))| json!({
                    "target": format!("node-{i}"), "configured":configured,
                    "available": *configured && *requested,
                })).collect();
            prop_assert!(valid_target_inventory(&json!(inventory)));
            inventory.reverse();
            prop_assert!(valid_target_inventory(&json!(inventory)));
            let duplicate = inventory[selected % inventory.len()].clone();
            inventory.push(duplicate);
            prop_assert!(!valid_target_inventory(&json!(inventory)));
        }

        #[test]
        fn one_invalid_sibling_invalidates_whole_inventory(
            count in 1usize..64, selected in any::<usize>(),
            value in malformed_boolean(), field in prop_oneof![Just("available"),Just("configured")],
        ) {
            let mut inventory:Vec<Value> = (0..count).map(|i|json!({
                "target":format!("node-{i}"),"configured":true,"available":true,
            })).collect();
            inventory[selected%count][field]=value;
            prop_assert!(!valid_target_inventory(&json!(inventory)));
        }

        #[test]
        fn contradiction_and_missing_identity_are_not_positive(
            count in 1usize..64, selected in any::<usize>(),
        ) {
            let mut inventory:Vec<Value> = (0..count).map(|i|json!({
                "target":format!("node-{i}"),"configured":true,"available":true,
            })).collect();
            let index=selected%count;
            inventory[index]["configured"]=json!(false);
            prop_assert!(!valid_target_inventory(&json!(inventory)));
            inventory[index]["configured"]=json!(true);
            inventory[index]["target"]=json!(" \u{1c}\u{1f}\t");
            prop_assert!(!valid_target_inventory(&json!(inventory)));
        }
    }
}
