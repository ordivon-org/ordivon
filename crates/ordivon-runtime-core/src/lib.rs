//! Trusted-local Workspace execution and recovery core for Ordivon.
//!
//! This crate owns Workspace operations, transactional Job and Attempt state,
//! runner dispatch, process-tree ownership, bounded results and Artifacts,
//! reconciliation, Runtime inspection, and administrative repair semantics.

#[cfg(feature = "transactional-runtime")]
mod runtime;
#[cfg(feature = "universal-executor")]
mod universal;

#[cfg(feature = "universal-executor")]
pub use universal::{
    create_git_workspace, mutate_workspace, read_workspace_content, read_workspace_slice_compact,
    read_workspace_text_compact, remove_git_workspace, workspace_changes_page, workspace_diff,
    workspace_diff_compact, write_workspace_text, CompactWorkspaceDiffResult,
    CompactWorkspaceOpenResult, CompactWorkspaceReadResult, CompactWorkspaceSliceResult,
    GitWorkspaceCreateRequest, UniversalExecError, UniversalExecErrorCode, UniversalExecutorConfig,
    WorkspaceChangeCursor, WorkspaceChangeEntry, WorkspaceChangeKind, WorkspaceChangePageRequest,
    WorkspaceChangePageResult, WorkspaceCloseRequest, WorkspaceCloseResult,
    WorkspaceClosureDisposition, WorkspaceContentMetadata, WorkspaceContentReadResult,
    WorkspaceContentRequest, WorkspaceDiffRequest, WorkspaceDiffResult, WorkspaceFilePatch,
    WorkspaceMutateRequest, WorkspaceMutateResult, WorkspaceMutation, WorkspaceMutationMode,
    WorkspaceMutationResult, WorkspacePatchPlan, WorkspacePatchPlanFile, WorkspacePatchPlanState,
    WorkspacePatchRequest, WorkspacePatchResult, WorkspacePatchedFile, WorkspaceReadRequest,
    WorkspaceReadResult, WorkspaceReadSliceRequest, WorkspaceReadSliceResult, WorkspaceRecord,
    WorkspaceRenamedPath, WorkspaceTextEdit, WorkspaceTextPosition, WorkspaceTextRange,
    WorkspaceWriteRequest, WorkspaceWriteResult, ENVIRONMENT_VARIABLE_NAME_PATTERN,
    MAX_WORKSPACE_CHANGE_PAGE_ENTRIES, MAX_WORKSPACE_IO_BYTES, UNIVERSAL_EXEC_SCHEMA_VERSION,
    WORKSPACE_ID_MAX_LENGTH, WORKSPACE_ID_MIN_LENGTH, WORKSPACE_ID_PATTERN,
};

#[cfg(all(feature = "universal-executor", unix))]
pub use universal::run_task_runner;

