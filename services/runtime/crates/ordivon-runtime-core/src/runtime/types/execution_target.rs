//! Original execution target domain wire contract and behavior.

use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionProfile {
    #[default]
    TrustedLocal,
    ContainedLocal,
}

impl ExecutionProfile {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::TrustedLocal => "trusted_local",
            Self::ContainedLocal => "contained_local",
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionTarget {
    #[default]
    LocalLinux,
    WindowsNative,
}

impl ExecutionTarget {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::LocalLinux => "local_linux",
            Self::WindowsNative => "windows_native",
        }
    }

    pub(crate) fn is_default(&self) -> bool {
        *self == Self::LocalLinux
    }
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum WindowsAuthority {
    #[default]
    Limited,
    Elevated,
    ActiveUser,
}

impl WindowsAuthority {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Limited => "limited",
            Self::Elevated => "elevated",
            Self::ActiveUser => "active_user",
        }
    }

    /// Compile the legacy flat Windows authority profile into the canonical
    /// orthogonal payload identity x payload privilege model.
    pub fn canonical_context(self) -> WindowsExecutionContextRequest {
        match self {
            Self::Limited => WindowsExecutionContextRequest {
                identity: WindowsExecutionIdentity::Service,
                privilege: WindowsPayloadPrivilege::Limited,
            },
            Self::Elevated => WindowsExecutionContextRequest {
                identity: WindowsExecutionIdentity::Service,
                privilege: WindowsPayloadPrivilege::Elevated,
            },
            Self::ActiveUser => WindowsExecutionContextRequest {
                identity: WindowsExecutionIdentity::ActiveUser,
                privilege: WindowsPayloadPrivilege::Limited,
            },
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum WindowsExecutionIdentity {
    #[default]
    Service,
    ActiveUser,
}

impl WindowsExecutionIdentity {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Service => "service",
            Self::ActiveUser => "active_user",
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum WindowsPayloadPrivilege {
    #[default]
    Limited,
    Elevated,
}

impl WindowsPayloadPrivilege {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Limited => "limited",
            Self::Elevated => "elevated",
        }
    }
}

#[derive(Clone, Copy, Debug, Default, Deserialize, Eq, PartialEq, JsonSchema, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WindowsExecutionContextRequest {
    #[serde(default)]
    pub identity: WindowsExecutionIdentity,
    #[serde(default)]
    pub privilege: WindowsPayloadPrivilege,
}

impl WindowsExecutionContextRequest {
    pub const fn new(
        identity: WindowsExecutionIdentity,
        privilege: WindowsPayloadPrivilege,
    ) -> Self {
        Self {
            identity,
            privilege,
        }
    }

    pub fn legacy_authority(self) -> Option<WindowsAuthority> {
        match (self.identity, self.privilege) {
            (WindowsExecutionIdentity::Service, WindowsPayloadPrivilege::Limited) => {
                Some(WindowsAuthority::Limited)
            }
            (WindowsExecutionIdentity::Service, WindowsPayloadPrivilege::Elevated) => {
                Some(WindowsAuthority::Elevated)
            }
            (WindowsExecutionIdentity::ActiveUser, WindowsPayloadPrivilege::Limited) => {
                Some(WindowsAuthority::ActiveUser)
            }
            (WindowsExecutionIdentity::ActiveUser, WindowsPayloadPrivilege::Elevated) => None,
        }
    }

    pub fn transport_authority(self) -> WindowsAuthority {
        match (self.identity, self.privilege) {
            (WindowsExecutionIdentity::Service, WindowsPayloadPrivilege::Limited) => {
                WindowsAuthority::Limited
            }
            (WindowsExecutionIdentity::Service, WindowsPayloadPrivilege::Elevated) => {
                WindowsAuthority::Elevated
            }
            (WindowsExecutionIdentity::ActiveUser, _) => WindowsAuthority::ActiveUser,
        }
    }

    pub fn compatible_with_legacy(self, authority: WindowsAuthority) -> bool {
        authority == WindowsAuthority::Limited || self.legacy_authority() == Some(authority)
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub(crate) enum WindowsTokenClass {
    Limited,
    Elevated,
    ActiveUser,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(crate) struct WindowsExecutionContext {
    pub token_class: WindowsTokenClass,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub payload_identity: Option<WindowsExecutionIdentity>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub payload_privilege: Option<WindowsPayloadPrivilege>,
    pub token_user_sid: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub session_id: Option<u32>,
    pub environment_source: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub privileged_broker_digest: Option<String>,
}
