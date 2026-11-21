//! Native supervisor recovery across Linux systemd and Windows launcher owners.
//! Identity, OS-specific classification and behavior tests have distinct ownership.
mod linux;
mod types;
mod windows;

pub(crate) use linux::classify_supervisor_recovery;
#[cfg(test)]
use linux::classify_terminal_state;
pub(crate) use types::{
    AttemptSupervisorOwner, SupervisorIdentity, SupervisorObservation,
    SupervisorRecoveryDisposition, SupervisorUnitState, TerminationIntent,
    WindowsLauncherOwnerObservation,
};
pub(crate) use windows::{classify_windows_launcher_recovery, validate_attempt_supervisor_owner};
#[cfg(test)]
mod tests;
