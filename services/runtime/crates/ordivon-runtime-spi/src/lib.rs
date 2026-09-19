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
    /// Node on which the Provider itself executes.
    pub node_id: FabricId,
    pub platform: FabricPlatform,
    #[serde(default)]
    pub capabilities: Vec<FabricId>,
    /// Additional resource-home nodes this Provider can explicitly control/observe.
    ///
    /// Empty means local-node-only. The Provider's own node is always reachable.
    /// This separates resource ownership/locality from actuator execution locality.
    #[serde(default)]
    pub target_node_ids: Vec<FabricId>,
}

impl ProviderDescriptor {
    pub fn validate(&self) -> Result<(), FabricContractError> {
        require_schema(self.schema_version)?;
        if self.capabilities.is_empty() {
            return Err(FabricContractError::EmptySet("capabilities"));
        }
        require_unique_ids("capabilities", &self.capabilities)?;
        require_unique_ids("targetNodeIds", &self.target_node_ids)
    }

    pub fn can_target_node(&self, target_node_id: &FabricId) -> bool {
        &self.node_id == target_node_id || self.target_node_ids.contains(target_node_id)
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
    InvalidDigest,
    InvalidControllerProposal(&'static str),
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
            Self::InvalidDigest => write!(f, "evidence digest must be sha256:<64 hex characters>"),
            Self::InvalidControllerProposal(message) => {
                write!(f, "invalid controller action proposal: {message}")
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
    fn provider_descriptor_requires_capability_membership() {
        let provider = ProviderDescriptor {
            schema_version: 1,
            provider_id: id("provider/windows/job-object"),
            node_id: id("runtime/windows-main"),
            platform: FabricPlatform::Windows,
            capabilities: vec![],
            target_node_ids: Vec::new(),
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
