//! Original resource bindings domain wire contract and behavior.
use super::{LOGICAL_ID_MAX_LENGTH, LOGICAL_ID_MIN_LENGTH, LOGICAL_ID_PATTERN};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ForeignReference {
    #[schemars(length(min = LOGICAL_ID_MIN_LENGTH, max = LOGICAL_ID_MAX_LENGTH), extend("pattern" = LOGICAL_ID_PATTERN))]
    pub namespace: String,
    #[serde(rename = "type")]
    #[schemars(length(min = LOGICAL_ID_MIN_LENGTH, max = LOGICAL_ID_MAX_LENGTH), extend("pattern" = LOGICAL_ID_PATTERN))]
    pub reference_type: String,
    #[schemars(length(min = LOGICAL_ID_MIN_LENGTH, max = LOGICAL_ID_MAX_LENGTH), extend("pattern" = LOGICAL_ID_PATTERN))]
    pub id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(length(min = LOGICAL_ID_MIN_LENGTH, max = LOGICAL_ID_MAX_LENGTH), extend("pattern" = LOGICAL_ID_PATTERN))]
    pub generation: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    #[schemars(length(min = LOGICAL_ID_MIN_LENGTH, max = LOGICAL_ID_MAX_LENGTH), extend("pattern" = LOGICAL_ID_PATTERN))]
    pub digest: Option<String>,
}

/// Agent-declared exact host file whose bytes are a known physical prerequisite of trusted-local execution.
/// Runtime validates the digest at admission and again at the target-spawn boundary; it does not infer
/// undeclared dynamic dependencies or claim that this list is a complete environment closure.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct HostDependencyBinding {
    /// Absolute host path to one regular non-symlink prerequisite file.
    pub path: String,
    pub expected_digest: String,
}

/// Operator-owned root from which Runtime may resolve immutable input objects.
/// This is Core configuration/authority, not Agent-authored path authority.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct InputAuthority {
    pub name: String,
    pub root: PathBuf,
}

/// Operator-owned systemd-encrypted credential source. Encrypted blobs are selected by opaque
/// logical name, authorized against the authenticated Runtime principal, snapshotted on new
/// admission, and never require the caller to know a content digest. Runtime never stores the
/// plaintext credential in its durable Job store.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CredentialAuthority {
    pub name: String,
    pub root: PathBuf,
    pub allowed_principals: Vec<String>,
}

/// Agent/domain-authored request for one named credential. Unlike immutable artifact inputs,
/// credentials deliberately do not expose or require a caller-held digest.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct CredentialBindingRequest {
    pub authority: String,
    pub credential: String,
}

/// Agent/domain-authored request for one exact object inside a named input authority.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct InputBindingRequest {
    pub authority: String,
    pub relative_object: String,
    pub expected_digest: String,
    pub presentation_relative_path: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionProviderContract {
    LocalLinuxRunnerV1,
    WindowsNativeLauncherV1,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct ExecutionProviderSnapshot {
    pub contract: ExecutionProviderContract,
    pub executable_digest: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub wsl_distribution: Option<String>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum InputAccessMode {
    ReadOnly,
}

/// Concrete immutable input truth frozen into one Runtime execution plan.
#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct EffectiveInputBinding {
    pub authority: String,
    pub relative_object: String,
    pub digest: String,
    pub byte_length: u64,
    pub presentation_relative_path: String,
    pub access: InputAccessMode,
}
