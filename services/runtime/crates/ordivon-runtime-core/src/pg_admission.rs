//! Native PostgreSQL admission facade. Transaction boundaries are independently
//! implemented per business effect below; no SQLite or parallel authority.
use postgres::{Client, IsolationLevel, NoTls};
use sha2::{Digest, Sha256};
use uuid::Uuid;

mod admission;
mod cancel_contract;
mod cancellation;
#[cfg(test)]
mod contract_tests;
#[path = "pg_dispatch.rs"]
mod dispatch;
mod input_contract;
#[path = "pg_issuer_guard.rs"]
mod issuer;
// Native Win32 observation/journal WRITER is Windows-only. The *same-PG*
// terminal read validator is cross-platform and must remain available even
// to the Linux PG CAS code when asked to validate original Win32 Attempt.
#[path = "pg_admission_native_windows_drain.rs"]
mod native_windows_drain;
#[cfg(all(test, feature = "postgres-registry-admission"))]
mod live_pg_tests;
mod readback;
mod release;
pub use readback::PgAdmissionObservation;
mod retry;
mod terminal;
mod terminal_contract;
mod writer_authority;
use cancel_contract::cancel_detail;
pub use cancel_contract::{PgCancelIntent, PgCancelObservation, PgCancelOutcome};
pub(crate) use dispatch::PgRunnerBound;
pub use dispatch::{PgBundleReady, PgDispatchIssued};
use input_contract::unambiguous_json_object;
pub use input_contract::PgAdmissionInput;
#[cfg(any(windows, test))]
pub(crate) use native_windows_drain::{PgNativeWindowsDrainInput, PgNativeWindowsDrainOutcome};
use terminal_contract::terminal_transition;
pub(crate) use terminal_contract::{pg_artifact_manifest_digest, valid_pg_artifacts};
pub use terminal_contract::{PgArtifactRegistration, PgTerminalNoArtifacts, PgTerminalOutcome};
pub use writer_authority::pg_writer_epoch_digest;
pub(crate) use writer_authority::require_pg_writer_epoch;
use writer_authority::{exact_schema, qualified_schema_constraints};

#[derive(Debug)]
pub enum PgAdmissionError {
    InvalidInput,
    Unqualified,
    Capacity,
    IdempotencyConflict,
    PendingEffect,
    /// Workspace physical identity changed after a Job was planned, but before
    /// its PG admission acquired the global effect/admission lock.
    WorkspaceStale,
    IssuerNotCurrent,
    Blocked,
    UnknownCommit,
    Database(postgres::Error),
}
impl From<postgres::Error> for PgAdmissionError {
    fn from(error: postgres::Error) -> Self {
        Self::Database(error)
    }
}

#[derive(Debug, PartialEq, Eq)]
pub enum PgAdmissionOutcome {
    Created(String),
    Existing(String),
}

pub struct PgAdmissionStore {
    pub(crate) client: Client,
}

// The PG readback and Runtime Job projection share only the bounded retry
// mechanism. Exactly-once effect admission is not a replayable retry closure.
pub(crate) use retry::retry_aborted_transaction;
