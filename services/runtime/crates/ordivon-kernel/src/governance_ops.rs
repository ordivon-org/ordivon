use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::HashMap;

use crate::types::{ActionClass, Verdict};

pub const COMPARATOR_ISSUER: &str = "ordivon-comparator";

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "PascalCase")]
pub enum SideEffectStatus {
    Requested,
    Authorized,
    Dispatched,
    Acked,
    Observed,
    Applied,
    Succeeded,
    Partial,
    Unknown,
    Failed,
    Compensating,
    Compensated,
    Irreversible,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SideEffectRecord {
    pub action_class: ActionClass,
    pub target_ref: String,
    pub status: SideEffectStatus,
    pub idempotency_key: String,
}

impl SideEffectRecord {
    pub fn acked(
        action_class: ActionClass,
        target_ref: impl Into<String>,
        idempotency_key: impl Into<String>,
    ) -> Self {
        Self {
            action_class,
            target_ref: target_ref.into(),
            status: SideEffectStatus::Acked,
            idempotency_key: idempotency_key.into(),
        }
    }

    pub fn is_success_verdict_source(&self) -> bool {
        matches!(
            self.status,
            SideEffectStatus::Observed | SideEffectStatus::Applied | SideEffectStatus::Succeeded
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "ReceiptDraft")]
pub struct Receipt {
    pub(crate) receipt_id: String,
    pub(crate) intent_id: String,
    pub(crate) obligation_id: String,
    pub(crate) verdict: Verdict,
    pub(crate) observed_event_refs: Vec<String>,
    pub(crate) state_transitions: Vec<String>,
    pub(crate) debt_refs: Vec<String>,
    pub(crate) issued_by: String,
    pub(crate) issued_at: String,
    pub(crate) comparator_digest: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ReceiptDraft {
    pub receipt_id: String,
    pub intent_id: String,
    pub obligation_id: String,
    pub verdict: Verdict,
    pub observed_event_refs: Vec<String>,
    pub state_transitions: Vec<String>,
    pub debt_refs: Vec<String>,
    pub issued_by: String,
    pub issued_at: String,
    pub comparator_digest: String,
}

impl Receipt {
    pub fn validate_comparator_issued(&self) -> Result<(), GovernanceOpsError> {
        if self.issued_by != COMPARATOR_ISSUER || self.comparator_digest.trim().is_empty() {
            return Err(GovernanceOpsError::ReceiptNotComparatorIssued);
        }
        Ok(())
    }

    pub fn receipt_id(&self) -> &str {
        &self.receipt_id
    }

    pub fn verdict(&self) -> &Verdict {
        &self.verdict
    }

    pub fn debt_refs(&self) -> &[String] {
        &self.debt_refs
    }
}

impl TryFrom<ReceiptDraft> for Receipt {
    type Error = GovernanceOpsError;

    fn try_from(draft: ReceiptDraft) -> Result<Self, Self::Error> {
        let receipt = Self {
            receipt_id: draft.receipt_id,
            intent_id: draft.intent_id,
            obligation_id: draft.obligation_id,
            verdict: draft.verdict,
            observed_event_refs: draft.observed_event_refs,
            state_transitions: draft.state_transitions,
            debt_refs: draft.debt_refs,
            issued_by: draft.issued_by,
            issued_at: draft.issued_at,
            comparator_digest: draft.comparator_digest,
        };
        receipt.validate_comparator_issued()?;
        if matches!(receipt.verdict, Verdict::ExactMatch) {
            return Err(GovernanceOpsError::HandWrittenSuccessReceipt);
        }
        Ok(receipt)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Debt {
    pub debt_id: String,
    pub debt_type: String,
    pub severity: String,
    pub owner: String,
    pub due_at: String,
    pub blocking_scope: String,
    pub introduced_by_receipt: String,
    pub root_cause_code: String,
    pub root_cause_hypothesis: String,
    #[serde(default)]
    pub verification_receipt: Option<String>,
    pub state: DebtState,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "PascalCase")]
pub enum DebtState {
    Open,
    Triage,
    Planned,
    Mitigated,
    Verified,
    Closed,
    Waived,
}

impl Debt {
    pub fn validate_closure(&self) -> Result<(), GovernanceOpsError> {
        if matches!(self.state, DebtState::Closed)
            && self
                .verification_receipt
                .as_deref()
                .is_none_or(|receipt| receipt.trim().is_empty())
        {
            return Err(GovernanceOpsError::MissingVerificationReceipt);
        }
        Ok(())
    }

