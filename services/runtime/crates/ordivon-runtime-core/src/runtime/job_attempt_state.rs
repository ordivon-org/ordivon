use super::{
    operation_request_identity_digest_from_plan, AttemptState, AttemptTerminationIntent,
    JobResolution, RuntimeError, RuntimeErrorCode, RuntimeExecutionPlan, RuntimeJobRecord,
    RuntimeResult, SubmitRequest, CREDENTIAL_BOUND_PROPOSAL_IDENTITY_PREFIX,
    INPUT_BOUND_IDENTITY_PREFIX, INPUT_BOUND_PROPOSAL_IDENTITY_PREFIX, PROPOSAL_IDENTITY_PREFIX,
    REQUEST_IDENTITY_PREFIX, RUNTIME_RELEASE_IDENTITY_PREFIX,
};
use crate::universal::sha256_bytes;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum OperationIdentityBindings<'a> {
    Legacy,
    Provider {
        provider_digest: &'a str,
    },
    ProviderWithHostDependencies {
        provider_digest: &'a str,
        host_dependencies_digest: &'a str,
    },
    ProviderWithRuntimeRelease {
        provider_digest: &'a str,
        runtime_release_digest: &'a str,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct JobIdentityContract {
    pub request_digest: String,
    pub operation_digest: String,
}

impl JobIdentityContract {
    pub(crate) fn from_submit(
        request: &SubmitRequest,
        plan_digest: &str,
        execution_provider_digest: Option<&str>,
        host_dependencies_digest: Option<&str>,
        runtime_release_digest: Option<&str>,
    ) -> RuntimeResult<Self> {
        let request_digest =
            if let Some(request_digest) = request.request_identity_digest.as_deref() {
                Self::validate_request_identity_digest(request_digest)?;
                request_digest.to_string()
            } else {
                let request_json = serde_json::to_vec(request).map_err(|error| {
                    RuntimeError::new(
                        RuntimeErrorCode::InvalidRequest,
                        format!("cannot serialize submit request: {error}"),
                        None,
                        false,
                    )
                })?;
                sha256_bytes(&request_json)
            };

        let bindings = match (
            execution_provider_digest,
            host_dependencies_digest,
            runtime_release_digest,
        ) {
            (Some(provider_digest), Some(host_dependencies_digest), None) => {
                OperationIdentityBindings::ProviderWithHostDependencies {
                    provider_digest,
                    host_dependencies_digest,
                }
            }
            (Some(provider_digest), None, Some(runtime_release_digest)) => {
                OperationIdentityBindings::ProviderWithRuntimeRelease {
                    provider_digest,
                    runtime_release_digest,
                }
            }
            (Some(provider_digest), None, None) => {
                OperationIdentityBindings::Provider { provider_digest }
            }
            (None, None, None) => OperationIdentityBindings::Legacy,
            (Some(_), Some(_), Some(_)) => {
                return Err(RuntimeError::invalid(
                    "Runtime Release effect and Host Dependencies cannot share one Job",
                    "hostDependencies",
                ));
            }
            (None, Some(_), _) => {
                return Err(RuntimeError::invalid(
                    "Host Dependencies require a committed execution provider",
                    "executionProvider",
                ));
            }
            (None, None, Some(_)) => {
                return Err(RuntimeError::invalid(
                    "Runtime Release effect requires a committed execution provider",
                    "executionProvider",
                ));
            }
        };

        Ok(Self {
            operation_digest: Self::operation_digest(&request_digest, plan_digest, bindings),
            request_digest,
        })
    }

