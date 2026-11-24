//! Original request identity domain wire contract and behavior.
#[cfg(test)]
use super::JobRunRequest;
use super::{
    CredentialBindingRequest, ExecutionBudget, ExecutionProfile, ExecutionStepProposal,
    ExecutionTarget, ForeignReference, HostDependencyBinding, InputBindingRequest, JobRunProposal,
    RuntimeError, RuntimeErrorCode, RuntimeExecutionPlan, RuntimeResult, UniversalExecutionStep,
    WindowsAuthority, WindowsExecutionContextRequest, CREDENTIAL_BOUND_PROPOSAL_IDENTITY_PREFIX,
    INPUT_BOUND_PROPOSAL_IDENTITY_PREFIX, PROPOSAL_IDENTITY_PREFIX, REQUEST_IDENTITY_PREFIX,
};
use serde::Serialize;
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct OperationRequestIdentity {
    schema_version: u32,
    principal: String,
    workspace_id: String,
    executable: String,
    args: Vec<String>,
    cwd_relative: String,
    env: BTreeMap<String, String>,
    timeout_ms: u64,
    stdout_limit_bytes: u64,
    stderr_limit_bytes: u64,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    steps: Vec<UniversalExecutionStep>,
    budget: ExecutionBudget,
    execution_profile: ExecutionProfile,
    #[serde(default, skip_serializing_if = "ExecutionTarget::is_default")]
    execution_target: ExecutionTarget,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    windows_authority: Option<WindowsAuthority>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    windows_context: Option<WindowsExecutionContextRequest>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    foreign_references: Vec<ForeignReference>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    host_dependencies: Vec<HostDependencyBinding>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct InputBindingIdentity {
    authority: String,
    relative_object: String,
    expected_digest: String,
    presentation_relative_path: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct InputBoundProposalIdentity {
    proposal: ProposalRequestIdentity,
    inputs: Vec<InputBindingIdentity>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct CredentialBindingIdentity {
    authority: String,
    credential: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct CredentialBoundProposalIdentity {
    proposal: ProposalRequestIdentity,
    credentials: Vec<CredentialBindingIdentity>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ProposalRequestIdentity {
    schema_version: u32,
    principal: String,
    workspace_id: String,
    executable: String,
    args: Vec<String>,
    cwd_relative: String,
    env: BTreeMap<String, String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    timeout_ms: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stdout_limit_bytes: Option<u64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stderr_limit_bytes: Option<u64>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    steps: Vec<ExecutionStepProposal>,
    budget: ExecutionBudget,
    execution_profile: ExecutionProfile,
    #[serde(default, skip_serializing_if = "ExecutionTarget::is_default")]
    execution_target: ExecutionTarget,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    windows_authority: Option<WindowsAuthority>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    windows_context: Option<WindowsExecutionContextRequest>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    foreign_references: Vec<ForeignReference>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    host_dependencies: Vec<HostDependencyBinding>,
}

fn identity_windows_authority(
    target: ExecutionTarget,
    authority: WindowsAuthority,
) -> Option<WindowsAuthority> {
    match (target, authority) {
        (ExecutionTarget::WindowsNative, WindowsAuthority::Limited) => None,
        (ExecutionTarget::WindowsNative, _) => Some(authority),
        _ => None,
    }
}

fn host_dependency_identities(
    dependencies: &[HostDependencyBinding],
) -> Vec<HostDependencyBinding> {
    let mut dependencies = dependencies.to_vec();
    dependencies.sort_by(|left, right| {
        (&left.path, &left.expected_digest).cmp(&(&right.path, &right.expected_digest))
    });
    dependencies
}

#[cfg(test)]
pub(crate) fn operation_request_identity_digest(request: &JobRunRequest) -> RuntimeResult<String> {
    operation_request_identity_digest_from_parts(operation_request_identity(request))
}

#[cfg(test)]
fn operation_request_identity(request: &JobRunRequest) -> OperationRequestIdentity {
    OperationRequestIdentity {
        schema_version: request.schema_version,
        principal: request.principal.clone(),
        workspace_id: request.execution.workspace_id.clone(),
        executable: normalize_path_text(&request.execution.executable),
        args: request.execution.args.clone(),
        cwd_relative: normalize_relative_path_text(&request.execution.cwd_relative),
        env: request.execution.env.clone(),
        timeout_ms: request.execution.timeout_ms,
        stdout_limit_bytes: request.execution.stdout_limit_bytes,
        stderr_limit_bytes: request.execution.stderr_limit_bytes,
        steps: request.execution.steps.clone(),
        budget: request.execution.budget.clone(),
        execution_profile: request.execution.execution_profile,
        execution_target: request.execution.execution_target,
        windows_authority: identity_windows_authority(
            request.execution.execution_target,
            request.execution.windows_authority,
        ),
        windows_context: request.execution.windows_context,
        foreign_references: request.execution.foreign_references.clone(),
        host_dependencies: host_dependency_identities(&request.execution.host_dependencies),
    }
}

fn input_binding_identities(inputs: &[InputBindingRequest]) -> Vec<InputBindingIdentity> {
    let mut inputs = inputs
        .iter()
        .map(|input| InputBindingIdentity {
            authority: input.authority.clone(),
            relative_object: input.relative_object.clone(),
            expected_digest: input.expected_digest.to_ascii_lowercase(),
            presentation_relative_path: input.presentation_relative_path.clone(),
        })
        .collect::<Vec<_>>();
    inputs.sort_by(|left, right| {
        (
            &left.presentation_relative_path,
            &left.authority,
            &left.relative_object,
            &left.expected_digest,
        )
            .cmp(&(
                &right.presentation_relative_path,
                &right.authority,
                &right.relative_object,
                &right.expected_digest,
            ))
    });
    inputs
}

fn credential_binding_identities(
    credentials: &[CredentialBindingRequest],
) -> Vec<CredentialBindingIdentity> {
    let mut credentials = credentials
        .iter()
        .map(|credential| CredentialBindingIdentity {
            authority: credential.authority.clone(),
            credential: credential.credential.clone(),
        })
        .collect::<Vec<_>>();
    credentials.sort_by(|left, right| {
        (&left.authority, &left.credential).cmp(&(&right.authority, &right.credential))
    });
    credentials
}

fn proposal_request_identity(proposal: &JobRunProposal) -> ProposalRequestIdentity {
    ProposalRequestIdentity {
        schema_version: proposal.schema_version,
        principal: proposal.principal.clone(),
        workspace_id: proposal.execution.workspace_id.clone(),
        executable: normalize_path_text(&proposal.execution.executable),
        args: proposal.execution.args.clone(),
        cwd_relative: normalize_relative_path_text(&proposal.execution.cwd_relative),
        env: proposal.execution.env.clone(),
        timeout_ms: proposal.execution.timeout_ms,
        stdout_limit_bytes: proposal.execution.stdout_limit_bytes,
        stderr_limit_bytes: proposal.execution.stderr_limit_bytes,
        steps: proposal
            .execution
            .steps
            .iter()
            .map(|step| ExecutionStepProposal {
                id: step.id.clone(),
                executable: normalize_path_text(&step.executable),
                args: step.args.clone(),
                cwd_relative: normalize_relative_path_text(&step.cwd_relative),
                env: step.env.clone(),
                timeout_ms: step.timeout_ms,
                continue_on_error: step.continue_on_error,
            })
            .collect(),
        budget: proposal.execution.budget.clone(),
        execution_profile: proposal.execution.execution_profile,
        execution_target: proposal.execution.execution_target,
        windows_authority: identity_windows_authority(
            proposal.execution.execution_target,
            proposal.execution.windows_authority,
        ),
        windows_context: proposal.execution.windows_context,
        foreign_references: proposal.execution.foreign_references.clone(),
        host_dependencies: host_dependency_identities(&proposal.execution.host_dependencies),
    }
}

pub(crate) fn legacy_request_identity_digest_from_proposal(
    proposal: &JobRunProposal,
) -> RuntimeResult<Option<String>> {
    let Some(timeout_ms) = proposal.execution.timeout_ms else {
        return Ok(None);
    };
    let Some(stdout_limit_bytes) = proposal.execution.stdout_limit_bytes else {
        return Ok(None);
    };
    let Some(stderr_limit_bytes) = proposal.execution.stderr_limit_bytes else {
        return Ok(None);
    };
    let mut steps = Vec::with_capacity(proposal.execution.steps.len());
    for step in &proposal.execution.steps {
        let Some(step_timeout_ms) = step.timeout_ms else {
            return Ok(None);
        };
        steps.push(UniversalExecutionStep {
            id: step.id.clone(),
            executable: normalize_path_text(&step.executable),
            args: step.args.clone(),
            cwd_relative: normalize_relative_path_text(&step.cwd_relative),
            env: step.env.clone(),
            timeout_ms: step_timeout_ms,
            continue_on_error: step.continue_on_error,
        });
    }
    operation_request_identity_digest_from_parts(OperationRequestIdentity {
        schema_version: proposal.schema_version,
        principal: proposal.principal.clone(),
        workspace_id: proposal.execution.workspace_id.clone(),
        executable: normalize_path_text(&proposal.execution.executable),
        args: proposal.execution.args.clone(),
        cwd_relative: normalize_relative_path_text(&proposal.execution.cwd_relative),
        env: proposal.execution.env.clone(),
        timeout_ms,
        stdout_limit_bytes,
        stderr_limit_bytes,
        steps,
        budget: proposal.execution.budget.clone(),
        execution_profile: proposal.execution.execution_profile,
        execution_target: proposal.execution.execution_target,
        windows_authority: identity_windows_authority(
            proposal.execution.execution_target,
            proposal.execution.windows_authority,
        ),
        windows_context: proposal.execution.windows_context,
        foreign_references: proposal.execution.foreign_references.clone(),
        host_dependencies: host_dependency_identities(&proposal.execution.host_dependencies),
    })
    .map(Some)
}

pub(crate) fn proposal_request_identity_digest(proposal: &JobRunProposal) -> RuntimeResult<String> {
    let bytes = serde_json::to_vec(&proposal_request_identity(proposal)).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            format!("cannot serialize execution proposal identity: {error}"),
            None,
            false,
        )
    })?;
    Ok(format!(
        "{PROPOSAL_IDENTITY_PREFIX}{}",
        crate::universal::sha256_bytes(&bytes)
    ))
}

pub(crate) fn input_bound_proposal_request_identity_digest(
    proposal: &JobRunProposal,
    inputs: &[InputBindingRequest],
) -> RuntimeResult<String> {
    let identity = InputBoundProposalIdentity {
        proposal: proposal_request_identity(proposal),
        inputs: input_binding_identities(inputs),
    };
    let bytes = serde_json::to_vec(&identity).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            format!("cannot serialize input-bound proposal identity: {error}"),
            None,
            false,
        )
    })?;
    Ok(format!(
        "{INPUT_BOUND_PROPOSAL_IDENTITY_PREFIX}{}",
        crate::universal::sha256_bytes(&bytes)
    ))
}

