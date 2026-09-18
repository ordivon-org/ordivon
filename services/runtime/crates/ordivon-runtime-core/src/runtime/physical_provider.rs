//! Private physical-dispatch seam for Runtime Core.
//!
//! Engine owns Job/Attempt state, bundle/input preparation and dispatch intent.
//! Platform implementations own the actual OS process boundary.  This module is
//! deliberately narrow: it centralizes those physical crossings without inventing
//! provider selection, policy, workflow, retry, or generic Effect semantics.

use std::process::Output;

use super::platform::{systemd_run, windows_systemd_run, SystemdRunSpec, WindowsSystemdRunSpec};
use super::windows::{spawn_windows_native, WindowsNativeRunSpec};
use super::RuntimeResult;

pub(crate) fn dispatch_linux(spec: &SystemdRunSpec<'_>) -> RuntimeResult<Output> {
    systemd_run(spec)
}

pub(crate) fn dispatch_windows_via_wsl(spec: &WindowsSystemdRunSpec<'_>) -> RuntimeResult<Output> {
    windows_systemd_run(spec)
}

pub(crate) fn dispatch_windows_native(spec: &WindowsNativeRunSpec<'_>) -> RuntimeResult<u32> {
    spawn_windows_native(spec)
}
