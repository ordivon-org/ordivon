//! Authenticated source projections; not Tool effect permission.
use ordivon_harness_core::CanonicalDocument;
use std::fmt;

#[derive(Debug)]
pub enum ReadError {
    Database(postgres::Error),
    MissingRun(String),
    InvalidSchema,
    Corruption(String),
    /// An old Python interpreter may admit this value under other depth/digit
    /// settings. This is NOT evidence of physically corrupt CAS bytes.
    UnsupportedLegacyRepresentation(String),
}

impl fmt::Display for ReadError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Database(error) => write!(f, "PostgreSQL read failed: {error}"),
            Self::MissingRun(run_id) => write!(f, "Harness Run is absent: {run_id}"),
            Self::InvalidSchema => {
                write!(f, "Harness schema must be one lower-case SQL identifier")
            }
            Self::Corruption(message) => write!(f, "Harness Journal corruption: {message}"),
            Self::UnsupportedLegacyRepresentation(digest) => write!(
                f,
                "Harness legacy CAS representation needs separate qualification: {digest}"
            ),
        }
    }
}

impl std::error::Error for ReadError {}

impl From<postgres::Error> for ReadError {
    fn from(value: postgres::Error) -> Self {
        Self::Database(value)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RunProjection {
    pub harness_run_id: String,
    pub contract_digest: String,
    pub contract_object_digest: String,
    pub caller_id: String,
    pub caller_run_ref: String,
    pub status: String,
    pub revision: i64,
    pub created_at_ms: i64,
    pub updated_at_ms: i64,
    pub terminal_event_id: Option<String>,
}

#[derive(Debug, Clone)]
pub struct RunEvent {
    pub sequence: i64,
    pub event_id: String,
    pub run_revision: i64,
    pub event_kind: String,
    pub payload_digest: String,
    pub payload: CanonicalDocument,
    pub caused_by_event_id: Option<String>,
    pub recorded_at_ms: i64,
}

/// A single Provider record CAS object authenticated inside A's READ ONLY
/// PG transaction and tied to the exact Run Event reference edge.
/// No lease, Provider dispatch permission, or revalidation of currentness.
#[derive(Debug, Clone)]
pub struct VerifiedProviderReference {
    pub(crate) event_id: String,
    pub(crate) digest: String,
    pub(crate) value: CanonicalDocument,
}
/// Explicitly bounded non-sensitive fields of a CAS-verified Provider
/// FailureReceipt. Raw failure detail and unrelated Run state stay private.
#[derive(Clone, Copy, Debug)]
pub enum ProviderFailureTextField {
    Kind,
    ProviderCallId,
    RequestDigest,
    ProviderRequestDigest,
    FailureCode,
    DispatchSafety,
}

/// One Provider FailureReceipt whose CAS bytes were already validated in
/// the single A-owned PG read-only snapshot. B evaluates domain semantics
/// from this narrow projection; A never exports the potentially sensitive
/// raw failure 'detail' string or an arbitrary CAS object for this purpose.
#[derive(Clone)]
pub struct VerifiedProviderFailureReference {
    pub(crate) event_id: String,
    pub(crate) digest: String,
    pub(crate) value: CanonicalDocument,
}
impl fmt::Debug for VerifiedProviderFailureReference {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("VerifiedProviderFailureReference")
            .field("event_id", &self.event_id)
            .field("digest", &self.digest)
            .field("value", &"<private failure detail redacted>")
            .finish()
    }
}
impl VerifiedProviderFailureReference {
    pub fn event_id(&self) -> &str {
        &self.event_id
    }
    pub fn digest(&self) -> &str {
        &self.digest
    }
    pub fn field_count(&self) -> Option<usize> {
        self.value.object_len()
    }
    pub fn version_is_one(&self) -> bool {
        self.value
            .field("schemaVersion")
            .and_then(|v| v.integer_text())
            == Some("1")
    }
    pub fn source_text_field(&self, field: ProviderFailureTextField) -> Option<&str> {
        let name = match field {
            ProviderFailureTextField::Kind => "kind",
            ProviderFailureTextField::ProviderCallId => "providerCallId",
            ProviderFailureTextField::RequestDigest => "requestDigest",
            ProviderFailureTextField::ProviderRequestDigest => "providerRequestDigest",
            ProviderFailureTextField::FailureCode => "failureCode",
            ProviderFailureTextField::DispatchSafety => "dispatchSafety",
        };
        self.value.field(name).and_then(|v| v.as_str())
    }
    pub fn detail_is_source_valid(&self, max_bytes: usize) -> bool {
        let Some(detail) = self.value.field("detail").and_then(|v| v.as_str()) else {
            return false;
        };
        !detail.is_empty()
            && detail.len() <= max_bytes
            && detail
                .trim_matches(|c: char| c.is_whitespace() || ('\u{001c}'..='\u{001f}').contains(&c))
                == detail
    }
}

/// A validated CAS reference edge, with kind/digest but NO unrelated private
/// object content exposed to the Agent consumer. Same PG snapshot.
#[derive(Debug, Clone)]
pub struct VerifiedReferenceLink {
    pub(crate) event_id: String,
    pub(crate) digest: String,
    pub(crate) kind: String,
    pub(crate) byte_length: i64,
}
impl VerifiedReferenceLink {
    pub fn event_id(&self) -> &str {
        &self.event_id
    }
    pub fn digest(&self) -> &str {
        &self.digest
    }
    pub fn kind(&self) -> &str {
        &self.kind
    }
    pub fn byte_length(&self) -> i64 {
        self.byte_length
    }
}
impl VerifiedProviderReference {
    pub fn event_id(&self) -> &str {
        &self.event_id
    }
    pub fn digest(&self) -> &str {
        &self.digest
    }
    pub fn value(&self) -> &CanonicalDocument {
        &self.value
    }
}

/// Verified metadata-only Tool execution semantic objects from the SAME
/// single read-only PG CAS/Journal transaction. Unlike arbitrary State,
/// Snapshot and Observation CAS, these three source kinds contain only
/// versioned Intent/Fence/Receipt identities and digests, not Tool payloads.
/// The existence of a verified Tool value is NOT execution authorization.
#[derive(Clone)]
pub struct VerifiedToolReference {
    pub(crate) event_id: String,
    pub(crate) digest: String,
    pub(crate) kind: String,
    pub(crate) value: CanonicalDocument,
}
// A Debug representation of the PG Readback is frequently logged by
// reviewers. Never dump the raw Tool Intent/Fence/Receipt (clientRequestId,
// recovery identifiers, future owner details) into cross-owner log text.
impl fmt::Debug for VerifiedToolReference {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("VerifiedToolReference")
            .field("event_id", &self.event_id)
            .field("digest", &self.digest)
            .field("kind", &self.kind)
            .field("value", &"<redacted>")
            .finish()
    }
}

