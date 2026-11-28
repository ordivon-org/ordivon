//! A domain Tool capability is a frozen catalog plus a narrower grant.
//! This projects the existing Python DomainToolCatalog into Rust using A's
//! sealed canonical codec and B's existing order-preserving selector.
//! It neither registers tools globally nor grants execution/effect authority.

use crate::{select_tool_indices, ToolSelectionError};
use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument, CanonicalRef};
use std::collections::HashSet;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum ToolSurfaceError {
    InvalidCatalog,
    InvalidGrant,
    GrantSelection(ToolSelectionError),
    BindingMismatch,
    CanonicalConstruction,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct DomainToolSurface {
    catalog_digest: String,
    grant_digest: String,
    selected_indices: Vec<usize>,
    ordered_names: Vec<String>,
}

impl DomainToolSurface {
    pub fn catalog_digest(&self) -> &str {
        &self.catalog_digest
    }
    pub fn grant_digest(&self) -> &str {
        &self.grant_digest
    }
    pub fn ordered_names(&self) -> &[String] {
        &self.ordered_names
    }

    /// A valid Tool Catalog does not imply this particular Run has its Grant.
    pub fn require_contract_binding(
        &self,
        catalog_digest: &str,
        grant_digest: &str,
    ) -> Result<(), ToolSurfaceError> {
        if catalog_digest != self.catalog_digest || grant_digest != self.grant_digest {
            return Err(ToolSurfaceError::BindingMismatch);
        }
        Ok(())
    }

    /// Expose exactly the ordered model-visible definitions after digest check.
    /// References are borrowed from the immutable, already validated catalog;
    /// the caller does not gain Tool execution authority from these references.
    pub fn model_definitions<'a>(
        &self,
        catalog: &'a CanonicalDocument,
    ) -> Result<Vec<CanonicalRef<'a>>, ToolSurfaceError> {
        if digest_bytes(&canonical_bytes(catalog)) != self.catalog_digest {
            return Err(ToolSurfaceError::BindingMismatch);
        }
        let tools = catalog
            .field("tools")
            .ok_or(ToolSurfaceError::InvalidCatalog)?;
        self.selected_indices
            .iter()
            .zip(&self.ordered_names)
            .map(|(index, expected)| {
                let definition = tools
                    .index(*index)
                    .ok_or(ToolSurfaceError::InvalidCatalog)?;
                if definition.field("name").and_then(CanonicalRef::as_str) != Some(expected) {
                    return Err(ToolSurfaceError::BindingMismatch);
                }
                Ok(definition)
            })
            .collect()
    }
}

fn valid_text(value: &str, max_bytes: usize, prefix: Option<&str>) -> bool {
    crate::python_text::valid_trimmed(value, max_bytes)
        && prefix.is_none_or(|prefix| value.starts_with(&format!("{prefix}:")))
}