#[cfg(feature = "transactional-runtime")]
pub use runtime::{
    inspect_job, runtime_release_effect_id, runtime_release_request_identity_digest,
    AdmissionOutcome, ArtifactDescriptor, ArtifactReadRequest, ArtifactReadResult,
    ArtifactRegistration, AttemptRecord, AttemptState, AttemptTerminationIntent, CreatedAdmission,
    DurableWorkspacePatchRequest, DurableWorkspacePatchResult, EffectiveExecutionLimits,
    EffectiveInputBinding, EffectiveStepTimeout, ExecutionBudget, ExecutionProfile,
    ExecutionProposal, ExecutionProviderContract, ExecutionProviderSnapshot, ExecutionStepProposal,
    ExecutionTarget, ForeignReference, HostDependencyBinding, InputAccessMode, InputAuthority,
    InputBindingRequest, JobDesiredState, JobProjection, JobResolution, ReconciliationFailure,
    ReconciliationReport, Registry, RegistryConfig, ReservationRecord, ReservationState,
    RunnerIdentity, Runtime, RuntimeArtifactRecord, RuntimeCapabilities, RuntimeCapacity,
    RuntimeConfig, RuntimeDeliveryDisposition, RuntimeError, RuntimeErrorCode,
    RuntimeExecutionPlan, RuntimeExecutionStep, RuntimeExecutionTargetCapability,
    RuntimeInspectionArtifactSummary, RuntimeInspectionAttempt, RuntimeInspectionCondition,
    RuntimeInspectionConfig, RuntimeInspectionEpisodes, RuntimeInspectionEvent,
    RuntimeInspectionJob, RuntimeInvariantViolation, RuntimeJobInspection, RuntimeJobListCursor,
    RuntimeJobListRequest, RuntimeJobListResult, RuntimeJobRecord, RuntimeJobSummary,
    RuntimeNodeIdentity, RuntimeNodePlatform, RuntimeReleaseAdmission, RuntimeReleaseContract,
    RuntimeReleaseDisposition, RuntimeReleaseEffectBinding, RuntimeReleaseGetRequest,
    RuntimeReleaseProjection, RuntimeReleaseRequest, RuntimeResult, RuntimeWorkspaceGetRequest,
    RuntimeWorkspaceIssue, RuntimeWorkspaceIssueStage, RuntimeWorkspaceListCursor,
    RuntimeWorkspaceListRequest, RuntimeWorkspaceListResult, RuntimeWorkspaceSummary,
    SubmitRequest, TaskCancelRequest, TaskObservation, TaskObserveRequest, TaskObserveWaitUntil,
    TaskRunProposal, TaskRunRequest, TerminalCommit, UniversalExecutionRequest,
    UniversalExecutionStep, WindowsAuthority, WindowsExecutionConfig, WindowsExecutionContext,
    WindowsTokenClass, WorkspacePatchOperationState, WorkspacePatchOperationStatus,
    WorkspacePatchStatusRequest, CLIENT_REQUEST_ID_MAX_LENGTH, CLIENT_REQUEST_ID_MIN_LENGTH,
    CLIENT_REQUEST_ID_PATTERN, DEFAULT_INSPECTION_EVENT_LIMIT, LOGICAL_ID_MAX_LENGTH,
    LOGICAL_ID_MIN_LENGTH, LOGICAL_ID_PATTERN, MAX_ARTIFACT_READ_BYTES, MAX_INSPECTION_EVENT_LIMIT,
    MAX_RUNTIME_LIST_LIMIT, MAX_TASK_TAIL_BYTES, MAX_TASK_WAIT_MS,
    RUNTIME_CONDITION_RETIREMENT_MIGRATION_CHECKSUM, RUNTIME_INSPECTION_SCHEMA_VERSION,
    RUNTIME_MIGRATION_CHECKSUM, RUNTIME_ORPHAN_RECLAIM_MIGRATION_CHECKSUM,
    RUNTIME_ORPHAN_RECOVERY_MIGRATION_CHECKSUM, RUNTIME_SCHEMA_VERSION,
    RUNTIME_TERMINAL_REPAIR_MIGRATION_CHECKSUM,
};

#[cfg(feature = "operator-tools")]
pub use runtime::{
    apply_runtime_repair, cancel_stale_recovery_required_attempt, inspect_registry,
    inspect_registry_activity, inspect_registry_archive, inspect_registry_markers,
    inspect_registry_status, inspect_registry_workspace_activity, inspect_runtime,
    inspect_workspace, summarize_experience, RuntimeDoctorAttemptState,
    RuntimeDoctorCapacityHolder, RuntimeDoctorCase, RuntimeDoctorConfig, RuntimeDoctorJobState,
    RuntimeDoctorProposal, RuntimeDoctorReport, RuntimeDoctorReservationState,
    RuntimeDoctorSummary, RuntimeExperienceArtifactSummary, RuntimeExperienceCancellationSummary,
    RuntimeExperienceDispatchSummary, RuntimeExperienceDurationSummary,
    RuntimeExperienceJobSummary, RuntimeExperienceMechanicalLatencySummary,
    RuntimeExperienceRecoverySummary, RuntimeExperienceSummary, RuntimeOperatorActiveWorkspace,
    RuntimeOperatorArchiveClassification, RuntimeOperatorArchiveClosure,
    RuntimeOperatorArchiveInspection, RuntimeOperatorArchiveSample, RuntimeOperatorDashboardJob,
    RuntimeOperatorDashboardJobs, RuntimeOperatorRegistryActivityInspection,
    RuntimeOperatorRegistryInspection, RuntimeOperatorRegistryMarkersInspection,
    RuntimeOperatorRegistryStatusInspection, RuntimeOperatorWorkspaceActivity,
    RuntimeOperatorWorkspaceActivityInspection, RuntimeOperatorWorkspaceLastActivity,
    RuntimeOperatorWorkspaceMarker, RuntimeRepairAction, RuntimeRepairActionKind,
    RuntimeRepairConfig, RuntimeRepairReport, RuntimeRepairRequest, RuntimeStaleCancelReport,
    RuntimeStaleCancelRequest, RuntimeWorkspaceInspection, RuntimeWorkspaceInspectionConfig,
    RuntimeWorkspaceInspectionJob, DEFAULT_ARCHIVE_SAMPLE_LIMIT,
    DEFAULT_WORKSPACE_INSPECTION_JOB_LIMIT, MAX_ARCHIVE_SAMPLE_LIMIT,
    MAX_WORKSPACE_INSPECTION_JOB_LIMIT, RUNTIME_DOCTOR_SCHEMA_VERSION,
    RUNTIME_REPAIR_SCHEMA_VERSION,
};
