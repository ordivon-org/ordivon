use serde::{Deserialize, Serialize};

use crate::digest::{compare_rfc3339, parse_rfc3339};
use crate::errors::KernelError;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Origin {
    HumanWritten,
    AiWritten,
    SystemObserved,
    SystemDerived,
    HumanAttested,
    ExternalAttested,
}

impl Origin {
    pub fn can_emit_observed_event(&self) -> bool {
        matches!(self, Self::SystemObserved | Self::ExternalAttested)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "PascalCase")]
pub enum Verdict {
    ExactMatch,
    Under,
    Over,
    Mis,
    Unverifiable,
    DeclarationInvalid,
    SystemError,
}

impl Verdict {
    pub fn priority(&self) -> u8 {
        match self {
            Self::DeclarationInvalid => 70,
            Self::SystemError => 60,
            Self::Unverifiable => 50,
            Self::Mis => 40,
            Self::Over => 30,
            Self::Under => 20,
            Self::ExactMatch => 10,
        }
    }

    pub fn is_blocking(&self) -> bool {
        !matches!(self, Self::ExactMatch)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Hash, PartialEq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ActionClass {
    ReadResource,
    CallToolReadonly,
    CallToolMutating,
    SendMessage,
    UpdateRecord,
    DeleteRecord,
    ExecuteCode,
    RequestApproval,
    ApplyApproval,
    StateTransition,
}

impl ActionClass {
    pub fn all() -> Vec<Self> {
        vec![
            Self::ReadResource,
            Self::CallToolReadonly,
            Self::CallToolMutating,
            Self::SendMessage,
            Self::UpdateRecord,
            Self::DeleteRecord,
            Self::ExecuteCode,
            Self::RequestApproval,
            Self::ApplyApproval,
            Self::StateTransition,
        ]
    }

    pub fn is_effectful(&self) -> bool {
        matches!(
            self,
            Self::CallToolMutating
                | Self::SendMessage
                | Self::UpdateRecord
                | Self::DeleteRecord
                | Self::ExecuteCode
                | Self::ApplyApproval
                | Self::StateTransition
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum RiskTier {
    R0,
    R1,
    R2,
    R3,
    R4,
    R5,
}

impl RiskTier {
    pub fn requires_authority(&self) -> bool {
        !matches!(self, Self::R0 | Self::R1)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Cardinality {
    pub min: u32,
    pub max: u32,
}

impl Cardinality {
    pub fn validate(&self) -> Result<(), KernelError> {
        if self.min > self.max {
            return Err(KernelError::InvalidDeclaration(
                "cardinality min cannot exceed max".to_string(),
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum OrderConstraint {
    None,
    DeclaredOrder,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ApprovalMode {
    None,
    Human,
    Policy,
    BreakGlass,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "PascalCase")]
pub enum ObservationStatus {
    Acked,
    Observed,
    Applied,
    Succeeded,
    Partial,
    Unknown,
    Failed,
}

impl ObservationStatus {
    pub fn is_success_evidence(&self) -> bool {
        matches!(self, Self::Observed | Self::Applied | Self::Succeeded)
    }

    pub fn is_unverifiable(&self) -> bool {
        matches!(self, Self::Acked | Self::Unknown)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "ActionSpecDraft")]
pub struct ActionSpec {
    pub(crate) action_class: ActionClass,
    pub(crate) target_ref: String,
    pub(crate) cardinality: Cardinality,
    pub(crate) order_constraint: OrderConstraint,
    pub(crate) approval_mode: ApprovalMode,
    pub(crate) success_predicate: String,
    #[serde(default)]
    pub(crate) authority_refs: Vec<String>,
    #[serde(default)]
    pub(crate) idempotency_key: Option<String>,
    #[serde(default)]
    pub(crate) expected_payload_hash: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ActionSpecDraft {
    pub action_class: ActionClass,
    pub target_ref: String,
    pub cardinality: Cardinality,
    pub order_constraint: OrderConstraint,
    pub approval_mode: ApprovalMode,
    pub success_predicate: String,
    #[serde(default)]
    pub authority_refs: Vec<String>,
    #[serde(default)]
    pub idempotency_key: Option<String>,
    #[serde(default)]
    pub expected_payload_hash: Option<String>,
}

impl ActionSpec {
    pub fn new(
        action_class: ActionClass,
        target_ref: impl Into<String>,
        approval_mode: ApprovalMode,
        idempotency_key: impl Into<String>,
    ) -> Self {
        Self {
            action_class,
            target_ref: target_ref.into(),
            cardinality: Cardinality { min: 1, max: 1 },
            order_constraint: OrderConstraint::DeclaredOrder,
            approval_mode,
            success_predicate: "mock action reached success observation".to_string(),
            authority_refs: Vec::new(),
            idempotency_key: Some(idempotency_key.into()),
            expected_payload_hash: None,
        }
    }

    pub fn validate(&self) -> Result<(), KernelError> {
        if self.target_ref.trim().is_empty() {
            return Err(KernelError::InvalidDeclaration(
                "action targetRef cannot be empty".to_string(),
            ));
        }
        if self.success_predicate.trim().is_empty() {
            return Err(KernelError::InvalidDeclaration(
                "action successPredicate cannot be empty".to_string(),
            ));
        }
        self.cardinality.validate()
    }

    pub fn action_class(&self) -> &ActionClass {
        &self.action_class
    }

    pub fn target_ref(&self) -> &str {
        &self.target_ref
    }

    pub fn cardinality(&self) -> &Cardinality {
        &self.cardinality
    }

    pub fn order_constraint(&self) -> &OrderConstraint {
        &self.order_constraint
    }

    pub fn approval_mode(&self) -> &ApprovalMode {
        &self.approval_mode
    }

    pub fn success_predicate(&self) -> &str {
        &self.success_predicate
    }

    pub fn authority_refs(&self) -> &[String] {
        &self.authority_refs
    }

    pub fn idempotency_key(&self) -> Option<&str> {
        self.idempotency_key.as_deref()
    }

    pub fn expected_payload_hash(&self) -> Option<&str> {
        self.expected_payload_hash.as_deref()
    }

    pub fn with_authority_refs(mut self, authority_refs: Vec<String>) -> Self {
        self.authority_refs = authority_refs;
        self
    }

    pub fn with_expected_payload_hash(mut self, expected_payload_hash: impl Into<String>) -> Self {
        self.expected_payload_hash = Some(expected_payload_hash.into());
        self
    }
}

impl TryFrom<ActionSpecDraft> for ActionSpec {
    type Error = KernelError;

    fn try_from(draft: ActionSpecDraft) -> Result<Self, Self::Error> {
        let action = Self {
            action_class: draft.action_class,
            target_ref: draft.target_ref,
            cardinality: draft.cardinality,
            order_constraint: draft.order_constraint,
            approval_mode: draft.approval_mode,
            success_predicate: draft.success_predicate,
            authority_refs: draft.authority_refs,
            idempotency_key: draft.idempotency_key,
            expected_payload_hash: draft.expected_payload_hash,
        };
        action.validate()?;
        Ok(action)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Intent {
    pub(crate) intent_id: String,
    pub(crate) requester: String,
    pub(crate) scope: Vec<String>,
    pub(crate) risk_tier: RiskTier,
    pub(crate) trace_id: String,
    pub(crate) created_at: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "ObligationDraft")]
pub struct Obligation {
    pub(crate) obligation_id: String,
    pub(crate) intent_id: String,
    pub(crate) declared_actions: Vec<ActionSpec>,
    pub(crate) declaration_hash: String,
    pub(crate) expires_at: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ObligationDraft {
    pub obligation_id: String,
    pub intent_id: String,
    pub declared_actions: Vec<ActionSpec>,
    pub declaration_hash: String,
    pub expires_at: String,
}

impl Obligation {
    pub fn validate_at(&self, now: &str) -> Result<(), KernelError> {
        if self.declared_actions.is_empty() {
            return Err(KernelError::InvalidDeclaration(
                "obligation must declare at least one action".to_string(),
            ));
        }
        if compare_rfc3339(now, &self.expires_at)? != std::cmp::Ordering::Less {
            return Err(KernelError::InvalidDeclaration(
                "obligation is expired".to_string(),
            ));
        }
        for action in &self.declared_actions {
            action.validate()?;
        }
        Ok(())
    }

    pub fn obligation_id(&self) -> &str {
        &self.obligation_id
    }

    pub fn intent_id(&self) -> &str {
        &self.intent_id
    }

    pub fn declared_actions(&self) -> &[ActionSpec] {
        &self.declared_actions
    }

    pub fn declaration_hash(&self) -> &str {
        &self.declaration_hash
    }

    pub fn expires_at(&self) -> &str {
        &self.expires_at
    }
}

impl TryFrom<ObligationDraft> for Obligation {
    type Error = KernelError;

    fn try_from(draft: ObligationDraft) -> Result<Self, Self::Error> {
        if draft.obligation_id.trim().is_empty()
            || draft.intent_id.trim().is_empty()
            || draft.declaration_hash.trim().is_empty()
        {
            return Err(KernelError::InvalidDeclaration(
                "obligation draft has empty required fields".to_string(),
            ));
        }
        parse_rfc3339(&draft.expires_at)?;
        let obligation = Self {
            obligation_id: draft.obligation_id,
            intent_id: draft.intent_id,
            declared_actions: draft.declared_actions,
            declaration_hash: draft.declaration_hash,
            expires_at: draft.expires_at,
        };
        if obligation.declared_actions.is_empty() {
            return Err(KernelError::InvalidDeclaration(
                "obligation must declare at least one action".to_string(),
            ));
        }
        for action in &obligation.declared_actions {
            action.validate()?;
        }
        Ok(obligation)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct Provenance {
    pub input_refs: Vec<String>,
    pub collector: String,
    pub digest: String,
    #[serde(default)]
    pub signature_refs: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BaseGovernanceObject {
    pub id: String,
    pub object_type: String,
    pub schema_version: String,
    pub origin: Origin,
    pub created_at: String,
    pub created_by: String,
    pub provenance: Provenance,
    pub state: String,
    pub digest: String,
    #[serde(default)]
    pub signature_refs: Vec<String>,
    pub retention_class: String,
}
