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
