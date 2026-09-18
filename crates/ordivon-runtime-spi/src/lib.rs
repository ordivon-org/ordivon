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
