//! Strict natural Runtime ArtifactDescriptor receiver; not byte or domain verification.
use crate::artifact_inventory;
use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct Descriptor {
    artifact_id: String,
    attempt_id: String,
    kind: String,
    digest: String,
    retained_bytes: u64,
    #[serde(skip_serializing_if = "Option::is_none")]
    dropped_bytes: Option<u64>,
    truncated: bool,
}

impl Descriptor {
    pub(crate) fn artifact_id(&self) -> &str {
        &self.artifact_id
    }
    pub(crate) fn digest(&self) -> &str {
        &self.digest
    }
    pub(crate) fn retained_bytes(&self) -> u64 {
        self.retained_bytes
    }
}

fn trimmed(s: &str) -> bool {
    !s.is_empty()
        && s == s.trim_matches(|c: char| c.is_whitespace() || ('\u{1c}'..='\u{1f}').contains(&c))
}

fn digest(s: &str) -> bool {
    s.strip_prefix("sha256:").is_some_and(|h| {
        h.len() == 64
            && h.bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    })
}

pub(crate) fn decode(row: &Value) -> Option<Descriptor> {
    // The natural producer omits absent droppedBytes; explicit null is not its wire contract.
    if row.get("droppedBytes").is_some_and(|v| !v.is_u64()) {
        return None;
    }
    let d: Descriptor = serde_json::from_value(row.clone()).ok()?;
    (trimmed(&d.artifact_id) && trimmed(&d.attempt_id) && trimmed(&d.kind) && digest(&d.digest))
        .then_some(d)
}

#[derive(Debug, PartialEq, Eq, Serialize)]
pub(crate) struct Qualification {
    identity_complete: Option<bool>,
    metadata_complete: Option<bool>,
    descriptors: Vec<Descriptor>,
}

pub(crate) fn qualify(payload: &Value, count: &Value) -> Qualification {
    let identity_complete = artifact_inventory::project(payload, count).complete();
    let descriptors: Option<Vec<_>> = payload
        .get("artifacts")
        .and_then(Value::as_array)
        .and_then(|rows| rows.iter().map(decode).collect());
    let metadata_complete = identity_complete.map(|complete| complete && descriptors.is_some());
    Qualification {
        identity_complete,
        metadata_complete,
        descriptors: if metadata_complete == Some(true) {
            descriptors.unwrap_or_default()
        } else {
            Vec::new()
        },
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    use serde_json::json;

    fn row(id: &str) -> Value {
        json!({"artifactId":id,"attemptId":"opaque-attempt","kind":"future-kind",
            "digest":format!("sha256:{}", "a".repeat(64)),"retainedBytes":0,"truncated":false})
    }

    #[test]
    fn identity_coverage_is_not_metadata_or_content() {
        let mut malformed = row("opaque-id");
        malformed["digest"] = json!(format!("sha256:{}", "z".repeat(64)));
        let q = qualify(&json!({"artifacts":[malformed]}), &json!(1));
        assert_eq!(q.identity_complete, Some(true));
        assert_eq!(q.metadata_complete, Some(false));
        assert!(q.descriptors.is_empty());
        let good = row("opaque-id");
        let q = qualify(&json!({"artifacts":[good.clone()]}), &json!(1));
        assert_eq!(q.metadata_complete, Some(true));
        assert_eq!(serde_json::to_value(q.descriptors).unwrap(), json!([good]));
        assert_eq!(
            qualify(&json!({"artifacts":[good.clone(),good]}), &json!(2)).metadata_complete,
            Some(false)
        );
        assert_eq!(
            qualify(&json!({"artifacts":[]}), &json!(0)).metadata_complete,
            Some(true)
        );
        assert_eq!(
            qualify(&json!({"artifacts":[]}), &Value::Null).metadata_complete,
            None
        );
    }

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(512))]
        #[test]
        fn generated_exact_descriptor_and_single_field_corruption(
            id in "[a-z0-9]{1,24}", attempt in "[a-z0-9]{1,24}",
            bytes in any::<u64>(), dropped in prop::option::of(any::<u64>()),
            truncated in any::<bool>(), field in 0u8..12,
        ) {
            let mut good=row(&id);
            good["attemptId"]=json!(attempt);
            good["retainedBytes"]=json!(bytes);
            good["truncated"]=json!(truncated);
            if let Some(n)=dropped { good["droppedBytes"]=json!(n); }
            let q=qualify(&json!({"artifacts":[good.clone()]}),&json!(1));
            prop_assert_eq!(q.metadata_complete,Some(true));
            prop_assert_eq!(serde_json::to_value(q.descriptors).unwrap(),json!([good.clone()]));
            match field {
                0=>good["digest"]=json!(format!("sha256:{}", "z".repeat(64))),
                1=>good["digest"]=json!(format!("sha256:{}", "A".repeat(64))),
                2=>good["attemptId"]=json!(" "),
                3=>good["kind"]=json!(" kind "),
                4=>good["retainedBytes"]=json!(-1),
                5=>good["retainedBytes"]=json!(true),
                6=>good["truncated"]=json!(0),
                7=>good["droppedBytes"]=Value::Null,
                8=>good["droppedBytes"]=json!(-1),
                9=>{good.as_object_mut().unwrap().remove("attemptId");},
                10=>good["unexpected"]=json!(true),
                _=>good["artifactId"]=json!(" x "),
            }
            let q=qualify(&json!({"artifacts":[good]}),&json!(1));
            prop_assert_eq!(q.metadata_complete,Some(false));
            prop_assert!(q.descriptors.is_empty());
        }
    }
}
