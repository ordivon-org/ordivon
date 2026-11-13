//! Frozen catalog Tool argument validation before any physical effect.
//! Mature upstream JSON Schema 2020-12 is reused, not a local validator.
//! A matching model name / grant is necessary but not sufficient authority.
use crate::tool_call::{inspect_model_tool_call, ModelToolCall};
use crate::tool_surface::DomainToolSurface;
use ordivon_harness_core::CanonicalDocument;
use serde_json::Value;

const MAX_SCHEMA_BYTES: usize = 65_536;
const MAX_ARGUMENT_BYTES: usize = 262_144;
const MAX_SCHEMA_DEPTH: u32 = 64;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ArgumentValidationError {
    InvalidCatalogBinding,
    ForgedCallIdentity,
    UnqualifiedSchema,
    InvalidArguments,
}

fn offline_local_references_only(value: &Value, depth: u32) -> bool {
    if depth > MAX_SCHEMA_DEPTH {
        return false;
    }
    match value {
        Value::Object(fields) => fields.iter().all(|(key, v)| {
            if key == "$ref" || key == "$dynamicRef" {
                // Valid local fragments are resolved from this exact catalog
                // definition. Never use filesystem or HTTP to resolve a Tool
                // schema on a Provider's untrusted path.
                if !v.as_str().is_some_and(|s| s == "#" || s.starts_with("#/")) {
                    return false;
                }
            }
            offline_local_references_only(v, depth + 1)
        }),
        Value::Array(items) => items
            .iter()
            .all(|item| offline_local_references_only(item, depth + 1)),
        _ => true,
    }
}

