//! Trusted-local Workspace execution and recovery core for Ordivon.
//!
//! This crate owns Workspace operations, transactional Job and Attempt state,
//! runner dispatch, process-tree ownership, bounded results and Artifacts,
//! reconciliation, Runtime inspection, and administrative repair semantics.

#[cfg(feature = "transactional-runtime")]
mod runtime;
#[cfg(feature = "universal-executor")]
mod universal;
#[cfg(windows)]
mod windows_security;
#[cfg(windows)]
pub use windows_security::{
    current_token_is_local_system as windows_current_token_is_local_system,
    validate_private_readonly_file_acl as validate_windows_private_readonly_file_acl,
};

#[cfg(feature = "universal-executor")]
pub use universal::{
    mutate_workspace, read_workspace_content, read_workspace_slice_compact,
    read_workspace_text_compact, workspace_changes_page, workspace_diff_compact,
    CompactWorkspaceDiffResult, CompactWorkspaceOpenResult, CompactWorkspaceReadResult,
    CompactWorkspaceSliceResult, GitWorkspaceCreateRequest, UniversalExecError,
    UniversalExecErrorCode, UniversalExecutorConfig, WorkspaceChangeCursor, WorkspaceChangeEntry,
    WorkspaceChangeKind, WorkspaceChangePageRequest, WorkspaceChangePageResult,
    WorkspaceCloseRequest, WorkspaceCloseResult, WorkspaceClosureDisposition,
    WorkspaceContentMetadata, WorkspaceContentReadResult, WorkspaceContentRequest,
    WorkspaceDiffRequest, WorkspaceMutateRequest, WorkspaceMutateResult, WorkspaceMutation,
    WorkspaceMutationMode, WorkspaceMutationResult, WorkspaceReadRequest,
    WorkspaceReadSliceRequest, WorkspaceRenamedPath, ENVIRONMENT_VARIABLE_NAME_PATTERN,
    MAX_WORKSPACE_CHANGE_PAGE_ENTRIES, MAX_WORKSPACE_IO_BYTES, UNIVERSAL_EXEC_SCHEMA_VERSION,
    WORKSPACE_ID_MAX_LENGTH, WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};

#[cfg(all(feature = "universal-executor", unix))]
pub use universal::run_job_runner;

#[cfg(feature = "transactional-runtime")]
pub use runtime::{
    inspect_job, runtime_release_effect_id, runtime_release_request_identity_digest,
    ArtifactDescriptor, ArtifactReadRequest, ArtifactReadResult, AttemptState,
    AttemptTerminationIntent, CredentialAuthority, CredentialBindingRequest,
    EffectiveExecutionLimits, EffectiveStepTimeout, ExecutionBudget, ExecutionProfile,
    ExecutionProposal, ExecutionProviderContract, ExecutionProviderSnapshot, ExecutionStepProposal,
    ExecutionTarget, ForeignReference, HostDependencyBinding, InputAuthority, InputBindingRequest,
    JobCancelRequest, JobDesiredState, JobObservation, JobObserveRequest, JobObserveWaitUntil,
    JobResolution, JobRunProposal, ReconciliationFailure, ReconciliationReport, RegistryConfig,
    ReservationState, Runtime, RuntimeCapabilities, RuntimeCapacity, RuntimeConfig,
    RuntimeDeliveryDisposition, RuntimeError, RuntimeErrorCode, RuntimeExecutionTargetCapability,
    RuntimeInspectionArtifactSummary, RuntimeInspectionAttempt, RuntimeInspectionCondition,
    RuntimeInspectionConfig, RuntimeInspectionEpisodes, RuntimeInspectionEvent,
    RuntimeInspectionJob, RuntimeJobInspection, RuntimeJobListCursor, RuntimeJobListRequest,
    RuntimeJobListResult, RuntimeJobSummary, RuntimeNodeIdentity, RuntimeNodePlatform,
    RuntimeReleaseAdmission, RuntimeReleaseContract, RuntimeReleaseDisposition,
    RuntimeReleaseGetRequest, RuntimeReleaseProjection, RuntimeReleaseRequest, RuntimeResult,
    RuntimeWorkspaceGetRequest, RuntimeWorkspaceIssue, RuntimeWorkspaceIssueStage,
    RuntimeWorkspaceListCursor, RuntimeWorkspaceListRequest, RuntimeWorkspaceListResult,
    RuntimeWorkspaceSummary, WindowsAuthority, WindowsExecutionConfig,
    WindowsExecutionContextRequest, WindowsExecutionIdentity, WindowsPayloadPrivilege,
    WindowsPrivilegedBrokerConfig, WorkspaceHeadroomConfig, CLIENT_REQUEST_ID_MAX_LENGTH,
    CLIENT_REQUEST_ID_MIN_LENGTH, CLIENT_REQUEST_ID_PATTERN, DEFAULT_INSPECTION_EVENT_LIMIT,
    LOGICAL_ID_MAX_LENGTH, LOGICAL_ID_MIN_LENGTH, LOGICAL_ID_PATTERN, MAX_INSPECTION_EVENT_LIMIT,
    MAX_TASK_TAIL_BYTES, MAX_TASK_WAIT_MS, RUNTIME_MAX_MIGRATION_VERSION, RUNTIME_SCHEMA_VERSION,
};