    pub(crate) fn operation_digest(
        request_digest: &str,
        plan_digest: &str,
        bindings: OperationIdentityBindings<'_>,
    ) -> String {
        match bindings {
            OperationIdentityBindings::Legacy => sha256_bytes(
                format!("runtime-operation-v3\0{request_digest}\0{plan_digest}").as_bytes(),
            ),
            OperationIdentityBindings::Provider { provider_digest } => sha256_bytes(
                format!(
                    "runtime-operation-v4\0{request_digest}\0{plan_digest}\0{provider_digest}"
                )
                .as_bytes(),
            ),
            OperationIdentityBindings::ProviderWithRuntimeRelease {
                provider_digest,
                runtime_release_digest,
            } => sha256_bytes(
                format!(
                    "runtime-operation-v5\0{request_digest}\0{plan_digest}\0{provider_digest}\0{runtime_release_digest}"
                )
                .as_bytes(),
            ),
            OperationIdentityBindings::ProviderWithHostDependencies {
                provider_digest,
                host_dependencies_digest,
            } => sha256_bytes(
                format!(
                    "runtime-operation-v6\0{request_digest}\0{plan_digest}\0{provider_digest}\0{host_dependencies_digest}"
                )
                .as_bytes(),
            ),
        }
    }

    pub(crate) fn stored_request_identity_digest(job: &RuntimeJobRecord) -> RuntimeResult<String> {
        if Self::is_versioned_request_identity(&job.request_digest) {
            Self::validate_request_identity_digest(&job.request_digest)?;
            return Ok(job.request_digest.clone());
        }
        let plan: RuntimeExecutionPlan =
            serde_json::from_str(&job.execution_plan_json).map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::RegistryCorrupt,
                    format!("stored execution plan is invalid: {error}"),
                    Some("executionPlan"),
                    false,
                )
            })?;
        operation_request_identity_digest_from_plan(&plan)
    }

    pub(crate) fn exact_replay_matches(
        existing: &RuntimeJobRecord,
        requested_request_identity: Option<&str>,
        requested_operation_digest: &str,
    ) -> RuntimeResult<bool> {
        if let Some(request_identity) = requested_request_identity {
            return Ok(Self::stored_request_identity_digest(existing)? == request_identity);
        }
        Ok(existing.operation_digest == requested_operation_digest)
    }

    pub(crate) fn compatible_request_identity_matches(
        stored_identity: &str,
        requested_identity: &str,
        compatible_requested_identity: Option<&str>,
    ) -> bool {
        stored_identity == requested_identity
            || compatible_requested_identity == Some(stored_identity)
    }

    pub(crate) fn validate_request_identity_digest(value: &str) -> RuntimeResult<()> {
        let digest = Self::strip_request_identity_prefix(value).ok_or_else(|| {
            RuntimeError::invalid(
                "unsupported request identity digest",
                "requestIdentityDigest",
            )
        })?;
        let valid = digest
            .strip_prefix("sha256:")
            .is_some_and(|hex| hex.len() == 64 && hex.bytes().all(|byte| byte.is_ascii_hexdigit()));
        if !valid {
            return Err(RuntimeError::invalid(
                "requestIdentityDigest must be a SHA-256 digest",
                "requestIdentityDigest",
            ));
        }
        Ok(())
    }

    pub(crate) fn idempotency_conflict() -> RuntimeError {
        RuntimeError::new(
            RuntimeErrorCode::IdempotencyConflict,
            "clientRequestId is already bound to a different operation request",
            Some("clientRequestId"),
            false,
        )
    }

    fn is_versioned_request_identity(value: &str) -> bool {
        Self::strip_request_identity_prefix(value).is_some()
    }

    fn strip_request_identity_prefix(value: &str) -> Option<&str> {
        value
            .strip_prefix(REQUEST_IDENTITY_PREFIX)
            .or_else(|| value.strip_prefix(PROPOSAL_IDENTITY_PREFIX))
            .or_else(|| value.strip_prefix(INPUT_BOUND_IDENTITY_PREFIX))
            .or_else(|| value.strip_prefix(INPUT_BOUND_PROPOSAL_IDENTITY_PREFIX))
            .or_else(|| value.strip_prefix(CREDENTIAL_BOUND_PROPOSAL_IDENTITY_PREFIX))
            .or_else(|| value.strip_prefix(RUNTIME_RELEASE_IDENTITY_PREFIX))
    }
}

