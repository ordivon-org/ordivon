//! Native Supervisor contract facade. The recovery models cannot widen original OS authority.
//! Identity contracts -> Linux or Windows recovery -> existing Engine and Runtime consumers.
mod contract;
mod linux_recovery;
mod windows_owner;

pub(crate) use contract::{
    SupervisorIdentity, SupervisorObservation, SupervisorRecoveryDisposition, SupervisorUnitState,
    TerminationIntent,
};
pub(crate) use linux_recovery::classify_supervisor_recovery;
pub(crate) use windows_owner::{
    classify_windows_launcher_recovery, validate_attempt_supervisor_owner, AttemptSupervisorOwner,
    WindowsLauncherOwnerObservation,
};

#[cfg(test)]
use linux_recovery::classify_terminal_state;
#[cfg(test)]
mod tests;
