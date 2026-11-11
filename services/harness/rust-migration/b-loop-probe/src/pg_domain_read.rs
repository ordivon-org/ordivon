//! Read-only PG Run → A-validated versioned Contract → frozen Domain Tool Grant.
//! The value is an observation only, NEVER a Tool/Provider effect admission.
use crate::tool_call::{preflight_domain_model_call, ModelToolCall, ModelToolCallStanding};
use crate::tool_surface::{project_domain_tool_surface, DomainToolSurface, ToolSurfaceError};
use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument, CanonicalRef};
use ordivon_harness_pg::{read_run_readonly, ReadError, Readback};
use postgres::Client;
use std::collections::HashSet;

#[derive(Clone, Copy, Debug)]
pub struct ExpectedModel<'a> {
    pub provider_id: &'a str,
    pub adapter_id: &'a str,
    pub requested_model_id: &'a str,
}
#[derive(Debug)]
pub enum PgDomainInspectionError {
    Store(ReadError),
    MissingVerifiedContractField(&'static str),
    ProviderSelectionMismatch(&'static str),
    DomainToolBinding(ToolSurfaceError),
    NotNoToolRunSurface,
}
impl From<ReadError> for PgDomainInspectionError {
    fn from(value: ReadError) -> Self {
        Self::Store(value)
    }
}
impl From<ToolSurfaceError> for PgDomainInspectionError {
    fn from(value: ToolSurfaceError) -> Self {
        Self::DomainToolBinding(value)
    }
}
/// Shared immutable observation of the same validated A-owned PG snapshot.
#[derive(Debug)]
struct ObservedModelIdentity {
    run_id: String,
    contract_digest: String,
    revision: i64,
    status: String,
    provider_id: String,
    adapter_id: String,
    model_id: String,
}
/// Private construction requires a real A-owned READ ONLY PG snapshot.
#[derive(Debug)]
pub struct ObservedDomainRun {
    model: ObservedModelIdentity,
    catalog_digest: String,
    grant_digest: String,
    surface: DomainToolSurface,
}
impl ObservedDomainRun {
    pub fn run_id(&self) -> &str {
        &self.model.run_id
    }
    pub fn contract_digest(&self) -> &str {
        &self.model.contract_digest
    }
    pub fn revision(&self) -> i64 {
        self.model.revision
    }
    pub fn status(&self) -> &str {
        &self.model.status
    }
    pub fn provider_id(&self) -> &str {
        &self.model.provider_id
    }
    pub fn adapter_id(&self) -> &str {
        &self.model.adapter_id
    }
    pub fn model_id(&self) -> &str {
        &self.model.model_id
    }
    pub fn ordered_tool_names(&self) -> &[String] {
        self.surface.ordered_names()
    }
    /// No new tool execution authority follows from successful preflight.
    pub fn preflight(
        &self,
        frozen_catalog: &CanonicalDocument,
        call: &ModelToolCall,
        seen: &HashSet<String>,
    ) -> Result<ModelToolCallStanding, ToolSurfaceError> {
        preflight_domain_model_call(
            &self.surface,
            frozen_catalog,
            &self.catalog_digest,
            &self.grant_digest,
            call,
            seen,
        )
    }
}
fn field<'a>(
    contract: &'a CanonicalDocument,
    name: &'static str,
) -> Result<&'a str, PgDomainInspectionError> {
    contract
        .field(name)
        .and_then(CanonicalRef::as_str)
        .ok_or(PgDomainInspectionError::MissingVerifiedContractField(name))
}
/// Source-proven PG snapshot, rather than a caller-created Readback.
/// Not a lease, dispatch fence, effect token, or live Run status guarantee.
pub fn inspect_pg_domain_run(
    connection: &mut Client,
    schema: &str,
    run_id: &str,
    catalog: &CanonicalDocument,
    allowed_tools: &[&str],
    expected: ExpectedModel<'_>,
) -> Result<ObservedDomainRun, PgDomainInspectionError> {
    let (snapshot, model) = read_bound_model(connection, schema, run_id, expected)?;
    let contract = &snapshot.contract;
    let surface = project_domain_tool_surface(catalog, allowed_tools)?;
    let catalog_digest = field(contract, "toolCatalogDigest")?;
    let grant_digest = field(contract, "toolGrantDigest")?;
    surface.require_contract_binding(catalog_digest, grant_digest)?;
    Ok(ObservedDomainRun {
        model,
        catalog_digest: catalog_digest.to_owned(),
        grant_digest: grant_digest.to_owned(),
        surface,
    })
}