pub(crate) struct AttemptLifecycleContract;

impl AttemptLifecycleContract {
    pub(crate) const INITIAL_ATTEMPT_NUMBER: u32 = 1;

    pub(crate) fn initial_state() -> AttemptState {
        AttemptState::Accepted
    }

    pub(crate) fn initial_termination_intent() -> AttemptTerminationIntent {
        AttemptTerminationIntent::Natural
    }

    pub(crate) fn is_terminal(state: AttemptState) -> bool {
        matches!(
            state,
            AttemptState::Succeeded
                | AttemptState::Failed
                | AttemptState::TimedOut
                | AttemptState::Cancelled
                | AttemptState::Lost
                | AttemptState::Orphaned
        )
    }

    pub(crate) fn can_transition(state: AttemptState, next: AttemptState) -> bool {
        match state {
            AttemptState::Accepted => matches!(
                next,
                AttemptState::Starting
                    | AttemptState::Cancelled
                    | AttemptState::Failed
                    | AttemptState::Lost
                    | AttemptState::Orphaned
            ),
            AttemptState::Starting => matches!(
                next,
                AttemptState::Running
                    | AttemptState::Recovering
                    | AttemptState::Succeeded
                    | AttemptState::Failed
                    | AttemptState::TimedOut
                    | AttemptState::Cancelled
                    | AttemptState::Lost
                    | AttemptState::Orphaned
            ),
            AttemptState::Running => matches!(
                next,
                AttemptState::Stopping
                    | AttemptState::Recovering
                    | AttemptState::Succeeded
                    | AttemptState::Failed
                    | AttemptState::TimedOut
                    | AttemptState::Cancelled
                    | AttemptState::Lost
                    | AttemptState::Orphaned
            ),
            AttemptState::Stopping => matches!(
                next,
                AttemptState::Recovering
                    | AttemptState::Succeeded
                    | AttemptState::Cancelled
                    | AttemptState::Failed
                    | AttemptState::TimedOut
                    | AttemptState::Lost
                    | AttemptState::Orphaned
            ),
            AttemptState::Recovering => matches!(
                next,
                AttemptState::Starting
                    | AttemptState::Running
                    | AttemptState::Stopping
                    | AttemptState::Succeeded
                    | AttemptState::Failed
                    | AttemptState::TimedOut
                    | AttemptState::Cancelled
                    | AttemptState::Lost
                    | AttemptState::Orphaned
            ),
            AttemptState::Succeeded
            | AttemptState::Failed
            | AttemptState::TimedOut
            | AttemptState::Cancelled
            | AttemptState::Lost
            | AttemptState::Orphaned => false,
        }
    }

    pub(crate) fn deadline_request_is_replay(
        state: AttemptState,
        termination_intent: AttemptTerminationIntent,
    ) -> bool {
        Self::is_terminal(state) || termination_intent != AttemptTerminationIntent::Natural
    }

    pub(crate) fn deadline_request_is_admissible(state: AttemptState) -> bool {
        matches!(
            state,
            AttemptState::Starting
                | AttemptState::Running
                | AttemptState::Recovering
                | AttemptState::Stopping
        )
    }

    pub(crate) fn cancel_target_state(state: AttemptState) -> Option<AttemptState> {
        match state {
            AttemptState::Accepted => Some(AttemptState::Cancelled),
            AttemptState::Starting | AttemptState::Running | AttemptState::Recovering => {
                Some(AttemptState::Stopping)
            }
            AttemptState::Stopping => Some(AttemptState::Stopping),
            AttemptState::Succeeded
            | AttemptState::Failed
            | AttemptState::TimedOut
            | AttemptState::Cancelled
            | AttemptState::Lost
            | AttemptState::Orphaned => None,
        }
    }

