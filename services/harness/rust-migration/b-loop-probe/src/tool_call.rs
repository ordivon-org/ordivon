//! Model -> Tool Call boundary of the existing Python AgentToolCall contract.
//!
//! This projection validates *what the model proposed*, not permission to
//! perform the physical operation. A complete Run Contract, PG lease/fence,
//! Tool Step Intent and owner receipt are separate, currently unproven gates.
use std::collections::HashSet;

use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument, CanonicalRef};

use crate::tool_surface::{DomainToolSurface, ToolSurfaceError};

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ToolCallDecodeError {
    InvalidModelToolCall,
    CanonicalConstruction,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ModelToolCall {
    tool_call_id: String,
    name: String,
    /// Python AgentToolCall.to_dict canonical SHA256, including the rule that
    /// all-null providerArguments is omitted from normalized output.
    digest: String,
    argument_error: Option<String>,
}

impl ModelToolCall {
    pub fn tool_call_id(&self) -> &str {
        &self.tool_call_id
    }

    pub fn name(&self) -> &str {
        &self.name
    }

    pub fn digest(&self) -> &str {
        &self.digest
    }

    pub fn argument_error(&self) -> Option<&str> {
        self.argument_error.as_deref()
    }
}

fn expect_string<'a>(
    document: &'a CanonicalDocument,
    key: &str,
    max_bytes: usize,
) -> Result<&'a str, ToolCallDecodeError> {
    let value = document
        .field(key)
        .and_then(CanonicalRef::as_str)
        .ok_or(ToolCallDecodeError::InvalidModelToolCall)?;
    if !crate::python_text::valid_trimmed(value, max_bytes) {
        return Err(ToolCallDecodeError::InvalidModelToolCall);
    }
    Ok(value)
}

fn valid_digest(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..]
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

/// Exact type/field validation of Python AgentToolCall.from_dict and
/// its to_dict canonical identity. Requires A's strict sealed representation;
/// no tool inputSchema execution validation is inferred from this parsing.
pub fn inspect_model_tool_call(
    value: &CanonicalDocument,
) -> Result<ModelToolCall, ToolCallDecodeError> {
    let field_count = value
        .object_len()
        .ok_or(ToolCallDecodeError::InvalidModelToolCall)?;
    let has_provider_arguments = value.field("providerArguments").is_some();
    if field_count != (if has_provider_arguments { 4 } else { 3 })
        || value.field("toolCallId").is_none()
        || value.field("name").is_none()
        || value
            .field("arguments")
            .and_then(CanonicalRef::object_len)
            .is_none()
    {
        return Err(ToolCallDecodeError::InvalidModelToolCall);
    }
    let id = expect_string(value, "toolCallId", 300)?;
    let name = expect_string(value, "name", 120)?;
    let mut argument_error = None;

    if has_provider_arguments {
        let args = value
            .get("providerArguments")
            .ok_or(ToolCallDecodeError::InvalidModelToolCall)?;
        if args.object_len() != Some(3)
            || args.field("error").is_none()
            || args.field("rawDigest").is_none()
            || args.field("preview").is_none()
        {
            return Err(ToolCallDecodeError::InvalidModelToolCall);
        }
        let null = CanonicalDocument::null();
        let all_null = ["error", "rawDigest", "preview"]
            .iter()
            .all(|key| args.get(key) == Some(null.clone()));
        if !all_null {
            let error = expect_string(&args, "error", 300)?;
            let digest = args
                .field("rawDigest")
                .and_then(CanonicalRef::as_str)
                .ok_or(ToolCallDecodeError::InvalidModelToolCall)?;
            let preview = args
                .field("preview")
                .and_then(CanonicalRef::as_str)
                .ok_or(ToolCallDecodeError::InvalidModelToolCall)?;
            if !valid_digest(digest) || preview.len() > 2048 {
                return Err(ToolCallDecodeError::InvalidModelToolCall);
            }
            argument_error = Some(error.to_owned());
        }
    }

    // Python keeps an all-null providerArguments dictionary on input but
    // drops it from to_dict/digest; don't mistake input bytes for call identity.
    let digest = if has_provider_arguments && argument_error.is_none() {
        let canonical = CanonicalDocument::object(vec![
            ("toolCallId".to_owned(), CanonicalDocument::string(id)),
            ("name".to_owned(), CanonicalDocument::string(name)),
            (
                "arguments".to_owned(),
                value
                    .get("arguments")
                    .ok_or(ToolCallDecodeError::InvalidModelToolCall)?,
            ),
        ])
        .map_err(|_| ToolCallDecodeError::CanonicalConstruction)?;
        digest_bytes(&canonical_bytes(&canonical))
    } else {
        digest_bytes(&canonical_bytes(value))
    };
    Ok(ModelToolCall {
        tool_call_id: id.to_owned(),
        name: name.to_owned(),
        digest,
        argument_error,
    })
}