    pub fn waive(&self) -> Self {
        let mut waived = self.clone();
        waived.state = DebtState::Waived;
        waived
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DebtCluster {
    pub cluster_id: String,
    pub fingerprint: String,
    pub debt_refs: Vec<String>,
    pub recurrence_count: usize,
    pub severity_ceiling: String,
    #[serde(default)]
    pub candidate_policy_ref: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "PascalCase")]
pub enum CandidatePolicyStatus {
    Candidate,
    Shadow,
    Review,
    LimitedRollout,
    Rejected,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "CandidatePolicyDraft")]
pub struct CandidatePolicy {
    pub(crate) candidate_policy_id: String,
    pub(crate) scope: String,
    pub(crate) rule_text: String,
    pub(crate) policy_module: Option<String>,
    pub(crate) evidence_refs: Vec<String>,
    pub(crate) metrics_gate: Value,
    pub(crate) status: CandidatePolicyStatus,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CandidatePolicyDraft {
    pub candidate_policy_id: String,
    pub scope: String,
    pub rule_text: String,
    pub policy_module: Option<String>,
    pub evidence_refs: Vec<String>,
    pub metrics_gate: Value,
    pub status: CandidatePolicyStatus,
}

impl CandidatePolicy {
    pub fn can_enforce_directly(&self) -> bool {
        false
    }

    pub fn candidate_policy_id(&self) -> &str {
        &self.candidate_policy_id
    }

    pub fn scope(&self) -> &str {
        &self.scope
    }

    pub fn evidence_refs(&self) -> &[String] {
        &self.evidence_refs
    }

    pub fn status(&self) -> &CandidatePolicyStatus {
        &self.status
    }
}

impl TryFrom<CandidatePolicyDraft> for CandidatePolicy {
    type Error = GovernanceOpsError;

    fn try_from(draft: CandidatePolicyDraft) -> Result<Self, Self::Error> {
        if !matches!(draft.status, CandidatePolicyStatus::Candidate)
            || draft.candidate_policy_id.trim().is_empty()
            || draft.scope.trim().is_empty()
            || draft.rule_text.trim().is_empty()
            || draft.evidence_refs.is_empty()
        {
            return Err(GovernanceOpsError::InvalidCandidatePolicy);
        }
        Ok(Self {
            candidate_policy_id: draft.candidate_policy_id,
            scope: draft.scope,
            rule_text: draft.rule_text,
            policy_module: draft.policy_module,
            evidence_refs: draft.evidence_refs,
            metrics_gate: draft.metrics_gate,
            status: draft.status,
        })
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "PascalCase")]
pub enum PolicyStatus {
    Shadow,
    LimitedRollout,
    Active,
    Deprecated,
    Retired,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "PolicyDraft")]
pub struct Policy {
    pub(crate) policy_id: String,
    pub(crate) candidate_policy_id: String,
    pub(crate) policy_hash: String,
    pub(crate) scope: String,
    pub(crate) status: PolicyStatus,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PolicyDraft {
    pub policy_id: String,
    pub candidate_policy_id: String,
    pub policy_hash: String,
    pub scope: String,
    pub status: PolicyStatus,
}

impl Policy {
    pub fn validate_not_hand_written_active(&self) -> Result<(), GovernanceOpsError> {
        if matches!(self.status, PolicyStatus::Active) {
            return Err(GovernanceOpsError::HandWrittenActivePolicy);
        }
        Ok(())
    }

    pub fn status(&self) -> &PolicyStatus {
        &self.status
    }
}

impl TryFrom<PolicyDraft> for Policy {
    type Error = GovernanceOpsError;

    fn try_from(draft: PolicyDraft) -> Result<Self, Self::Error> {
        let policy = Self {
            policy_id: draft.policy_id,
            candidate_policy_id: draft.candidate_policy_id,
            policy_hash: draft.policy_hash,
            scope: draft.scope,
            status: draft.status,
        };
        policy.validate_not_hand_written_active()?;
        Ok(policy)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "PromotionDraft")]
pub struct Promotion {
    pub(crate) promotion_id: String,
    pub(crate) candidate_policy_ref: String,
    pub(crate) shadow_passed: bool,
    pub(crate) replay_passed: bool,
    pub(crate) reviewer_authority_refs: Vec<String>,
    pub(crate) rollout_plan: String,
    pub(crate) rollback_plan: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PromotionDraft {
    pub promotion_id: String,
    pub candidate_policy_ref: String,
    pub shadow_passed: bool,
    pub replay_passed: bool,
    pub reviewer_authority_refs: Vec<String>,
    pub rollout_plan: String,
    pub rollback_plan: String,
}

impl Promotion {
    pub fn validate(&self) -> Result<(), GovernanceOpsError> {
        if self.promotion_id.trim().is_empty()
            || self.candidate_policy_ref.trim().is_empty()
            || !self.shadow_passed
            || !self.replay_passed
            || self.reviewer_authority_refs.is_empty()
            || self.rollout_plan.trim().is_empty()
            || self.rollback_plan.trim().is_empty()
        {
            return Err(GovernanceOpsError::PromotionPreconditionsNotMet);
        }
        Ok(())
    }
}

impl TryFrom<PromotionDraft> for Promotion {
    type Error = GovernanceOpsError;

