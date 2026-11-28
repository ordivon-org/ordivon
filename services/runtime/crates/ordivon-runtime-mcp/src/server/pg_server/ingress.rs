//! Original ingress classification and exact-key recovery for Runtime PG agents.
//! Not an extra authorization registry: upstream route identity and PG Core own effects.
use super::{
    ExecutionProfile, JobObservation, JobRunProposal, McpError, RuntimeError, Tool, json,
};

// A private in-process ingress classification, NOT a caller-supplied
// permission. Only pg_main's separately authenticated Harness route may
// select DedicatedFinalizer. The ordinary tool transport must never infer
// release authority from an ordinary bearer or the absence of a finalizer.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) enum ClaimReleaseIngress {
    Ordinary,
    // Original same-PG Harness Issuer remains able to admit Job requests.
    DedicatedFinalizer,
    // Separate original Run resource ownership from source-current Job issuance.
    // The minimal port needs no foreign Harness tables in Runtime PostgreSQL.
    DedicatedClaimOnly,
}

impl ClaimReleaseIngress {
    pub(super) const fn may_release(self) -> bool {
        // The original Run's complete independently received output bytes AND
        // every issued native OS effect remain unverified. An authenticated
        // route bearer or clientRequestId is not finalizer authority.
        // Keep the release capability unavailable until a real independently
        // witnessed Domain/OS finalizer is implemented, not a caller boolean.
        match self {
            Self::Ordinary | Self::DedicatedFinalizer | Self::DedicatedClaimOnly => false,
        }
    }

    pub(super) const fn claim_only(self) -> bool {
        matches!(self, Self::DedicatedClaimOnly)
    }
}

pub(super) const CLAIM_ONLY_TOOL_NAMES: &[&str] = &[
    "workspace.get",
    "workspace.claim.reserve",
    "workspace.claim.get",
];

pub(super) fn claim_only_route_guard(ingress: ClaimReleaseIngress, name: &str) -> Result<(), McpError> {
    if ingress.claim_only() && !CLAIM_ONLY_TOOL_NAMES.contains(&name) {
        return Err(McpError::invalid_params(
            "Claim Finalizer ingress does not grant Job execution or Runtime administration",
            None,
        ));
    }
    Ok(())
}

/// A caller-supplied key is a recovery coordinate, never release authority.
/// Keep the real raw-dispatch check testable without constructing a PG client.
pub(super) fn claim_release_route_guard(_route_bearer_authenticated: bool, name: &str) -> Result<(), McpError> {
    // Deliberately refuse EVEN authenticated finalizer bearers. No current
    // ingress carries independently verified original Domain bytes and
    // all-issued OS NoFutureSpawn; a boolean is never a sufficient receipt.
    if name == "workspace.claim.release" {
        return Err(McpError::invalid_params(
            "workspace.claim.release unavailable: independently received complete Run output and all-issued native OS NoFutureSpawn proof are not verified",
            None,
        ));
    }
    Ok(())
}

/// Advertise only profiles accepted for NEW effects by the authenticated
/// transport, rather than exposing a caller-selected privileged alternative.
pub(super) fn project_ingress_execution_profiles(
    description: &mut serde_json::Value,
    required: Option<ExecutionProfile>,
) {
    let Some(required) = required else { return; };
    if let Some(targets) = description.get_mut("targets").and_then(serde_json::Value::as_array_mut) {
        for target in targets {
            if target.get("target").and_then(serde_json::Value::as_str) == Some("local_linux") {
                target["executionProfiles"] = json!([required.as_str()]);
            }
        }
    }
}

/// Restrict advertised new effects for an authenticated contained-only Agent.
/// A manually authored raw tools/call is independently checked by Core after
/// committed replay; tools/list filtering is never the authorization gate.
pub(super) fn restrict_new_effect_catalog(
    tools: &mut Vec<Tool>,
    required: Option<ExecutionProfile>,
) {
    if required == Some(ExecutionProfile::ContainedLocal) {
        tools.retain(|tool| tool.name.as_ref() != "release.apply");
        for tool in tools {
            if matches!(tool.name.as_ref(), "workspace.exec" | "workspace.execPlan") {
                tool.description = Some(
                    "Authenticated contained_local-only Job admission. Caller-selected trusted_local is DENIED for new effects; exact previously committed Job recovery remains allowed.".into()
                );
            }
        }
    }
}

/// A direct MCP caller may omit executionProfile because the original
/// public Tool schema defaults to trusted_local. Historical committed Jobs
/// must be observed through that ORIGINAL identity first, even after the
/// authenticated ordinary ingress is restricted to contained_local.
///
/// Only a qualified native precommit profile denial or exact PG-key conflict
/// permits one alternate contained admission. The PG Store rechecks the
/// principal and full immutable request digest; the MCP layer is not a new
/// permission authority or retry ledger.
pub(super) fn run_pg_direct_implicit_profile(
    runtime: &ordivon_runtime_core::PgRuntime,
    mut bound: JobRunProposal,
    required: Option<ExecutionProfile>,
    caller_omitted_profile: bool,
) -> Result<JobObservation, RuntimeError> {
    let initial = runtime.run_with_execution_profile_policy(&bound, required);
    let can_reenter_contained = caller_omitted_profile
        && required == Some(ExecutionProfile::ContainedLocal)
        && bound.execution.execution_profile == ExecutionProfile::TrustedLocal
        && initial.as_ref().err().is_some_and(|error| {
            !error.retryable
                && error.operation_id.is_none()
                && match error.code {
                    ordivon_runtime_core::RuntimeErrorCode::AuthorizationDenied => {
                        error.field.as_deref() == Some("execution.executionProfile")
                    }
                    ordivon_runtime_core::RuntimeErrorCode::IdempotencyConflict => {
                        error.field.is_none()
                    }
                    _ => false,
                }
        });
    if can_reenter_contained {
        bound.execution.execution_profile = ExecutionProfile::ContainedLocal;
        runtime.run_with_execution_profile_policy(&bound, required)
    } else {
        initial
    }
}

pub(super) fn profile_omitted_from_raw_tool_arguments(arguments: &serde_json::Value) -> bool {
    arguments.get("execution")
        .and_then(serde_json::Value::as_object)
        .is_some_and(|execution| !execution.contains_key("executionProfile"))
}
