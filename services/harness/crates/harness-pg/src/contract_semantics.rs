//! Exact, read-only consumer of Python HarnessRunContract.from_dict v1/v2.
//!
//! CAS identity and Journal revision are necessary but not enough: a forged
//! but self-consistent CAS must not become an authorized Harness Run.
//! This module neither changes storage nor creates a competing admission path.

use std::cmp::Ordering;
use std::collections::BTreeSet;

use ordivon_harness_core::{CanonicalDocument, CanonicalRef};

use super::{corrupted, ReadError};

const CONTRACT_FIELDS: &[&str] = &[
    "schemaVersion",
    "kind",
    "harnessRunId",
    "harnessImplementationId",
    "callerId",
    "callerRunRef",
    "objectiveRef",
    "contextRefs",
    "providerId",
    "adapterId",
    "requestedModelId",
    "toolCatalogDigest",
    "toolGrantDigest",
    "budget",
    "completionContract",
    "systemManifestRef",
    "createdAtMs",
    "sourceRefs",
    "priorArtifactRefs",
    "privacy",
    "deadlineMs",
];
const LEGACY_PROFILE: &str = "local-json-schema-draft-2020-12-profile-v1";
const JSON_SCHEMA_2020_12: &str = "https://json-schema.org/draft/2020-12/schema";
const STRUCTURED_MODE: &str = "structured-result-v1";
const MAX_SCHEMA_BYTES: usize = 65_536;

fn invalid(reason: &str) -> ReadError {
    corrupted(format!("Run contract semantic mismatch: {reason}"))
}

fn required<'a>(value: CanonicalRef<'a>, field: &str) -> Result<CanonicalRef<'a>, ReadError> {
    value.field(field).ok_or_else(|| invalid(field))
}

fn exact_object(value: CanonicalRef<'_>, fields: &[&str], label: &str) -> Result<(), ReadError> {
    if value.object_len() != Some(fields.len())
        || fields.iter().any(|field| value.field(field).is_none())
    {
        return Err(invalid(label));
    }
    Ok(())
}

fn string<'a>(value: CanonicalRef<'a>, label: &str) -> Result<&'a str, ReadError> {
    value.as_str().ok_or_else(|| invalid(label))
}

fn trimmed<'a>(
    value: CanonicalRef<'a>,
    max_bytes: usize,
    label: &str,
) -> Result<&'a str, ReadError> {
    let raw = string(value, label)?;
    // CPython str.strip includes C0 U+001C..U+001F in addition to
    // Unicode White_Space; this is the same existing contract B qualified.
    if raw.is_empty()
        || raw.len() > max_bytes
        || raw
            .trim_matches(|ch: char| ch.is_whitespace() || ('\u{001c}'..='\u{001f}').contains(&ch))
            != raw
    {
        return Err(invalid(label));
    }
    Ok(raw)
}

fn identity<'a>(value: CanonicalRef<'a>, prefix: &str, label: &str) -> Result<&'a str, ReadError> {
    let raw = trimmed(value, 300, label)?;
    if !raw.starts_with(prefix) || raw.as_bytes().get(prefix.len()) != Some(&b':') {
        return Err(invalid(label));
    }
    Ok(raw)
}

fn digest(value: CanonicalRef<'_>, label: &str) -> Result<(), ReadError> {
    let raw = string(value, label)?;
    let Some(hex) = raw.strip_prefix("sha256:") else {
        return Err(invalid(label));
    };
    if hex.len() != 64
        || !hex
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err(invalid(label));
    }
    Ok(())
}

fn reference<'a>(value: CanonicalRef<'a>) -> Result<&'a str, ReadError> {
    exact_object(value, &["ref", "kind", "digest"], "bound reference fields")?;
    let reference = trimmed(required(value, "ref")?, 1_024, "reference ref")?;
    trimmed(required(value, "kind")?, 200, "reference kind")?;
    digest(required(value, "digest")?, "reference digest")?;
    Ok(reference)
}

fn reference_list(
    value: CanonicalRef<'_>,
    label: &str,
    require_nonempty: bool,
) -> Result<(), ReadError> {
    let count = value.array_len().ok_or_else(|| invalid(label))?;
    if require_nonempty && count == 0 {
        return Err(invalid(label));
    }
    let mut names = BTreeSet::new();
    for idx in 0..count {
        let entry = value.index(idx).ok_or_else(|| invalid(label))?;
        let name = reference(entry)?;
        if !names.insert(name) {
            return Err(invalid("duplicate bound reference"));
        }
    }
    Ok(())
}