    pub(crate) fn runner_identity_bound_state(state: AttemptState) -> Option<AttemptState> {
        match state {
            AttemptState::Starting | AttemptState::Recovering => Some(AttemptState::Running),
            _ => None,
        }
    }

    pub(crate) fn supervisor_owner_bound_state(state: AttemptState) -> Option<AttemptState> {
        match state {
            AttemptState::Starting | AttemptState::Recovering => Some(AttemptState::Running),
            AttemptState::Stopping => Some(AttemptState::Stopping),
            _ => None,
        }
    }

    pub(crate) fn physical_owner_replay_matches(
        state: AttemptState,
        existing_owner_digest: &str,
        requested_owner_digest: &str,
        stored_start_digest: Option<&str>,
        requested_start_digest: &str,
    ) -> bool {
        existing_owner_digest == requested_owner_digest
            && matches!(state, AttemptState::Running | AttemptState::Stopping)
            && stored_start_digest == Some(requested_start_digest)
    }

    pub(crate) fn resolution(state: AttemptState) -> Option<JobResolution> {
        match state {
            AttemptState::Succeeded => Some(JobResolution::Succeeded),
            AttemptState::Failed => Some(JobResolution::Failed),
            AttemptState::TimedOut => Some(JobResolution::TimedOut),
            AttemptState::Cancelled => Some(JobResolution::Cancelled),
            AttemptState::Lost => Some(JobResolution::Lost),
            AttemptState::Orphaned => Some(JobResolution::Orphaned),
            AttemptState::Accepted
            | AttemptState::Starting
            | AttemptState::Running
            | AttemptState::Stopping
            | AttemptState::Recovering => None,
        }
    }

    pub(crate) fn require_terminal_resolution(state: AttemptState) -> RuntimeResult<JobResolution> {
        Self::resolution(state)
            .ok_or_else(|| RuntimeError::invalid("Attempt state is not terminal", "state"))
    }

