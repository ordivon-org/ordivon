//! Stable, execution-free contracts for the Ordivon Execution Fabric.
//!
//! This crate deliberately contains no process spawning, Registry access, policy
//! evaluation, scheduling, controller loop, provider implementation, or network I/O.
//! It names pieces that other owners may compose without moving their authority
//! into Runtime Core.

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::fmt;

pub const EXECUTION_FABRIC_SCHEMA_VERSION: u32 = 1;

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, JsonSchema)]
#[serde(transparent)]
pub struct FabricId(String);

impl FabricId {
    pub fn parse(value: impl Into<String>) -> Result<Self, FabricContractError> {
        let value = value.into();
        validate_fabric_id(&value)?;
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl<'de> Deserialize<'de> for FabricId {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let value = String::deserialize(deserializer)?;
        Self::parse(value).map_err(serde::de::Error::custom)
    }
}

impl fmt::Display for FabricId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}

fn validate_fabric_id(value: &str) -> Result<(), FabricContractError> {
    if value.is_empty() {
        return Err(FabricContractError::InvalidId("identifier is empty"));
    }
    if value.len() > 256 {
        return Err(FabricContractError::InvalidId(
            "identifier exceeds 256 bytes",
        ));
    }
    if value.starts_with('/') || value.ends_with('/') || value.contains("//") {
        return Err(FabricContractError::InvalidId(
            "identifier must contain non-empty slash-separated segments",
        ));
    }
    if !value
        .bytes()
        .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'/' | b'.' | b'_' | b':' | b'@' | b'-'))
    {
        return Err(FabricContractError::InvalidId(
            "identifier contains unsupported characters",
        ));
    }
    Ok(())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum FabricPlatform {
    Windows,
    Linux,
    Macos,
    Cloud,
    Remote,
    Unknown,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct ResourceDescriptor {
    pub schema_version: u32,
    pub resource_id: FabricId,
    pub resource_kind: FabricId,
    pub node_id: Option<FabricId>,
    #[serde(default)]
    pub conflict_domains: Vec<FabricId>,
}

impl ResourceDescriptor {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        require_unique_ids("conflictDomains", &self.conflict_domains)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct CapabilityDescriptor {
    pub schema_version: u32,
    pub capability_id: FabricId,
    pub resource_kind: FabricId,
    pub observation_only: bool,
}

impl CapabilityDescriptor {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct ProviderDescriptor {
    pub schema_version: u32,
    pub provider_id: FabricId,
    pub node_id: FabricId,
    pub platform: FabricPlatform,
    #[serde(default)]
    pub capabilities: Vec<FabricId>,
}

impl ProviderDescriptor {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        if self.capabilities.is_empty() {
            return Err(FabricContractError::EmptySet("capabilities"));
        }
        require_unique_ids("capabilities", &self.capabilities)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct NodeDescriptor {
    pub schema_version: u32,
    pub node_id: FabricId,
    pub platform: FabricPlatform,
    pub native_control_plane: bool,
    pub trust_domain: FabricId,
    #[serde(default)]
    pub providers: Vec<FabricId>,
    #[serde(default)]
    pub capabilities: Vec<FabricId>,
    #[serde(default)]
    pub authority_contexts: Vec<FabricId>,
}

impl NodeDescriptor {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        require_unique_ids("providers", &self.providers)?;
        require_unique_ids("capabilities", &self.capabilities)?;
        require_unique_ids("authorityContexts", &self.authority_contexts)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum AuthorityMode {
    OpenControl,
    Normal,
    Maintenance,
    Recovery,
    Security,
    SecurityLab,
    Emergency,
    Strict,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ConflictMode {
    Observer,
    SharedRead,
    ExclusiveWrite,
    CooperativeWrite,
    AdversarialLab,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum AuthorityEnforcement {
    Shadow,
    Permissive,
    Enforcing,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AuthorityVector {
    pub schema_version: u32,
    pub principal_id: FabricId,
    pub trust_domain: FabricId,
    pub resource_scope: FabricId,
    #[serde(default)]
    pub capabilities: Vec<FabricId>,
    pub os_authority: FabricId,
    pub mode: AuthorityMode,
    pub conflict_mode: ConflictMode,
    pub enforcement: AuthorityEnforcement,
    pub budget_id: Option<FabricId>,
    pub evidence_policy_id: Option<FabricId>,
}

impl AuthorityVector {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        if self.capabilities.is_empty() {
            return Err(FabricContractError::EmptySet("capabilities"));
        }
        require_unique_ids("capabilities", &self.capabilities)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AuthorityLease {
    pub schema_version: u32,
    pub lease_id: FabricId,
    pub authority: AuthorityVector,
    pub issued_at_ms: u64,
    pub expires_at_ms: u64,
    pub revoked_at_ms: Option<u64>,
}

impl AuthorityLease {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        self.authority.validate()?;
        if self.expires_at_ms <= self.issued_at_ms {
            return Err(FabricContractError::InvalidLease(
                "expiresAtMs must be greater than issuedAtMs",
            ));
        }
        if let Some(revoked) = self.revoked_at_ms {
            if revoked < self.issued_at_ms {
                return Err(FabricContractError::InvalidLease(
                    "revokedAtMs cannot predate issuedAtMs",
                ));
            }
        }
        Ok(())
    }

    pub fn is_active_at(&self, now_ms: u64) -> bool {
        self.revoked_at_ms.is_none() && now_ms >= self.issued_at_ms && now_ms < self.expires_at_ms
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AuthorityEffectCandidate {
    pub schema_version: u32,
    pub principal_id: FabricId,
    pub trust_domain: FabricId,
    pub resource_scope: FabricId,
    pub capability_id: FabricId,
    pub os_authority: FabricId,
    pub mode: AuthorityMode,
    pub conflict_mode: ConflictMode,
}

impl AuthorityEffectCandidate {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum AuthorityConflictClassification {
    None,
    SharedObservation,
    CooperativeOverlap,
    ExclusiveOverlap,
    AdversarialOverlap,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct AuthorityShadowDecision {
    pub schema_version: u32,
    pub shadow_only: bool,
    pub would_allow: bool,
    pub conflict: AuthorityConflictClassification,
    #[serde(default)]
    pub matching_lease_ids: Vec<FabricId>,
    #[serde(default)]
    pub overlapping_lease_ids: Vec<FabricId>,
}

/// Evaluate one candidate against already-materialized leases without enforcing the result.
///
/// R1 overlap is deliberately exact-resource-scope only. Conflict-domain expansion belongs to
/// the later Resource/Controller layer. This function performs no I/O, mutation, admission,
/// dispatch, revocation, renewal, or policy-provider call.
pub fn evaluate_authority_shadow(
    candidate: &AuthorityEffectCandidate,
    leases: &[AuthorityLease],
    now_ms: u64,
) -> Result<AuthorityShadowDecision, FabricContractError> {
    candidate.validate()?;

    let mut matching = Vec::new();
    let mut overlapping = Vec::new();
    let mut overlap_modes = Vec::new();

    for lease in leases {
        lease.validate()?;
        if !lease.is_active_at(now_ms) {
            continue;
        }
        let authority = &lease.authority;
        if authority.trust_domain != candidate.trust_domain
            || authority.resource_scope != candidate.resource_scope
        {
            continue;
        }
        overlapping.push(lease.lease_id.clone());
        overlap_modes.push(authority.conflict_mode);

        if authority.principal_id == candidate.principal_id
            && authority.capabilities.contains(&candidate.capability_id)
            && authority.os_authority == candidate.os_authority
            && authority.mode == candidate.mode
            && authority.conflict_mode == candidate.conflict_mode
        {
            matching.push(lease.lease_id.clone());
        }
    }

    let conflict = classify_authority_overlap(candidate.conflict_mode, &overlap_modes);
    Ok(AuthorityShadowDecision {
        schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
        shadow_only: true,
        would_allow: !matching.is_empty(),
        conflict,
        matching_lease_ids: matching,
        overlapping_lease_ids: overlapping,
    })
}

fn classify_authority_overlap(
    requested: ConflictMode,
    existing: &[ConflictMode],
) -> AuthorityConflictClassification {
    if existing.is_empty() {
        return AuthorityConflictClassification::None;
    }
    if existing
        .iter()
        .any(|mode| *mode == ConflictMode::AdversarialLab)
        || requested == ConflictMode::AdversarialLab
    {
        return AuthorityConflictClassification::AdversarialOverlap;
    }
    if existing
        .iter()
        .any(|mode| *mode == ConflictMode::ExclusiveWrite)
        || requested == ConflictMode::ExclusiveWrite
    {
        return AuthorityConflictClassification::ExclusiveOverlap;
    }
    if existing
        .iter()
        .any(|mode| *mode == ConflictMode::CooperativeWrite)
        || requested == ConflictMode::CooperativeWrite
    {
        return AuthorityConflictClassification::CooperativeOverlap;
    }
    AuthorityConflictClassification::SharedObservation
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ControllerReconcileDisposition {
    Converged,
    ActionRequired,
    ObservationIncomplete,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum ProviderAvailability {
    Available,
    Unavailable,
    Unknown,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct ProviderHealthObservation {
    pub schema_version: u32,
    pub controller_id: FabricId,
    pub resource_id: FabricId,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub provider_id: Option<FabricId>,
    pub desired_available: bool,
    pub observed: ProviderAvailability,
    pub reason_code: FabricId,
}

impl ProviderHealthObservation {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct ControllerPreview {
    pub schema_version: u32,
    pub controller_id: FabricId,
    pub resource_id: FabricId,
    pub desired_state: FabricId,
    pub observed_state: FabricId,
    pub disposition: ControllerReconcileDisposition,
    pub reason_code: FabricId,
}

/// Pure reconciliation preview for provider availability.
///
/// This function does not execute an action, acquire authority, choose a provider,
/// retry, wait, mutate Runtime state, or imply semantic completion.
pub fn preview_provider_health(
    observation: &ProviderHealthObservation,
) -> Result<ControllerPreview, FabricContractError> {
    observation.validate()?;
    let desired_state = FabricId::parse(if observation.desired_available {
        "state/provider-available"
    } else {
        "state/provider-unavailable"
    })?;
    let observed_state = FabricId::parse(match observation.observed {
        ProviderAvailability::Available => "state/provider-available",
        ProviderAvailability::Unavailable => "state/provider-unavailable",
        ProviderAvailability::Unknown => "state/provider-unknown",
    })?;
    let disposition = match observation.observed {
        ProviderAvailability::Unknown => ControllerReconcileDisposition::ObservationIncomplete,
        ProviderAvailability::Available if observation.desired_available => {
            ControllerReconcileDisposition::Converged
        }
        ProviderAvailability::Unavailable if !observation.desired_available => {
            ControllerReconcileDisposition::Converged
        }
        ProviderAvailability::Available | ProviderAvailability::Unavailable => {
            ControllerReconcileDisposition::ActionRequired
        }
    };
    Ok(ControllerPreview {
        schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
        controller_id: observation.controller_id.clone(),
        resource_id: observation.resource_id.clone(),
        desired_state,
        observed_state,
        disposition,
        reason_code: observation.reason_code.clone(),
    })
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct ControllerActionProposal {
    pub schema_version: u32,
    pub controller_id: FabricId,
    pub resource_id: FabricId,
    pub requested_capability_id: FabricId,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub preferred_provider_id: Option<FabricId>,
    pub authority_mode: AuthorityMode,
    pub conflict_mode: ConflictMode,
    pub reason_code: FabricId,
    /// Always false in the Execution Fabric R1 proposal contract. A proposal is intent,
    /// not admission, authority, dispatch, or proof that an effect occurred.
    pub effect_dispatched: bool,
}

impl ControllerActionProposal {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        if self.effect_dispatched {
            return Err(FabricContractError::InvalidControllerProposal(
                "controller action proposal cannot claim a dispatched effect",
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct ProviderHealthPlan {
    pub schema_version: u32,
    pub preview: ControllerPreview,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub action: Option<ControllerActionProposal>,
}

/// Convert provider-health desired/observed state into a pure action proposal.
///
/// The proposal is deliberately one layer above Runtime admission: it names a requested
/// capability and authority/conflict semantics but cannot acquire a lease, select a final
/// provider, dispatch an effect, retry, or mutate the observed resource.
pub fn plan_provider_health(
    observation: &ProviderHealthObservation,
) -> Result<ProviderHealthPlan, FabricContractError> {
    let preview = preview_provider_health(observation)?;
    let action = match preview.disposition {
        ControllerReconcileDisposition::ActionRequired => {
            let requested_capability_id = FabricId::parse(if observation.desired_available {
                "capability/provider/recover"
            } else {
                "capability/provider/deactivate"
            })?;
            Some(ControllerActionProposal {
                schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
                controller_id: observation.controller_id.clone(),
                resource_id: observation.resource_id.clone(),
                requested_capability_id,
                preferred_provider_id: observation.provider_id.clone(),
                authority_mode: AuthorityMode::Recovery,
                conflict_mode: ConflictMode::ExclusiveWrite,
                reason_code: observation.reason_code.clone(),
                effect_dispatched: false,
            })
        }
        ControllerReconcileDisposition::Converged
        | ControllerReconcileDisposition::ObservationIncomplete => None,
    };
    if let Some(action) = &action {
        action.validate()?;
    }
    Ok(ProviderHealthPlan {
        schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
        preview,
        action,
    })
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum WorkflowStepKind {
    Observe,
    Gate,
    Act,
    Verify,
    Recover,
    Compensate,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct WorkflowStep {
    pub schema_version: u32,
    pub step_id: FabricId,
    pub kind: WorkflowStepKind,
    pub resource_id: FabricId,
    pub requested_capability_id: FabricId,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub preferred_provider_id: Option<FabricId>,
    pub authority_mode: AuthorityMode,
    pub conflict_mode: ConflictMode,
    #[serde(default)]
    pub depends_on: Vec<FabricId>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub evidence_policy_id: Option<FabricId>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub compensates_step_id: Option<FabricId>,
    /// Always false in an R1 WorkflowPlan. A plan names intended effects and gates;
    /// Runtime admission/dispatch truth continues to live in Runtime Job/Attempt state.
    pub effect_dispatched: bool,
}

impl WorkflowStep {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        require_unique_ids("workflowStep.dependsOn", &self.depends_on)?;
        if self.depends_on.contains(&self.step_id) {
            return Err(FabricContractError::InvalidWorkflowPlan(
                "workflow step cannot depend on itself",
            ));
        }
        if self.effect_dispatched {
            return Err(FabricContractError::InvalidWorkflowPlan(
                "workflow step cannot claim a dispatched effect",
            ));
        }
        match (self.kind, self.compensates_step_id.is_some()) {
            (WorkflowStepKind::Compensate, false) => {
                return Err(FabricContractError::InvalidWorkflowPlan(
                    "compensation step must name compensatesStepId",
                ));
            }
            (WorkflowStepKind::Compensate, true) => {}
            (_, true) => {
                return Err(FabricContractError::InvalidWorkflowPlan(
                    "only compensation steps may name compensatesStepId",
                ));
            }
            (_, false) => {}
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct WorkflowPlan {
    pub schema_version: u32,
    pub workflow_id: FabricId,
    pub owner_id: FabricId,
    #[serde(default)]
    pub steps: Vec<WorkflowStep>,
    /// Always false in the R1 planning contract. Workflow execution belongs to a
    /// workflow/controller owner above Runtime admission.
    pub execution_started: bool,
}

impl WorkflowPlan {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        if self.steps.is_empty() {
            return Err(FabricContractError::EmptySet("workflowPlan.steps"));
        }
        if self.execution_started {
            return Err(FabricContractError::InvalidWorkflowPlan(
                "workflow plan cannot claim execution has started",
            ));
        }

        for (index, step) in self.steps.iter().enumerate() {
            step.validate()?;
            if self.steps[..index]
                .iter()
                .any(|existing| existing.step_id == step.step_id)
            {
                return Err(FabricContractError::DuplicateId(
                    "workflowPlan.steps",
                    step.step_id.to_string(),
                ));
            }
        }

        for step in &self.steps {
            for dependency in &step.depends_on {
                if !self
                    .steps
                    .iter()
                    .any(|candidate| &candidate.step_id == dependency)
                {
                    return Err(FabricContractError::InvalidWorkflowPlan(
                        "workflow dependency references unknown step",
                    ));
                }
            }
            if let Some(compensates) = &step.compensates_step_id {
                if !self
                    .steps
                    .iter()
                    .any(|candidate| &candidate.step_id == compensates)
                {
                    return Err(FabricContractError::InvalidWorkflowPlan(
                        "compensation references unknown step",
                    ));
                }
            }
        }

        let mut visit_state = vec![0_u8; self.steps.len()];
        for index in 0..self.steps.len() {
            validate_workflow_acyclic(self, index, &mut visit_state)?;
        }
        Ok(())
    }
}

fn validate_workflow_acyclic(
    plan: &WorkflowPlan,
    index: usize,
    state: &mut [u8],
) -> Result<(), FabricContractError> {
    match state[index] {
        2 => return Ok(()),
        1 => {
            return Err(FabricContractError::InvalidWorkflowPlan(
                "workflow dependency graph contains a cycle",
            ));
        }
        _ => {}
    }
    state[index] = 1;
    for dependency in &plan.steps[index].depends_on {
        let dependency_index = plan
            .steps
            .iter()
            .position(|candidate| &candidate.step_id == dependency)
            .ok_or(FabricContractError::InvalidWorkflowPlan(
                "workflow dependency references unknown step",
            ))?;
        validate_workflow_acyclic(plan, dependency_index, state)?;
    }
    state[index] = 2;
    Ok(())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "snake_case")]
pub enum WorkflowBindingDisposition {
    Resolved,
    Unresolved,
    Ambiguous,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct WorkflowStepBinding {
    pub schema_version: u32,
    pub step_id: FabricId,
    pub resource_id: FabricId,
    pub requested_capability_id: FabricId,
    pub disposition: WorkflowBindingDisposition,
    #[serde(default)]
    pub candidate_node_ids: Vec<FabricId>,
    #[serde(default)]
    pub candidate_provider_ids: Vec<FabricId>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_node_id: Option<FabricId>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_provider_id: Option<FabricId>,
    pub reason_code: FabricId,
    /// Always false in the EF6b resolver. Binding is planning truth, not Runtime dispatch truth.
    pub dispatch_started: bool,
}

impl WorkflowStepBinding {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        require_unique_ids(
            "workflowStepBinding.candidateNodeIds",
            &self.candidate_node_ids,
        )?;
        require_unique_ids(
            "workflowStepBinding.candidateProviderIds",
            &self.candidate_provider_ids,
        )?;
        if self.dispatch_started {
            return Err(FabricContractError::InvalidWorkflowBinding(
                "workflow binding cannot claim dispatch has started",
            ));
        }
        match self.disposition {
            WorkflowBindingDisposition::Resolved => {
                if self.selected_node_id.is_none() || self.selected_provider_id.is_none() {
                    return Err(FabricContractError::InvalidWorkflowBinding(
                        "resolved workflow binding requires selected node and provider",
                    ));
                }
                if self.candidate_provider_ids.len() != 1 || self.candidate_node_ids.len() != 1 {
                    return Err(FabricContractError::InvalidWorkflowBinding(
                        "resolved workflow binding must have exactly one candidate",
                    ));
                }
            }
            WorkflowBindingDisposition::Unresolved | WorkflowBindingDisposition::Ambiguous => {
                if self.selected_node_id.is_some() || self.selected_provider_id.is_some() {
                    return Err(FabricContractError::InvalidWorkflowBinding(
                        "non-resolved workflow binding cannot select a node or provider",
                    ));
                }
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct WorkflowBindingPlan {
    pub schema_version: u32,
    pub workflow_id: FabricId,
    pub fully_resolved: bool,
    #[serde(default)]
    pub bindings: Vec<WorkflowStepBinding>,
    /// Always false in EF6b. A dry-run binding plan never dispatches.
    pub dispatch_started: bool,
}

impl WorkflowBindingPlan {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        if self.bindings.is_empty() {
            return Err(FabricContractError::EmptySet(
                "workflowBindingPlan.bindings",
            ));
        }
        if self.dispatch_started {
            return Err(FabricContractError::InvalidWorkflowBinding(
                "workflow binding plan cannot claim dispatch has started",
            ));
        }
        for (index, binding) in self.bindings.iter().enumerate() {
            binding.validate()?;
            if self.bindings[..index]
                .iter()
                .any(|existing| existing.step_id == binding.step_id)
            {
                return Err(FabricContractError::DuplicateId(
                    "workflowBindingPlan.bindings",
                    binding.step_id.to_string(),
                ));
            }
        }
        let observed_fully_resolved = self
            .bindings
            .iter()
            .all(|binding| binding.disposition == WorkflowBindingDisposition::Resolved);
        if observed_fully_resolved != self.fully_resolved {
            return Err(FabricContractError::InvalidWorkflowBinding(
                "fullyResolved does not match step binding dispositions",
            ));
        }
        Ok(())
    }
}

/// Resolve one WorkflowPlan against a concrete Resource/Node/Provider catalog without routing,
/// policy, authority acquisition, Runtime admission, or dispatch.
///
/// EF6b is deliberately conservative:
/// - missing resources are unresolved;
/// - a resource pinned to one node only considers providers on that node;
/// - preferredProviderId is an exact filter, not a hint;
/// - zero providers is unresolved;
/// - one provider is resolved;
/// - multiple providers is ambiguous and remains unselected.
pub fn resolve_workflow_bindings(
    plan: &WorkflowPlan,
    resources: &[ResourceDescriptor],
    nodes: &[NodeDescriptor],
    providers: &[ProviderDescriptor],
) -> Result<WorkflowBindingPlan, FabricContractError> {
    plan.validate()?;

    for (index, resource) in resources.iter().enumerate() {
        resource.validate()?;
        if resources[..index]
            .iter()
            .any(|existing| existing.resource_id == resource.resource_id)
        {
            return Err(FabricContractError::DuplicateId(
                "workflowBinding.resources",
                resource.resource_id.to_string(),
            ));
        }
    }
    for (index, node) in nodes.iter().enumerate() {
        node.validate()?;
        if nodes[..index]
            .iter()
            .any(|existing| existing.node_id == node.node_id)
        {
            return Err(FabricContractError::DuplicateId(
                "workflowBinding.nodes",
                node.node_id.to_string(),
            ));
        }
    }
    for (index, provider) in providers.iter().enumerate() {
        provider.validate()?;
        if providers[..index]
            .iter()
            .any(|existing| existing.provider_id == provider.provider_id)
        {
            return Err(FabricContractError::DuplicateId(
                "workflowBinding.providers",
                provider.provider_id.to_string(),
            ));
        }
        let Some(node) = nodes.iter().find(|node| node.node_id == provider.node_id) else {
            return Err(FabricContractError::InvalidWorkflowBinding(
                "provider references unknown node",
            ));
        };
        if !node.providers.contains(&provider.provider_id) {
            return Err(FabricContractError::InvalidWorkflowBinding(
                "provider is not advertised by its node",
            ));
        }
    }

    let mut bindings = Vec::with_capacity(plan.steps.len());
    for step in &plan.steps {
        let Some(resource) = resources
            .iter()
            .find(|resource| resource.resource_id == step.resource_id)
        else {
            bindings.push(WorkflowStepBinding {
                schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
                step_id: step.step_id.clone(),
                resource_id: step.resource_id.clone(),
                requested_capability_id: step.requested_capability_id.clone(),
                disposition: WorkflowBindingDisposition::Unresolved,
                candidate_node_ids: Vec::new(),
                candidate_provider_ids: Vec::new(),
                selected_node_id: None,
                selected_provider_id: None,
                reason_code: FabricId::parse("reason/workflow-resource-unresolved")?,
                dispatch_started: false,
            });
            continue;
        };

        let mut candidates = providers
            .iter()
            .filter(|provider| {
                provider
                    .capabilities
                    .contains(&step.requested_capability_id)
                    && resource
                        .node_id
                        .as_ref()
                        .is_none_or(|node_id| &provider.node_id == node_id)
                    && step
                        .preferred_provider_id
                        .as_ref()
                        .is_none_or(|preferred| &provider.provider_id == preferred)
            })
            .collect::<Vec<_>>();
        candidates.sort_by(|left, right| left.provider_id.cmp(&right.provider_id));

        let mut candidate_node_ids = candidates
            .iter()
            .map(|provider| provider.node_id.clone())
            .collect::<Vec<_>>();
        candidate_node_ids.sort();
        candidate_node_ids.dedup();
        let candidate_provider_ids = candidates
            .iter()
            .map(|provider| provider.provider_id.clone())
            .collect::<Vec<_>>();

        let (disposition, selected_node_id, selected_provider_id, reason_code) =
            match candidates.as_slice() {
                [] => (
                    WorkflowBindingDisposition::Unresolved,
                    None,
                    None,
                    FabricId::parse(if step.preferred_provider_id.is_some() {
                        "reason/preferred-provider-unavailable"
                    } else {
                        "reason/no-capable-provider"
                    })?,
                ),
                [provider] => (
                    WorkflowBindingDisposition::Resolved,
                    Some(provider.node_id.clone()),
                    Some(provider.provider_id.clone()),
                    FabricId::parse("reason/workflow-binding-resolved")?,
                ),
                _ => (
                    WorkflowBindingDisposition::Ambiguous,
                    None,
                    None,
                    FabricId::parse("reason/multiple-capable-providers")?,
                ),
            };

        let binding = WorkflowStepBinding {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            step_id: step.step_id.clone(),
            resource_id: step.resource_id.clone(),
            requested_capability_id: step.requested_capability_id.clone(),
            disposition,
            candidate_node_ids,
            candidate_provider_ids,
            selected_node_id,
            selected_provider_id,
            reason_code,
            dispatch_started: false,
        };
        binding.validate()?;
        bindings.push(binding);
    }

    let binding_plan = WorkflowBindingPlan {
        schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
        workflow_id: plan.workflow_id.clone(),
        fully_resolved: bindings
            .iter()
            .all(|binding| binding.disposition == WorkflowBindingDisposition::Resolved),
        bindings,
        dispatch_started: false,
    };
    binding_plan.validate()?;
    Ok(binding_plan)
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "camelCase")]
pub struct EvidenceReference {
    pub schema_version: u32,
    pub evidence_id: FabricId,
    pub evidence_kind: FabricId,
    pub digest: String,
    pub producer_id: FabricId,
}

impl EvidenceReference {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        if !is_sha256_digest(&self.digest) {
            return Err(FabricContractError::InvalidDigest);
        }
        Ok(())
    }
}

fn is_sha256_digest(value: &str) -> bool {
    let Some(hex) = value.strip_prefix("sha256:") else {
        return false;
    };
    hex.len() == 64 && hex.bytes().all(|b| b.is_ascii_hexdigit())
}

fn require_schema(schema_version: u32) -> Result<(), FabricContractError> {
    if schema_version != EXECUTION_FABRIC_SCHEMA_VERSION {
        return Err(FabricContractError::UnsupportedSchema(schema_version));
    }
    Ok(())
}

fn require_unique_ids(name: &'static str, values: &[FabricId]) -> Result<(), FabricContractError> {
    for (index, value) in values.iter().enumerate() {
        if values[..index].contains(value) {
            return Err(FabricContractError::DuplicateId(name, value.to_string()));
        }
    }
    Ok(())
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum FabricContractError {
    InvalidId(&'static str),
    UnsupportedSchema(u32),
    EmptySet(&'static str),
    DuplicateId(&'static str, String),
    InvalidLease(&'static str),
    InvalidDigest,
    InvalidControllerProposal(&'static str),
    InvalidWorkflowPlan(&'static str),
    InvalidWorkflowBinding(&'static str),
}

impl fmt::Display for FabricContractError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidId(message) => write!(f, "invalid FabricId: {message}"),
            Self::UnsupportedSchema(version) => {
                write!(f, "unsupported execution-fabric schema version: {version}")
            }
            Self::EmptySet(name) => write!(f, "{name} must not be empty"),
            Self::DuplicateId(name, id) => write!(f, "{name} contains duplicate id {id}"),
            Self::InvalidLease(message) => write!(f, "invalid authority lease: {message}"),
            Self::InvalidDigest => write!(f, "evidence digest must be sha256:<64 hex characters>"),
            Self::InvalidControllerProposal(message) => {
                write!(f, "invalid controller action proposal: {message}")
            }
            Self::InvalidWorkflowPlan(message) => {
                write!(f, "invalid workflow plan: {message}")
            }
            Self::InvalidWorkflowBinding(message) => {
                write!(f, "invalid workflow binding: {message}")
            }
        }
    }
}

impl std::error::Error for FabricContractError {}

#[cfg(test)]
mod tests {
    use super::*;

    fn id(value: &str) -> FabricId {
        FabricId::parse(value).unwrap()
    }

    #[test]
    fn fabric_id_rejects_ambiguous_or_unsafe_shapes() {
        for value in [
            "",
            "/windows",
            "windows/",
            "windows//service",
            "windows service",
            "x\\\\y",
        ] {
            assert!(FabricId::parse(value).is_err(), "{value:?} must fail");
        }
        assert_eq!(
            FabricId::parse("service/windows/OrdivonLifeboat")
                .unwrap()
                .as_str(),
            "service/windows/OrdivonLifeboat"
        );
        assert!(serde_json::from_str::<FabricId>(r#""windows service""#).is_err());
    }

    #[test]
    fn authority_lease_keeps_dimensions_orthogonal() {
        let lease = AuthorityLease {
            schema_version: 1,
            lease_id: id("lease/security-lab/001"),
            authority: AuthorityVector {
                schema_version: 1,
                principal_id: id("agent/windows/red/03"),
                trust_domain: id("trust/ordivon-local"),
                resource_scope: id("lab/windows-target-01"),
                capabilities: vec![id("service.stop"), id("process.terminate")],
                os_authority: id("windows/system"),
                mode: AuthorityMode::SecurityLab,
                conflict_mode: ConflictMode::AdversarialLab,
                enforcement: AuthorityEnforcement::Permissive,
                budget_id: Some(id("budget/security-lab/default")),
                evidence_policy_id: Some(id("evidence/security-campaign/full")),
            },
            issued_at_ms: 100,
            expires_at_ms: 200,
            revoked_at_ms: None,
        };
        lease.validate().unwrap();
        assert!(lease.is_active_at(100));
        assert!(lease.is_active_at(199));
        assert!(!lease.is_active_at(200));
        assert_eq!(lease.authority.os_authority.as_str(), "windows/system");
        assert_eq!(lease.authority.mode, AuthorityMode::SecurityLab);
        assert_eq!(lease.authority.conflict_mode, ConflictMode::AdversarialLab);
    }

    #[test]
    fn provider_descriptor_requires_capability_membership() {
        let provider = ProviderDescriptor {
            schema_version: 1,
            provider_id: id("provider/windows/job-object"),
            node_id: id("runtime/windows-main"),
            platform: FabricPlatform::Windows,
            capabilities: vec![],
        };
        assert_eq!(
            provider.validate(),
            Err(FabricContractError::EmptySet("capabilities"))
        );
    }

    #[test]
    fn evidence_reference_requires_content_digest_shape() {
        let value = EvidenceReference {
            schema_version: 1,
            evidence_id: id("evidence/attempt/001"),
            evidence_kind: id("runtime/terminal-evidence"),
            digest: format!("sha256:{}", "a".repeat(64)),
            producer_id: id("runtime/windows-main"),
        };
        value.validate().unwrap();

        let mut bad = value;
        bad.digest = "sha256:not-a-digest".into();
        assert_eq!(bad.validate(), Err(FabricContractError::InvalidDigest));
    }

    #[test]
    fn authority_shadow_is_descriptive_and_never_self_enforcing() {
        let candidate = AuthorityEffectCandidate {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            principal_id: id("agent/windows/red-01"),
            trust_domain: id("ordivon.local"),
            resource_scope: id("machine/windows-main"),
            capability_id: id("capability/windows/service-stop"),
            os_authority: id("windows/system"),
            mode: AuthorityMode::SecurityLab,
            conflict_mode: ConflictMode::AdversarialLab,
        };
        let lease = AuthorityLease {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            lease_id: id("lease/security-lab/red-01"),
            authority: AuthorityVector {
                schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
                principal_id: candidate.principal_id.clone(),
                trust_domain: candidate.trust_domain.clone(),
                resource_scope: candidate.resource_scope.clone(),
                capabilities: vec![candidate.capability_id.clone()],
                os_authority: candidate.os_authority.clone(),
                mode: candidate.mode,
                conflict_mode: candidate.conflict_mode,
                enforcement: AuthorityEnforcement::Shadow,
                budget_id: None,
                evidence_policy_id: None,
            },
            issued_at_ms: 100,
            expires_at_ms: 1_000,
            revoked_at_ms: None,
        };

        let decision = evaluate_authority_shadow(&candidate, &[lease], 500).unwrap();
        assert!(decision.shadow_only);
        assert!(decision.would_allow);
        assert_eq!(
            decision.conflict,
            AuthorityConflictClassification::AdversarialOverlap
        );
        assert_eq!(
            decision.matching_lease_ids,
            vec![id("lease/security-lab/red-01")]
        );
        assert_eq!(
            decision.overlapping_lease_ids,
            vec![id("lease/security-lab/red-01")]
        );
    }

    #[test]
    fn authority_shadow_classifies_exclusive_overlap_without_granting_candidate() {
        let candidate = AuthorityEffectCandidate {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            principal_id: id("agent/windows/maintenance-02"),
            trust_domain: id("ordivon.local"),
            resource_scope: id("distro/archlinux"),
            capability_id: id("capability/wsl/terminate"),
            os_authority: id("windows/administrator"),
            mode: AuthorityMode::Maintenance,
            conflict_mode: ConflictMode::ExclusiveWrite,
        };
        let existing = AuthorityLease {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            lease_id: id("lease/maintenance/owner-01"),
            authority: AuthorityVector {
                schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
                principal_id: id("agent/windows/maintenance-01"),
                trust_domain: candidate.trust_domain.clone(),
                resource_scope: candidate.resource_scope.clone(),
                capabilities: vec![candidate.capability_id.clone()],
                os_authority: candidate.os_authority.clone(),
                mode: candidate.mode,
                conflict_mode: ConflictMode::ExclusiveWrite,
                enforcement: AuthorityEnforcement::Shadow,
                budget_id: None,
                evidence_policy_id: None,
            },
            issued_at_ms: 100,
            expires_at_ms: 1_000,
            revoked_at_ms: None,
        };

        let decision = evaluate_authority_shadow(&candidate, &[existing], 500).unwrap();
        assert!(decision.shadow_only);
        assert!(!decision.would_allow);
        assert_eq!(
            decision.conflict,
            AuthorityConflictClassification::ExclusiveOverlap
        );
        assert!(decision.matching_lease_ids.is_empty());
        assert_eq!(
            decision.overlapping_lease_ids,
            vec![id("lease/maintenance/owner-01")]
        );
    }

    #[test]
    fn authority_shadow_ignores_expired_or_different_resource_leases() {
        let candidate = AuthorityEffectCandidate {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            principal_id: id("agent/linux/blue-01"),
            trust_domain: id("ordivon.local"),
            resource_scope: id("service/linux/runtime"),
            capability_id: id("capability/service/start"),
            os_authority: id("linux/root"),
            mode: AuthorityMode::Recovery,
            conflict_mode: ConflictMode::ExclusiveWrite,
        };
        let expired = AuthorityLease {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            lease_id: id("lease/expired"),
            authority: AuthorityVector {
                schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
                principal_id: candidate.principal_id.clone(),
                trust_domain: candidate.trust_domain.clone(),
                resource_scope: candidate.resource_scope.clone(),
                capabilities: vec![candidate.capability_id.clone()],
                os_authority: candidate.os_authority.clone(),
                mode: candidate.mode,
                conflict_mode: candidate.conflict_mode,
                enforcement: AuthorityEnforcement::Shadow,
                budget_id: None,
                evidence_policy_id: None,
            },
            issued_at_ms: 10,
            expires_at_ms: 20,
            revoked_at_ms: None,
        };
        let other_resource = AuthorityLease {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            lease_id: id("lease/other-resource"),
            authority: AuthorityVector {
                schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
                principal_id: candidate.principal_id.clone(),
                trust_domain: candidate.trust_domain.clone(),
                resource_scope: id("service/linux/host"),
                capabilities: vec![candidate.capability_id.clone()],
                os_authority: candidate.os_authority.clone(),
                mode: candidate.mode,
                conflict_mode: candidate.conflict_mode,
                enforcement: AuthorityEnforcement::Shadow,
                budget_id: None,
                evidence_policy_id: None,
            },
            issued_at_ms: 100,
            expires_at_ms: 1_000,
            revoked_at_ms: None,
        };

        let decision =
            evaluate_authority_shadow(&candidate, &[expired, other_resource], 500).unwrap();
        assert!(!decision.would_allow);
        assert_eq!(decision.conflict, AuthorityConflictClassification::None);
        assert!(decision.matching_lease_ids.is_empty());
        assert!(decision.overlapping_lease_ids.is_empty());
    }

    #[test]
    fn provider_health_preview_reports_converged_without_acting() {
        let observation = ProviderHealthObservation {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            controller_id: id("controller/provider-health/linux"),
            resource_id: id("execution-target/node/local-linux"),
            provider_id: Some(id("provider/node/local-linux-runner-v1")),
            desired_available: true,
            observed: ProviderAvailability::Available,
            reason_code: id("reason/provider-available"),
        };
        let preview = preview_provider_health(&observation).unwrap();
        assert_eq!(
            preview.disposition,
            ControllerReconcileDisposition::Converged
        );
        assert_eq!(preview.desired_state, id("state/provider-available"));
        assert_eq!(preview.observed_state, id("state/provider-available"));
    }

    #[test]
    fn provider_health_preview_reports_action_required_for_unavailable_provider() {
        let observation = ProviderHealthObservation {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            controller_id: id("controller/provider-health/windows"),
            resource_id: id("execution-target/node/windows-native"),
            provider_id: None,
            desired_available: true,
            observed: ProviderAvailability::Unavailable,
            reason_code: id("reason/execution-provider-unavailable"),
        };
        let preview = preview_provider_health(&observation).unwrap();
        assert_eq!(
            preview.disposition,
            ControllerReconcileDisposition::ActionRequired
        );
        assert_eq!(preview.observed_state, id("state/provider-unavailable"));
    }

    #[test]
    fn provider_health_preview_preserves_unknown_observation_as_incomplete() {
        let observation = ProviderHealthObservation {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            controller_id: id("controller/provider-health/unknown"),
            resource_id: id("execution-target/node/unknown"),
            provider_id: None,
            desired_available: true,
            observed: ProviderAvailability::Unknown,
            reason_code: id("reason/provider-observation-incomplete"),
        };
        let preview = preview_provider_health(&observation).unwrap();
        assert_eq!(
            preview.disposition,
            ControllerReconcileDisposition::ObservationIncomplete
        );
        assert_eq!(preview.observed_state, id("state/provider-unknown"));
    }

    #[test]
    fn provider_health_plan_proposes_recovery_without_dispatching() {
        let observation = ProviderHealthObservation {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            controller_id: id("controller/provider-health/windows"),
            resource_id: id("execution-target/windows-main/windows-native"),
            provider_id: Some(id("provider/windows-main/windows-native-launcher-v1")),
            desired_available: true,
            observed: ProviderAvailability::Unavailable,
            reason_code: id("reason/execution-provider-unavailable"),
        };
        let plan = plan_provider_health(&observation).unwrap();
        assert_eq!(
            plan.preview.disposition,
            ControllerReconcileDisposition::ActionRequired
        );
        let action = plan
            .action
            .expect("action required should produce proposal");
        assert_eq!(
            action.requested_capability_id,
            id("capability/provider/recover")
        );
        assert_eq!(action.authority_mode, AuthorityMode::Recovery);
        assert_eq!(action.conflict_mode, ConflictMode::ExclusiveWrite);
        assert!(!action.effect_dispatched);
    }

    #[test]
    fn provider_health_plan_emits_no_action_when_converged_or_unknown() {
        for observed in [
            ProviderAvailability::Available,
            ProviderAvailability::Unknown,
        ] {
            let observation = ProviderHealthObservation {
                schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
                controller_id: id("controller/provider-health/test"),
                resource_id: id("execution-target/node/test"),
                provider_id: None,
                desired_available: true,
                observed,
                reason_code: id("reason/provider-state"),
            };
            let plan = plan_provider_health(&observation).unwrap();
            assert!(plan.action.is_none());
        }
    }

    #[test]
    fn controller_action_proposal_cannot_claim_dispatch() {
        let action = ControllerActionProposal {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            controller_id: id("controller/provider-health/test"),
            resource_id: id("execution-target/node/test"),
            requested_capability_id: id("capability/provider/recover"),
            preferred_provider_id: None,
            authority_mode: AuthorityMode::Recovery,
            conflict_mode: ConflictMode::ExclusiveWrite,
            reason_code: id("reason/provider-unavailable"),
            effect_dispatched: true,
        };
        assert!(matches!(
            action.validate(),
            Err(FabricContractError::InvalidControllerProposal(_))
        ));
    }

    fn workflow_step(
        step_id: &str,
        kind: WorkflowStepKind,
        resource_id: &str,
        capability_id: &str,
        depends_on: &[&str],
    ) -> WorkflowStep {
        WorkflowStep {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            step_id: id(step_id),
            kind,
            resource_id: id(resource_id),
            requested_capability_id: id(capability_id),
            preferred_provider_id: None,
            authority_mode: AuthorityMode::Maintenance,
            conflict_mode: ConflictMode::ExclusiveWrite,
            depends_on: depends_on.iter().map(|value| id(value)).collect(),
            evidence_policy_id: Some(id("evidence/workflow-r1")),
            compensates_step_id: None,
            effect_dispatched: false,
        }
    }

    #[test]
    fn workflow_plan_expresses_wsl_recovery_without_claiming_execution() {
        let plan = WorkflowPlan {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            workflow_id: id("workflow/wsl-control-plane-recovery-r1"),
            owner_id: id("controller/recovery/windows-edge"),
            steps: vec![
                workflow_step(
                    "step/probe-wsl",
                    WorkflowStepKind::Observe,
                    "distro/archlinux",
                    "capability/wsl/probe",
                    &[],
                ),
                workflow_step(
                    "step/probe-services",
                    WorkflowStepKind::Gate,
                    "service/linux/control-plane",
                    "capability/service/probe",
                    &["step/probe-wsl"],
                ),
                workflow_step(
                    "step/ensure-services",
                    WorkflowStepKind::Recover,
                    "service/linux/control-plane",
                    "capability/service/start",
                    &["step/probe-services"],
                ),
                workflow_step(
                    "step/verify-runtime-health",
                    WorkflowStepKind::Verify,
                    "runtime/linux-archlinux",
                    "capability/runtime/health",
                    &["step/ensure-services"],
                ),
            ],
            execution_started: false,
        };
        plan.validate().unwrap();
        assert!(plan.steps.iter().all(|step| !step.effect_dispatched));
    }

    #[test]
    fn workflow_plan_expresses_compact_safety_gates_as_dependencies() {
        let plan = WorkflowPlan {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            workflow_id: id("workflow/d-drive-vhd-compact-r2"),
            owner_id: id("controller/maintenance/windows-edge"),
            steps: vec![
                workflow_step(
                    "step/fence-admission",
                    WorkflowStepKind::Gate,
                    "runtime/linux-archlinux",
                    "capability/runtime/drain",
                    &[],
                ),
                workflow_step(
                    "step/verify-health",
                    WorkflowStepKind::Gate,
                    "runtime/linux-archlinux",
                    "capability/runtime/doctor",
                    &["step/fence-admission"],
                ),
                workflow_step(
                    "step/validate-authorization",
                    WorkflowStepKind::Gate,
                    "storage/d-drive/ext4-vhdx",
                    "capability/authority/validate",
                    &["step/verify-health"],
                ),
                workflow_step(
                    "step/trim-filesystem",
                    WorkflowStepKind::Act,
                    "filesystem/linux-root",
                    "capability/storage/trim",
                    &["step/validate-authorization"],
                ),
                workflow_step(
                    "step/terminate-wsl",
                    WorkflowStepKind::Act,
                    "distro/archlinux",
                    "capability/wsl/terminate",
                    &["step/trim-filesystem"],
                ),
                workflow_step(
                    "step/exclusive-open",
                    WorkflowStepKind::Gate,
                    "storage/d-drive/ext4-vhdx",
                    "capability/storage/exclusive-open",
                    &["step/terminate-wsl"],
                ),
                workflow_step(
                    "step/compact-vhd",
                    WorkflowStepKind::Act,
                    "storage/d-drive/ext4-vhdx",
                    "capability/storage/compact",
                    &["step/exclusive-open"],
                ),
                workflow_step(
                    "step/recover-control-plane",
                    WorkflowStepKind::Recover,
                    "runtime/linux-archlinux",
                    "capability/runtime/recover",
                    &["step/compact-vhd"],
                ),
                workflow_step(
                    "step/post-doctor",
                    WorkflowStepKind::Verify,
                    "runtime/linux-archlinux",
                    "capability/runtime/doctor",
                    &["step/recover-control-plane"],
                ),
            ],
            execution_started: false,
        };
        plan.validate().unwrap();
        assert_eq!(plan.steps.len(), 9);
    }

    #[test]
    fn workflow_plan_rejects_cycles_unknown_dependencies_and_dispatch_claims() {
        let mut cycle = WorkflowPlan {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            workflow_id: id("workflow/cycle"),
            owner_id: id("controller/test"),
            steps: vec![
                workflow_step(
                    "step/a",
                    WorkflowStepKind::Act,
                    "resource/a",
                    "capability/a",
                    &["step/b"],
                ),
                workflow_step(
                    "step/b",
                    WorkflowStepKind::Verify,
                    "resource/b",
                    "capability/b",
                    &["step/a"],
                ),
            ],
            execution_started: false,
        };
        assert!(matches!(
            cycle.validate(),
            Err(FabricContractError::InvalidWorkflowPlan(_))
        ));

        cycle.steps[0].depends_on = vec![id("step/missing")];
        cycle.steps[1].depends_on.clear();
        assert!(matches!(
            cycle.validate(),
            Err(FabricContractError::InvalidWorkflowPlan(_))
        ));

        cycle.steps[0].depends_on.clear();
        cycle.steps[0].effect_dispatched = true;
        assert!(matches!(
            cycle.validate(),
            Err(FabricContractError::InvalidWorkflowPlan(_))
        ));
    }

    fn binding_fixture_plan(preferred_provider_id: Option<&str>) -> WorkflowPlan {
        let mut step = workflow_step(
            "step/do-thing",
            WorkflowStepKind::Act,
            "resource/test",
            "capability/test/do",
            &[],
        );
        step.preferred_provider_id = preferred_provider_id.map(id);
        WorkflowPlan {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            workflow_id: id("workflow/binding-fixture"),
            owner_id: id("controller/binding-fixture"),
            steps: vec![step],
            execution_started: false,
        }
    }

    fn binding_fixture_resource(node_id: Option<&str>) -> ResourceDescriptor {
        ResourceDescriptor {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            resource_id: id("resource/test"),
            resource_kind: id("resource-kind/test"),
            node_id: node_id.map(id),
            conflict_domains: Vec::new(),
        }
    }

    fn binding_fixture_node(provider_ids: &[&str]) -> NodeDescriptor {
        NodeDescriptor {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            node_id: id("runtime/test-node"),
            platform: FabricPlatform::Linux,
            native_control_plane: true,
            trust_domain: id("ordivon.local"),
            providers: provider_ids.iter().map(|value| id(value)).collect(),
            capabilities: vec![id("capability/test/do")],
            authority_contexts: vec![id("linux/root")],
        }
    }

    fn binding_fixture_provider(provider_id: &str) -> ProviderDescriptor {
        ProviderDescriptor {
            schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
            provider_id: id(provider_id),
            node_id: id("runtime/test-node"),
            platform: FabricPlatform::Linux,
            capabilities: vec![id("capability/test/do")],
        }
    }

    #[test]
    fn workflow_binding_resolves_only_unique_provider_without_dispatch() {
        let plan = binding_fixture_plan(None);
        let provider = binding_fixture_provider("provider/test/a");
        let binding = resolve_workflow_bindings(
            &plan,
            &[binding_fixture_resource(Some("runtime/test-node"))],
            &[binding_fixture_node(&["provider/test/a"])],
            &[provider],
        )
        .unwrap();
        assert!(binding.fully_resolved);
        assert!(!binding.dispatch_started);
        assert_eq!(
            binding.bindings[0].disposition,
            WorkflowBindingDisposition::Resolved
        );
        assert_eq!(
            binding.bindings[0].selected_provider_id,
            Some(id("provider/test/a"))
        );
        assert!(!binding.bindings[0].dispatch_started);
    }

    #[test]
    fn workflow_binding_leaves_multiple_capable_providers_ambiguous() {
        let plan = binding_fixture_plan(None);
        let binding = resolve_workflow_bindings(
            &plan,
            &[binding_fixture_resource(Some("runtime/test-node"))],
            &[binding_fixture_node(&[
                "provider/test/a",
                "provider/test/b",
            ])],
            &[
                binding_fixture_provider("provider/test/b"),
                binding_fixture_provider("provider/test/a"),
            ],
        )
        .unwrap();
        assert!(!binding.fully_resolved);
        assert_eq!(
            binding.bindings[0].disposition,
            WorkflowBindingDisposition::Ambiguous
        );
        assert_eq!(
            binding.bindings[0].candidate_provider_ids,
            vec![id("provider/test/a"), id("provider/test/b")]
        );
        assert!(binding.bindings[0].selected_provider_id.is_none());
    }

    #[test]
    fn workflow_binding_preferred_provider_is_exact_not_a_hint() {
        let resolved = resolve_workflow_bindings(
            &binding_fixture_plan(Some("provider/test/b")),
            &[binding_fixture_resource(Some("runtime/test-node"))],
            &[binding_fixture_node(&[
                "provider/test/a",
                "provider/test/b",
            ])],
            &[
                binding_fixture_provider("provider/test/a"),
                binding_fixture_provider("provider/test/b"),
            ],
        )
        .unwrap();
        assert!(resolved.fully_resolved);
        assert_eq!(
            resolved.bindings[0].selected_provider_id,
            Some(id("provider/test/b"))
        );

        let unresolved = resolve_workflow_bindings(
            &binding_fixture_plan(Some("provider/test/missing")),
            &[binding_fixture_resource(Some("runtime/test-node"))],
            &[binding_fixture_node(&["provider/test/a"])],
            &[binding_fixture_provider("provider/test/a")],
        )
        .unwrap();
        assert_eq!(
            unresolved.bindings[0].disposition,
            WorkflowBindingDisposition::Unresolved
        );
        assert_eq!(
            unresolved.bindings[0].reason_code,
            id("reason/preferred-provider-unavailable")
        );
    }

    #[test]
    fn workflow_binding_reports_missing_resource_or_capability_unresolved() {
        let missing_resource =
            resolve_workflow_bindings(&binding_fixture_plan(None), &[], &[], &[]).unwrap();
        assert_eq!(
            missing_resource.bindings[0].reason_code,
            id("reason/workflow-resource-unresolved")
        );

        let missing_capability = resolve_workflow_bindings(
            &binding_fixture_plan(None),
            &[binding_fixture_resource(Some("runtime/test-node"))],
            &[binding_fixture_node(&["provider/test/other"])],
            &[ProviderDescriptor {
                schema_version: EXECUTION_FABRIC_SCHEMA_VERSION,
                provider_id: id("provider/test/other"),
                node_id: id("runtime/test-node"),
                platform: FabricPlatform::Linux,
                capabilities: vec![id("capability/test/other")],
            }],
        )
        .unwrap();
        assert_eq!(
            missing_capability.bindings[0].reason_code,
            id("reason/no-capable-provider")
        );
    }

    #[test]
    fn workflow_binding_rejects_provider_not_advertised_by_node() {
        let error = resolve_workflow_bindings(
            &binding_fixture_plan(None),
            &[binding_fixture_resource(Some("runtime/test-node"))],
            &[binding_fixture_node(&[])],
            &[binding_fixture_provider("provider/test/a")],
        )
        .unwrap_err();
        assert!(matches!(
            error,
            FabricContractError::InvalidWorkflowBinding(_)
        ));
    }

    #[test]
    fn contracts_round_trip_without_execution_semantics() {
        let descriptor = NodeDescriptor {
            schema_version: 1,
            node_id: id("runtime/linux-archlinux"),
            platform: FabricPlatform::Linux,
            native_control_plane: true,
            trust_domain: id("trust/ordivon-local"),
            providers: vec![id("provider/linux/systemd")],
            capabilities: vec![id("service.start"), id("service.stop")],
            authority_contexts: vec![id("linux/user"), id("linux/root")],
        };
        descriptor.validate().unwrap();

        let json = serde_json::to_string(&descriptor).unwrap();
        let restored: NodeDescriptor = serde_json::from_str(&json).unwrap();
        assert_eq!(restored, descriptor);
    }
}
