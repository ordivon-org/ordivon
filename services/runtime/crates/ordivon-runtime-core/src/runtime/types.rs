use schemars::JsonSchema;

use crate::universal::{
    ENVIRONMENT_VARIABLE_NAME_PATTERN, WORKSPACE_ID_MAX_LENGTH, WORKSPACE_ID_MIN_LENGTH,
    WORKSPACE_ID_PATTERN,
};

use super::{RuntimeError, RuntimeErrorCode, RuntimeResult};

pub const RUNTIME_SCHEMA_VERSION: u32 = 1;

fn default_schema_version() -> u32 {
    RUNTIME_SCHEMA_VERSION
}

pub(crate) const MAX_RUNTIME_LIST_LIMIT: u32 = 100;
pub const MAX_TASK_WAIT_MS: u64 = 30_000;
pub const MAX_TASK_TAIL_BYTES: u64 = 64 * 1024;
pub(crate) const MAX_ARTIFACT_READ_BYTES: u64 = 1024 * 1024;

pub const LOGICAL_ID_MIN_LENGTH: usize = 1;
pub const LOGICAL_ID_MAX_LENGTH: usize = 256;
pub const LOGICAL_ID_PATTERN: &str = r"^[^\u0000-\u0020\u007f-\u00a0\u1680\u2000-\u200a\u2028-\u2029\u202f\u205f\u3000](?:[^\u0000-\u001f\u007f-\u009f]*[^\u0000-\u0020\u007f-\u00a0\u1680\u2000-\u200a\u2028-\u2029\u202f\u205f\u3000])?$";
pub const CLIENT_REQUEST_ID_MIN_LENGTH: usize = LOGICAL_ID_MIN_LENGTH;
pub const CLIENT_REQUEST_ID_MAX_LENGTH: usize = LOGICAL_ID_MAX_LENGTH;
pub const CLIENT_REQUEST_ID_PATTERN: &str = LOGICAL_ID_PATTERN;

/// Lexical SHA-256 syntax only. Mixed-case ASCII hexadecimal is accepted;
/// consumers requiring canonical lowercase or byte identity check it separately.
pub(crate) fn is_sha256_digest(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value[7..].bytes().all(|byte| byte.is_ascii_hexdigit())
}

pub(crate) fn validate_logical_id(value: &str, field: &str) -> RuntimeResult<()> {
    let scalar_length = value.chars().count();
    if !(LOGICAL_ID_MIN_LENGTH..=LOGICAL_ID_MAX_LENGTH).contains(&scalar_length)
        || value != value.trim()
        || value.chars().any(char::is_control)
    {
        return Err(RuntimeError::invalid(
            format!(
                "{field} must contain 1..={LOGICAL_ID_MAX_LENGTH} Unicode characters, be trimmed, and be control-free"
            ),
            field,
        ));
    }
    Ok(())
}

pub(crate) fn validate_client_request_id(value: &str, field: &str) -> RuntimeResult<()> {
    validate_logical_id(value, field)
}

#[allow(dead_code)]
#[derive(JsonSchema)]
#[schemars(extend("pattern" = ENVIRONMENT_VARIABLE_NAME_PATTERN))]
struct EnvironmentVariableNameSchema(String);

pub(crate) const REQUEST_IDENTITY_PREFIX: &str = "runtime-request-v1:";
pub(crate) const PROPOSAL_IDENTITY_PREFIX: &str = "runtime-request-v2:";
pub(crate) const INPUT_BOUND_IDENTITY_PREFIX: &str = "runtime-request-input-v1:";
pub(crate) const INPUT_BOUND_PROPOSAL_IDENTITY_PREFIX: &str = "runtime-request-input-v2:";
pub(crate) const CREDENTIAL_BOUND_PROPOSAL_IDENTITY_PREFIX: &str = "runtime-request-credential-v1:";
pub(crate) const RUNTIME_RELEASE_IDENTITY_PREFIX: &str = "runtime-release-v1:";

mod job_attempt_states;
pub use job_attempt_states::{
    AttemptState, AttemptTerminationIntent, JobDesiredState, JobResolution, ReservationState,
};

mod execution_target;
pub use execution_target::{
    ExecutionProfile, ExecutionTarget, WindowsAuthority, WindowsExecutionContextRequest,
    WindowsExecutionIdentity, WindowsPayloadPrivilege,
};
pub(crate) use execution_target::{WindowsExecutionContext, WindowsTokenClass};

mod resource_bindings;
pub use resource_bindings::{
    CredentialAuthority, CredentialBindingRequest, ExecutionProviderContract,
    ExecutionProviderSnapshot, ForeignReference, HostDependencyBinding, InputAuthority,
    InputBindingRequest,
};
pub(crate) use resource_bindings::{EffectiveInputBinding, InputAccessMode};

mod runtime_release;
pub(crate) use runtime_release::RuntimeReleaseEffectBinding;
pub use runtime_release::{
    RuntimeReleaseAdmission, RuntimeReleaseContract, RuntimeReleaseDisposition,
    RuntimeReleaseGetRequest, RuntimeReleaseProjection, RuntimeReleaseRequest,
};

