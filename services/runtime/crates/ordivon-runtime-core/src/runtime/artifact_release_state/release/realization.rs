use super::super::super::job_attempt_state::JobIdentityContract;
use super::super::super::{
    ExecutionProfile, ExecutionProviderContract, ExecutionTarget, RuntimeError,
    RuntimeReleaseContract, RuntimeReleaseEffectBinding, RuntimeResult, SubmitRequest,
    WindowsAuthority, WindowsTokenClass, RUNTIME_RELEASE_IDENTITY_PREFIX,
};
use super::super::validation::{is_lower_hex, validate_sha256};
use std::path::Path;

impl super::ReleaseStateContract {
    pub(crate) fn validate_committed_binding(
        release: &RuntimeReleaseEffectBinding,
        request: &SubmitRequest,
    ) -> RuntimeResult<()> {
        if release.contract != RuntimeReleaseContract::RuntimeReleaseV1 {
            return Err(RuntimeError::invalid(
                "unsupported Runtime Release contract",
                "runtimeReleaseEffect.contract",
            ));
        }
        if !is_lower_hex(&release.effect_id, 64) {
            return Err(RuntimeError::invalid(
                "Runtime Release effectId must be 64 lowercase hexadecimal characters",
                "runtimeReleaseEffect.effectId",
            ));
        }
        if !release
            .request_digest
            .starts_with(RUNTIME_RELEASE_IDENTITY_PREFIX)
        {
            return Err(RuntimeError::invalid(
                "Runtime Release request digest has the wrong contract prefix",
                "runtimeReleaseEffect.requestDigest",
            ));
        }
        JobIdentityContract::validate_request_identity_digest(&release.request_digest)?;
        if request.request_identity_digest.as_deref() != Some(release.request_digest.as_str()) {
            return Err(RuntimeError::invalid(
                "Runtime Release side truth must match the committed request identity",
                "runtimeReleaseEffect.requestDigest",
            ));
        }
        if release.workspace_id != request.plan.workspace_id {
            return Err(RuntimeError::invalid(
                "Runtime Release workspace does not match the execution plan",
                "runtimeReleaseEffect.workspaceId",
            ));
        }
        if !is_lower_hex(&release.commit, 40) {
            return Err(RuntimeError::invalid(
                "Runtime Release commit must be exactly 40 lowercase hexadecimal characters",
                "runtimeReleaseEffect.commit",
            ));
        }
        validate_sha256(
            &release.candidate_manifest_digest,
            "runtimeReleaseEffect.candidateManifestDigest",
        )?;
        if !Path::new(&release.receipt_path).is_absolute()
            || release.receipt_path.as_bytes().contains(&0)
        {
            return Err(RuntimeError::invalid(
                "Runtime Release receipt path must be absolute and NUL-free",
                "runtimeReleaseEffect.receiptPath",
            ));
        }
        if request.plan.execution_profile != ExecutionProfile::TrustedLocal {
            return Err(RuntimeError::invalid(
                "Runtime Release v1 requires trusted_local execution",
                "runtimeReleaseEffect.contract",
            ));
        }
        match request.plan.execution_target {
            ExecutionTarget::LocalLinux => {
                if request.plan.windows_authority != WindowsAuthority::Limited
                    || request.plan.windows_execution_context.is_some()
                {
                    return Err(RuntimeError::invalid(
                        "local Linux Runtime Release cannot carry Windows elevated authority",
                        "plan.windowsAuthority",
                    ));
                }
                if !matches!(
                    request
                        .execution_provider
                        .as_ref()
                        .map(|provider| provider.contract),
                    Some(ExecutionProviderContract::LocalLinuxRunnerV1)
                ) {
                    return Err(RuntimeError::invalid(
                        "local Linux Runtime Release requires a committed local Linux Runner",
                        "executionProvider",
                    ));
                }
            }
            ExecutionTarget::WindowsNative => {
                if request.plan.windows_authority != WindowsAuthority::Elevated {
                    return Err(RuntimeError::invalid(
                        "native Windows Runtime Release requires elevated authority",
                        "plan.windowsAuthority",
                    ));
                }
                if !matches!(
                    request
                        .execution_provider
                        .as_ref()
                        .map(|provider| provider.contract),
                    Some(ExecutionProviderContract::WindowsNativeLauncherV1)
                ) {
                    return Err(RuntimeError::invalid(
                        "native Windows Runtime Release requires a committed Windows launcher",
                        "executionProvider",
                    ));
                }
                let context = request
                    .plan
                    .windows_execution_context
                    .as_ref()
                    .ok_or_else(|| {
                        RuntimeError::invalid(
                        "native Windows Runtime Release requires frozen elevated execution context",
                        "plan.windowsExecutionContext",
                    )
                    })?;
                if context.token_class != WindowsTokenClass::Elevated
                    || context.environment_source
                        != "windows_privileged_broker_profile_allowlist_v1"
                {
                    return Err(RuntimeError::invalid(
                        "native Windows Runtime Release requires privileged broker execution context",
                        "plan.windowsExecutionContext",
                    ));
                }
                let broker_digest =
                    context.privileged_broker_digest.as_deref().ok_or_else(|| {
                        RuntimeError::invalid(
                        "native Windows Runtime Release requires a frozen privileged broker digest",
                        "plan.windowsExecutionContext.privilegedBrokerDigest",
                    )
                    })?;
                validate_sha256(
                    broker_digest,
                    "plan.windowsExecutionContext.privilegedBrokerDigest",
                )?;
            }
        }
        Ok(())
    }
}