pub(crate) fn credential_bound_proposal_request_identity_digest(
    proposal: &JobRunProposal,
    credentials: &[CredentialBindingRequest],
) -> RuntimeResult<String> {
    let identity = CredentialBoundProposalIdentity {
        proposal: proposal_request_identity(proposal),
        credentials: credential_binding_identities(credentials),
    };
    let bytes = serde_json::to_vec(&identity).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            format!("cannot serialize credential-bound proposal identity: {error}"),
            None,
            false,
        )
    })?;
    Ok(format!(
        "{CREDENTIAL_BOUND_PROPOSAL_IDENTITY_PREFIX}{}",
        crate::universal::sha256_bytes(&bytes)
    ))
}

pub(crate) fn operation_request_identity_digest_from_plan(
    plan: &RuntimeExecutionPlan,
) -> RuntimeResult<String> {
    let cwd = Path::new(&plan.cwd)
        .strip_prefix(&plan.workspace_path)
        .map_err(|_| {
            RuntimeError::new(
                RuntimeErrorCode::RegistryCorrupt,
                "stored execution cwd is outside its Workspace",
                Some("executionPlan"),
                false,
            )
        })?;
    operation_request_identity_digest_from_parts(OperationRequestIdentity {
        schema_version: plan.schema_version,
        principal: plan.principal.clone(),
        workspace_id: plan.workspace_id.clone(),
        executable: normalize_path_text(&plan.executable),
        args: plan.args.clone(),
        cwd_relative: normalize_relative_path_text(&cwd.to_string_lossy()),
        env: plan.env.clone(),
        timeout_ms: plan.timeout_ms,
        stdout_limit_bytes: plan.stdout_limit_bytes,
        stderr_limit_bytes: plan.stderr_limit_bytes,
        steps: plan
            .steps
            .iter()
            .map(|step| UniversalExecutionStep {
                id: step.id.clone(),
                executable: normalize_path_text(&step.executable),
                args: step.args.clone(),
                cwd_relative: Path::new(&step.cwd)
                    .strip_prefix(&plan.workspace_path)
                    .map(|path| normalize_relative_path_text(&path.to_string_lossy()))
                    .unwrap_or_else(|_| step.cwd.clone()),
                env: step.env.clone(),
                timeout_ms: step.timeout_ms,
                continue_on_error: step.continue_on_error,
            })
            .collect(),
        budget: plan.budget.clone(),
        execution_profile: plan.execution_profile,
        execution_target: plan.execution_target,
        windows_authority: identity_windows_authority(
            plan.execution_target,
            plan.windows_authority,
        ),
        windows_context: plan.windows_context,
        foreign_references: plan.foreign_references.clone(),
        host_dependencies: Vec::new(),
    })
}