mod node_capability;
pub use node_capability::{
    RuntimeCapabilities, RuntimeExecutionTargetCapability, RuntimeNodeIdentity, RuntimeNodePlatform,
};

mod execution_plan;
pub use execution_plan::{ExecutionBudget, ExecutionStepProposal};
pub(crate) use execution_plan::{
    RuntimeExecutionPlan, RuntimeExecutionStep, SubmitRequest, UniversalExecutionStep,
};

mod release_identity;
pub use release_identity::{runtime_release_effect_id, runtime_release_request_identity_digest};

mod request_identity;
#[cfg(test)]
pub(crate) use request_identity::operation_request_identity_digest;
pub(crate) use request_identity::{
    credential_bound_proposal_request_identity_digest,
    input_bound_proposal_request_identity_digest, legacy_request_identity_digest_from_proposal,
    operation_request_identity_digest_from_plan, proposal_request_identity_digest,
};

mod record_projection;
pub(crate) use record_projection::{
    AdmissionOutcome, AttemptRecord, CreatedAdmission, JobProjection, ReservationRecord,
    RuntimeArtifactRecord, RuntimeJobRecord,
};
pub use record_projection::{
    ArtifactDescriptor, ArtifactRegistration, RuntimeDeliveryDisposition, TerminalCommit,
};

mod job_workspace_query;
pub(crate) use job_workspace_query::RunnerIdentity;
#[cfg(any(test, feature = "operator-tools"))]
pub use job_workspace_query::RuntimeInvariantViolation;
pub use job_workspace_query::{
    RuntimeJobListCursor, RuntimeJobListRequest, RuntimeJobListResult, RuntimeJobSummary,
    RuntimeWorkspaceGetRequest, RuntimeWorkspaceIssue, RuntimeWorkspaceIssueStage,
    RuntimeWorkspaceListCursor, RuntimeWorkspaceListRequest, RuntimeWorkspaceListResult,
    RuntimeWorkspaceSummary,
};

mod job_execution_proposal;
pub use job_execution_proposal::{ExecutionProposal, JobRunProposal};
pub(crate) use job_execution_proposal::{JobRunRequest, UniversalExecutionRequest};

mod job_observation;
pub use job_observation::{
    EffectiveExecutionLimits, EffectiveStepTimeout, JobCancelRequest, JobObservation,
    JobObserveRequest, JobObserveWaitUntil,
};

mod artifact_access;
pub use artifact_access::{
    ArtifactContentMetadata, ArtifactContentReadResult, ArtifactContentRequest,
    ArtifactReadRequest, ArtifactReadResult,
};

pub(crate) fn default_task_wait_ms() -> u64 {
    30_000
}

pub(crate) fn default_task_tail_bytes() -> u64 {
    4096
}

fn is_false(value: &bool) -> bool {
    !*value
}

#[cfg(test)]
mod workspace_issue_schema_contract_tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn pg_workspace_projection_issue_is_an_admitted_public_wire_stage() {
        // PgRuntime::list_workspaces emits this stage for a page-local get
        // failure. Do not turn a recoverable individual issue into a
        // schema-invalid whole-list success response.
        let wire = json!({
            "workspaceId": "ws-projection-error",
            "stage": "projection",
            "code": "WORKSPACE_STATE_MISMATCH",
            "message": "Workspace projection could not be proven",
            "retryable": true
        });
        let typed: RuntimeWorkspaceIssue =
            serde_json::from_value(wire.clone()).expect("PG stage must round-trip");
        assert_eq!(serde_json::to_value(typed).unwrap(), wire);
        let published = serde_json::to_value(schemars::schema_for!(RuntimeWorkspaceIssueStage))
            .expect("public stage schema");
        assert!(
            published["enum"]
                .as_array()
                .unwrap()
                .contains(&json!("projection")),
            "MCP tools/list must permit the actual PG list issue stage"
        );
    }
}

#[cfg(test)]
mod digest_syntax_tests {
    use super::is_sha256_digest;

    #[test]
    fn sha256_syntax_preserves_legacy_hex_contract() {
        let original = format!("sha256:{}", "0".repeat(64));
        let legacy = |value: &str| {
            value.strip_prefix("sha256:").is_some_and(|hex| {
                hex.len() == 64 && hex.bytes().all(|byte| byte.is_ascii_hexdigit())
            })
        };
        for offset in 0..original.len() {
            for byte in 0..=127u8 {
                let mut candidate = original.clone().into_bytes();
                candidate[offset] = byte;
                let candidate = String::from_utf8(candidate).unwrap();
                assert_eq!(is_sha256_digest(&candidate), legacy(&candidate));
            }
        }
        for length in 0..=128 {
            let candidate = format!("sha256:{}", "a".repeat(length));
            assert_eq!(is_sha256_digest(&candidate), length == 64);
        }
        assert!(is_sha256_digest(&format!("sha256:{}", "aF".repeat(32))));
        assert!(!is_sha256_digest(&format!("sha256:{}", "é".repeat(32))));
        assert!(!is_sha256_digest(&format!("SHA256:{}", "a".repeat(64))));
    }
}
