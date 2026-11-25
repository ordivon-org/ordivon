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
fn canonical(s: &str) -> bool {
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

#[derive(Debug, thiserror::Error)]
pub enum EffectError {
    #[error("effect input unrepresentable")]
    Invalid,
    #[error("effect lock unavailable")]
    Busy,
    #[error("effect actor mismatch")]
    ActorMismatch,
    #[error("effect identifier already bound")]
    Conflict,
    #[error("selected Grant missing or changed")]
    GrantChanged,
    #[error("effect commit binding rejected")]
    Binding,
    #[error("approval or mutable authority rejected")]
    Fence,
    #[error("note not publishable")]
    NotPublishable,
    #[error("grant belongs to another Principal")]
    GrantPrincipalMismatch,
    #[error("pending approval binding conflict")]
    PendingConflict,
    #[error("pending approval is absent or expired")]
    PendingNotFound,
    #[error("verified approval binding changed")]
    ApprovalBinding,
    #[error("approval or effect is terminal")]
    ApprovalClosed,
    #[error("authority commit outcome unknown in {operation} for {coordinate}: {source}")]
    AuthorityCommitUnknown {
        operation: &'static str,
        coordinate: String,
        #[source]
        source: tokio_postgres::Error,
    },
    #[error("stored projection invalid")]
    Corrupt,
    #[error("expected one write: {0}")]
    Write(&'static str),
    #[error("transaction readback mismatch: {0}")]
    Mismatch(&'static str),
    #[error("pool: {0}")]
    Pool(#[source] crate::NoteError),
    #[error("native database error in {phase}: {source}")]
    Database {
        phase: &'static str,
        #[source]
        source: tokio_postgres::Error,
    },
    #[error("rollback outcome unknown: {cause}; {rollback}")]
    RollbackUnknown {
        cause: Box<EffectError>,
        rollback: tokio_postgres::Error,
    },
    #[error("commit outcome unknown for {effect_id}: {source}")]
    CommitUnknown {
        effect_id: String,
        #[source]
        source: tokio_postgres::Error,
    },
}
impl EffectError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::Invalid => "effect-unrepresentable",
            Self::Busy => "effect-busy",
            Self::ActorMismatch => "effect-actor-mismatch",
            Self::Conflict => "effect-conflict",
            Self::GrantChanged => "agent-grant-changed",
            Self::Binding => "agent-effect-not-authorized",
            Self::Fence => "effect-fence-rejected",
            Self::NotPublishable => "canary-note-not-publishable",
            Self::GrantPrincipalMismatch => "agent-grant-principal-mismatch",
            Self::PendingConflict => "pending-effect-conflict",
            Self::PendingNotFound => "pending-effect-not-found",
            Self::ApprovalBinding => "effect-approval-binding-invalid",
            Self::ApprovalClosed => "effect-approval-closed",
            Self::AuthorityCommitUnknown { .. } => "authority-commit-unknown",
            Self::Corrupt => "effect-corrupt",
            Self::Write(_) => "effect-write-not-applied",
            Self::Mismatch(_) => "effect-postcondition-mismatch",
            Self::Pool(_) => "effect-pool-unavailable",
            Self::Database { .. } => "effect-database-error",
            Self::RollbackUnknown { .. } => "effect-rollback-unknown",
            Self::CommitUnknown { .. } => "effect-commit-unknown",
        }
    }
}
pub(crate) fn db(phase: &'static str, source: tokio_postgres::Error) -> EffectError {
    if source.code().is_some_and(|c| c.code() == "55P03") {
        EffectError::Busy
    } else {
        EffectError::Database { phase, source }
    }
}
pub(crate) fn one(n: u64, subject: &'static str) -> Result<(), EffectError> {
    if n == 1 {
        Ok(())
    } else {
        Err(EffectError::Write(subject))
    }
}