/// Validate exact source ToolCall *and* input against the granted Tool's
/// frozen JSON Schema. This is not an execution permit: PG admission, Run
/// revision, Intent/Fence and owner authorization are separate gates.
pub fn validate_granted_tool_arguments(
    surface: &DomainToolSurface,
    catalog: &CanonicalDocument,
    proposed: &ModelToolCall,
    proposed_document: &CanonicalDocument,
) -> Result<(), ArgumentValidationError> {
    let decoded = inspect_model_tool_call(proposed_document)
        .map_err(|_| ArgumentValidationError::ForgedCallIdentity)?;
    if decoded != *proposed {
        return Err(ArgumentValidationError::ForgedCallIdentity);
    }
    let definitions = surface
        .model_definitions(catalog)
        .map_err(|_| ArgumentValidationError::InvalidCatalogBinding)?;
    let definition = definitions
        .into_iter()
        .find(|d| d.field("name").and_then(|v| v.as_str()) == Some(proposed.name()))
        .ok_or(ArgumentValidationError::InvalidCatalogBinding)?;
    let schema_bytes = definition
        .field("inputSchema")
        .ok_or(ArgumentValidationError::UnqualifiedSchema)?
        .canonical_bytes();
    if schema_bytes.len() > MAX_SCHEMA_BYTES {
        return Err(ArgumentValidationError::UnqualifiedSchema);
    }
    let schema: Value = serde_json::from_slice(&schema_bytes)
        .map_err(|_| ArgumentValidationError::UnqualifiedSchema)?;
    if !offline_local_references_only(&schema, 0)
        || !jsonschema::draft202012::meta::is_valid(&schema)
    {
        return Err(ArgumentValidationError::UnqualifiedSchema);
    }
    // No network/file resolver features are enabled for jsonschema. Compile
    // once for this preflight, never interpret remote references.
    let validator = jsonschema::draft202012::options()
        .should_validate_formats(true)
        .build(&schema)
        .map_err(|_| ArgumentValidationError::UnqualifiedSchema)?;
    let argument_bytes = proposed_document
        .field("arguments")
        .ok_or(ArgumentValidationError::InvalidArguments)?
        .canonical_bytes();
    if argument_bytes.len() > MAX_ARGUMENT_BYTES {
        return Err(ArgumentValidationError::InvalidArguments);
    }
    let instance: Value = serde_json::from_slice(&argument_bytes)
        .map_err(|_| ArgumentValidationError::InvalidArguments)?;
    if !validator.is_valid(&instance) {
        return Err(ArgumentValidationError::InvalidArguments);
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::tool_surface::project_domain_tool_surface;
    use ordivon_harness_core::loads_strict;

    fn fixture(schema: &str) -> (CanonicalDocument, DomainToolSurface) {
        let catalog = loads_strict(&format!(
            r#"{{"schemaVersion":1,"kind":"ordivon.domain-tool-catalog",
            "domainId":"domain:validation","revision":"r1","tools":[
              {{"name":"read","description":"Read","inputSchema":{schema}}}]}}"#
        ))
        .unwrap();
        let surface = project_domain_tool_surface(&catalog, &["read"]).unwrap();
        (catalog, surface)
    }
    fn check(
        catalog: &CanonicalDocument,
        surface: &DomainToolSurface,
        doc: &str,
    ) -> Result<(), ArgumentValidationError> {
        let document = loads_strict(doc).unwrap();
        let parsed = inspect_model_tool_call(&document).unwrap();
        validate_granted_tool_arguments(surface, catalog, &parsed, &document)
    }
    #[test]
    fn mature_draft202012_validates_required_integer_and_extra_properties() {
        let (c, s) = fixture(
            r#"{"type":"object","properties":{"n":{"type":"integer","minimum":1}},
            "required":["n"],"additionalProperties":false}"#,
        );
        assert!(check(
            &c,
            &s,
            r#"{"toolCallId":"x","name":"read","arguments":{"n":2}}"#
        )
        .is_ok());
        for args in [
            r#"{}"#,
            r#"{"n":"2"}"#,
            r#"{"n":0}"#,
            r#"{"n":1,"bad":true}"#,
        ] {
            let doc = format!(r#"{{"toolCallId":"x","name":"read","arguments":{args}}}"#);
            assert_eq!(
                check(&c, &s, &doc),
                Err(ArgumentValidationError::InvalidArguments)
            );
        }
    }
    #[test]
    fn local_ref_and_large_exact_integer_are_supported() {
        let (c, s) = fixture(
            r##"{"$defs":{"count":{"type":"integer","minimum":0}},
            "type":"object","properties":{"n":{"$ref":"#/$defs/count"}},"required":["n"]}"##,
        );
        assert!(check(
            &c,
            &s,
            r#"{"toolCallId":"x","name":"read","arguments":{"n":184467440737095516170}}"#
        )
        .is_ok());
    }
    #[test]
    fn external_references_are_not_fetched_for_model_proposals() {
        let (c, s) = fixture(r#"{"$ref":"https://example.invalid/tool-schema"}"#);
        assert_eq!(
            check(&c, &s, r#"{"toolCallId":"x","name":"read","arguments":{}}"#),
            Err(ArgumentValidationError::UnqualifiedSchema)
        );
    }
    #[test]
    fn malformed_schema_is_rejected_not_silently_treated_as_any() {
        let (c, s) = fixture(r#"{"type":12}"#);
        assert_eq!(
            check(&c, &s, r#"{"toolCallId":"x","name":"read","arguments":{}}"#),
            Err(ArgumentValidationError::UnqualifiedSchema)
        );
    }
    #[test]
    fn forged_call_identity_cannot_reuse_prior_validated_tool() {
        let (c, s) = fixture(r#"{}"#);
        let original = loads_strict(r#"{"toolCallId":"a","name":"read","arguments":{}}"#).unwrap();
        let forged = loads_strict(r#"{"toolCallId":"b","name":"read","arguments":{}}"#).unwrap();
        let parsed = inspect_model_tool_call(&original).unwrap();
        assert_eq!(
            validate_granted_tool_arguments(&s, &c, &parsed, &forged),
            Err(ArgumentValidationError::ForgedCallIdentity)
        );
    }
}
