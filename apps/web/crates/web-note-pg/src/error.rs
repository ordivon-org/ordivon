//! Storage operation outcomes; native errors remain attributable to their phase.
#[derive(Debug, thiserror::Error)]
pub enum NoteError {
    #[error("input is not representable by the PostgreSQL/JavaScript text and integer contract")]
    Unrepresentable,
    #[error("pool checkout failed: {0}")]
    Pool(#[source] deadpool_postgres::PoolError),
    #[error("invalid pool configuration")]
    PoolConfig,
    #[error("note-write-not-applied")]
    WriteNotApplied,
    #[error("note-business-mismatch")]
    BusinessMismatch,
    #[error("note-audit-mismatch")]
    AuditMismatch,
    #[error("database failure before commit in {phase}: {source}")]
    Database {
        phase: &'static str,
        #[source]
        source: tokio_postgres::Error,
    },
    #[error("rollback confirmation unavailable: {rollback}; original failure: {cause}")]
    RollbackUnknown {
        cause: Box<NoteError>,
        rollback: tokio_postgres::Error,
    },
    #[error("commit acknowledgement unavailable for note {note_id}: {source}")]
    CommitUnknown {
        note_id: String,
        #[source]
        source: tokio_postgres::Error,
    },
}

impl NoteError {
    pub fn code(&self) -> &'static str {
        match self {
            Self::Unrepresentable => "note-unrepresentable",
            Self::Pool(_) => "note-pool-unavailable",
            Self::PoolConfig => "note-pool-config-invalid",
            Self::WriteNotApplied => "note-write-not-applied",
            Self::BusinessMismatch => "note-business-mismatch",
            Self::AuditMismatch => "note-audit-mismatch",
            Self::Database { .. } => "note-database-error",
            Self::RollbackUnknown { .. } => "note-rollback-unknown",
            Self::CommitUnknown { .. } => "note-commit-unknown",
        }
    }
}