impl VerifiedToolReference {
    pub fn event_id(&self) -> &str {
        &self.event_id
    }
    pub fn digest(&self) -> &str {
        &self.digest
    }
    pub fn kind(&self) -> &str {
        &self.kind
    }
    pub fn value(&self) -> &CanonicalDocument {
        &self.value
    }
}

/// Only SOURCE Snapshot authority binding fields extracted from verified
/// CAS bytes. Private State, Observation, messages and arbitrary budget JSON
/// are never exposed. This is an observation, not a dispatch permit.
#[derive(Debug, Clone)]
pub struct VerifiedToolSnapshotMetadata {
    pub(crate) event_id: String,
    pub(crate) digest: String,
    pub(crate) fields: CanonicalDocument,
    pub(crate) source_contract_valid: bool,
}
impl VerifiedToolSnapshotMetadata {
    pub fn event_id(&self) -> &str {
        &self.event_id
    }
    pub fn digest(&self) -> &str {
        &self.digest
    }
    pub fn fields(&self) -> &CanonicalDocument {
        &self.fields
    }
    pub fn source_contract_valid(&self) -> bool {
        self.source_contract_valid
    }
}

#[derive(Debug, Clone)]
pub struct Readback {
    pub projection: RunProjection,
    pub contract: CanonicalDocument,
    pub events: Vec<RunEvent>,
    /// Expose only Provider record references already authenticated against
    /// the same PG snapshot; do not expose other potentially private CAS.
    pub provider_record_references: Vec<VerifiedProviderReference>,
    /// Only verified Provider FailureReceipt CAS bodies, for B's source
    /// protocol validation. Not the private Run State/Request/Result bodies.
    pub provider_failure_references: Vec<VerifiedProviderFailureReference>,
    /// Source-authenticated metadata only, necessary for proving the current
    /// Provider record's state/Result/Failure attachments actually belong to
    /// the same Run Event; prevents forged unattached Provider CAS.
    pub verified_reference_links: Vec<VerifiedReferenceLink>,
    /// Qualified *only* for the three Tool metadata CAS kinds. Untrusted
    /// Event data is still interpreted separately by the B semantic consumer.
    pub tool_metadata_references: Vec<VerifiedToolReference>,
    /// Whitelisted active-intent SOURCE Snapshot metadata from the same PG
    /// transaction; excludes all raw messages, State and Observations.
    pub tool_snapshot_metadata: Vec<VerifiedToolSnapshotMetadata>,
}
