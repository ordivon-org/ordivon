use crate::domain::representable;
use serde::Serialize;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GrantFence {
    pub grant_id: String,
    pub grant_digest: String,
    pub principal_id: String,
    pub agent_id: String,
    pub revision: i64,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EffectRequest {
    pub effect_id: String,
    pub effect_digest: String,
    pub agent_id: String,
    pub audience: String,
    pub action: String,
    pub resource: String,
    pub effect_type: String,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EffectOperation {
    // Caller owns these identities before await, including audit identity.
    Create {
        note_id: uuid::Uuid,
        content: String,
    },
    Publish {
        note_id: String,
    },
}
impl EffectOperation {
    pub(crate) fn binds(&self, r: &EffectRequest) -> bool {
        match self {
            Self::Create { .. } => {
                r.action == "canary.note.create"
                    && r.resource == "/canary/notes"
                    && r.effect_type == "website.canary.note.create"
            }
            Self::Publish { note_id } => {
                r.action == "canary.note.publish"
                    && r.resource == format!("/canary/notes/{note_id}")
                    && r.effect_type == "website.canary.note.publish"
            }
        }
    }
    pub(crate) fn valid(&self) -> bool {
        match self {
            Self::Create { content, .. } => !content.contains('\0'),
            Self::Publish { note_id } => !note_id.is_empty() && !note_id.contains('\0'),
        }
    }
}
pub(crate) fn valid_input(
    r: &EffectRequest,
    g: &GrantFence,
    op: &EffectOperation,
    now: i64,
) -> bool {
    [
        r.effect_id.as_str(),
        &r.effect_digest,
        &r.agent_id,
        &r.audience,
        &r.action,
        &r.resource,
        &r.effect_type,
        &g.grant_id,
        &g.grant_digest,
        &g.principal_id,
        &g.agent_id,
    ]
    .iter()
    .all(|v| !v.is_empty() && !v.contains('\0'))
        && representable("", "", now)
        && representable("", "", g.revision)
        && g.revision >= 1
        && op.valid()
}
pub(super) fn canonical(s: &str) -> bool {
    s.starts_with('/')
        && !s.contains("//")
        && !s
            .chars()
            .any(|c| matches!(c, '\\' | '%' | '?' | '#' | '\u{7f}') || c <= '\u{1f}')
        && !s.split('/').any(|v| v == "." || v == "..")
}
pub(crate) fn scope_contains(prefix: &str, resource: &str) -> bool {
    canonical(prefix)
        && canonical(resource)
        && (resource == prefix
            || resource
                .strip_prefix(prefix)
                .is_some_and(|r| prefix.ends_with('/') || r.starts_with('/')))
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct EffectOutcome {
    pub receipt: super::EffectReceipt,
    pub replayed: bool,
}

pub(crate) use crate::owner_error::{db, one};