    pub(crate) fn terminal_evidence_complete(
        state: AttemptState,
        result_digest_present: bool,
        finished_at_present: bool,
        job_resolution: Option<JobResolution>,
        current_attempt_present: bool,
    ) -> bool {
        Self::is_terminal(state)
            && result_digest_present
            && finished_at_present
            && job_resolution == Self::resolution(state)
            && !current_attempt_present
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn initial_attempt_generation_and_default_intent_are_stable() {
        assert_eq!(AttemptLifecycleContract::INITIAL_ATTEMPT_NUMBER, 1);
        assert_eq!(
            AttemptLifecycleContract::initial_state(),
            AttemptState::Accepted
        );
        assert_eq!(
            AttemptLifecycleContract::initial_termination_intent(),
            AttemptTerminationIntent::Natural
        );
    }

    #[test]
    fn state_transition_matrix_preserves_terminal_absorption_and_recovery_paths() {
        assert!(AttemptLifecycleContract::can_transition(
            AttemptState::Accepted,
            AttemptState::Starting
        ));
        assert!(AttemptLifecycleContract::can_transition(
            AttemptState::Running,
            AttemptState::Stopping
        ));
        assert!(AttemptLifecycleContract::can_transition(
            AttemptState::Recovering,
            AttemptState::Running
        ));
        assert!(!AttemptLifecycleContract::can_transition(
            AttemptState::Accepted,
            AttemptState::Running
        ));
        for terminal in [
            AttemptState::Succeeded,
            AttemptState::Failed,
            AttemptState::TimedOut,
            AttemptState::Cancelled,
            AttemptState::Lost,
            AttemptState::Orphaned,
        ] {
            assert!(AttemptLifecycleContract::is_terminal(terminal));
            assert!(!AttemptLifecycleContract::can_transition(
                terminal,
                AttemptState::Running
            ));
        }
    }

    #[test]
    fn termination_intent_and_control_targets_preserve_first_committed_control_intent() {
        assert!(AttemptLifecycleContract::deadline_request_is_replay(
            AttemptState::Running,
            AttemptTerminationIntent::StopRequested
        ));
        assert!(AttemptLifecycleContract::deadline_request_is_replay(
            AttemptState::Running,
            AttemptTerminationIntent::DeadlineExceeded
        ));
        assert!(!AttemptLifecycleContract::deadline_request_is_replay(
            AttemptState::Running,
            AttemptTerminationIntent::Natural
        ));
        assert!(AttemptLifecycleContract::deadline_request_is_admissible(
            AttemptState::Stopping
        ));
        assert!(!AttemptLifecycleContract::deadline_request_is_admissible(
            AttemptState::Accepted
        ));
        assert_eq!(
            AttemptLifecycleContract::cancel_target_state(AttemptState::Accepted),
            Some(AttemptState::Cancelled)
        );
        assert_eq!(
            AttemptLifecycleContract::cancel_target_state(AttemptState::Running),
            Some(AttemptState::Stopping)
        );
        assert_eq!(
            AttemptLifecycleContract::cancel_target_state(AttemptState::Stopping),
            Some(AttemptState::Stopping)
        );
    }

    #[test]
    fn physical_owner_binding_preserves_stopping_and_replay_identity() {
        assert_eq!(
            AttemptLifecycleContract::runner_identity_bound_state(AttemptState::Starting),
            Some(AttemptState::Running)
        );
        assert_eq!(
            AttemptLifecycleContract::runner_identity_bound_state(AttemptState::Stopping),
            None
        );
        assert_eq!(
            AttemptLifecycleContract::supervisor_owner_bound_state(AttemptState::Stopping),
            Some(AttemptState::Stopping)
        );
        assert!(AttemptLifecycleContract::physical_owner_replay_matches(
            AttemptState::Running,
            "sha256:owner",
            "sha256:owner",
            Some("sha256:start"),
            "sha256:start",
        ));
        assert!(!AttemptLifecycleContract::physical_owner_replay_matches(
            AttemptState::Running,
            "sha256:owner-a",
            "sha256:owner-b",
            Some("sha256:start"),
            "sha256:start",
        ));
    }

    #[test]
    fn terminal_resolution_is_total_only_for_terminal_attempt_states() {
        let mappings = [
            (AttemptState::Succeeded, JobResolution::Succeeded),
            (AttemptState::Failed, JobResolution::Failed),
            (AttemptState::TimedOut, JobResolution::TimedOut),
            (AttemptState::Cancelled, JobResolution::Cancelled),
            (AttemptState::Lost, JobResolution::Lost),
            (AttemptState::Orphaned, JobResolution::Orphaned),
        ];
        for (state, resolution) in mappings {
            assert_eq!(
                AttemptLifecycleContract::resolution(state),
                Some(resolution)
            );
            assert_eq!(
                AttemptLifecycleContract::require_terminal_resolution(state).unwrap(),
                resolution
            );
        }
        for state in [
            AttemptState::Accepted,
            AttemptState::Starting,
            AttemptState::Running,
            AttemptState::Stopping,
            AttemptState::Recovering,
        ] {
            assert_eq!(AttemptLifecycleContract::resolution(state), None);
            let error = AttemptLifecycleContract::require_terminal_resolution(state).unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
            assert_eq!(error.field.as_deref(), Some("state"));
        }
    }

    #[test]
    fn terminal_evidence_requires_result_finish_matching_resolution_and_no_current_attempt() {
        assert!(AttemptLifecycleContract::terminal_evidence_complete(
            AttemptState::Succeeded,
            true,
            true,
            Some(JobResolution::Succeeded),
            false,
        ));
        assert!(AttemptLifecycleContract::terminal_evidence_complete(
            AttemptState::Orphaned,
            true,
            true,
            Some(JobResolution::Orphaned),
            false,
        ));

        for complete in [
            AttemptLifecycleContract::terminal_evidence_complete(
                AttemptState::Running,
                true,
                true,
                None,
                false,
            ),
            AttemptLifecycleContract::terminal_evidence_complete(
                AttemptState::Succeeded,
                false,
                true,
                Some(JobResolution::Succeeded),
                false,
            ),
            AttemptLifecycleContract::terminal_evidence_complete(
                AttemptState::Succeeded,
                true,
                false,
                Some(JobResolution::Succeeded),
                false,
            ),
            AttemptLifecycleContract::terminal_evidence_complete(
                AttemptState::Succeeded,
                true,
                true,
                Some(JobResolution::Failed),
                false,
            ),
            AttemptLifecycleContract::terminal_evidence_complete(
                AttemptState::Succeeded,
                true,
                true,
                Some(JobResolution::Succeeded),
                true,
            ),
        ] {
            assert!(!complete);
        }
    }

    #[test]
    fn operation_identity_versions_are_stable_and_side_truth_specific() {
        let request = "sha256:request";
        let plan = "sha256:plan";
        let provider = "sha256:provider";
        let host = "sha256:host";
        let release = "sha256:release";

        assert_eq!(
            JobIdentityContract::operation_digest(request, plan, OperationIdentityBindings::Legacy),
            sha256_bytes(format!("runtime-operation-v3\0{request}\0{plan}").as_bytes())
        );
        assert_eq!(
            JobIdentityContract::operation_digest(
                request,
                plan,
                OperationIdentityBindings::Provider {
                    provider_digest: provider,
                },
            ),
            sha256_bytes(format!("runtime-operation-v4\0{request}\0{plan}\0{provider}").as_bytes())
        );
        assert_eq!(
            JobIdentityContract::operation_digest(
                request,
                plan,
                OperationIdentityBindings::ProviderWithRuntimeRelease {
                    provider_digest: provider,
                    runtime_release_digest: release,
                },
            ),
            sha256_bytes(
                format!("runtime-operation-v5\0{request}\0{plan}\0{provider}\0{release}")
                    .as_bytes()
            )
        );
        assert_eq!(
            JobIdentityContract::operation_digest(
                request,
                plan,
                OperationIdentityBindings::ProviderWithHostDependencies {
                    provider_digest: provider,
                    host_dependencies_digest: host,
                },
            ),
            sha256_bytes(
                format!("runtime-operation-v6\0{request}\0{plan}\0{provider}\0{host}").as_bytes()
            )
        );
    }

    #[test]
    fn compatible_request_identity_requires_exact_requested_or_declared_legacy_identity() {
        assert!(JobIdentityContract::compatible_request_identity_matches(
            "runtime-request-v1:sha256:old",
            "runtime-request-v1:sha256:old",
            None,
        ));
        assert!(JobIdentityContract::compatible_request_identity_matches(
            "runtime-request-v1:sha256:old",
            "runtime-request-v2:sha256:new",
            Some("runtime-request-v1:sha256:old"),
        ));
        assert!(!JobIdentityContract::compatible_request_identity_matches(
            "runtime-request-v1:sha256:old",
            "runtime-request-v2:sha256:new",
            None,
        ));
    }

    #[test]
    fn request_identity_validation_preserves_historical_hex_acceptance() {
        let lowercase = format!("{REQUEST_IDENTITY_PREFIX}sha256:{}", "a".repeat(64));
        let uppercase = format!("{REQUEST_IDENTITY_PREFIX}sha256:{}", "A".repeat(64));
        assert!(JobIdentityContract::validate_request_identity_digest(&lowercase).is_ok());
        assert!(JobIdentityContract::validate_request_identity_digest(&uppercase).is_ok());

        let error = JobIdentityContract::validate_request_identity_digest(
            "runtime-request-unknown:sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
        .unwrap_err();
        assert_eq!(error.code, RuntimeErrorCode::InvalidRequest);
        assert_eq!(error.field.as_deref(), Some("requestIdentityDigest"));
    }
}