fn privacy(value: CanonicalRef<'_>) -> Result<(), ReadError> {
    exact_object(
        value,
        &["contentPolicy", "allowModelContent", "allowToolContent"],
        "privacy fields",
    )?;
    let content = string(required(value, "contentPolicy")?, "content policy")?;
    if !matches!(content, "metadata-only" | "bounded-private-content") {
        return Err(invalid("content policy"));
    }
    let model = required(value, "allowModelContent")?
        .as_bool()
        .ok_or_else(|| invalid("allowModelContent boolean"))?;
    let tool = required(value, "allowToolContent")?
        .as_bool()
        .ok_or_else(|| invalid("allowToolContent boolean"))?;
    if content == "metadata-only" && (model || tool) {
        return Err(invalid("metadata-only content capture"));
    }
    Ok(())
}

fn nonnegative_int<'a>(value: CanonicalRef<'a>, label: &str) -> Result<&'a str, ReadError> {
    let raw = value.integer_text().ok_or_else(|| invalid(label))?;
    if raw.starts_with('-') {
        return Err(invalid(label));
    }
    Ok(raw)
}

fn compare_unsigned(lhs: &str, rhs: &str) -> Ordering {
    lhs.len().cmp(&rhs.len()).then_with(|| lhs.cmp(rhs))
}

fn valid_traceparent(value: &str) -> bool {
    let b = value.as_bytes();
    b.len() == 55
        && b[2] == b'-'
        && b[35] == b'-'
        && b[52] == b'-'
        && b.iter().enumerate().all(|(i, ch)| {
            matches!(i, 2 | 35 | 52) || ch.is_ascii_digit() || (b'a'..=b'f').contains(ch)
        })
        && b[3..35].iter().any(|c| *c != b'0')
        && b[36..52].iter().any(|c| *c != b'0')
}

fn legacy_correlation(value: CanonicalRef<'_>) -> Result<(), ReadError> {
    exact_object(
        value,
        &["traceparent", "tracestate", "links"],
        "v1 correlation",
    )?;
    let tp = required(value, "traceparent")?;
    if !tp.is_null() && !valid_traceparent(string(tp, "traceparent")?) {
        return Err(invalid("traceparent"));
    }
    let state = required(value, "tracestate")?;
    if !state.is_null() {
        trimmed(state, 512, "tracestate")?;
    }
    reference_list(required(value, "links")?, "correlation links", false)
}

fn legacy_schema_profile(schema: CanonicalRef<'_>) -> Result<(), ReadError> {
    let entries = schema
        .object_entries()
        .ok_or_else(|| invalid("legacy resultSchema node"))?;
    const ALLOWED: &[&str] = &[
        "type",
        "properties",
        "additionalProperties",
        "required",
        "items",
        "enum",
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "minItems",
        "maxItems",
    ];
    for (key, _) in entries {
        if !ALLOWED.contains(&key) {
            return Err(invalid("legacy resultSchema keyword"));
        }
    }
    if let Some(kind) = schema.field("type") {
        if !kind.is_null()
            && !matches!(
                kind.as_str(),
                Some("object" | "array" | "string" | "integer" | "boolean")
            )
        {
            return Err(invalid("legacy resultSchema type"));
        }
    }
    if let Some(properties) = schema.field("properties") {
        if !properties.is_null() {
            let children = properties
                .object_entries()
                .ok_or_else(|| invalid("legacy schema properties"))?;
            for (_name, child) in children {
                legacy_schema_profile(child)?;
            }
        }
    }
    if let Some(items) = schema.field("items") {
        if !items.is_null() {
            legacy_schema_profile(items)?;
        }
    }
    if let Some(additional) = schema.field("additionalProperties") {
        if !additional.is_null() && additional.as_bool().is_none() {
            return Err(invalid("legacy additionalProperties"));
        }
    }
    Ok(())
}

