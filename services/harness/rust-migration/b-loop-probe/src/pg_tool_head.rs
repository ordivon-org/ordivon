//! One A-owned verified PostgreSQL CAS/Journal snapshot -> typed Tool
//! Intent/Fence/Receipt HEAD. No second SQL reader, Store, codec, Registry,
//! Owner dispatch identity or physical execution permission.
//!
//! Mature serde's exact typed decoding is ONLY semantic interpretation
//! of A's already verified canonical JSON. Do not use serde to recompute CAS
//! hashes, infer currentness after transaction, or dispatch a Runtime Job.
use crate::python_text::valid_trimmed;
use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument};
use ordivon_harness_pg::{read_run_readonly, ReadError, Readback, RunEvent, VerifiedToolReference};
use postgres::Client;
use serde::de::DeserializeOwned;
use serde::Deserialize;
use std::collections::BTreeSet;

#[derive(Debug)]
pub enum ToolHeadError {
    Run(ReadError),
    Invalid(&'static str),
    Mismatch(&'static str),
    UnsupportedHistoricalFence,
}
impl From<ReadError> for ToolHeadError {
    fn from(error: ReadError) -> Self {
        Self::Run(error)
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ToolHeadStanding {
    PreparedNeedsOwnerAdmission,
    UnknownRequiresOwnerReconciliation,
    ReceiptObservedNoRedispatch,
    PendingCancellationRequiresOwnerReconciliation,
}
/// Provenanced *observation* of one Run. Does not contain a Dispatch Permit
/// or a method that can call the Runtime/Provider/Gateway Owner.
#[derive(Debug)]
pub struct ObservedToolHead {
    event_id: String,
    run_id: String,
    run_revision: i64,
    prepared_revision: i64,
    intent_digest: String,
    fence_digest: String,
    client_request_id: String,
    tool_call_id: String,
    consequence: String,
    standing: ToolHeadStanding,
}
impl ObservedToolHead {
    pub fn event_id(&self) -> &str {
        &self.event_id
    }
    pub fn run_id(&self) -> &str {
        &self.run_id
    }
    pub fn run_revision(&self) -> i64 {
        self.run_revision
    }
    pub fn prepared_revision(&self) -> i64 {
        self.prepared_revision
    }
    pub fn intent_digest(&self) -> &str {
        &self.intent_digest
    }
    pub fn fence_digest(&self) -> &str {
        &self.fence_digest
    }
    pub fn client_request_id(&self) -> &str {
        &self.client_request_id
    }
    pub fn tool_call_id(&self) -> &str {
        &self.tool_call_id
    }
    pub fn recovery_consequence(&self) -> &str {
        &self.consequence
    }
    pub fn standing(&self) -> ToolHeadStanding {
        self.standing
    }
    /// This test compares two historical revisions in a snapshot only.
    /// Even "true" does NOT authorize any physical Tool execution.
    pub fn prepared_revision_is_current(&self) -> bool {
        self.standing == ToolHeadStanding::PreparedNeedsOwnerAdmission
            && self.prepared_revision == self.run_revision
    }
}

// Source Python HarnessToolStepIntent/FenceV2/Receipt use strict, versioned
// exact schemas. Reuse serde's deny_unknown_fields instead of a second
// ad-hoc JSON parser or hand-coded field list validator.
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Intent {
    schema_version: i64,
    kind: String,
    intent_id: String,
    harness_run_id: String,
    assignment_id: String,
    assignment_generation: i64,
    assignment_digest: String,
    turn_id: String,
    tool_call_id: String,
    tool_name: String,
    tool_call_digest: String,
    runtime_operation: String,
    runtime_arguments_digest: String,
    client_request_id: String,
    recovery_consequence: String,
    created_at_ms: i64,
}
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Fence {
    schema_version: i64,
    kind: String,
    fence_id: String,
    harness_run_id: String,
    run_revision: i64,
    binding_digest: String,
    intent_digest: String,
    runtime_operation: String,
    client_request_id: String,
    issued_at_ms: i64,
    expires_at_ms: i64,
}
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Receipt {
    schema_version: i64,
    kind: String,
    receipt_id: String,
    intent_digest: String,
    harness_run_id: String,
    tool_call_id: String,
    status: String,
    runtime_job_ref: Option<String>,
    observation_digest: Option<String>,
    reconciled: bool,
    created_at_ms: i64,
    previous_receipt_digest: Option<String>,
}
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct SourceSnapshot {
    schema_version: i64,
    kind: String,
    snapshot_id: String,
    harness_run_id: String,
    assignment_id: String,
    assignment_generation: i64,
    assignment_digest: String,
    tool_catalog_digest: String,
    requested_model_id: String,
    active_tool_step_intent_digests: Vec<String>,
    pause_reason: String,
    created_at_ms: i64,
}
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct PreparedData {
    tool_step_intent_digest: String,
    tool_step_intent_object_digest: String,
    dispatch_fence_digest: String,
    dispatch_fence_object_digest: String,
    snapshot_digest: String,
    snapshot_object_digest: String,
    state_object_digest: String,
    receipt_digest: Option<String>,
    receipt_object_digest: Option<String>,
    previous_receipt_object_digest: Option<String>,
    observation_object_digest: Option<String>,
}
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct ReceiptData {
    tool_step_intent_digest: String,
    tool_step_intent_object_digest: String,
    dispatch_fence_digest: String,
    dispatch_fence_object_digest: String,
    receipt_digest: String,
    receipt_object_digest: String,
    previous_receipt_object_digest: Option<String>,
    observation_object_digest: Option<String>,
}
fn parsed<T: DeserializeOwned>(
    value: &CanonicalDocument,
    fields: &[&str],
) -> Result<T, ToolHeadError> {
    let actual: BTreeSet<_> = value
        .object_entries()
        .ok_or(ToolHeadError::Invalid("not an object"))?
        .map(|(key, _)| key)
        .collect();
    let required: BTreeSet<_> = fields.iter().copied().collect();
    if actual != required {
        return Err(ToolHeadError::Invalid("not Source exact schema"));
    }
    serde_json::from_slice(&canonical_bytes(value))
        .map_err(|_| ToolHeadError::Invalid("invalid Source typed value"))
}
const INTENT_KEYS: &[&str] = &[
    "schemaVersion",
    "kind",
    "intentId",
    "harnessRunId",
    "assignmentId",
    "assignmentGeneration",
    "assignmentDigest",
    "turnId",
    "toolCallId",
    "toolName",
    "toolCallDigest",
    "runtimeOperation",
    "runtimeArgumentsDigest",
    "clientRequestId",
    "recoveryConsequence",
    "createdAtMs",
];
const FENCE_KEYS: &[&str] = &[
    "schemaVersion",
    "kind",
    "fenceId",
    "harnessRunId",
    "runRevision",
    "bindingDigest",
    "intentDigest",
    "runtimeOperation",
    "clientRequestId",
    "issuedAtMs",
    "expiresAtMs",
];
const RECEIPT_KEYS: &[&str] = &[
    "schemaVersion",
    "kind",
    "receiptId",
    "intentDigest",
    "harnessRunId",
    "toolCallId",
    "status",
    "runtimeJobRef",
    "observationDigest",
    "reconciled",
    "createdAtMs",
    "previousReceiptDigest",
];
const SNAPSHOT_KEYS: &[&str] = &[
    "schemaVersion",
    "kind",
    "snapshotId",
    "harnessRunId",
    "assignmentId",
    "assignmentGeneration",
    "assignmentDigest",
    "toolCatalogDigest",
    "requestedModelId",
    "activeToolStepIntentDigests",
    "pauseReason",
    "createdAtMs",
];
const PREPARED_KEYS: &[&str] = &[
    "toolStepIntentDigest",
    "toolStepIntentObjectDigest",
    "dispatchFenceDigest",
    "dispatchFenceObjectDigest",
    "snapshotDigest",
    "snapshotObjectDigest",
    "stateObjectDigest",
    "receiptDigest",
    "receiptObjectDigest",
    "previousReceiptObjectDigest",
    "observationObjectDigest",
];
const OUTCOME_KEYS: &[&str] = &[
    "toolStepIntentDigest",
    "toolStepIntentObjectDigest",
    "dispatchFenceDigest",
    "dispatchFenceObjectDigest",
    "receiptDigest",
    "receiptObjectDigest",
    "previousReceiptObjectDigest",
    "observationObjectDigest",
];
fn sha(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..]
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn valid_id(value: &str, prefix: &str, max: usize) -> bool {
    valid_trimmed(value, max) && value.starts_with(prefix)
}
fn related<'a>(
    state: &'a Readback,
    event: &RunEvent,
    kind: &str,
    digest: &str,
) -> Result<&'a VerifiedToolReference, ToolHeadError> {
    let mut found = state
        .tool_metadata_references
        .iter()
        .filter(|r| r.event_id() == event.event_id && r.kind() == kind && r.digest() == digest);
    let one = found
        .next()
        .ok_or(ToolHeadError::Mismatch("missing typed CAS edge"))?;
    if found.next().is_some() {
        return Err(ToolHeadError::Mismatch("ambiguous typed CAS edge"));
    }
    Ok(one)
}
fn edges_match(
    state: &Readback,
    event: &RunEvent,
    expected: &BTreeSet<(String, String)>,
) -> Result<(), ToolHeadError> {
    let actual: BTreeSet<_> = state
        .verified_reference_links
        .iter()
        .filter(|r| r.event_id() == event.event_id)
        .map(|r| (r.kind().to_owned(), r.digest().to_owned()))
        .collect();
    if &actual != expected {
        return Err(ToolHeadError::Mismatch("whole Tool CAS edge set"));
    }
    Ok(())
}
fn bind_id(run: &str, contract: &str) -> Result<String, ToolHeadError> {
    if !sha(contract) {
        return Err(ToolHeadError::Invalid("Contract digest"));
    }
    let representation = CanonicalDocument::object(vec![
        (
            "schemaVersion".into(),
            CanonicalDocument::integer_from_decimal("1")
                .map_err(|_| ToolHeadError::Invalid("version"))?,
        ),
        (
            "kind".into(),
            CanonicalDocument::string("ordivon.harness-run-store-binding"),
        ),
        ("harnessRunId".into(), CanonicalDocument::string(run)),
        (
            "assignmentId".into(),
            CanonicalDocument::string(format!("assignment:external:{}", &contract[7..31])),
        ),
        (
            "assignmentGeneration".into(),
            CanonicalDocument::integer_from_decimal("1")
                .map_err(|_| ToolHeadError::Invalid("assignment generation"))?,
        ),
        (
            "assignmentDigest".into(),
            CanonicalDocument::string(contract),
        ),
    ])
    .map_err(|_| ToolHeadError::Invalid("binding schema"))?;
    Ok(digest_bytes(&canonical_bytes(&representation)))
}
fn add_edge(edges: &mut BTreeSet<(String, String)>, kind: &str, digest: &str) {
    edges.insert((kind.to_owned(), digest.to_owned()));
}
fn qualify(read: &Readback, event: &RunEvent) -> Result<ObservedToolHead, ToolHeadError> {
    let event_kind = event.event_kind.as_str();
    let prepared = event_kind == "harness.tool-step-prepared";
    if !prepared
        && !matches!(
            event_kind,
            "harness.tool-step-recorded"
                | "harness.tool-step-unknown"
                | "harness.tool-step-reconciled"
        )
    {
        return Err(ToolHeadError::Invalid("not Tool Event"));
    }
    let data = event
        .payload
        .get("data")
        .ok_or(ToolHeadError::Invalid("Event data"))?;
    // Event schema is exact: null and missing are not interchangeable, even
    // though serde Option alone would accept an omitted field.
    let (intent_digest, intent_ref, fence_digest, standing, prepared_revision) = {
        let intent_ref_raw = data
            .field("toolStepIntentObjectDigest")
            .and_then(|v| v.as_str())
            .ok_or(ToolHeadError::Invalid("Intent ref"))?;
        let intent_semantic = data
            .field("toolStepIntentDigest")
            .and_then(|v| v.as_str())
            .ok_or(ToolHeadError::Invalid("Intent SHA"))?;
        let intent_value = related(read, event, "harness-tool-step-intent", intent_ref_raw)?;
        let intent: Intent = parsed(intent_value.value(), INTENT_KEYS)?;
        let canonical_intent = digest_bytes(&canonical_bytes(intent_value.value()));
        if !sha(intent_ref_raw)
            || canonical_intent != intent_ref_raw
            || canonical_intent != intent_semantic
            || intent.schema_version != 1
            || intent.kind != "ordivon.harness-tool-step-intent"
        {
            return Err(ToolHeadError::Mismatch("Intent value/digest/schema"));
        }
        let contract = &read.projection.contract_digest;
        let run = &read.projection.harness_run_id;
        if !valid_id(&intent.intent_id, "harness-tool-step-intent:", 512)
            || intent.harness_run_id != *run
            || intent.assignment_id != format!("assignment:external:{}", &contract[7..31])
            || intent.assignment_generation != 1
            || intent.assignment_digest != *contract
            || !valid_id(&intent.turn_id, "turn:", 512)
            || !valid_id(&intent.tool_call_id, "", 300)
            || !valid_id(&intent.tool_name, "", 120)
            || !valid_id(&intent.runtime_operation, "", 160)
            || !valid_id(&intent.client_request_id, "", 300)
            || !sha(&intent.tool_call_digest)
            || !sha(&intent.runtime_arguments_digest)
            || intent.created_at_ms < 0
            || intent.created_at_ms > event.recorded_at_ms
            || !matches!(
                intent.recovery_consequence.as_str(),
                "observation-only"
                    | "workspace-change-possible"
                    | "process-or-external-effect-possible"
            )
        {
            return Err(ToolHeadError::Mismatch("Intent vs Run binding/source"));
        }
        let fence_ref_raw = data
            .field("dispatchFenceObjectDigest")
            .and_then(|v| v.as_str())
            .ok_or(ToolHeadError::UnsupportedHistoricalFence)?;
        let fence_semantic = data
            .field("dispatchFenceDigest")
            .and_then(|v| v.as_str())
            .ok_or(ToolHeadError::UnsupportedHistoricalFence)?;
        let fence_value = related(read, event, "harness-dispatch-fence", fence_ref_raw)?;
        let fence: Fence = parsed(fence_value.value(), FENCE_KEYS)?;
        let canonical_fence = digest_bytes(&canonical_bytes(fence_value.value()));
        if fence.schema_version != 2 {
            return Err(ToolHeadError::UnsupportedHistoricalFence);
        }
        if fence.kind != "ordivon.harness-dispatch-fence"
            || !sha(fence_ref_raw)
            || canonical_fence != fence_ref_raw
            || canonical_fence != fence_semantic
            || !valid_id(&fence.fence_id, "harness-dispatch-fence:", 512)
            || fence.harness_run_id != *run
            || fence.binding_digest != bind_id(run, contract)?
            || fence.intent_digest != canonical_intent
            || fence.runtime_operation != intent.runtime_operation
            || fence.client_request_id != intent.client_request_id
            || fence.run_revision < 1
            || fence.issued_at_ms < 0
            || fence.issued_at_ms < intent.created_at_ms
            || fence.expires_at_ms <= fence.issued_at_ms
        {
            return Err(ToolHeadError::Mismatch("Fence vs Intent/Run/source"));
        }

        let mut expected = BTreeSet::from([
            (
                "harness-tool-step-intent".to_owned(),
                canonical_intent.clone(),
            ),
            ("harness-dispatch-fence".to_owned(), canonical_fence.clone()),
        ]);
        let standing = if prepared {
            let prepared_data: PreparedData = parsed(&data, PREPARED_KEYS)?;
            if prepared_data.tool_step_intent_digest != canonical_intent
                || prepared_data.tool_step_intent_object_digest != canonical_intent
                || prepared_data.dispatch_fence_digest != canonical_fence
                || prepared_data.dispatch_fence_object_digest != canonical_fence
                || prepared_data.snapshot_digest != prepared_data.snapshot_object_digest
                || !sha(&prepared_data.snapshot_digest)
                || !sha(&prepared_data.state_object_digest)
                || prepared_data.receipt_digest.is_some()
                || prepared_data.receipt_object_digest.is_some()
                || prepared_data.previous_receipt_object_digest.is_some()
                || prepared_data.observation_object_digest.is_some()
                || fence.run_revision != event.run_revision
            {
                return Err(ToolHeadError::Mismatch(
                    "prepared Tool Event/Fence metadata",
                ));
            }
            add_edge(
                &mut expected,
                "harness-run-snapshot",
                &prepared_data.snapshot_digest,
            );
            add_edge(
                &mut expected,
                "harness-run-state",
                &prepared_data.state_object_digest,
            );
            let mut snapshots = read.tool_snapshot_metadata.iter().filter(|s| {
                s.event_id() == event.event_id && s.digest() == prepared_data.snapshot_digest
            });
            let meta = snapshots
                .next()
                .ok_or(ToolHeadError::Mismatch("Tool Snapshot CAS missing"))?;
            if snapshots.next().is_some() || !meta.source_contract_valid() {
                return Err(ToolHeadError::Mismatch("Tool Snapshot source field set"));
            }
            let source: SourceSnapshot = parsed(meta.fields(), SNAPSHOT_KEYS)?;
            let catalog = read
                .contract
                .field("toolCatalogDigest")
                .and_then(|v| v.as_str())
                .ok_or(ToolHeadError::Invalid("Tool Catalog Contract"))?;
            let model = read
                .contract
                .field("requestedModelId")
                .and_then(|v| v.as_str())
                .ok_or(ToolHeadError::Invalid("Provider model Contract"))?;
            if source.schema_version != 1
                || source.kind != "ordivon.harness-run-snapshot"
                || !valid_id(&source.snapshot_id, "harness-run-snapshot:", 512)
                || source.harness_run_id != *run
                || source.assignment_id != intent.assignment_id
                || source.assignment_generation != 1
                || source.assignment_digest != *contract
                || source.tool_catalog_digest != catalog
                || source.requested_model_id != model
                || source.pause_reason != "effect-dispatch-pending"
                || source.created_at_ms != event.recorded_at_ms
                || source.active_tool_step_intent_digests != vec![canonical_intent.clone()]
            {
                return Err(ToolHeadError::Mismatch(
                    "Source Snapshot lacks active Intent",
                ));
            }
            ToolHeadStanding::PreparedNeedsOwnerAdmission
        } else {
            let recorded: ReceiptData = parsed(&data, OUTCOME_KEYS)?;
            if recorded.tool_step_intent_digest != canonical_intent
                || recorded.tool_step_intent_object_digest != canonical_intent
                || recorded.dispatch_fence_digest != canonical_fence
                || recorded.dispatch_fence_object_digest != canonical_fence
                || fence.run_revision >= event.run_revision
                || !sha(&recorded.receipt_digest)
                || !sha(&recorded.receipt_object_digest)
                || recorded.receipt_digest != recorded.receipt_object_digest
            {
                return Err(ToolHeadError::Mismatch("Receipt Event/Fence binding"));
            }
            let record = related(
                read,
                event,
                "harness-tool-step-receipt",
                &recorded.receipt_object_digest,
            )?;
            let receipt: Receipt = parsed(record.value(), RECEIPT_KEYS)?;
            if digest_bytes(&canonical_bytes(record.value())) != recorded.receipt_digest
                || receipt.schema_version != 1
                || receipt.kind != "ordivon.harness-tool-step-receipt"
                || !valid_id(&receipt.receipt_id, "harness-tool-step-receipt:", 512)
                || receipt.intent_digest != canonical_intent
                || receipt.harness_run_id != *run
                || receipt.tool_call_id != intent.tool_call_id
                || receipt.created_at_ms < 0
                || receipt.created_at_ms > event.recorded_at_ms
                || receipt.previous_receipt_digest != recorded.previous_receipt_object_digest
                || !matches!(
                    receipt.status.as_str(),
                    "observed" | "rejected" | "unknown" | "cancel-requested" | "cancelled"
                )
                || receipt
                    .runtime_job_ref
                    .as_ref()
                    .is_some_and(|id| !valid_id(id, "", 512))
                || receipt
                    .observation_digest
                    .as_ref()
                    .is_some_and(|id| !sha(id))
                || receipt
                    .previous_receipt_digest
                    .as_ref()
                    .is_some_and(|id| !sha(id))
            {
                return Err(ToolHeadError::Mismatch("Receipt vs Intent/Run/source"));
            }
            if matches!(
                receipt.status.as_str(),
                "observed" | "rejected" | "unknown" | "cancelled"
            ) && receipt.observation_digest.is_none()
            {
                return Err(ToolHeadError::Mismatch(
                    "terminal receipt missing observation",
                ));
            }
            if receipt.status == "rejected" && receipt.runtime_job_ref.is_some()
                || receipt.status == "cancel-requested" && receipt.runtime_job_ref.is_none()
            {
                return Err(ToolHeadError::Mismatch("Receipt Runtime Job requirement"));
            }
            if event_kind == "harness.tool-step-unknown" && receipt.status != "unknown"
                || event_kind == "harness.tool-step-recorded"
                    && (receipt.status == "unknown" || receipt.reconciled)
                || event_kind == "harness.tool-step-reconciled"
                    && (receipt.status == "unknown" || !receipt.reconciled)
            {
                return Err(ToolHeadError::Mismatch("Event/Receipt status mismatch"));
            }
            add_edge(
                &mut expected,
                "harness-tool-step-receipt",
                &recorded.receipt_object_digest,
            );
            if let Some(ref prior_sha) = recorded.previous_receipt_object_digest {
                let prior = related(read, event, "harness-tool-step-receipt", prior_sha)?;
                let previous: Receipt = parsed(prior.value(), RECEIPT_KEYS)?;
                if digest_bytes(&canonical_bytes(prior.value())) != *prior_sha
                    || previous.intent_digest != canonical_intent
                    || previous.harness_run_id != *run
                    || previous.tool_call_id != intent.tool_call_id
                    || matches!(
                        previous.status.as_str(),
                        "observed" | "rejected" | "unknown" | "cancelled"
                    )
                    || previous.created_at_ms > receipt.created_at_ms
                {
                    return Err(ToolHeadError::Mismatch("previous Receipt binding/terminal"));
                }
                add_edge(&mut expected, "harness-tool-step-receipt", prior_sha);
            }
            if let Some(ref observation_sha) = recorded.observation_object_digest {
                if receipt.observation_digest.as_ref() != Some(observation_sha)
                    || !sha(observation_sha)
                {
                    return Err(ToolHeadError::Mismatch("retained Observation vs Receipt"));
                }
                add_edge(&mut expected, "harness-tool-observation", observation_sha);
            }
            match receipt.status.as_str() {
                "unknown" => ToolHeadStanding::UnknownRequiresOwnerReconciliation,
                "cancel-requested" => {
                    ToolHeadStanding::PendingCancellationRequiresOwnerReconciliation
                }
                _ => ToolHeadStanding::ReceiptObservedNoRedispatch,
            }
        };
        edges_match(read, event, &expected)?;
        (
            canonical_intent,
            intent,
            canonical_fence,
            standing,
            fence.run_revision,
        )
    };
    // Keep only useful typed facts and no CAS/Tool arguments or authority token.
    Ok(ObservedToolHead {
        event_id: event.event_id.clone(),
        run_id: read.projection.harness_run_id.clone(),
        run_revision: read.projection.revision,
        prepared_revision,
        intent_digest,
        fence_digest,
        client_request_id: intent_ref.client_request_id.clone(),
        tool_call_id: intent_ref.tool_call_id.clone(),
        consequence: intent_ref.recovery_consequence.clone(),
        standing,
    })
}
pub fn inspect_pg_tool_head(
    db: &mut Client,
    schema: &str,
    run: &str,
) -> Result<Option<ObservedToolHead>, ToolHeadError> {
    let read = read_run_readonly(db, schema, run)?;
    read.events
        .iter()
        .rev()
        .find(|event| {
            matches!(
                event.event_kind.as_str(),
                "harness.tool-step-prepared"
                    | "harness.tool-step-recorded"
                    | "harness.tool-step-unknown"
                    | "harness.tool-step-reconciled"
            )
        })
        .map(|event| qualify(&read, event))
        .transpose()
}
