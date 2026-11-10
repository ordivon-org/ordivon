//! Byte-compatible representation of the existing Python anc_canonical contract.
//!
//! This is intentionally NOT RFC 8785/JCS. The authoritative legacy encoder is
//! services/harness/src/anc_canonical/canonical.py. Keep the byte format stable
//! until a versioned consumer migration has been proven.
#![forbid(unsafe_code)]

use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fmt;

/// Integer decimal text is used instead of i64/u64 or f64 to preserve Python
/// JSON's arbitrary-precision integer semantics in the supported input range.
#[derive(Debug, Clone, PartialEq, Eq)]
enum CanonicalValue {
    Null,
    Bool(bool),
    Integer(String),
    String(String),
    Array(Vec<CanonicalValue>),
    Object(BTreeMap<String, CanonicalValue>),
}

/// Sealed document produced by the strict parser. Invalid integer spellings
/// cannot be constructed by consumers before a versioned typed API exists.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CanonicalDocument(CanonicalValue);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CanonicalError {
    InvalidJson,
    DuplicateKey(String),
    NonIntegerNumber,
    IntegerDigitLimit,
    ExcessiveNesting,
}

impl fmt::Display for CanonicalError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidJson => write!(f, "invalid JSON"),
            Self::DuplicateKey(key) => write!(f, "duplicate JSON object key: {key}"),
            Self::NonIntegerNumber => write!(f, "non-integer JSON number is forbidden"),
            Self::IntegerDigitLimit => write!(f, "integer exceeds default Python JSON digit limit"),
            Self::ExcessiveNesting => write!(f, "JSON nesting exceeds bounded parser limit"),
        }
    }
}
impl std::error::Error for CanonicalError {}

/// Python's default sys.int_max_str_digits is 4300 (Python >=3.11).
/// The reference interpreter's actual setting must be qualified before use
/// in an environment that changes this configuration.
const PYTHON_DEFAULT_MAX_INTEGER_DIGITS: usize = 4300;
const MAX_NESTING: usize = 512;

struct Parser<'a> {
    input: &'a str,
    position: usize,
}

