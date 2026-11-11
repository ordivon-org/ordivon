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

/// Authentication here is from A's single PG snapshot, not an arbitrary
/// caller-supplied Provider JSON. This has no execution or retry permission.
#[derive(Debug)]
pub enum PgProviderRecoveryError {
    Run(PgDomainInspectionError),
    MissingOrAmbiguousEventReference,
    EventRecordMismatch(&'static str),
    UnsupportedV3ProviderRecord,
    InvalidProviderV4,
}
impl From<PgDomainInspectionError> for PgProviderRecoveryError {
    fn from(value: PgDomainInspectionError) -> Self {
        Self::Run(value)
    }
}

#[derive(Debug)]
pub struct ObservedProviderHead {
    model: ObservedModelIdentity,
    event_id: String,
    record: crate::provider_head::ProviderRecordHead,
}
impl ObservedProviderHead {
    pub fn event_id(&self) -> &str {
        &self.event_id
    }
    pub fn run_id(&self) -> &str {
        &self.model.run_id
    }
    pub fn run_revision(&self) -> i64 {
        self.model.revision
    }
    pub fn status(&self) -> crate::provider_head::ProviderStatus {
        self.record.status
    }
    pub fn recovery_posture(&self) -> crate::provider_head::RecoveryPosture {
        self.record.status.recovery_posture()
    }
    pub fn record_digest(&self) -> &str {
        &self.record.canonical_digest
    }
    pub fn result_digest(&self) -> Option<&str> {
        self.record.result_digest.as_deref()
    }
}

fn provider_event_status(event_kind: &str) -> Option<crate::provider_head::ProviderStatus> {
    use crate::provider_head::ProviderStatus;
    match event_kind {
        "harness.provider-call-claimed" | "harness.provider-call-superseded" => {
            Some(ProviderStatus::Claimed)
        }
        "harness.provider-call-dispatching" => Some(ProviderStatus::Dispatching),
        "harness.provider-call-completed" => Some(ProviderStatus::Completed),
        "harness.provider-call-failed" => Some(ProviderStatus::Failed),
        "harness.provider-call-unknown" => Some(ProviderStatus::Unknown),
        _ => None,
    }
}
fn provider_event_clears_head(event_kind: &str) -> bool {
    matches!(
        event_kind,
        "harness.snapshot-recorded"
            | "harness.working-set-recorded"
            | "harness.run-paused"
            | "harness.tool-step-prepared"
            | "harness.run-stopped"
            | "harness.run-completed"
            | "harness.run-failed"
    )
}
fn event_text<'a>(
    doc: &'a CanonicalDocument,
    key: &str,
) -> Result<&'a str, PgProviderRecoveryError> {
    doc.field(key)
        .and_then(|v| v.as_str())
        .ok_or(PgProviderRecoveryError::EventRecordMismatch(
            "missing Provider event field",
        ))
}

/// The Python source EventSourcedRunContinuity._heads() clears Provider heads
/// on snapshot/tool/terminal events. Otherwise the final Provider Event is
/// authoritative for a bounded current-head observation. Never redispatch:
/// dispatching and unknown call for authoritative Provider reconciliation.
pub fn inspect_pg_provider_head(
    connection: &mut Client,
    schema: &str,
    run_id: &str,
    expected: ExpectedModel<'_>,
) -> Result<Option<ObservedProviderHead>, PgProviderRecoveryError> {
    let (snapshot, model) = read_bound_model(connection, schema, run_id, expected)?;
    let mut head = None;
    for event in &snapshot.events {
        if provider_event_clears_head(&event.event_kind) {
            head = None;
        }
        if provider_event_status(&event.event_kind).is_some() {
            head = Some(event);
        }
    }
    let Some(event) = head else { return Ok(None) };
    let expected_status = provider_event_status(&event.event_kind).ok_or(
        PgProviderRecoveryError::EventRecordMismatch("unrecognized Provider status"),
    )?;
    let data = event
        .payload
        .get("data")
        .ok_or(PgProviderRecoveryError::EventRecordMismatch(
            "missing Event data",
        ))?;
    let object_digest = event_text(&data, "providerCallRecordObjectDigest")?;
    let record_digest = event_text(&data, "providerCallRecordDigest")?;
    let related: Vec<_> = snapshot
        .provider_record_references
        .iter()
        .filter(|r| r.event_id() == event.event_id)
        .collect();
    if related.len() != 1 || related[0].digest() != object_digest {
        return Err(PgProviderRecoveryError::MissingOrAmbiguousEventReference);
    }
    let record = related[0].value();
    match record.field("schemaVersion").and_then(|v| v.integer_text()) {
        Some("3") => return Err(PgProviderRecoveryError::UnsupportedV3ProviderRecord),
        Some("4") => {}
        _ => return Err(PgProviderRecoveryError::InvalidProviderV4),
    };
    let parsed = crate::provider_head::inspect_v4(record)
        .map_err(|_| PgProviderRecoveryError::InvalidProviderV4)?;
    let recorded_ms = event.recorded_at_ms.to_string();
    if parsed.status != expected_status
        || parsed.canonical_digest != record_digest
        || record.field("harnessRunId").and_then(|v| v.as_str()) != Some(run_id)
        || record.field("adapterId").and_then(|v| v.as_str()) != Some(expected.adapter_id)
        || record.field("requestedModelId").and_then(|v| v.as_str())
            != Some(expected.requested_model_id)
        || record.field("recordedAtMs").and_then(|v| v.integer_text()) != Some(recorded_ms.as_str())
    {
        return Err(PgProviderRecoveryError::EventRecordMismatch(
            "Provider event/status/model/digest/time mismatch",
        ));
    }

    // Python _append_provider_event links precisely record, state and optional
    // request/result/failure content to this same event, with source-defined
    // CAS kinds. Validate the *set*, not just one matching record digest.
    let mut expected_edges = std::collections::BTreeSet::new();
    expected_edges.insert(("harness-provider-call-record", object_digest.to_owned()));
    for (field, kind) in [
        ("stateObjectDigest", "harness-run-state"),
        ("requestObjectDigest", "agent-turn-request"),
        ("resultObjectDigest", "agent-turn-result"),
        ("failureObjectDigest", "harness-provider-call-failure"),
    ] {
        let observed = record
            .get(field)
            .ok_or(PgProviderRecoveryError::InvalidProviderV4)?;
        if data.get(field) != Some(observed.clone()) {
            return Err(PgProviderRecoveryError::EventRecordMismatch(
                "Provider event vs record ref mismatch",
            ));
        }
        if let Some(digest) = observed.as_string() {
            expected_edges.insert((kind, digest.to_owned()));
        }
    }
    let real_edges: std::collections::BTreeSet<_> = snapshot
        .verified_reference_links
        .iter()
        .filter(|r| r.event_id() == event.event_id)
        .map(|r| (r.kind(), r.digest().to_owned()))
        .collect();
    if real_edges != expected_edges {
        return Err(PgProviderRecoveryError::EventRecordMismatch(
            "Provider referenced CAS edge set mismatch",
        ));
    }
    Ok(Some(ObservedProviderHead {
        model,
        event_id: event.event_id.clone(),
        record: parsed,
    }))
}