/// Shared A-verified immutable Run observation for both composition paths.
/// The Readback struct itself is never caller-supplied as a trust source.
fn read_bound_model(
    connection: &mut Client,
    schema: &str,
    run_id: &str,
    expected: ExpectedModel<'_>,
) -> Result<(Readback, ObservedModelIdentity), PgDomainInspectionError> {
    let snapshot = read_run_readonly(connection, schema, run_id)?;
    let contract = &snapshot.contract;
    for (name, expected_value) in [
        ("providerId", expected.provider_id),
        ("adapterId", expected.adapter_id),
        ("requestedModelId", expected.requested_model_id),
    ] {
        if field(contract, name)? != expected_value {
            return Err(PgDomainInspectionError::ProviderSelectionMismatch(name));
        }
    }
    let identity = ObservedModelIdentity {
        run_id: snapshot.projection.harness_run_id.clone(),
        contract_digest: snapshot.projection.contract_digest.clone(),
        revision: snapshot.projection.revision,
        status: snapshot.projection.status.clone(),
        provider_id: expected.provider_id.to_owned(),
        adapter_id: expected.adapter_id.to_owned(),
        model_id: expected.requested_model_id.to_owned(),
    };
    Ok((snapshot, identity))
}

/// A's sealed canonical byte builder projects the immutable Python
/// NO_TOOL_AGENT_SURFACE / NO_TOOL_AGENT_GRANT definitions, instead of
/// embedding opaque SHA256 literal constants or inventing a second codec.
fn no_tool_source_digest(kind: &str) -> String {
    let representation = CanonicalDocument::object(vec![
        (
            "schemaVersion".to_owned(),
            CanonicalDocument::integer_from_decimal("1")
                .expect("static schemaVersion is canonical"),
        ),
        ("kind".to_owned(), CanonicalDocument::string(kind)),
        (
            "tools".to_owned(),
            CanonicalDocument::array(vec![]).expect("static empty Tool list is canonical"),
        ),
    ])
    .expect("static immutable no-Tool document is canonical");
    digest_bytes(&canonical_bytes(&representation))
}

/// Real PG snapshot for the Provider-only, zero Tool Python Run profile.
/// No Tool/Runtime adapter or executable preflight is present on this type.
/// Observed revision/status may become stale as soon as the read returns.
#[derive(Debug)]
pub struct ObservedNoToolRun {
    model: ObservedModelIdentity,
}
impl ObservedNoToolRun {
    pub fn run_id(&self) -> &str {
        &self.model.run_id
    }
    pub fn contract_digest(&self) -> &str {
        &self.model.contract_digest
    }
    pub fn revision(&self) -> i64 {
        self.model.revision
    }
    pub fn status(&self) -> &str {
        &self.model.status
    }
    pub fn provider_id(&self) -> &str {
        &self.model.provider_id
    }
    pub fn adapter_id(&self) -> &str {
        &self.model.adapter_id
    }
    pub fn model_id(&self) -> &str {
        &self.model.model_id
    }
    pub fn model_visible_tool_count(&self) -> usize {
        0
    }
}

/// Fetch through A's actual PG Contract semantic reader, then require the
/// exact Python no-Tool Catalog/Grant pair. Mixed digests, custom Domain Tool
/// and Runtime Search Run all fail closed. No Provider transport or effects.
pub fn inspect_pg_no_tool_run(
    connection: &mut Client,
    schema: &str,
    run_id: &str,
    expected: ExpectedModel<'_>,
) -> Result<ObservedNoToolRun, PgDomainInspectionError> {
    let (snapshot, model) = read_bound_model(connection, schema, run_id, expected)?;
    let contract = &snapshot.contract;
    let expected_surface = no_tool_source_digest("ordivon.no-tool-agent-surface");
    let expected_grant = no_tool_source_digest("ordivon.no-tool-grant");
    if field(contract, "toolCatalogDigest")? != expected_surface
        || field(contract, "toolGrantDigest")? != expected_grant
    {
        return Err(PgDomainInspectionError::NotNoToolRunSurface);
    }
    Ok(ObservedNoToolRun { model })
}