impl<'a> Parser<'a> {
    fn remaining(&self) -> &'a str {
        &self.input[self.position..]
    }
    fn skip_whitespace(&mut self) {
        while let Some(&b' ' | &b'\n' | &b'\r' | &b'\t') = self.input.as_bytes().get(self.position)
        {
            self.position += 1;
        }
    }
    fn take(&mut self, expected: u8) -> bool {
        if self.input.as_bytes().get(self.position) == Some(&expected) {
            self.position += 1;
            true
        } else {
            false
        }
    }
    fn parse_string(&mut self) -> Result<String, CanonicalError> {
        if self.input.as_bytes().get(self.position) != Some(&b'"') {
            return Err(CanonicalError::InvalidJson);
        }
        let start = self.position;
        let mut at = start + 1;
        let bytes = self.input.as_bytes();
        while at < bytes.len() {
            match bytes[at] {
                b'\\' => at += 2,
                b'"' => {
                    let value = serde_json::from_str::<String>(&self.input[start..=at])
                        .map_err(|_| CanonicalError::InvalidJson)?;
                    self.position = at + 1;
                    return Ok(value);
                }
                _ => at += 1,
            }
        }
        Err(CanonicalError::InvalidJson)
    }
    fn parse_integer(&mut self) -> Result<CanonicalValue, CanonicalError> {
        let begin = self.position;
        self.take(b'-');
        let start_digits = self.position;
        if self.take(b'0') {
            if self
                .input
                .as_bytes()
                .get(self.position)
                .is_some_and(u8::is_ascii_digit)
            {
                return Err(CanonicalError::InvalidJson);
            }
        } else {
            match self.input.as_bytes().get(self.position) {
                Some(b'1'..=b'9') => {
                    self.position += 1;
                    while self
                        .input
                        .as_bytes()
                        .get(self.position)
                        .is_some_and(u8::is_ascii_digit)
                    {
                        self.position += 1;
                    }
                }
                _ => return Err(CanonicalError::InvalidJson),
            }
        }
        if self
            .input
            .as_bytes()
            .get(self.position)
            .is_some_and(|byte| matches!(byte, b'.' | b'e' | b'E'))
        {
            return Err(CanonicalError::NonIntegerNumber);
        }
        if self.position - start_digits > PYTHON_DEFAULT_MAX_INTEGER_DIGITS {
            return Err(CanonicalError::IntegerDigitLimit);
        }
        let value = &self.input[begin..self.position];
        Ok(CanonicalValue::Integer(
            if value == "-0" { "0" } else { value }.to_owned(),
        ))
    }
    fn parse_value(&mut self, depth: usize) -> Result<CanonicalValue, CanonicalError> {
        if depth > MAX_NESTING {
            return Err(CanonicalError::ExcessiveNesting);
        }
        self.skip_whitespace();
        match self.input.as_bytes().get(self.position) {
            Some(b'n') if self.remaining().starts_with("null") => {
                self.position += 4;
                Ok(CanonicalValue::Null)
            }
            Some(b't') if self.remaining().starts_with("true") => {
                self.position += 4;
                Ok(CanonicalValue::Bool(true))
            }
            Some(b'f') if self.remaining().starts_with("false") => {
                self.position += 5;
                Ok(CanonicalValue::Bool(false))
            }
            Some(b'"') => self.parse_string().map(CanonicalValue::String),
            Some(b'[') => {
                self.position += 1;
                let mut values = Vec::new();
                self.skip_whitespace();
                if self.take(b']') {
                    return Ok(CanonicalValue::Array(values));
                }
                loop {
                    values.push(self.parse_value(depth + 1)?);
                    self.skip_whitespace();
                    if self.take(b']') {
                        break;
                    }
                    if !self.take(b',') {
                        return Err(CanonicalError::InvalidJson);
                    }
                }
                Ok(CanonicalValue::Array(values))
            }
            Some(b'{') => {
                self.position += 1;
                let mut entries = BTreeMap::new();
                self.skip_whitespace();
                if self.take(b'}') {
                    return Ok(CanonicalValue::Object(entries));
                }
                loop {
                    self.skip_whitespace();
                    let key = self.parse_string()?;
                    self.skip_whitespace();
                    if !self.take(b':') {
                        return Err(CanonicalError::InvalidJson);
                    }
                    let value = self.parse_value(depth + 1)?;
                    if entries.insert(key.clone(), value).is_some() {
                        return Err(CanonicalError::DuplicateKey(key));
                    }
                    self.skip_whitespace();
                    if self.take(b'}') {
                        break;
                    }
                    if !self.take(b',') {
                        return Err(CanonicalError::InvalidJson);
                    }
                }
                Ok(CanonicalValue::Object(entries))
            }
            Some(b'-' | b'0'..=b'9') => self.parse_integer(),
            _ => Err(CanonicalError::InvalidJson),
        }
    }
}

/// Strictly decode the same domain as the current Python anc_canonical.loads_strict:
/// null/bool/integers/strings/lists/maps, no floats, NaNs or duplicate object keys.
pub fn loads_strict(input: &str) -> Result<CanonicalDocument, CanonicalError> {
    let mut parser = Parser { input, position: 0 };
    let value = parser.parse_value(0)?;
    parser.skip_whitespace();
    if parser.position != input.len() {
        return Err(CanonicalError::InvalidJson);
    }
    Ok(CanonicalDocument(value))
}

fn write_canonical(value: &CanonicalValue, output: &mut String) {
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

/// Existing Python json.dumps(sort_keys=True, separators=(',', ':'),
/// ensure_ascii=False, allow_nan=False), serialized as UTF-8 bytes.
/// BTreeMap string order matches Unicode scalar order for valid UTF-8.
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

#[cfg(test)]
mod unit_tests {
    use super::*;

    #[test]
    fn rejects_duplicate_unescaped_key() {
        assert_eq!(
            loads_strict(r#"{"z":1,"\u007a":2}"#),
            Err(CanonicalError::DuplicateKey("z".into()))
        );
    }

    #[test]
    fn no_floating_point_or_nonfinite() {
        for source in ["3.1", "3e2", "-0.0", "NaN", "Infinity", "-Infinity"] {
            assert!(loads_strict(source).is_err(), "{source}");
        }
    }
}
