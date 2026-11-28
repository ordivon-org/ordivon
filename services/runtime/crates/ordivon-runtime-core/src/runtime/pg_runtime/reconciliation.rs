//! PostgreSQL Attempt readback, native reconciliation, and Job result projection.
use super::*;

// Composition only: one PgRuntime, one PG store and one systemd Runner.
// Each private child owns a distinct logical responsibility; no alternate
// authorizer, registry or source-file placement contract is introduced.
mod attempt_readback;
mod dispatch_accepted;
mod native_stop_evidence;
mod native_terminal;
mod observation;
mod pid_witness;
mod pre_dispatch_cancel;
mod projection;
mod scan;
#[cfg(test)]
mod tests;

use attempt_readback::{
    needs_recovery_observation, RECONCILIATION_STAGE_SQL, RELEASE_CURRENT_ATTEMPT_STATE_SQL,
};
#[cfg(test)]
use attempt_readback::{
    require_recovery_current_attempt, READBACK_VERIFIED_ATTEMPT_SQL, RECOVERY_CURRENT_ATTEMPT_SQL,
};
use observation::{
    active_log_window, output_projection_relative_path, runner_result_still_absent,
    verified_terminal_log_window,
};
#[cfg(test)]
use pid_witness::namespace_pid_from_host_status;
use pid_witness::{native_running_witness, observed_namespace_pid, NativePidReadback};
#[cfg(test)]
use scan::{
    advance_reconciliation_cursor, latest_reconciliation_key, next_reconciliation_cursor,
    scan_reconciliation_page,
};

use crate::PgJobSnapshot;
