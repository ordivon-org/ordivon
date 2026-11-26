//! Shared owner persistence error vocabulary. Existing wire code strings are retained.
#[derive(Debug, thiserror::Error)]
pub enum OwnerError {
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
    #[error("grant not found")]
    GrantNotFound,
    #[error("grant unavailable")]
    GrantUnavailable,
    #[error("multiple matching grants")]
    GrantAmbiguous,
    #[error("invalid grant scope")]
    InvalidGrantScope,
    #[error("principal identity conflict")]
    PrincipalConflict,
    #[error("principal not found")]
    PrincipalNotFound,
    #[error("credential not found or revoked")]
    CredentialNotFound,
    #[error("credential verified pre-state changed")]
    CredentialConflict,
    #[error("session missing, expired or revoked")]
    SessionInvalid,
    #[error("session clock coordinate stale")]
    SessionStale,
    #[error("entropy unavailable")]
    Entropy,
    #[error("challenge missing, expired, consumed or wrong binding")]
    ChallengeInvalid,
    #[error("challenge payload integrity failure")]
    ChallengeCorrupt,
    #[error("invalid DPoP proof identity or expiry")]
    DpopInvalid,
    #[error("DPoP proof already consumed")]
    DpopReplayed,
    #[error("login challenge already finalized")]
    LoginCompleted,
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
        cause: Box<OwnerError>,
        rollback: tokio_postgres::Error,
    },
    #[error("commit outcome unknown for {effect_id}: {source}")]
    CommitUnknown {
        effect_id: String,
        #[source]
        source: tokio_postgres::Error,
    },
}
impl OwnerError {
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
            Self::GrantNotFound => "agent-grant-not-found",
            Self::GrantUnavailable => "agent-grant-unavailable",
            Self::GrantAmbiguous => "agent-grant-ambiguous",
            Self::InvalidGrantScope => "invalid-agent-grant-scope",
            Self::PrincipalConflict => "principal-identity-conflict",
            Self::PrincipalNotFound => "principal-not-found",
            Self::CredentialNotFound => "credential-not-found",
            Self::CredentialConflict => "credential-counter-conflict",
            Self::SessionInvalid => "session-invalid",
            Self::SessionStale => "session-clock-stale",
            Self::Entropy => "session-entropy-unavailable",
            Self::ChallengeInvalid => "challenge-invalid",
            Self::ChallengeCorrupt => "challenge-corrupt",
            Self::DpopInvalid => "dpop-proof-invalid",
            Self::DpopReplayed => "dpop-proof-replayed",
            Self::LoginCompleted => "login-already-completed",
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
pub(crate) fn db(phase: &'static str, source: tokio_postgres::Error) -> OwnerError {
    if source.code().is_some_and(|c| c.code() == "55P03") {
        OwnerError::Busy
    } else {
        OwnerError::Database { phase, source }
    }
}
pub(crate) fn one(n: u64, subject: &'static str) -> Result<(), OwnerError> {
    if n == 1 {
        Ok(())
    } else {
        Err(OwnerError::Write(subject))
    }
}
