//! Private physical-dispatch seam for Runtime Core.
//!
//! Engine owns Job/Attempt state, bundle/input preparation and dispatch intent.
//! Platform implementations own the actual OS process boundary.  This module is
//! deliberately narrow: it centralizes those physical crossings without inventing
//! provider selection, policy, workflow, retry, or generic Effect semantics.

use std::process::Output;

use super::platform::{
    nonempty_property, process_identity, read_trimmed, release_terminal_unit, supervisor_identity,
    systemctl_show, systemd_run, unit_is_active, windows_systemd_run, SystemdRunSpec,
    WindowsSystemdRunSpec,
};
use super::supervisor::{
    SupervisorIdentity, SupervisorObservation, SupervisorUnitState, WindowsLauncherOwnerObservation,
};
use super::windows::{
    observe_windows_launcher_owner, spawn_windows_native, WindowsExecutionConfig,
    WindowsNativeRunSpec,
};
use super::{AttemptRecord, RuntimeResult};

pub(crate) fn dispatch_linux(spec: &SystemdRunSpec<'_>) -> RuntimeResult<Output> {
    systemd_run(spec)
}

pub(crate) fn dispatch_windows_via_wsl(spec: &WindowsSystemdRunSpec<'_>) -> RuntimeResult<Output> {
    windows_systemd_run(spec)
}

pub(crate) fn dispatch_windows_native(spec: &WindowsNativeRunSpec<'_>) -> RuntimeResult<u32> {
    spawn_windows_native(spec)
}

pub(crate) fn observe_windows_process_owner(
    config: &WindowsExecutionConfig,
    launcher_process_id: u32,
) -> RuntimeResult<WindowsLauncherOwnerObservation> {
    observe_windows_launcher_owner(config, launcher_process_id)
}

pub(crate) fn observe_linux_process_owner(
    attempt: &AttemptRecord,
) -> RuntimeResult<(SupervisorIdentity, SupervisorObservation)> {
    let expected = supervisor_identity(attempt)?;
    let properties = systemctl_show(&attempt.unit_name)?;
    let current_boot_id = read_trimmed("/proc/sys/kernel/random/boot_id")?;
    let unit_state = if unit_is_active(&properties) {
        SupervisorUnitState::Running
    } else if properties
        .get("LoadState")
        .is_some_and(|state| state == "not-found")
    {
        SupervisorUnitState::NotFound
    } else {
        SupervisorUnitState::Terminal
    };
    let recorded_pid_alive = attempt.main_pid.is_some_and(|pid| {
        process_identity(pid)
            .as_deref()
            .zip(attempt.process_start_identity.as_deref())
            .is_some_and(|(observed, expected)| observed == expected)
    });
    let observation = SupervisorObservation {
        boot_id: current_boot_id,
        unit_state,
        invocation_id: nonempty_property(&properties, "InvocationID"),
        control_group: nonempty_property(&properties, "ControlGroup"),
        main_pid: properties
            .get("MainPID")
            .and_then(|value| value.parse::<u32>().ok())
            .filter(|pid| *pid > 0),
        main_process_start_identity: properties
            .get("MainPID")
            .and_then(|value| value.parse::<u32>().ok())
            .and_then(process_identity),
        recorded_pid_alive,
        recorded_pid_start_identity: attempt.main_pid.and_then(process_identity),
        result: nonempty_property(&properties, "Result"),
        exec_main_code: properties
            .get("ExecMainCode")
            .and_then(|value| value.parse().ok()),
        exec_main_status: properties
            .get("ExecMainStatus")
            .and_then(|value| value.parse().ok()),
    };
    Ok((expected, observation))
}

pub(crate) fn release_linux_process_owner(unit_name: &str) {
    release_terminal_unit(unit_name);
}
