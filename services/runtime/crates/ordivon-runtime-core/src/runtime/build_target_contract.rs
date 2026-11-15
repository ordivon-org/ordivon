//! Existing trusted-local Cargo target presentation and compatibility selection.
//! Shared by legacy Engine, native Linux Provider and PG reconciliation.
use super::RuntimeExecutionPlan;

/// Per-Job systemd bind mount: stable compiler-visible path, Workspace-private bytes.
/// Unlike /proc/self/fd/198, ordinary subprocesses may close inherited FDs.
pub(crate) const TRUSTED_BUILD_TARGET_PRESENTATION: &str = "/run/ordivon/cargo-target";
/// Old committed PG plans keep the original FD implementation; never rewrite their env.
pub(crate) const LEGACY_TRUSTED_BUILD_TARGET_PRESENTATION: &str = "/proc/self/fd/198";

fn plan_uses_cargo_target(plan: &RuntimeExecutionPlan, target: &str) -> bool {
    plan.env.get("CARGO_TARGET_DIR").map(String::as_str) == Some(target)
        || plan
            .steps
            .iter()
            .any(|step| step.env.get("CARGO_TARGET_DIR").map(String::as_str) == Some(target))
}

pub(crate) fn requires_private_cargo_build_target(plan: &RuntimeExecutionPlan) -> bool {
    plan.execution_target == crate::runtime::ExecutionTarget::LocalLinux
        && plan.execution_profile == crate::runtime::ExecutionProfile::TrustedLocal
        && (plan_uses_cargo_target(plan, TRUSTED_BUILD_TARGET_PRESENTATION)
            || plan_uses_cargo_target(plan, LEGACY_TRUSTED_BUILD_TARGET_PRESENTATION))
}

pub(crate) fn requires_native_cargo_target_mount(plan: &RuntimeExecutionPlan) -> bool {
    plan.execution_target == crate::runtime::ExecutionTarget::LocalLinux
        && plan.execution_profile == crate::runtime::ExecutionProfile::TrustedLocal
        && plan_uses_cargo_target(plan, TRUSTED_BUILD_TARGET_PRESENTATION)
}
