use super::{
    operation_request_identity_digest_from_plan, RuntimeError, RuntimeErrorCode,
    RuntimeExecutionPlan, RuntimeJobRecord, RuntimeResult, SubmitRequest,
    CREDENTIAL_BOUND_PROPOSAL_IDENTITY_PREFIX, INPUT_BOUND_IDENTITY_PREFIX,
    INPUT_BOUND_PROPOSAL_IDENTITY_PREFIX, PROPOSAL_IDENTITY_PREFIX, REQUEST_IDENTITY_PREFIX,
    RUNTIME_RELEASE_IDENTITY_PREFIX,
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

#[cfg(test)]
mod tests {
    use super::*;

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