#[cfg(feature = "operator-tools")]
pub use runtime::{
    apply_runtime_repair, cancel_stale_recovery_required_attempt, inspect_registry,
    inspect_registry_activity, inspect_registry_archive, inspect_registry_markers,
    inspect_registry_status, inspect_registry_workspace_activity, inspect_runtime,
    inspect_runtime_release_effect, inspect_runtime_release_effect_owner, inspect_workspace,
    summarize_experience, ArtifactRegistration, RuntimeDoctorAttemptState,
    RuntimeDoctorCapacityHolder, RuntimeDoctorCase, RuntimeDoctorConfig, RuntimeDoctorJobState,
    RuntimeDoctorProposal, RuntimeDoctorReport, RuntimeDoctorReservationState,
    RuntimeDoctorSummary, RuntimeExperienceArtifactSummary, RuntimeExperienceCancellationSummary,
    RuntimeExperienceDispatchSummary, RuntimeExperienceDurationSummary,
    RuntimeExperienceJobSummary, RuntimeExperienceMechanicalLatencySummary,
    RuntimeExperienceRecoverySummary, RuntimeExperienceSummary, RuntimeInvariantViolation,
    RuntimeOperatorActiveWorkspace, RuntimeOperatorArchiveClassification,
    RuntimeOperatorArchiveClosure, RuntimeOperatorArchiveInspection, RuntimeOperatorArchiveSample,
    RuntimeOperatorAttemptSupervisorOwner, RuntimeOperatorDashboardJob,
    RuntimeOperatorDashboardJobs, RuntimeOperatorRegistryActivityInspection,
    RuntimeOperatorRegistryInspection, RuntimeOperatorRegistryMarkersInspection,
    RuntimeOperatorRegistryStatusInspection, RuntimeOperatorReleaseEffectInspection,
    RuntimeOperatorWorkspaceActivity, RuntimeOperatorWorkspaceActivityInspection,
    RuntimeOperatorWorkspaceLastActivity, RuntimeOperatorWorkspaceMarker, RuntimeRepairAction,
    RuntimeRepairActionKind, RuntimeRepairConfig, RuntimeRepairReport, RuntimeRepairRequest,
    RuntimeStaleCancelReport, RuntimeStaleCancelRequest, RuntimeWorkspaceInspection,
    RuntimeWorkspaceInspectionConfig, RuntimeWorkspaceInspectionJob, DEFAULT_ARCHIVE_SAMPLE_LIMIT,
    DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT, MAX_ARCHIVE_SAMPLE_LIMIT,
    MAX_WORKSPACE_INSPECTION_JOB_LIMIT, RUNTIME_DOCTOR_SCHEMA_VERSION,
    RUNTIME_REPAIR_SCHEMA_VERSION,
};