fn operation_request_identity_digest_from_parts(
    identity: OperationRequestIdentity,
) -> RuntimeResult<String> {
    let bytes = serde_json::to_vec(&identity).map_err(|error| {
        RuntimeError::new(
            RuntimeErrorCode::InvalidRequest,
            format!("cannot serialize operation request identity: {error}"),
            None,
            false,
        )
    })?;
    Ok(format!(
        "{REQUEST_IDENTITY_PREFIX}{}",
        crate::universal::sha256_bytes(&bytes)
    ))
}

fn normalize_path_text(value: &str) -> String {
    use std::path::Component;

    let path = Path::new(value);
    let absolute = path.is_absolute();
    let mut normalized = if absolute {
        PathBuf::from("/")
    } else {
        PathBuf::new()
    };
    for component in path.components() {
        match component {
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
            Component::RootDir | Component::CurDir => {}
            Component::ParentDir => {
                let can_pop = normalized
                    .file_name()
                    .is_some_and(|name| name != std::ffi::OsStr::new(".."));
                if can_pop {
                    normalized.pop();
                } else if !absolute {
                    normalized.push("..");
                }
            }
            Component::Normal(part) => normalized.push(part),
        }
    }
    normalized.to_string_lossy().into_owned()
}

fn normalize_relative_path_text(value: &str) -> String {
    let normalized = normalize_path_text(value);
    if normalized.is_empty() {
        ".".to_string()
    } else {
        normalized
    }
}
