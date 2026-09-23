#[cfg(feature = "operator-tools")]
mod doctor;
mod engine;
mod error;
mod evidence;
mod inspection;
mod job_attempt_state;
mod platform;
mod registry;
#[cfg(feature = "operator-tools")]
mod repair;
mod supervisor;
mod types;
mod windows;
mod windows_broker;
mod workspace_state;

#[cfg(feature = "operator-tools")]
pub use doctor::{
    inspect_runtime, RuntimeDoctorAttemptState, RuntimeDoctorCapacityHolder, RuntimeDoctorCase,
    RuntimeDoctorConfig, RuntimeDoctorJobState, RuntimeDoctorProposal, RuntimeDoctorReport,
    RuntimeDoctorReservationState, RuntimeDoctorSummary, RUNTIME_DOCTOR_SCHEMA_VERSION,
};
pub use engine::{
    ReconciliationFailure, ReconciliationReport, Runtime, RuntimeConfig,
    WorkspaceAdmissionHeadroomConfig,
};
pub use error::{RuntimeCapacity, RuntimeError, RuntimeErrorCode, RuntimeResult};
pub const RUNTIME_MAX_MIGRATION_VERSION: i64 = registry::MAX_MIGRATION_VERSION;
pub use inspection::{
    inspect_job, RuntimeInspectionArtifactSummary, RuntimeInspectionAttempt,
    RuntimeInspectionCondition, RuntimeInspectionConfig, RuntimeInspectionEpisodes,
    RuntimeInspectionEvent, RuntimeInspectionJob, RuntimeJobInspection,
    DEFAULT_INSPECTION_EVENT_LIMIT, MAX_INSPECTION_EVENT_LIMIT,
};
#[cfg(feature = "operator-tools")]
pub use inspection::{
    inspect_registry, inspect_registry_activity, inspect_registry_archive,
    inspect_registry_markers, inspect_registry_status, inspect_registry_workspace_activity,
    inspect_runtime_release_effect, inspect_runtime_release_effect_owner, inspect_workspace,
    summarize_experience, RuntimeExperienceArtifactSummary, RuntimeExperienceCancellationSummary,
    RuntimeExperienceDispatchSummary, RuntimeExperienceDurationSummary,
    RuntimeExperienceJobSummary, RuntimeExperienceMechanicalLatencySummary,
    RuntimeExperienceRecoverySummary, RuntimeExperienceSummary, RuntimeOperatorActiveWorkspace,
    RuntimeOperatorArchiveClassification, RuntimeOperatorArchiveClosure,
    RuntimeOperatorArchiveInspection, RuntimeOperatorArchiveSample,
    RuntimeOperatorAttemptSupervisorOwner, RuntimeOperatorDashboardJob,
    RuntimeOperatorDashboardJobs, RuntimeOperatorRegistryActivityInspection,
    RuntimeOperatorRegistryInspection, RuntimeOperatorRegistryMarkersInspection,
    RuntimeOperatorRegistryStatusInspection, RuntimeOperatorReleaseEffectInspection,
    RuntimeOperatorWorkspaceActivity, RuntimeOperatorWorkspaceActivityInspection,
    RuntimeOperatorWorkspaceLastActivity, RuntimeOperatorWorkspaceMarker,
    RuntimeWorkspaceInspection, RuntimeWorkspaceInspectionConfig, RuntimeWorkspaceInspectionJob,
    DEFAULT_ARCHIVE_SAMPLE_LIMIT, DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT, MAX_ARCHIVE_SAMPLE_LIMIT,
    MAX_WORKSPACE_INSPECTION_JOB_LIMIT,
};
pub(crate) use registry::Registry;
pub use registry::RegistryConfig;
#[cfg(test)]
pub(crate) use registry::{
    RUNTIME_CONDITION_RETIREMENT_MIGRATION_CHECKSUM, RUNTIME_MIGRATION_CHECKSUM,
    RUNTIME_ORPHAN_RECLAIM_MIGRATION_CHECKSUM, RUNTIME_ORPHAN_RECOVERY_MIGRATION_CHECKSUM,
    RUNTIME_TERMINAL_REPAIR_MIGRATION_CHECKSUM,
    RUNTIME_WORKSPACE_PATCH_RETIREMENT_MIGRATION_CHECKSUM,
};
#[cfg(feature = "operator-tools")]
pub use repair::{
    apply_runtime_repair, cancel_stale_recovery_required_attempt, RuntimeRepairAction,
    RuntimeRepairActionKind, RuntimeRepairConfig, RuntimeRepairReport, RuntimeRepairRequest,
    RuntimeStaleCancelReport, RuntimeStaleCancelRequest, RUNTIME_REPAIR_SCHEMA_VERSION,
};
#[cfg(test)]
pub(crate) use types::operation_request_identity_digest;
pub(crate) use types::{
    credential_bound_proposal_request_identity_digest,
    input_bound_proposal_request_identity_digest, legacy_request_identity_digest_from_proposal,
    operation_request_identity_digest_from_plan, proposal_request_identity_digest,
    validate_client_request_id, validate_logical_id, AdmissionOutcome, AttemptRecord,
    CreatedAdmission, EffectiveInputBinding, InputAccessMode, JobProjection, JobRunRequest,
    ReservationRecord, RunnerIdentity, RuntimeArtifactRecord, RuntimeExecutionPlan,
    RuntimeExecutionStep, RuntimeJobRecord, RuntimeReleaseEffectBinding, SubmitRequest,
    UniversalExecutionRequest, UniversalExecutionStep, WindowsExecutionContext, WindowsTokenClass,
    CREDENTIAL_BOUND_PROPOSAL_IDENTITY_PREFIX, INPUT_BOUND_IDENTITY_PREFIX,
    INPUT_BOUND_PROPOSAL_IDENTITY_PREFIX, MAX_ARTIFACT_READ_BYTES, MAX_RUNTIME_LIST_LIMIT,
    PROPOSAL_IDENTITY_PREFIX, REQUEST_IDENTITY_PREFIX, RUNTIME_RELEASE_IDENTITY_PREFIX,
};
pub use types::{
    runtime_release_effect_id, runtime_release_request_identity_digest, ArtifactDescriptor,
    ArtifactReadRequest, ArtifactReadResult, AttemptState, AttemptTerminationIntent,
    CredentialAuthority, CredentialBindingRequest, EffectiveExecutionLimits, EffectiveStepTimeout,
    ExecutionBudget, ExecutionProfile, ExecutionProposal, ExecutionProviderContract,
    ExecutionProviderSnapshot, ExecutionStepProposal, ExecutionTarget, ForeignReference,
    HostDependencyBinding, InputAuthority, InputBindingRequest, JobCancelRequest, JobDesiredState,
    JobObservation, JobObserveRequest, JobObserveWaitUntil, JobResolution, JobRunProposal,
    ReservationState, RuntimeCapabilities, RuntimeDeliveryDisposition,
    RuntimeExecutionTargetCapability, RuntimeJobListCursor, RuntimeJobListRequest,
    RuntimeJobListResult, RuntimeJobSummary, RuntimeNodeIdentity, RuntimeNodePlatform,
    RuntimeReleaseAdmission, RuntimeReleaseContract, RuntimeReleaseDisposition,
    RuntimeReleaseGetRequest, RuntimeReleaseProjection, RuntimeReleaseRequest,
    RuntimeWorkspaceAdmissionHeadroom, RuntimeWorkspaceGetRequest, RuntimeWorkspaceIssue,
    RuntimeWorkspaceIssueStage, RuntimeWorkspaceListCursor, RuntimeWorkspaceListRequest,
    RuntimeWorkspaceListResult, RuntimeWorkspaceSummary, WindowsAuthority,
    CLIENT_REQUEST_ID_MAX_LENGTH, CLIENT_REQUEST_ID_MIN_LENGTH, CLIENT_REQUEST_ID_PATTERN,
    LOGICAL_ID_MAX_LENGTH, LOGICAL_ID_MIN_LENGTH, LOGICAL_ID_PATTERN, MAX_TASK_TAIL_BYTES,
    MAX_TASK_WAIT_MS, RUNTIME_SCHEMA_VERSION,
};
#[cfg(not(any(test, feature = "operator-tools")))]
pub(crate) use types::{ArtifactRegistration, TerminalCommit};

#[cfg(any(test, feature = "operator-tools"))]
pub use types::{ArtifactRegistration, RuntimeInvariantViolation, TerminalCommit};
pub use windows::WindowsExecutionConfig;
pub use windows_broker::WindowsPrivilegedBrokerConfig;

#[cfg(test)]
mod integration_tests;
#[cfg(test)]
mod tests;
