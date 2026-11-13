use crate::document::{CanonicalDocument, CanonicalValue};
use crate::error::CanonicalError;
use crate::parse::loads_strict;
use sha2::{Digest, Sha256};

pub(crate) fn write_canonical(value: &CanonicalValue, output: &mut String) {
    match value {
        CanonicalValue::Null => output.push_str("null"),
        CanonicalValue::Bool(v) => output.push_str(if *v { "true" } else { "false" }),
        CanonicalValue::Integer(v) => output.push_str(v),
        CanonicalValue::String(v) => output.push_str(
            &serde_json::to_string(v).expect("UTF-8 Rust String always JSON serializable"),
        ),
        CanonicalValue::Array(values) => {
            output.push('[');
            for (index, value) in values.iter().enumerate() {
                if index > 0 {
                    output.push(',');
                }
                write_canonical(value, output);
            }
            output.push(']');
        }
        CanonicalValue::Object(entries) => {
            output.push('{');
            for (index, (key, value)) in entries.iter().enumerate() {
                if index > 0 {
                    output.push(',');
                }
                output.push_str(
                    &serde_json::to_string(key)
                        .expect("UTF-8 Rust String always JSON serializable"),
                );
                output.push(':');
                write_canonical(value, output);
            }
            output.push('}');
        }
    }
}

/// Native canonical bytes, sorted object keys.
pub fn canonical_bytes(value: &CanonicalDocument) -> Vec<u8> {
    let mut output = String::new();
    write_canonical(&value.0, &mut output);
    output.into_bytes()
}

pub fn canonical_bytes_from_json(input: &str) -> Result<Vec<u8>, CanonicalError> {
    loads_strict(input).map(|value| canonical_bytes(&value))
}

pub fn digest_bytes(input: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(input)))
}

pub fn canonical_digest_from_json(input: &str) -> Result<String, CanonicalError> {
    canonical_bytes_from_json(input).map(|bytes| digest_bytes(&bytes))
}
