use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use time::{format_description::well_known::Rfc3339, OffsetDateTime};

use crate::errors::KernelError;

pub fn canonical_json(value: &Value) -> Result<String, KernelError> {
    let normalized = sort_json(value);
    serde_json::to_string(&normalized)
        .map_err(|err| KernelError::CanonicalizationFailed(err.to_string()))
}

pub fn sha256_digest(value: &Value) -> Result<String, KernelError> {
    let canonical = canonical_json(value)?;
    let mut hasher = Sha256::new();
    hasher.update(canonical.as_bytes());
    Ok(format!("sha256:{}", hex::encode(hasher.finalize())))
}

fn sort_json(value: &Value) -> Value {
    match value {
        Value::Array(items) => Value::Array(items.iter().map(sort_json).collect()),
        Value::Object(map) => {
            let mut sorted = Map::new();
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort();
            for key in keys {
                sorted.insert(key.clone(), sort_json(&map[key]));
            }
            Value::Object(sorted)
        }
        scalar => scalar.clone(),
    }
}

pub fn parse_rfc3339(value: &str) -> Result<OffsetDateTime, KernelError> {
    OffsetDateTime::parse(value, &Rfc3339).map_err(|err| KernelError::InvalidTime(err.to_string()))
}

pub(crate) fn compare_rfc3339(left: &str, right: &str) -> Result<std::cmp::Ordering, KernelError> {
    Ok(parse_rfc3339(left)?.cmp(&parse_rfc3339(right)?))
}
