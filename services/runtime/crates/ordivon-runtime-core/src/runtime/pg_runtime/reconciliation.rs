//! PostgreSQL Attempt readback, native reconciliation, and Job result projection.
use super::*;

/// NSpid lists kernel PIDs in nested namespaces, from the namespace of the
/// host procfs mount through the innermost namespace. A private systemd
/// PID namespace changes the Runner's getpid() without changing the kernel
/// process starttime. Reject malformed, duplicated, or mismatched host
/// identities rather than trusting a supplied namespace PID alone.
// Composition only: one PgRuntime, one PG store and one systemd Runner.
// Each private child owns a distinct logical responsibility; no alternate
// authorizer, registry or source-file placement contract is introduced.
mod attempt_readback;
mod native_effects;
mod observation;
mod pid_witness;
mod pre_dispatch_cancel;
mod projection;
mod scan;
#[cfg(test)]
mod tests;

use attempt_readback::*;
use observation::*;
use pid_witness::*;
use scan::*;

/// Preserve original SQLSTATE rather than translating PG failures into generic I/O.
fn pg_read_error(error: postgres::Error) -> RuntimeError {
    pg(PgAdmissionError::Database(error))
}
use crate::PgJobSnapshot;