    fn try_from(draft: PromotionDraft) -> Result<Self, Self::Error> {
        let promotion = Self {
            promotion_id: draft.promotion_id,
            candidate_policy_ref: draft.candidate_policy_ref,
            shadow_passed: draft.shadow_passed,
            replay_passed: draft.replay_passed,
            reviewer_authority_refs: draft.reviewer_authority_refs,
            rollout_plan: draft.rollout_plan,
            rollback_plan: draft.rollback_plan,
        };
        promotion.validate()?;
        Ok(promotion)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "PascalCase")]
pub enum ReviewActionKind {
    TriageDebt,
    WaiveDebt,
    SuppressDebt,
    CloseDebt,
    PromoteCandidatePolicy,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ReviewDecision {
    pub decision_id: String,
    pub action: ReviewActionKind,
    pub target_ref: String,
    pub reviewer: String,
    pub authority_ref: Option<String>,
    pub created_at: String,
}

impl ReviewDecision {
    pub fn validate_authorized(&self) -> Result<(), GovernanceOpsError> {
        if self
            .authority_ref
            .as_deref()
            .is_some_and(|authority_ref| !authority_ref.trim().is_empty())
        {
            Ok(())
        } else {
            Err(GovernanceOpsError::MissingAuthority)
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "SuppressionDraft")]
pub struct Suppression {
    pub(crate) suppression_id: String,
    pub(crate) target_ref: String,
    pub(crate) reason: String,
    pub(crate) approved_by: String,
    pub(crate) expires_at: String,
    pub(crate) review_at: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SuppressionDraft {
    pub suppression_id: String,
    pub target_ref: String,
    pub reason: String,
    pub approved_by: String,
    pub expires_at: String,
    pub review_at: String,
}

impl Suppression {
    pub fn validate(&self) -> Result<(), GovernanceOpsError> {
        if self.approved_by.trim().is_empty() {
            return Err(GovernanceOpsError::MissingAuthority);
        }
        if self.expires_at.trim().is_empty() || self.review_at.trim().is_empty() {
            return Err(GovernanceOpsError::MissingSuppressionExpiry);
        }
        Ok(())
    }
}

impl TryFrom<SuppressionDraft> for Suppression {
    type Error = GovernanceOpsError;

    fn try_from(draft: SuppressionDraft) -> Result<Self, Self::Error> {
        let suppression = Self {
            suppression_id: draft.suppression_id,
            target_ref: draft.target_ref,
            reason: draft.reason,
            approved_by: draft.approved_by,
            expires_at: draft.expires_at,
            review_at: draft.review_at,
        };
        suppression.validate()?;
        Ok(suppression)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "ClosureDraft")]
pub struct Closure {
    pub(crate) closure_id: String,
    pub(crate) target_ref: String,
    pub(crate) closure_reason: String,
    pub(crate) verification_receipt: Option<String>,
    pub(crate) reopen_conditions: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ClosureDraft {
    pub closure_id: String,
    pub target_ref: String,
    pub closure_reason: String,
    pub verification_receipt: Option<String>,
    pub reopen_conditions: Vec<String>,
}

impl Closure {
    pub fn validate(&self) -> Result<(), GovernanceOpsError> {
        if self
            .verification_receipt
            .as_deref()
            .is_some_and(|receipt| !receipt.trim().is_empty())
        {
            Ok(())
        } else {
            Err(GovernanceOpsError::MissingVerificationReceipt)
        }
    }
}

impl TryFrom<ClosureDraft> for Closure {
    type Error = GovernanceOpsError;

