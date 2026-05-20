use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

use base64::{engine::general_purpose::STANDARD as BASE64, Engine as _};

use crate::digest::{canonical_json, compare_rfc3339, parse_rfc3339};
use crate::errors::KernelError;
use crate::types::ActionClass;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", try_from = "AuthorityTokenDraft")]
pub struct AuthorityToken {
    pub(crate) jti: String,
    pub(crate) kid: String,
    pub(crate) iss: String,
    pub(crate) sub: String,
    pub(crate) audience: String,
    pub(crate) intent_id: String,
    pub(crate) obligation_id: String,
    pub(crate) action_class: ActionClass,
    pub(crate) target_ref: String,
    pub(crate) policy_hash: String,
    pub(crate) issued_at: String,
    pub(crate) not_before: String,
    pub(crate) expires_at: String,
    pub(crate) max_use_count: u32,
    pub(crate) idempotency_key: String,
    pub(crate) seal_ref: String,
    pub(crate) signature: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AuthorityTokenDraft {
    pub jti: String,
    pub kid: String,
    pub iss: String,
    pub sub: String,
    pub audience: String,
    pub intent_id: String,
    pub obligation_id: String,
    pub action_class: ActionClass,
    pub target_ref: String,
    pub policy_hash: String,
    pub issued_at: String,
    pub not_before: String,
    pub expires_at: String,
    pub max_use_count: u32,
    pub idempotency_key: String,
    pub seal_ref: String,
    #[serde(default)]
    pub signature: String,
}

impl AuthorityToken {
    pub fn from_unsigned_draft(draft: AuthorityTokenDraft) -> Result<Self, KernelError> {
        Self::try_from(draft)
    }

    pub fn unsigned_payload(&self) -> Result<String, KernelError> {
        canonical_json(&serde_json::json!({
            "jti": self.jti,
            "kid": self.kid,
            "iss": self.iss,
            "sub": self.sub,
            "audience": self.audience,
            "intentId": self.intent_id,
            "obligationId": self.obligation_id,
            "actionClass": self.action_class,
            "targetRef": self.target_ref,
            "policyHash": self.policy_hash,
            "issuedAt": self.issued_at,
            "notBefore": self.not_before,
            "expiresAt": self.expires_at,
            "maxUseCount": self.max_use_count,
            "idempotencyKey": self.idempotency_key,
            "sealRef": self.seal_ref,
        }))
    }

    pub fn jti(&self) -> &str {
        &self.jti
    }

    pub fn signature(&self) -> &str {
        &self.signature
    }
}

impl TryFrom<AuthorityTokenDraft> for AuthorityToken {
    type Error = KernelError;

    fn try_from(draft: AuthorityTokenDraft) -> Result<Self, Self::Error> {
        if draft.jti.trim().is_empty()
            || draft.kid.trim().is_empty()
            || draft.iss.trim().is_empty()
            || draft.sub.trim().is_empty()
            || draft.audience.trim().is_empty()
            || draft.intent_id.trim().is_empty()
            || draft.obligation_id.trim().is_empty()
            || draft.target_ref.trim().is_empty()
            || draft.policy_hash.trim().is_empty()
            || draft.idempotency_key.trim().is_empty()
            || draft.seal_ref.trim().is_empty()
        {
            return Err(KernelError::InvalidDeclaration(
                "authority token draft has empty required fields".to_string(),
            ));
        }
        parse_rfc3339(&draft.issued_at)?;
        parse_rfc3339(&draft.not_before)?;
        parse_rfc3339(&draft.expires_at)?;
        if draft.max_use_count != 1 {
            return Err(KernelError::InvalidDeclaration(
                "authority token maxUseCount must be 1".to_string(),
            ));
        }
        Ok(Self {
            jti: draft.jti,
            kid: draft.kid,
            iss: draft.iss,
            sub: draft.sub,
            audience: draft.audience,
            intent_id: draft.intent_id,
            obligation_id: draft.obligation_id,
            action_class: draft.action_class,
            target_ref: draft.target_ref,
            policy_hash: draft.policy_hash,
            issued_at: draft.issued_at,
            not_before: draft.not_before,
            expires_at: draft.expires_at,
            max_use_count: draft.max_use_count,
            idempotency_key: draft.idempotency_key,
            seal_ref: draft.seal_ref,
            signature: draft.signature,
        })
    }
}

#[derive(Clone)]
pub struct AuthorityVerifier {
    trusted_keys: HashMap<String, VerifyingKey>,
    expected_issuer: String,
    expected_audience: String,
}

impl AuthorityVerifier {
    pub fn new(
        trusted_keys: HashMap<String, VerifyingKey>,
        expected_issuer: impl Into<String>,
        expected_audience: impl Into<String>,
    ) -> Self {
        Self {
            trusted_keys,
            expected_issuer: expected_issuer.into(),
            expected_audience: expected_audience.into(),
        }
    }

