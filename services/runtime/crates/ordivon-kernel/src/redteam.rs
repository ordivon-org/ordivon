use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::HashMap;

use base64::{engine::general_purpose::STANDARD as BASE64, Engine as _};
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};

use crate::digest::{canonical_json, compare_rfc3339, sha256_digest};
use crate::errors::KernelError;
use crate::types::Verdict;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub enum RedTeamAttack {
    AiForgedObservation,
    TokenReplay,
    WrongTarget,
    DuplicateDispatch,
    AckAsSuccess,
    LedgerTamper,
    ProjectionDrift,
    PolicyPromotionBypass,
    ClosureWithoutVerification,
    SuppressionWithoutExpiry,
    CompromisedAdapterSourceIdentity,
    DelayedObservationAfterExpiry,
    DuplicateObservation,
    ObservationForWrongDispatch,
    QueryBackMismatch,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RedTeamScenario {
    pub scenario_id: String,
    pub description: String,
    pub attack: RedTeamAttack,
    #[serde(default)]
    pub expected_verdict: Option<Verdict>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct RedTeamOutcome {
    pub scenario_id: String,
    pub blocked: bool,
    pub actual_verdict: Option<Verdict>,
    pub finding: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DogfoodSeal {
    pub seal_id: String,
    pub payload_type: String,
    pub predicate_type: String,
    pub subject_digest: String,
    pub scenario_count: usize,
    pub critical_bypasses: usize,
    pub scenario_refs: Vec<String>,
    pub receipt_refs: Vec<String>,
    pub issued_at: String,
    #[serde(default)]
    pub signatures: Vec<EvidenceSignature>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct EvidenceSignature {
    pub kid: String,
    pub sig: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "PascalCase")]
pub enum KeyStatus {
    Active,
    Stale,
    Revoked,
}

#[derive(Clone, Debug)]
pub struct KeyMetadata {
    pub kid: String,
    pub public_key: VerifyingKey,
    pub not_before: String,
    pub not_after: String,
    pub status: KeyStatus,
}

impl KeyMetadata {
    fn verify_for_signature(&self, now: &str) -> Result<(), KernelError> {
        if !matches!(self.status, KeyStatus::Active) {
            return Err(KernelError::InvalidDeclaration(format!(
                "key {} is not active",
                self.kid
            )));
        }
        if compare_rfc3339(now, &self.not_before)? == std::cmp::Ordering::Less {
            return Err(KernelError::InvalidDeclaration(format!(
                "key {} is not yet valid",
                self.kid
            )));
        }
        if compare_rfc3339(now, &self.not_after)? != std::cmp::Ordering::Less {
            return Err(KernelError::InvalidDeclaration(format!(
                "key {} is expired",
                self.kid
            )));
        }
        Ok(())
    }
}

pub trait KeyResolver {
    fn resolve_key(&self, kid: &str) -> Option<KeyMetadata>;
}

#[derive(Clone, Debug, Default)]
pub struct InMemoryKeyResolver {
    keys: HashMap<String, KeyMetadata>,
}

impl InMemoryKeyResolver {
    pub fn new(keys: Vec<KeyMetadata>) -> Self {
        Self {
            keys: keys.into_iter().map(|key| (key.kid.clone(), key)).collect(),
        }
    }
}

impl KeyResolver for InMemoryKeyResolver {
    fn resolve_key(&self, kid: &str) -> Option<KeyMetadata> {
        self.keys.get(kid).cloned()
    }
}

pub trait SealSigner {
    fn kid(&self) -> &str;
    fn sign(&self, payload: &[u8]) -> Result<EvidenceSignature, KernelError>;
}

#[derive(Clone)]
pub struct Ed25519SealSigner {
    kid: String,
    signing_key: SigningKey,
}

impl Ed25519SealSigner {
    pub fn new(kid: impl Into<String>, signing_key: SigningKey) -> Self {
        Self {
            kid: kid.into(),
            signing_key,
        }
    }
}

impl SealSigner for Ed25519SealSigner {
    fn kid(&self) -> &str {
        &self.kid
    }

    fn sign(&self, payload: &[u8]) -> Result<EvidenceSignature, KernelError> {
        let signature = self.signing_key.sign(payload);
        Ok(EvidenceSignature {
            kid: self.kid.clone(),
            sig: BASE64.encode(signature.to_bytes()),
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct VerifiedRedTeamRun {
    run_id: String,
    outcomes: Vec<RedTeamOutcome>,
    critical_bypasses: usize,
    receipt_refs: Vec<String>,
    issued_at: String,
}

pub fn bootstrap_red_team_scenarios() -> Vec<RedTeamScenario> {
    vec![
        RedTeamScenario {
            scenario_id: "rt:ai-forged-observed-event".to_string(),
            description: "AI payload attempts to claim SYSTEM_OBSERVED origin".to_string(),
            attack: RedTeamAttack::AiForgedObservation,
            expected_verdict: Some(Verdict::DeclarationInvalid),
        },
        RedTeamScenario {
            scenario_id: "rt:authority-token-replay".to_string(),
            description: "Authority token is consumed more than once".to_string(),
            attack: RedTeamAttack::TokenReplay,
            expected_verdict: None,
        },
        RedTeamScenario {
            scenario_id: "rt:wrong-target".to_string(),
            description: "Observed action changes target not declared by obligation".to_string(),
            attack: RedTeamAttack::WrongTarget,
            expected_verdict: Some(Verdict::Mis),
        },
        RedTeamScenario {
            scenario_id: "rt:duplicate-dispatch".to_string(),
            description: "Same target is observed twice despite max cardinality one".to_string(),
            attack: RedTeamAttack::DuplicateDispatch,
            expected_verdict: Some(Verdict::Over),
        },
        RedTeamScenario {
            scenario_id: "rt:acked-as-success".to_string(),
            description: "Adapter ack is misused as success evidence".to_string(),
            attack: RedTeamAttack::AckAsSuccess,
            expected_verdict: Some(Verdict::Unverifiable),
        },
        RedTeamScenario {
            scenario_id: "rt:ledger-tamper".to_string(),
            description: "Ledger payload is modified after append".to_string(),
            attack: RedTeamAttack::LedgerTamper,
            expected_verdict: None,
        },
        RedTeamScenario {
            scenario_id: "rt:projection-drift".to_string(),
            description: "Projection head is stale after later ledger append".to_string(),
            attack: RedTeamAttack::ProjectionDrift,
            expected_verdict: None,
        },
        RedTeamScenario {
            scenario_id: "rt:policy-promotion-bypass".to_string(),
            description: "Policy promotion bypasses replay/review/rollback gates".to_string(),
            attack: RedTeamAttack::PolicyPromotionBypass,
            expected_verdict: None,
        },
        RedTeamScenario {
            scenario_id: "rt:closure-without-verification".to_string(),
            description: "Debt closure is attempted without verification receipt".to_string(),
            attack: RedTeamAttack::ClosureWithoutVerification,
            expected_verdict: None,
        },
        RedTeamScenario {
            scenario_id: "rt:suppression-without-expiry".to_string(),
            description: "Suppression is attempted without expiry/review boundary".to_string(),
            attack: RedTeamAttack::SuppressionWithoutExpiry,
            expected_verdict: None,
        },
        RedTeamScenario {
            scenario_id: "rt:compromised-adapter-source".to_string(),
            description: "Unregistered adapter source attempts to emit trusted evidence"
                .to_string(),
            attack: RedTeamAttack::CompromisedAdapterSourceIdentity,
            expected_verdict: None,
        },
        RedTeamScenario {
            scenario_id: "rt:delayed-observation-after-expiry".to_string(),
            description: "Observation arrives after obligation expiry".to_string(),
            attack: RedTeamAttack::DelayedObservationAfterExpiry,
            expected_verdict: Some(Verdict::DeclarationInvalid),
        },
        RedTeamScenario {
            scenario_id: "rt:duplicate-observation".to_string(),
            description: "Same dispatch is observed twice".to_string(),
            attack: RedTeamAttack::DuplicateObservation,
            expected_verdict: Some(Verdict::Over),
        },
        RedTeamScenario {
            scenario_id: "rt:wrong-dispatch-observation".to_string(),
            description: "Observation references a dispatch that does not exist".to_string(),
            attack: RedTeamAttack::ObservationForWrongDispatch,
            expected_verdict: None,
        },
        RedTeamScenario {
            scenario_id: "rt:query-back-mismatch".to_string(),
            description: "Adapter reports success but query-back evidence disagrees".to_string(),
            attack: RedTeamAttack::QueryBackMismatch,
            expected_verdict: Some(Verdict::Mis),
        },
    ]
}

impl VerifiedRedTeamRun {
    pub fn run_id(&self) -> &str {
        &self.run_id
    }

    pub fn outcomes(&self) -> &[RedTeamOutcome] {
        &self.outcomes
    }

    pub fn critical_bypasses(&self) -> usize {
        self.critical_bypasses
    }

    pub fn receipt_refs(&self) -> &[String] {
        &self.receipt_refs
    }

    pub fn issued_at(&self) -> &str {
        &self.issued_at
    }
}

#[cfg(any(test, feature = "test-support"))]
pub fn verified_red_team_run(
    run_id: impl Into<String>,
    outcomes: Vec<RedTeamOutcome>,
    issued_at: impl Into<String>,
) -> VerifiedRedTeamRun {
    let receipt_refs = outcomes
        .iter()
        .filter_map(|outcome| outcome.actual_verdict.as_ref())
        .enumerate()
        .map(|(index, verdict)| format!("receipt:red-team:{index}:{verdict:?}"))
        .collect();
    let critical_bypasses = outcomes.iter().filter(|outcome| !outcome.blocked).count();
    VerifiedRedTeamRun {
        run_id: run_id.into(),
        outcomes,
        critical_bypasses,
        receipt_refs,
        issued_at: issued_at.into(),
    }
}

pub fn build_dogfood_seal(seal_id: impl Into<String>, run: &VerifiedRedTeamRun) -> DogfoodSeal {
    let seal_id = seal_id.into();
    let scenario_refs: Vec<String> = run
        .outcomes
        .iter()
        .map(|outcome| outcome.scenario_id.clone())
        .collect();
    let subject_digest = dogfood_seal_subject_digest(&seal_id, run, &scenario_refs)
        .unwrap_or_else(|err| format!("digest-error:{err}"));
    DogfoodSeal {
        seal_id,
        payload_type: "application/vnd.in-toto+json".to_string(),
        predicate_type: "https://ordivon.dev/predicate/red-team-seal/v1".to_string(),
        subject_digest,
        scenario_count: run.outcomes.len(),
        critical_bypasses: run.critical_bypasses,
        scenario_refs,
        receipt_refs: run.receipt_refs.clone(),
        issued_at: run.issued_at.clone(),
        signatures: Vec::new(),
    }
}

pub fn verify_dogfood_seal(
    seal: &DogfoodSeal,
    run: &VerifiedRedTeamRun,
) -> Result<(), KernelError> {
    if seal.scenario_count != run.outcomes.len()
        || seal.critical_bypasses != run.critical_bypasses
        || seal.receipt_refs != run.receipt_refs
    {
        return Err(KernelError::InvalidDeclaration(
            "dogfood seal does not match verified red-team run".to_string(),
        ));
    }
    let expected = dogfood_seal_subject_digest(&seal.seal_id, run, &seal.scenario_refs)?;
    if seal.subject_digest != expected {
        return Err(KernelError::InvalidDeclaration(
            "dogfood seal subject digest mismatch".to_string(),
        ));
    }
    Ok(())
}

pub fn sign_dogfood_seal(
    seal: &DogfoodSeal,
    signer: &dyn SealSigner,
    resolver: &dyn KeyResolver,
    now: &str,
) -> Result<DogfoodSeal, KernelError> {
    let key = resolver
        .resolve_key(signer.kid())
        .ok_or_else(|| KernelError::InvalidDeclaration("unknown signing key".to_string()))?;
    key.verify_for_signature(now)?;
    let mut signed = seal.clone();
    signed.signatures = vec![signer.sign(dogfood_seal_signature_payload(seal)?.as_bytes())?];
    Ok(signed)
}

pub fn verify_signed_dogfood_seal(
    seal: &DogfoodSeal,
    run: &VerifiedRedTeamRun,
    resolver: &dyn KeyResolver,
    now: &str,
) -> Result<(), KernelError> {
    verify_dogfood_seal(seal, run)?;
    let signature = seal
        .signatures
        .first()
        .ok_or_else(|| KernelError::InvalidDeclaration("dogfood seal is unsigned".to_string()))?;
    let key = resolver
        .resolve_key(&signature.kid)
        .ok_or_else(|| KernelError::InvalidDeclaration("unknown signing key".to_string()))?;
    key.verify_for_signature(now)?;
    let decoded = BASE64
        .decode(&signature.sig)
        .map_err(|_| KernelError::InvalidDeclaration("invalid seal signature".to_string()))?;
    let signature = Signature::from_slice(&decoded)
        .map_err(|_| KernelError::InvalidDeclaration("invalid seal signature".to_string()))?;
    let payload = dogfood_seal_signature_payload(seal)?;
    key.public_key
        .verify(payload.as_bytes(), &signature)
        .map_err(|_| KernelError::InvalidDeclaration("invalid seal signature".to_string()))
}

fn dogfood_seal_signature_payload(seal: &DogfoodSeal) -> Result<String, KernelError> {
    canonical_json(&json!({
        "payloadType": seal.payload_type,
        "predicateType": seal.predicate_type,
        "sealId": seal.seal_id,
        "subjectDigest": seal.subject_digest,
        "scenarioCount": seal.scenario_count,
        "criticalBypasses": seal.critical_bypasses,
        "scenarioRefs": seal.scenario_refs,
        "receiptRefs": seal.receipt_refs,
        "issuedAt": seal.issued_at,
    }))
}

fn dogfood_seal_subject_digest(
    seal_id: &str,
    run: &VerifiedRedTeamRun,
    scenario_refs: &[String],
) -> Result<String, KernelError> {
    sha256_digest(&json!({
        "sealId": seal_id,
        "predicateType": "https://ordivon.dev/predicate/red-team-seal/v1",
        "runId": run.run_id,
        "scenarioCount": run.outcomes.len(),
        "criticalBypasses": run.critical_bypasses,
        "scenarioRefs": scenario_refs,
        "receiptRefs": run.receipt_refs,
        "issuedAt": run.issued_at,
    }))
}