/// Project a Python DomainToolCatalog.to_dict and an allowed-tools grant.
/// Missing/duplicate Tools fail closed; model-visible order always follows
/// the immutable catalog, not caller-provided allowed-tools order.
pub fn project_domain_tool_surface(
    catalog: &CanonicalDocument,
    allowed_tools: &[&str],
) -> Result<DomainToolSurface, ToolSurfaceError> {
    const CATALOG_FIELDS: [&str; 5] = ["schemaVersion", "kind", "domainId", "revision", "tools"];
    let keys: Vec<&str> = catalog
        .object_entries()
        .ok_or(ToolSurfaceError::InvalidCatalog)?
        .map(|(key, _)| key)
        .collect();
    if keys.len() != CATALOG_FIELDS.len()
        || CATALOG_FIELDS.iter().any(|key| !keys.contains(key))
        || catalog
            .field("schemaVersion")
            .and_then(CanonicalRef::integer_text)
            != Some("1")
        || catalog.field("kind").and_then(CanonicalRef::as_str)
            != Some("ordivon.domain-tool-catalog")
    {
        return Err(ToolSurfaceError::InvalidCatalog);
    }
    let domain_id = catalog
        .field("domainId")
        .and_then(CanonicalRef::as_str)
        .ok_or(ToolSurfaceError::InvalidCatalog)?;
    let revision = catalog
        .field("revision")
        .and_then(CanonicalRef::as_str)
        .ok_or(ToolSurfaceError::InvalidCatalog)?;
    if !valid_text(domain_id, 300, Some("domain")) || !valid_text(revision, 300, None) {
        return Err(ToolSurfaceError::InvalidCatalog);
    }
    let tools = catalog
        .field("tools")
        .ok_or(ToolSurfaceError::InvalidCatalog)?;
    let count = tools.array_len().ok_or(ToolSurfaceError::InvalidCatalog)?;
    if count == 0 {
        return Err(ToolSurfaceError::InvalidCatalog);
    }
    let mut names = Vec::with_capacity(count);
    let mut unique = HashSet::with_capacity(count);
    for index in 0..count {
        let tool = tools.index(index).ok_or(ToolSurfaceError::InvalidCatalog)?;
        if tool.object_len() != Some(3)
            || tool
                .field("inputSchema")
                .and_then(CanonicalRef::object_len)
                .is_none()
        {
            return Err(ToolSurfaceError::InvalidCatalog);
        }
        let name = tool
            .field("name")
            .and_then(CanonicalRef::as_str)
            .ok_or(ToolSurfaceError::InvalidCatalog)?;
        let description = tool
            .field("description")
            .and_then(CanonicalRef::as_str)
            .ok_or(ToolSurfaceError::InvalidCatalog)?;
        if !valid_text(name, 120, None)
            || !valid_text(description, 1000, None)
            || !unique.insert(name)
        {
            return Err(ToolSurfaceError::InvalidCatalog);
        }
        names.push(name);
    }
    if allowed_tools.is_empty() {
        return Err(ToolSurfaceError::InvalidGrant);
    }
    let selected_indices = select_tool_indices(&names, Some(allowed_tools))
        .map_err(ToolSurfaceError::GrantSelection)?;
    let ordered_names: Vec<String> = selected_indices
        .iter()
        .map(|index| names[*index].to_owned())
        .collect();
    let catalog_digest = digest_bytes(&canonical_bytes(catalog));
    let grant_object = CanonicalDocument::object(vec![
        (
            "schemaVersion".to_owned(),
            CanonicalDocument::integer_from_decimal("1")
                .map_err(|_| ToolSurfaceError::CanonicalConstruction)?,
        ),
        (
            "kind".to_owned(),
            CanonicalDocument::string("ordivon.domain-tool-catalog-grant"),
        ),
        (
            "catalogDigest".to_owned(),
            CanonicalDocument::string(&catalog_digest),
        ),
        (
            "allowedTools".to_owned(),
            CanonicalDocument::array(
                ordered_names
                    .iter()
                    .map(CanonicalDocument::string)
                    .collect(),
            )
            .map_err(|_| ToolSurfaceError::CanonicalConstruction)?,
        ),
    ])
    .map_err(|_| ToolSurfaceError::CanonicalConstruction)?;
    let grant_digest = digest_bytes(&canonical_bytes(&grant_object));
    Ok(DomainToolSurface {
        catalog_digest,
        grant_digest,
        selected_indices,
        ordered_names,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use ordivon_harness_core::loads_strict;

    #[test]
    fn malformed_catalog_is_not_a_valid_tool_surface() {
        let missing = loads_strict(
            r#"{"schemaVersion":1,"kind":"ordivon.domain-tool-catalog",
            "domainId":"domain:x","revision":"v1","tools":[]}"#,
        )
        .unwrap();
        assert_eq!(
            project_domain_tool_surface(&missing, &["run"]),
            Err(ToolSurfaceError::InvalidCatalog)
        );
    }

    #[test]
    fn unchecked_grant_is_never_a_dispatch_capability() {
        let catalog = loads_strict(
            r#"{"schemaVersion":1,"kind":"ordivon.domain-tool-catalog",
            "domainId":"domain:x","revision":"v1",
            "tools":[{"name":"read","description":"read file","inputSchema":{"type":"object"}},
                {"name":"edit","description":"edit file","inputSchema":{"type":"object"}}]}"#,
        )
        .unwrap();
        let surface = project_domain_tool_surface(&catalog, &["edit"]).unwrap();
        assert_eq!(surface.ordered_names(), &["edit".to_string()]);
        assert!(surface
            .require_contract_binding(surface.catalog_digest(), surface.grant_digest())
            .is_ok());
        assert_eq!(
            surface.require_contract_binding(surface.catalog_digest(), "sha256:wrong"),
            Err(ToolSurfaceError::BindingMismatch)
        );
        assert_eq!(surface.model_definitions(&catalog).unwrap().len(), 1);
    }
}