fn completion(value: CanonicalRef<'_>) -> Result<(), ReadError> {
    if value.object_len().is_none_or(|n| n == 0) {
        return Err(invalid("completionContract must be nonempty object"));
    }
    let structured = value.field("mode").and_then(|v| v.as_str()) == Some(STRUCTURED_MODE);
    if !structured {
        if value.field("conformancePolicy").is_some() {
            return Err(invalid("conformancePolicy requires structured result"));
        }
        return Ok(());
    }
    let schema = required(value, "resultSchema")?;
    if schema.object_len().is_none_or(|n| n == 0) {
        return Err(invalid("structured resultSchema must be nonempty object"));
    }
    let raw = schema.canonical_bytes();
    if raw.len() > MAX_SCHEMA_BYTES {
        return Err(invalid("resultSchema exceeds 65536 canonical bytes"));
    }
    let legacy = match value.field("conformancePolicy") {
        Some(policy) if !policy.is_null() => {
            if trimmed(policy, usize::MAX, "conformancePolicy")? != LEGACY_PROFILE {
                return Err(invalid("legacy conformancePolicy"));
            }
            true
        }
        _ => false,
    };
    let dialect = if legacy {
        legacy_schema_profile(schema)?;
        true
    } else {
        match schema.field("$schema") {
            Some(dialect) if !dialect.is_null() => {
                if trimmed(dialect, usize::MAX, "schema dialect")? != JSON_SCHEMA_2020_12 {
                    return Err(invalid("structured resultSchema dialect"));
                }
                true
            }
            _ => false,
        }
    };
    // The Python owner uses jsonschema.Draft202012Validator.check_schema
    // only when the declared contract opts into a dialect/profile.
    // Reuse upstream jsonschema rather than adding a custom JSON Schema
    // engine. Offline meta validation never fetches a remote reference.
    if dialect {
        let projected: serde_json::Value =
            serde_json::from_slice(&raw).map_err(|_| invalid("resultSchema JSON projection"))?;
        if !jsonschema::draft202012::meta::is_valid(&projected) {
            return Err(invalid("resultSchema Draft 2020-12"));
        }
    }
    Ok(())
}

/// Validate exact Python schema-v1/v2 Contract semantics for an already
/// CAS-verified immutable document. Return Corruption for a self-consistent
/// but invalid Contract; never infer effect authority from this read.
pub fn validate_contract(doc: &CanonicalDocument) -> Result<(), ReadError> {
    let root = doc.as_borrowed();
    let schema_version = required(root, "schemaVersion")?;
    // Python `schema_version in {1, 2}` admits bool True as schema-v1
    // (True == 1 in Python). Preserve this unusual historical contract
    // representation rather than falsely classifying its CAS as corrupt.
    let version = if schema_version.as_bool() == Some(true) {
        "1"
    } else {
        schema_version
            .integer_text()
            .ok_or_else(|| invalid("schemaVersion integer"))?
    };
    if !matches!(version, "1" | "2") {
        return Err(invalid("schemaVersion"));
    }
    let mut fields = CONTRACT_FIELDS.to_vec();
    if version == "1" {
        fields.push("correlation");
    }
    exact_object(root, &fields, "contract field set")?;
    if string(required(root, "kind")?, "kind")? != "ordivon.harness-run-contract" {
        return Err(invalid("contract kind"));
    }
    identity(
        required(root, "harnessRunId")?,
        "harness-run",
        "harnessRunId",
    )?;
    identity(required(root, "callerId")?, "caller", "callerId")?;
    trimmed(
        required(root, "harnessImplementationId")?,
        300,
        "harnessImplementationId",
    )?;
    trimmed(required(root, "callerRunRef")?, 1_024, "callerRunRef")?;
    for key in ["providerId", "adapterId", "requestedModelId"] {
        trimmed(required(root, key)?, 300, key)?;
    }
    digest(required(root, "toolCatalogDigest")?, "toolCatalogDigest")?;
    digest(required(root, "toolGrantDigest")?, "toolGrantDigest")?;
    reference(required(root, "objectiveRef")?)?;
    reference(required(root, "systemManifestRef")?)?;
    reference_list(required(root, "contextRefs")?, "contextRefs", true)?;
    reference_list(required(root, "sourceRefs")?, "sourceRefs", false)?;
    reference_list(
        required(root, "priorArtifactRefs")?,
        "priorArtifactRefs",
        false,
    )?;
    privacy(required(root, "privacy")?)?;
    if required(root, "budget")?
        .object_len()
        .is_none_or(|n| n == 0)
    {
        return Err(invalid("budget must be nonempty object"));
    }
    completion(required(root, "completionContract")?)?;
    let created = nonnegative_int(required(root, "createdAtMs")?, "createdAtMs")?;
    let due = required(root, "deadlineMs")?;
    if !due.is_null() {
        let deadline = nonnegative_int(due, "deadlineMs")?;
        if compare_unsigned(deadline, created) == Ordering::Less {
            return Err(invalid("deadline precedes creation"));
        }
    }
    if version == "1" {
        legacy_correlation(required(root, "correlation")?)?;
    }
    Ok(())
}
