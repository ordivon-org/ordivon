//! Read-only PG Run → A-validated versioned Contract → frozen Domain Tool Grant.
//! The value is an observation only, NEVER a Tool/Provider effect admission.
use crate::tool_call::{preflight_domain_model_call, ModelToolCall, ModelToolCallStanding};
use crate::tool_surface::{project_domain_tool_surface, DomainToolSurface, ToolSurfaceError};
use ordivon_harness_core::{CanonicalDocument, CanonicalRef};
use ordivon_harness_pg::{read_run_readonly, ReadError};
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
/// Private construction requires a real A-owned READ ONLY PG snapshot.
#[derive(Debug)]
pub struct ObservedDomainRun {
    run_id: String,
    contract_digest: String,
    revision: i64,
    status: String,
    provider_id: String,
    adapter_id: String,
    model_id: String,
    catalog_digest: String,
    grant_digest: String,
    surface: DomainToolSurface,
}
impl ObservedDomainRun {
    pub fn run_id(&self) -> &str {
        &self.run_id
    }
    pub fn contract_digest(&self) -> &str {
        &self.contract_digest
    }
    pub fn revision(&self) -> i64 {
        self.revision
    }
    pub fn status(&self) -> &str {
        &self.status
    }
    pub fn provider_id(&self) -> &str {
        &self.provider_id
    }
    pub fn adapter_id(&self) -> &str {
        &self.adapter_id
    }
    pub fn model_id(&self) -> &str {
        &self.model_id
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
    let surface = project_domain_tool_surface(catalog, allowed_tools)?;
    let catalog_digest = field(contract, "toolCatalogDigest")?;
    let grant_digest = field(contract, "toolGrantDigest")?;
    surface.require_contract_binding(catalog_digest, grant_digest)?;
    Ok(ObservedDomainRun {
        run_id: snapshot.projection.harness_run_id,
        contract_digest: snapshot.projection.contract_digest,
        revision: snapshot.projection.revision,
        status: snapshot.projection.status,
        provider_id: expected.provider_id.to_owned(),
        adapter_id: expected.adapter_id.to_owned(),
        model_id: expected.requested_model_id.to_owned(),
        catalog_digest: catalog_digest.to_owned(),
        grant_digest: grant_digest.to_owned(),
        surface,
    })
}
