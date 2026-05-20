use serde::{Deserialize, Serialize};
use serde_json::json;

use crate::authority::PolicyDecision;
use crate::digest::sha256_digest;
use crate::errors::KernelError;
use crate::types::ActionClass;

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PolicyEvaluationRequest {
    pub decision_id: String,
    pub policy_hash: String,
    pub evaluator: String,
    pub intent_id: String,
    pub obligation_id: String,
    pub action_class: ActionClass,
    pub target_ref: String,
    pub idempotency_key: String,
    pub created_at: String,
}

impl PolicyEvaluationRequest {
    pub fn input_digest(&self) -> Result<String, KernelError> {
        sha256_digest(&json!({
            "intentId": self.intent_id,
            "obligationId": self.obligation_id,
            "actionClass": self.action_class,
            "targetRef": self.target_ref,
            "idempotencyKey": self.idempotency_key,
            "policyHash": self.policy_hash,
        }))
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PolicyDecisionRecord {
    pub decision_id: String,
    pub policy_hash: String,
    pub input_digest: String,
    pub evaluator: String,
    pub decision: PolicyDecision,
    pub reason_code: String,
    pub created_at: String,
}

impl PolicyDecisionRecord {
    pub fn from_request(
        request: &PolicyEvaluationRequest,
        decision: PolicyDecision,
        reason_code: impl Into<String>,
    ) -> Result<Self, KernelError> {
        let reason_code = reason_code.into();
        if request.decision_id.trim().is_empty()
            || request.policy_hash.trim().is_empty()
            || request.evaluator.trim().is_empty()
            || reason_code.trim().is_empty()
        {
            return Err(KernelError::InvalidDeclaration(
                "policy decision evidence has empty required fields".to_string(),
            ));
        }
        Ok(Self {
            decision_id: request.decision_id.clone(),
            policy_hash: request.policy_hash.clone(),
            input_digest: request.input_digest()?,
            evaluator: request.evaluator.clone(),
            decision,
            reason_code,
            created_at: request.created_at.clone(),
        })
    }
}

pub trait PolicyEvaluator {
    fn evaluate(
        &self,
        request: &PolicyEvaluationRequest,
    ) -> Result<PolicyDecisionRecord, KernelError>;
}

#[derive(Clone, Debug)]
pub struct StaticPolicyEvaluator {
    decision: PolicyDecision,
    evaluator: String,
    reason_code: String,
}

impl StaticPolicyEvaluator {
    pub fn new(
        decision: PolicyDecision,
        evaluator: impl Into<String>,
        reason_code: impl Into<String>,
    ) -> Self {
        Self {
            decision,
            evaluator: evaluator.into(),
            reason_code: reason_code.into(),
        }
    }
}

impl PolicyEvaluator for StaticPolicyEvaluator {
    fn evaluate(
        &self,
        request: &PolicyEvaluationRequest,
    ) -> Result<PolicyDecisionRecord, KernelError> {
        let mut scoped = request.clone();
        scoped.evaluator = self.evaluator.clone();
        PolicyDecisionRecord::from_request(&scoped, self.decision, self.reason_code.clone())
    }
}

#[cfg(feature = "policy-http")]
#[derive(Clone, Debug)]
pub struct HttpPolicyEvaluator {
    evaluator: String,
    endpoint: String,
}

#[cfg(feature = "policy-http")]
impl HttpPolicyEvaluator {
    pub fn new(evaluator: impl Into<String>, endpoint: impl Into<String>) -> Self {
        Self {
            evaluator: evaluator.into(),
            endpoint: endpoint.into(),
        }
    }

    pub fn endpoint(&self) -> &str {
        &self.endpoint
    }
}

#[cfg(feature = "policy-http")]
impl PolicyEvaluator for HttpPolicyEvaluator {
    fn evaluate(
        &self,
        request: &PolicyEvaluationRequest,
    ) -> Result<PolicyDecisionRecord, KernelError> {
        let mut scoped = request.clone();
        scoped.evaluator = self.evaluator.clone();
        PolicyDecisionRecord::from_request(
            &scoped,
            PolicyDecision::Error,
            "HTTP_EVALUATOR_NOT_BOUND",
        )
    }
}
