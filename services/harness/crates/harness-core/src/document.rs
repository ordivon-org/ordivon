use crate::encode::write_canonical;
use crate::error::CanonicalError;
use crate::parse::{loads_strict, MAX_NESTING};
use std::collections::BTreeMap;

/// Integer decimal text is used instead of i64/u64 or f64 to preserve Python
/// JSON's arbitrary-precision integer semantics in the supported input range.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum CanonicalValue {
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
pub struct CanonicalDocument(pub(crate) CanonicalValue);

/// Minimal safe construction and read surface for the Rust Agent Loop.
/// No Provider/Tool schema, PG writer or independent JSON serializer is owned here.
/// Invalid decimal integers, duplicate object keys and excessive nesting
/// cannot enter the sealed value through these constructors.
impl CanonicalDocument {
    pub fn null() -> Self {
        Self(CanonicalValue::Null)
    }

    pub fn boolean(value: bool) -> Self {
        Self(CanonicalValue::Bool(value))
    }

    pub fn string(value: impl Into<String>) -> Self {
        Self(CanonicalValue::String(value.into()))
    }

    pub fn integer_from_decimal(value: &str) -> Result<Self, CanonicalError> {
        let parsed = loads_strict(value)?;
        if matches!(&parsed.0, CanonicalValue::Integer(_)) {
            Ok(parsed)
        } else {
            Err(CanonicalError::NonIntegerNumber)
        }
    }

    pub fn array(items: Vec<Self>) -> Result<Self, CanonicalError> {
        let value = CanonicalValue::Array(items.into_iter().map(|item| item.0).collect());
        if nesting_depth(&value) > MAX_NESTING {
            return Err(CanonicalError::ExcessiveNesting);
        }
        Ok(Self(value))
    }

    pub fn object(entries: Vec<(String, Self)>) -> Result<Self, CanonicalError> {
        let mut fields = BTreeMap::new();
        for (key, value) in entries {
            if fields.insert(key.clone(), value.0).is_some() {
                return Err(CanonicalError::DuplicateKey(key));
            }
        }
        let value = CanonicalValue::Object(fields);
        if nesting_depth(&value) > MAX_NESTING {
            return Err(CanonicalError::ExcessiveNesting);
        }
        Ok(Self(value))
    }

    pub fn get(&self, key: &str) -> Option<Self> {
        match &self.0 {
            CanonicalValue::Object(fields) => fields.get(key).cloned().map(Self),
            _ => None,
        }
    }

    pub fn as_integer_decimal(&self) -> Option<&str> {
        match &self.0 {
            CanonicalValue::Integer(text) => Some(text),
            _ => None,
        }
    }

    pub fn as_string(&self) -> Option<&str> {
        match &self.0 {
            CanonicalValue::String(text) => Some(text),
            _ => None,
        }
    }

    pub fn as_bool(&self) -> Option<bool> {
        match &self.0 {
            CanonicalValue::Bool(value) => Some(*value),
            _ => None,
        }
    }
}

fn nesting_depth(value: &CanonicalValue) -> usize {
    match value {
        CanonicalValue::Array(items) => 1 + items.iter().map(nesting_depth).max().unwrap_or(0),
        CanonicalValue::Object(fields) => 1 + fields.values().map(nesting_depth).max().unwrap_or(0),
        _ => 0,
    }
}

/// Read-only borrowed view into a validated Canonical Document.
#[derive(Clone, Copy, Debug)]
pub struct CanonicalRef<'a>(&'a CanonicalValue);

impl CanonicalDocument {
    /// Borrow the sealed canonical root without cloning or lossy JSON conversion.
    pub fn as_borrowed(&self) -> CanonicalRef<'_> {
        CanonicalRef(&self.0)
    }

    /// Inspect an object field without re-parsing or lossy i64/f64 conversion.
    pub fn field(&self, key: &str) -> Option<CanonicalRef<'_>> {
        CanonicalRef(&self.0).field(key)
    }
    pub fn is_object(&self) -> bool {
        matches!(self.0, CanonicalValue::Object(_))
    }
    pub fn object_len(&self) -> Option<usize> {
        CanonicalRef(&self.0).object_len()
    }

    /// Borrow an array element without decoding through lossy serde_json::Value.
    pub fn index(&self, index: usize) -> Option<CanonicalRef<'_>> {
        CanonicalRef(&self.0).index(index)
    }

    /// Keep object iteration read-only; the original sorted keys remain sealed.
    pub fn object_entries(&self) -> Option<impl Iterator<Item = (&str, CanonicalRef<'_>)>> {
        match &self.0 {
            CanonicalValue::Object(entries) => Some(
                entries
                    .iter()
                    .map(|(key, value)| (key.as_str(), CanonicalRef(value))),
            ),
            _ => None,
        }
    }
}

impl<'a> CanonicalRef<'a> {
    pub fn field(self, key: &str) -> Option<Self> {
        match self.0 {
            CanonicalValue::Object(values) => values.get(key).map(Self),
            _ => None,
        }
    }
    pub fn as_str(self) -> Option<&'a str> {
        match self.0 {
            CanonicalValue::String(value) => Some(value),
            _ => None,
        }
    }
    pub fn integer_text(self) -> Option<&'a str> {
        match self.0 {
            CanonicalValue::Integer(value) => Some(value),
            _ => None,
        }
    }
    pub fn as_bool(self) -> Option<bool> {
        match self.0 {
            CanonicalValue::Bool(value) => Some(*value),
            _ => None,
        }
    }
    pub fn is_null(self) -> bool {
        matches!(self.0, CanonicalValue::Null)
    }
    pub fn canonical_bytes(self) -> Vec<u8> {
        let mut output = String::new();
        write_canonical(self.0, &mut output);
        output.into_bytes()
    }
    pub fn object_len(self) -> Option<usize> {
        match self.0 {
            CanonicalValue::Object(entries) => Some(entries.len()),
            _ => None,
        }
    }
    /// Borrow sorted fields without exposing internal mutable representation.
    pub fn object_entries(self) -> Option<impl Iterator<Item = (&'a str, CanonicalRef<'a>)>> {
        match self.0 {
            CanonicalValue::Object(entries) => Some(
                entries
                    .iter()
                    .map(|(key, value)| (key.as_str(), CanonicalRef(value))),
            ),
            _ => None,
        }
    }
    pub fn array_len(self) -> Option<usize> {
        match self.0 {
            CanonicalValue::Array(entries) => Some(entries.len()),
            _ => None,
        }
    }

    pub fn index(self, index: usize) -> Option<Self> {
        match self.0 {
            CanonicalValue::Array(entries) => entries.get(index).map(Self),
            _ => None,
        }
    }
}