/// Pure standing only: never grants a Runtime/Provider dispatch.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ModelToolCallStanding {
    DuplicateCallIdentity,
    LocallyRejectedProviderArguments,
    NotOnVisibleGrantedToolSurface,
    /// STILL NOT authorized: must validate the full Run Contract and durable
    /// Store/Lease/Fence before Runtime or Domain-owned Tool execution.
    NeedsAuthenticatedContractAndDurableAdmission,
}

/// Source order: Python ordivon/loop.py processes duplicate identities
/// BEFORE argument errors, then domain_tools._GrantedDomainToolBridge checks
/// admitted names before forwarding an executable call. No seen-set mutation
/// occurs in this pure function; the actual Loop must journal and own it.
pub fn preflight_domain_model_call(
    surface: &DomainToolSurface,
    catalog: &CanonicalDocument,
    contract_catalog_digest: &str,
    contract_grant_digest: &str,
    proposed: &ModelToolCall,
    prior_call_ids: &HashSet<String>,
) -> Result<ModelToolCallStanding, ToolSurfaceError> {
    surface.require_contract_binding(contract_catalog_digest, contract_grant_digest)?;
    surface.model_definitions(catalog)?;
    if prior_call_ids.contains(proposed.tool_call_id()) {
        return Ok(ModelToolCallStanding::DuplicateCallIdentity);
    }
    if proposed.argument_error().is_some() {
        return Ok(ModelToolCallStanding::LocallyRejectedProviderArguments);
    }
    if !surface
        .ordered_names()
        .iter()
        .any(|name| name == proposed.name())
    {
        return Ok(ModelToolCallStanding::NotOnVisibleGrantedToolSurface);
    }
    Ok(ModelToolCallStanding::NeedsAuthenticatedContractAndDurableAdmission)
}

#[cfg(test)]
mod tests {
    use super::*;
    use ordivon_harness_core::loads_strict;

    #[test]
    fn all_null_diagnostics_are_normalized_away() {
        let a = loads_strict(r#"{"toolCallId":"call:1","name":"tool","arguments":{}}"#).unwrap();
        let b = loads_strict(r#"{"toolCallId":"call:1","name":"tool","arguments":{},"providerArguments":{"error":null,"rawDigest":null,"preview":null}}"#).unwrap();
        assert_eq!(
            inspect_model_tool_call(&a).unwrap().digest(),
            inspect_model_tool_call(&b).unwrap().digest()
        );
    }

    #[test]
    fn partial_provider_diagnostics_fail_closed() {
        let x = loads_strict(r#"{"toolCallId":"call:1","name":"tool","arguments":{},"providerArguments":{"error":"broken","rawDigest":null,"preview":null}}"#).unwrap();
        assert_eq!(
            inspect_model_tool_call(&x),
            Err(ToolCallDecodeError::InvalidModelToolCall)
        );
    }

    #[test]
    fn untrusted_model_call_cannot_become_execution_authority() {
        let catalog = loads_strict(r#"{"schemaVersion":1,"kind":"ordivon.domain-tool-catalog","domainId":"domain:lab","revision":"r1","tools":[{"name":"read","description":"Read file","inputSchema":{}},{"name":"edit","description":"Edit file","inputSchema":{}}]}"#).unwrap();
        let surface =
            crate::tool_surface::project_domain_tool_surface(&catalog, &["read"]).unwrap();
        let call = inspect_model_tool_call(
            &loads_strict(r#"{"toolCallId":"call:1","name":"read","arguments":{}}"#).unwrap(),
        )
        .unwrap();
        let standing = preflight_domain_model_call(
            &surface,
            &catalog,
            surface.catalog_digest(),
            surface.grant_digest(),
            &call,
            &HashSet::new(),
        )
        .unwrap();
        assert_eq!(
            standing,
            ModelToolCallStanding::NeedsAuthenticatedContractAndDurableAdmission
        );
        assert_eq!(
            preflight_domain_model_call(
                &surface,
                &catalog,
                "sha256:forged",
                surface.grant_digest(),
                &call,
                &HashSet::new()
            ),
            Err(ToolSurfaceError::BindingMismatch)
        );
    }
}
