//! Ingress profile and issuer-bound intent decisions.
use super::*;

// A foreign reference is caller-authored metadata, never execution authority.
// Without a configured same-PG issuer verifier it cannot affect the environment.
// With a verifier, preserve exact source intent for the PG transactional guard.
pub(super) fn preserve_qualified_issuer_environment(
    issuer_schema: Option<&str>,
    references: &[ForeignReference],
) -> bool {
    issuer_schema.is_some()
        && references.iter().any(|reference| {
            reference.namespace == "ordivon.harness" && reference.reference_type == "dispatch_fence"
        })
}

pub(super) fn authorize_new_execution_profile(
    requested: ExecutionProfile,
    required: Option<ExecutionProfile>,
) -> RuntimeResult<()> {
    if required.is_some_and(|expected| expected != requested) {
        return Err(RuntimeError::new(
            RuntimeErrorCode::AuthorizationDenied,
            "authenticated ingress does not authorize this executionProfile",
            Some("execution.executionProfile"),
            false,
        ));
    }
    Ok(())
}

#[cfg(test)]
mod profile_admission_guard_tests {
    use super::*;

    #[test]
    fn profile_authority_is_fixed_by_ingress_not_proposal() {
        assert!(authorize_new_execution_profile(
            ExecutionProfile::ContainedLocal,
            Some(ExecutionProfile::ContainedLocal)
        )
        .is_ok());
        let denied = authorize_new_execution_profile(
            ExecutionProfile::TrustedLocal,
            Some(ExecutionProfile::ContainedLocal),
        )
        .unwrap_err();
        assert_eq!(denied.code, RuntimeErrorCode::AuthorizationDenied);
        assert!(
            authorize_new_execution_profile(ExecutionProfile::TrustedLocal, None).is_ok(),
            "existing trusted local operator path stays available"
        );
    }
}
