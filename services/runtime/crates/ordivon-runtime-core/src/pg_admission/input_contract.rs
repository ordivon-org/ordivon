//! Pure admission-request structure and unambiguous JSON validation.
//! No PostgreSQL I/O, process launch, or principal/role grant happens here.
use super::PgAdmissionError;
use serde::de::{self, MapAccess, SeqAccess, Visitor};
use serde::Deserialize;
use std::collections::HashSet;

#[derive(Clone)]
pub struct PgAdmissionInput {
    pub job_id: String,
    pub attempt_id: String,
    pub reservation_id: String,
    pub principal: String,
    pub client_request_id: String,
    pub request_digest: String,
    pub operation_digest: String,
    pub workspace_id: String,
    pub workspace_snapshot_json: String,
    pub execution_plan_json: String,
    pub execution_plan_digest: String,
    pub launch_token_digest: String,
    pub bundle_path: String,
    pub unit_name: String,
    pub global_limit: i32,
    pub created_at_ms: i64,
    pub expected_source_sha256: String,
}

/// One-pass JSON admission: reject duplicate members at ANY depth, including
/// keys that become identical after JSON escape decoding. Do not retain a
/// second JSON AST; the durable typed consumers parse only after this gate.
struct JsonObjectWithUniqueKeys(bool);

impl<'de> Deserialize<'de> for JsonObjectWithUniqueKeys {
    fn deserialize<D: serde::Deserializer<'de>>(input: D) -> Result<Self, D::Error> {
        struct UniqueKeysVisitor;
        impl<'de> Visitor<'de> for UniqueKeysVisitor {
            type Value = JsonObjectWithUniqueKeys;

            fn expecting(&self, fmt: &mut std::fmt::Formatter) -> std::fmt::Result {
                write!(fmt, "a JSON value with unique object members")
            }

            fn visit_bool<E: de::Error>(self, _: bool) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_i64<E: de::Error>(self, _: i64) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_u64<E: de::Error>(self, _: u64) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_f64<E: de::Error>(self, _: f64) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_str<E: de::Error>(self, _: &str) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_string<E: de::Error>(self, _: String) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_unit<E: de::Error>(self) -> Result<Self::Value, E> {
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_seq<A: SeqAccess<'de>>(self, mut seq: A) -> Result<Self::Value, A::Error> {
                while seq.next_element::<JsonObjectWithUniqueKeys>()?.is_some() {}
                Ok(JsonObjectWithUniqueKeys(false))
            }
            fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Self::Value, A::Error> {
                let mut keys = HashSet::new();
                while let Some((key, _)) = map.next_entry::<String, JsonObjectWithUniqueKeys>()? {
                    if !keys.insert(key) {
                        return Err(de::Error::custom("duplicate JSON object member"));
                    }
                }
                Ok(JsonObjectWithUniqueKeys(true))
            }
        }
        input.deserialize_any(UniqueKeysVisitor)
    }
}

pub(super) fn unambiguous_json_object(raw: &str) -> bool {
    matches!(
        serde_json::from_str::<JsonObjectWithUniqueKeys>(raw),
        Ok(JsonObjectWithUniqueKeys(true))
    )
}

impl PgAdmissionInput {
    pub(super) fn validate(&self) -> Result<(), PgAdmissionError> {
        let strings = [
            &self.job_id,
            &self.attempt_id,
            &self.reservation_id,
            &self.principal,
            &self.client_request_id,
            &self.request_digest,
            &self.operation_digest,
            &self.workspace_id,
            &self.workspace_snapshot_json,
            &self.execution_plan_json,
            &self.execution_plan_digest,
            &self.launch_token_digest,
            &self.bundle_path,
            &self.unit_name,
        ];
        if strings.iter().any(|s| s.is_empty())
            || self.created_at_ms < 0
            || self.global_limit < 0
            || self.expected_source_sha256.len() != 64
            || !self
                .expected_source_sha256
                .bytes()
                .all(|b| b.is_ascii_hexdigit())
            // Durable Runtime consumers decode both carriers as records.
            // Parsing any JSON value alone admits null/scalars/arrays that
            // cannot satisfy their existing typed source contracts.
            || !unambiguous_json_object(&self.workspace_snapshot_json)
            || !unambiguous_json_object(&self.execution_plan_json)
        {
            return Err(PgAdmissionError::InvalidInput);
        }
        Ok(())
    }
}
