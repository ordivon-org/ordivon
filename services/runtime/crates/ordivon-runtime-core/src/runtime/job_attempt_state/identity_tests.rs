//! Job replay and effect identity require exact semantic bindings and replay compatibility.
use super::super::{RuntimeErrorCode, REQUEST_IDENTITY_PREFIX};
use super::{JobIdentityContract, OperationIdentityBindings};
use crate::universal::sha256_bytes;

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
            format!("runtime-operation-v5\0{request}\0{plan}\0{provider}\0{release}").as_bytes()
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