    fn try_from(draft: ClosureDraft) -> Result<Self, Self::Error> {
        let closure = Self {
            closure_id: draft.closure_id,
            target_ref: draft.target_ref,
            closure_reason: draft.closure_reason,
            verification_receipt: draft.verification_receipt,
            reopen_conditions: draft.reopen_conditions,
        };
        closure.validate()?;
        Ok(closure)
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GovernanceOpsError {
    MissingAuthority,
    MissingSuppressionExpiry,
    MissingVerificationReceipt,
    PromotionPreconditionsNotMet,
    ReceiptNotComparatorIssued,
    HandWrittenSuccessReceipt,
    HandWrittenActivePolicy,
    InvalidCandidatePolicy,
}

impl std::fmt::Display for GovernanceOpsError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::MissingAuthority => write!(f, "missing authority"),
            Self::MissingSuppressionExpiry => write!(f, "missing suppression expiry"),
            Self::MissingVerificationReceipt => write!(f, "missing verification receipt"),
            Self::PromotionPreconditionsNotMet => write!(f, "promotion preconditions not met"),
            Self::ReceiptNotComparatorIssued => write!(f, "receipt was not comparator issued"),
            Self::HandWrittenSuccessReceipt => {
                write!(f, "hand-written success receipt is forbidden")
            }
            Self::HandWrittenActivePolicy => write!(f, "hand-written active policy is forbidden"),
            Self::InvalidCandidatePolicy => write!(f, "invalid candidate policy"),
        }
    }
}

impl std::error::Error for GovernanceOpsError {}

pub fn cluster_debts(debts: &[Debt]) -> Vec<DebtCluster> {
    let mut groups: HashMap<String, Vec<&Debt>> = HashMap::new();
    for debt in debts {
        let fingerprint = debt_fingerprint(debt);
        groups.entry(fingerprint).or_default().push(debt);
    }

    let mut clusters: Vec<_> = groups
        .into_iter()
        .map(|(fingerprint, grouped)| {
            let mut debt_refs: Vec<_> = grouped.iter().map(|debt| debt.debt_id.clone()).collect();
            debt_refs.sort();
            let severity_ceiling = grouped
                .iter()
                .map(|debt| debt.severity.as_str())
                .max_by_key(|severity| severity_rank(severity))
                .unwrap_or("info")
                .to_string();
            let cluster_id = format!("debt-cluster:{}", short_fingerprint(&fingerprint));
            DebtCluster {
                cluster_id,
                fingerprint,
                recurrence_count: debt_refs.len(),
                severity_ceiling,
                debt_refs,
                candidate_policy_ref: None,
            }
        })
        .collect();
    clusters.sort_by(|left, right| left.cluster_id.cmp(&right.cluster_id));
    clusters
}

pub fn candidate_policies_from_clusters(
    clusters: &[DebtCluster],
    min_recurrence: usize,
) -> Vec<CandidatePolicy> {
    clusters
        .iter()
        .filter(|cluster| cluster.recurrence_count >= min_recurrence)
        .map(|cluster| CandidatePolicy {
            candidate_policy_id: format!("candidate-policy:{}", cluster.cluster_id),
            scope: "new-kernel-hardening".to_string(),
            rule_text: format!(
                "Investigate recurring debt fingerprint {} before promotion.",
                cluster.fingerprint
            ),
            policy_module: None,
            evidence_refs: cluster.debt_refs.clone(),
            metrics_gate: serde_json::json!({
                "minRecurrence": min_recurrence,
                "observedRecurrence": cluster.recurrence_count,
                "requiredStatus": "CandidateOnly"
            }),
            status: CandidatePolicyStatus::Candidate,
        })
        .collect()
}

pub fn promote_candidate_policy(
    candidate: &CandidatePolicy,
    promotion: &Promotion,
    policy_hash: impl Into<String>,
) -> Result<Policy, GovernanceOpsError> {
    if promotion.candidate_policy_ref != candidate.candidate_policy_id
        || !promotion.shadow_passed
        || !promotion.replay_passed
        || promotion.reviewer_authority_refs.is_empty()
        || promotion.rollout_plan.trim().is_empty()
        || promotion.rollback_plan.trim().is_empty()
    {
        return Err(GovernanceOpsError::PromotionPreconditionsNotMet);
    }

    Ok(Policy {
        policy_id: format!("policy:{}", candidate.candidate_policy_id),
        candidate_policy_id: candidate.candidate_policy_id.clone(),
        policy_hash: policy_hash.into(),
        scope: candidate.scope.clone(),
        status: PolicyStatus::LimitedRollout,
    })
}

pub fn debt_fingerprint(debt: &Debt) -> String {
    format!(
        "{}|{}|{}",
        debt.debt_type, debt.blocking_scope, debt.root_cause_code
    )
}

fn short_fingerprint(fingerprint: &str) -> String {
    let digest = Sha256::digest(fingerprint.as_bytes());
    hex::encode(digest)[..12].to_string()
}

fn severity_rank(severity: &str) -> u8 {
    match severity {
        "critical" => 5,
        "high" => 4,
        "medium" => 3,
        "low" => 2,
        "info" => 1,
        _ => 0,
    }
}