    pub fn verify_signature(&self, token: &AuthorityToken) -> Result<(), AuthorityError> {
        let key = self
            .trusted_keys
            .get(&token.kid)
            .ok_or_else(|| AuthorityError::UnknownKey {
                kid: token.kid.clone(),
            })?;
        if token.signature.trim().is_empty() {
            return Err(AuthorityError::MissingSignature);
        }
        let decoded = BASE64
            .decode(&token.signature)
            .map_err(|_| AuthorityError::InvalidSignature)?;
        let signature =
            Signature::from_slice(&decoded).map_err(|_| AuthorityError::InvalidSignature)?;
        let payload = token
            .unsigned_payload()
            .map_err(|err| AuthorityError::InvalidPayload(err.to_string()))?;
        key.verify(payload.as_bytes(), &signature)
            .map_err(|_| AuthorityError::InvalidSignature)
    }
}

#[derive(Clone, Copy)]
pub struct AuthorityValidationRequest<'a> {
    pub token: &'a AuthorityToken,
    pub verifier: &'a AuthorityVerifier,
    pub intent_id: &'a str,
    pub obligation_id: &'a str,
    pub action_class: &'a ActionClass,
    pub target_ref: &'a str,
    pub policy_hash: &'a str,
    pub idempotency_key: &'a str,
    pub now: &'a str,
    pub policy_decision: PolicyDecision,
}

#[derive(Default)]
pub struct AuthorityUseLedger {
    used_tokens: HashSet<String>,
    revoked_tokens: HashSet<String>,
}

impl AuthorityUseLedger {
    pub fn validate_and_consume(
        &mut self,
        request: AuthorityValidationRequest<'_>,
    ) -> Result<(), AuthorityError> {
        if matches!(
            request.policy_decision,
            PolicyDecision::Deny | PolicyDecision::Error
        ) {
            return Err(AuthorityError::PolicyDenied);
        }
        let token = request.token;
        let verifier = request.verifier;
        verifier.verify_signature(token)?;
        if token.iss != verifier.expected_issuer {
            return Err(AuthorityError::IssuerMismatch);
        }
        if token.audience != verifier.expected_audience {
            return Err(AuthorityError::AudienceMismatch);
        }
        if token.max_use_count != 1 {
            return Err(AuthorityError::InvalidMaxUseCount {
                actual: token.max_use_count,
            });
        }
        if self.revoked_tokens.contains(&token.jti) {
            return Err(AuthorityError::RevokedToken {
                jti: token.jti.clone(),
            });
        }
        if self.used_tokens.contains(&token.jti) {
            return Err(AuthorityError::ReplayedToken {
                jti: token.jti.clone(),
            });
        }
        if token.intent_id != request.intent_id {
            return Err(AuthorityError::IntentMismatch);
        }
        if token.obligation_id != request.obligation_id {
            return Err(AuthorityError::ObligationMismatch);
        }
        if &token.action_class != request.action_class {
            return Err(AuthorityError::ActionClassMismatch);
        }
        if token.target_ref != request.target_ref {
            return Err(AuthorityError::TargetMismatch);
        }
        if token.policy_hash != request.policy_hash {
            return Err(AuthorityError::PolicyHashMismatch);
        }
        if token.idempotency_key != request.idempotency_key {
            return Err(AuthorityError::IdempotencyMismatch);
        }
        if compare_rfc3339(request.now, &token.not_before).map_err(AuthorityError::InvalidTime)?
            == std::cmp::Ordering::Less
        {
            return Err(AuthorityError::NotYetValid);
        }
        if compare_rfc3339(request.now, &token.expires_at).map_err(AuthorityError::InvalidTime)?
            != std::cmp::Ordering::Less
        {
            return Err(AuthorityError::Expired);
        }

        self.used_tokens.insert(token.jti.clone());
        Ok(())
    }

    pub fn revoke(&mut self, jti: impl Into<String>) {
        self.revoked_tokens.insert(jti.into());
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "PascalCase")]
pub enum PolicyDecision {
    Allow,
    Deny,
    Error,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AuthorityError {
    MissingSignature,
    InvalidSignature,
    UnknownKey { kid: String },
    InvalidPayload(String),
    InvalidMaxUseCount { actual: u32 },
    ReplayedToken { jti: String },
    RevokedToken { jti: String },
    IntentMismatch,
    ObligationMismatch,
    ActionClassMismatch,
    TargetMismatch,
    PolicyHashMismatch,
    IdempotencyMismatch,
    IssuerMismatch,
    AudienceMismatch,
    NotYetValid,
    Expired,
    PolicyDenied,
    InvalidTime(KernelError),
}
