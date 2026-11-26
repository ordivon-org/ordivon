//! Existing Web v1 identity bytes and typed Grant preparation.
use super::domain::canonical;
use super::rows::{AuditRow, GrantRow};
use super::{EffectError, GrantFence};
use crate::domain::representable;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use uuid::Uuid;
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GrantCreate {
    pub grant_id: String,
    pub principal_id: String,
    pub agent_id: String,
    pub audience: String,
    pub allowed_actions: Vec<String>,
    pub resource_prefixes: Vec<String>,
    pub expires_at_epoch_seconds: i64,
    pub max_risk_class: String,
    pub step_up_at_or_above: String,
    pub remaining_effects: i64,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GrantSnapshot {
    pub grant_id: String,
    pub grant_digest: String,
    pub principal_id: String,
    pub agent_id: String,
    pub audience: String,
    pub allowed_actions: Vec<String>,
    pub resource_prefixes: Vec<String>,
    pub expires_at_epoch_seconds: i64,
    pub max_risk_class: String,
    pub step_up_at_or_above: String,
    pub remaining_effects: i64,
    pub active: bool,
    pub revision: i64,
}
impl GrantSnapshot {
    pub fn fence(&self) -> GrantFence {
        GrantFence {
            grant_id: self.grant_id.clone(),
            grant_digest: self.grant_digest.clone(),
            principal_id: self.principal_id.clone(),
            agent_id: self.agent_id.clone(),
            revision: self.revision,
        }
    }
}
impl GrantRow {
    pub(super) fn snapshot(&self) -> Result<GrantSnapshot, EffectError> {
        let (allowed_actions, resource_prefixes) = self.checked()?;
        Ok(GrantSnapshot {
            grant_id: self.grant_id.clone(),
            grant_digest: self.grant_digest.clone(),
            principal_id: self.principal_id.clone(),
            agent_id: self.agent_id.clone(),
            audience: self.audience.clone(),
            allowed_actions,
            resource_prefixes,
            expires_at_epoch_seconds: self.expires_at,
            max_risk_class: self.max_risk_class.clone(),
            step_up_at_or_above: self.step_up_at_or_above.clone(),
            remaining_effects: self.remaining_effects,
            active: self.active == 1,
            revision: self.revision,
        })
    }
}
// JS Array.sort compares UTF-16 code units, not Unicode scalar order.
// Precompute keys once rather than re-encoding strings on every comparison.
fn normalize(values: Vec<String>) -> Vec<String> {
    let mut keys: Vec<_> = values
        .into_iter()
        .map(|s| (s.encode_utf16().collect::<Vec<_>>(), s))
        .collect();
    keys.sort_unstable_by(|a, b| a.0.cmp(&b.0));
    keys.dedup_by(|a, b| a.0 == b.0);
    keys.into_iter().map(|(_, s)| s).collect()
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct Identity<'a> {
    grant_id: &'a str,
    principal_id: &'a str,
    agent_id: &'a str,
    audience: &'a str,
    allowed_actions: &'a [String],
    resource_prefixes: &'a [String],
    expires_at_epoch_seconds: i64,
    max_risk_class: &'a str,
    step_up_at_or_above: &'a str,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct IssuedDetail<'a> {
    agent_id: &'a str,
    grant_digest: &'a str,
}
fn encode(v: &impl Serialize) -> Result<String, EffectError> {
    serde_json::to_string(v).map_err(|_| EffectError::Invalid)
}
#[derive(Debug, Clone)]
pub struct PreparedGrant {
    pub(super) row: GrantRow,
    pub(super) audit: AuditRow,
}
impl PreparedGrant {
    pub fn new(mut input: GrantCreate, audit_id: Uuid, now: i64) -> Result<Self, EffectError> {
        if input.resource_prefixes.is_empty()
            || input.resource_prefixes.iter().any(|p| !canonical(p))
        {
            return Err(EffectError::InvalidGrantScope);
        }
        if [
            &input.grant_id,
            &input.principal_id,
            &input.agent_id,
            &input.audience,
        ]
        .iter()
        .any(|v| v.is_empty() || v.contains('\0'))
            || input.allowed_actions.iter().any(|v| v.contains('\0'))
            || !representable("", "", now)
            || !representable("", "", input.expires_at_epoch_seconds)
            || !representable("", "", input.remaining_effects)
            || input.remaining_effects < 0
        {
            return Err(EffectError::Invalid);
        }
        input.allowed_actions = normalize(input.allowed_actions);
        input.resource_prefixes = normalize(input.resource_prefixes);
        let identity = Identity {
            grant_id: &input.grant_id,
            principal_id: &input.principal_id,
            agent_id: &input.agent_id,
            audience: &input.audience,
            allowed_actions: &input.allowed_actions,
            resource_prefixes: &input.resource_prefixes,
            expires_at_epoch_seconds: input.expires_at_epoch_seconds,
            max_risk_class: &input.max_risk_class,
            step_up_at_or_above: &input.step_up_at_or_above,
        };
        let mut digest = String::with_capacity(71);
        digest.push_str("sha256:");
        for byte in Sha256::digest(encode(&identity)?.as_bytes()) {
            use std::fmt::Write as _;
            write!(&mut digest, "{byte:02x}").expect("writing to String");
        }
        let audit = AuditRow {
            event_id: audit_id.to_string(),
            principal_id: Some(input.principal_id.clone()),
            event_type: "agent.grant.issued".into(),
            object_type: Some("agent-grant".into()),
            object_id: Some(input.grant_id.clone()),
            detail_json: encode(&IssuedDetail {
                agent_id: &input.agent_id,
                grant_digest: &digest,
            })?,
            created_at: now,
        };
        let row = GrantRow {
            grant_id: input.grant_id,
            grant_digest: digest,
            principal_id: input.principal_id,
            agent_id: input.agent_id,
            audience: input.audience,
            allowed_actions_json: encode(&input.allowed_actions)?,
            resource_prefixes_json: encode(&input.resource_prefixes)?,
            expires_at: input.expires_at_epoch_seconds,
            max_risk_class: input.max_risk_class,
            step_up_at_or_above: input.step_up_at_or_above,
            remaining_effects: input.remaining_effects,
            active: 1,
            revision: 1,
        };
        row.checked().map_err(|_| EffectError::Invalid)?;
        Ok(Self { row, audit })
    }
    pub fn snapshot(&self) -> GrantSnapshot {
        self.row.snapshot().expect("prepared checked row")
    }
    pub fn audit_id(&self) -> &str {
        &self.audit.event_id
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GrantObservation {
    // Exact immutable issuance/audit evidence with current mutable projection.
    // Does NOT establish original quota after later mutations.
    Exact(Box<GrantSnapshot>),
    Unobserved,
    Mismatch,
}
