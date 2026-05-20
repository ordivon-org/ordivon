use serde::{Deserialize, Serialize};

use crate::digest::parse_rfc3339;
use crate::errors::KernelError;
use crate::types::{ActionClass, ObservationStatus, Origin};

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "ObservedEventWire")]
pub struct ObservedEvent {
    pub(crate) event_id: String,
    pub(crate) trace_id: String,
    pub(crate) source: String,
    pub(crate) source_identity: String,
    pub(crate) observed_sequence: u64,
    pub(crate) event_type: String,
    pub(crate) action_class: ActionClass,
    pub(crate) target_ref: String,
    pub(crate) timestamp: String,
    pub(crate) payload_hash: String,
    pub(crate) prev_event_hash: String,
    pub(crate) origin: Origin,
    pub(crate) status: ObservationStatus,
    pub(crate) authority_ref: String,
    pub(crate) idempotency_key: String,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct ObservedEventWire {
    event_id: String,
    trace_id: String,
    source: String,
    source_identity: String,
    observed_sequence: u64,
    event_type: String,
    action_class: ActionClass,
    target_ref: String,
    timestamp: String,
    payload_hash: String,
    prev_event_hash: String,
    origin: Origin,
    status: ObservationStatus,
    authority_ref: String,
    idempotency_key: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TrustedObservedEventDraft {
    pub event_id: String,
    pub trace_id: String,
    pub source: String,
    pub source_identity: String,
    pub observed_sequence: u64,
    pub event_type: String,
    pub action_class: ActionClass,
    pub target_ref: String,
    pub timestamp: String,
    pub payload_hash: String,
    pub prev_event_hash: String,
    pub origin: Origin,
    pub status: ObservationStatus,
    pub authority_ref: String,
    pub idempotency_key: String,
}

impl ObservedEvent {
    pub fn trusted(draft: TrustedObservedEventDraft) -> Result<Self, KernelError> {
        let event = Self {
            event_id: draft.event_id,
            trace_id: draft.trace_id,
            source: draft.source,
            source_identity: draft.source_identity,
            observed_sequence: draft.observed_sequence,
            event_type: draft.event_type,
            action_class: draft.action_class,
            target_ref: draft.target_ref,
            timestamp: draft.timestamp,
            payload_hash: draft.payload_hash,
            prev_event_hash: draft.prev_event_hash,
            origin: draft.origin,
            status: draft.status,
            authority_ref: draft.authority_ref,
            idempotency_key: draft.idempotency_key,
        };
        event.validate()?;
        Ok(event)
    }

    pub fn validate_origin(&self) -> Result<(), KernelError> {
        if self.origin.can_emit_observed_event() {
            Ok(())
        } else {
            Err(KernelError::ForgedObservedEvent {
                origin: format!("{:?}", self.origin),
            })
        }
    }

    pub fn validate(&self) -> Result<(), KernelError> {
        self.validate_origin()?;
        if self.source_identity.trim().is_empty() {
            return Err(KernelError::MissingTrustedSourceIdentity);
        }
        if self.target_ref.trim().is_empty() {
            return Err(KernelError::MissingTargetRef);
        }
        if self.authority_ref.trim().is_empty() && self.action_class.is_effectful() {
            return Err(KernelError::MissingAuthorityReference);
        }
        if self.idempotency_key.trim().is_empty() && self.action_class.is_effectful() {
            return Err(KernelError::MissingIdempotencyKey);
        }
        parse_rfc3339(&self.timestamp)?;
        Ok(())
    }

    pub fn event_id(&self) -> &str {
        &self.event_id
    }

    pub fn trace_id(&self) -> &str {
        &self.trace_id
    }

    pub fn source_identity(&self) -> &str {
        &self.source_identity
    }

    pub fn observed_sequence(&self) -> u64 {
        self.observed_sequence
    }

    pub fn action_class(&self) -> &ActionClass {
        &self.action_class
    }

    pub fn target_ref(&self) -> &str {
        &self.target_ref
    }

    pub fn timestamp(&self) -> &str {
        &self.timestamp
    }

    pub fn payload_hash(&self) -> &str {
        &self.payload_hash
    }

    pub fn status(&self) -> &ObservationStatus {
        &self.status
    }

    pub fn authority_ref(&self) -> &str {
        &self.authority_ref
    }

    pub fn idempotency_key(&self) -> &str {
        &self.idempotency_key
    }
}

impl TryFrom<ObservedEventWire> for ObservedEvent {
    type Error = KernelError;

    fn try_from(value: ObservedEventWire) -> Result<Self, Self::Error> {
        Self::trusted(TrustedObservedEventDraft {
            event_id: value.event_id,
            trace_id: value.trace_id,
            source: value.source,
            source_identity: value.source_identity,
            observed_sequence: value.observed_sequence,
            event_type: value.event_type,
            action_class: value.action_class,
            target_ref: value.target_ref,
            timestamp: value.timestamp,
            payload_hash: value.payload_hash,
            prev_event_hash: value.prev_event_hash,
            origin: value.origin,
            status: value.status,
            authority_ref: value.authority_ref,
            idempotency_key: value.idempotency_key,
        })
    }
}
