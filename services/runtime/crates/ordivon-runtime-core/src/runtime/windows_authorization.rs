//! Operator-owned Windows admission authorization, independent of Windows execution.
//!
//! Profile selection and maintenance admission policy live here. The native
//! launcher, Job Object, result publication and credential materializer do not.

use serde::{Deserialize, Serialize};
use std::fs;

use super::windows::WindowsExecutionConfig;
use super::{
    ForeignReference, JobRunProposal, RuntimeError, RuntimeErrorCode, RuntimeResult,
    WindowsPayloadPrivilege,
};

pub(super) const WINDOWS_PRIVILEGED_PROFILE_NAMESPACE: &str = "ordivon.windows";
pub(super) const WINDOWS_PRIVILEGED_PROFILE_TYPE: &str = "privileged_profile";

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WindowsElevatedCommandProfile {
    pub executable: String,
    #[serde(default)]
    pub argument_prefix: Vec<String>,
    #[serde(default)]
    pub allow_additional_arguments: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub struct WindowsElevatedExecutionProfile {
    pub id: String,
    pub principals: Vec<String>,
    pub commands: Vec<WindowsElevatedCommandProfile>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "camelCase")]
struct WindowsMaintenanceLease {
    schema_version: u32,
    kind: String,
    maintenance_id: String,
    expires_at_utc: String,
    expires_at_unix_ms: u64,
}

fn valid_privileged_profile_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 128
        && value.bytes().all(|byte| {
            byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-' | b':' | b'/')
        })
}

fn normalized_windows_command_path(value: &str) -> String {
    let mut value = value.replace('/', "\\");
    if let Some(stripped) = value.strip_prefix("\\\\?\\") {
        value = stripped.to_string();
    }
    value.make_ascii_lowercase();
    value
}

fn command_matches_profile(
    executable: &str,
    args: &[String],
    profile: &WindowsElevatedCommandProfile,
) -> bool {
    if normalized_windows_command_path(executable)
        != normalized_windows_command_path(&profile.executable)
    {
        return false;
    }
    if args.len() < profile.argument_prefix.len()
        || args[..profile.argument_prefix.len()] != profile.argument_prefix
    {
        return false;
    }
    profile.allow_additional_arguments || args.len() == profile.argument_prefix.len()
}

fn requested_privileged_profile(
    references: &[ForeignReference],
) -> RuntimeResult<Option<&ForeignReference>> {
    let selected = references
        .iter()
        .filter(|reference| {
            reference.namespace == WINDOWS_PRIVILEGED_PROFILE_NAMESPACE
                && reference.reference_type == WINDOWS_PRIVILEGED_PROFILE_TYPE
        })
        .collect::<Vec<_>>();
    if selected.len() > 1 {
        return Err(RuntimeError::new(
            RuntimeErrorCode::AuthorizationDenied,
            "elevated Windows execution may select exactly one privileged profile",
            Some("execution.foreignReferences"),
            false,
        ));
    }
    Ok(selected.into_iter().next())
}

pub(super) fn validate_windows_elevated_principals(principals: &[String]) -> RuntimeResult<()> {
    let mut seen = std::collections::BTreeSet::new();
    for principal in principals {
        if principal.is_empty()
            || principal.len() > 256
            || principal.chars().any(char::is_whitespace)
            || !seen.insert(principal.as_str())
        {
            return Err(RuntimeError::invalid(
                "Windows elevated principals must be unique, non-empty, whitespace-free, and at most 256 characters",
                "windows.elevatedPrincipals",
            ));
        }
    }
    Ok(())
}

pub(super) fn validate_configuration(config: &WindowsExecutionConfig) -> RuntimeResult<()> {
    validate_windows_elevated_principals(&config.elevated_principals)?;
    let mut profile_ids = std::collections::BTreeSet::new();
    for profile in &config.elevated_profiles {
        if !valid_privileged_profile_id(&profile.id) || !profile_ids.insert(profile.id.as_str()) {
            return Err(RuntimeError::invalid(
                "Windows elevated profile ids must be unique stable logical ids",
                "windows.elevatedProfiles",
            ));
        }
        validate_windows_elevated_principals(&profile.principals)?;
        if profile.principals.is_empty() || profile.commands.is_empty() {
            return Err(RuntimeError::invalid(
                "Windows elevated profiles require at least one principal and command",
                "windows.elevatedProfiles",
            ));
        }
        for command in &profile.commands {
            if command.executable.is_empty() || command.executable.chars().any(|c| c == '\0') {
                return Err(RuntimeError::invalid(
                    "Windows elevated profile commands require a non-empty NUL-free executable",
                    "windows.elevatedProfiles",
                ));
            }
        }
    }
    if let Some(path) = &config.maintenance_lease_path {
        if cfg!(windows) && !path.is_absolute() {
            return Err(RuntimeError::invalid(
                "Windows maintenance lease path must be absolute",
                "windows.maintenanceLeasePath",
            ));
        }
    }
    Ok(())
}

impl WindowsExecutionConfig {
    pub(crate) fn authorize_new_proposal(&self, proposal: &JobRunProposal) -> RuntimeResult<()> {
        if proposal.execution.execution_target != super::ExecutionTarget::WindowsNative {
            return Ok(());
        }
        self.authorize_maintenance_fence()?;
        self.authorize_elevated_proposal(proposal)
    }

    fn authorize_maintenance_fence(&self) -> RuntimeResult<()> {
        let Some(path) = self.maintenance_lease_path.as_ref() else {
            return Ok(());
        };
        let metadata = match fs::symlink_metadata(path) {
            Ok(metadata) => metadata,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(()),
            Err(error) => {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::AuthorizationDenied,
                    format!("cannot inspect Windows maintenance lease: {error}"),
                    Some("windows.maintenanceLeasePath"),
                    false,
                ))
            }
        };
        if metadata.file_type().is_symlink() || !metadata.is_file() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                "Windows maintenance lease must be a regular non-symlink file",
                Some("windows.maintenanceLeasePath"),
                false,
            ));
        }
        let bytes = fs::read(path).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                format!("cannot read Windows maintenance lease: {error}"),
                Some("windows.maintenanceLeasePath"),
                false,
            )
        })?;
        let lease: WindowsMaintenanceLease = serde_json::from_slice(&bytes).map_err(|error| {
            RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                format!("invalid Windows maintenance lease JSON: {error}"),
                Some("windows.maintenanceLeasePath"),
                false,
            )
        })?;
        if lease.schema_version != 3
            || lease.kind != "ordivon.d-drive-compact-request"
            || !valid_privileged_profile_id(&lease.maintenance_id)
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                "Windows maintenance lease identity is invalid",
                Some("windows.maintenanceLeasePath"),
                false,
            ));
        }
        let now_ms = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map_err(|error| {
                RuntimeError::new(
                    RuntimeErrorCode::AuthorizationDenied,
                    format!("cannot determine current time for Windows maintenance lease: {error}"),
                    Some("windows.maintenanceLeasePath"),
                    false,
                )
            })?
            .as_millis() as u64;
        if lease.expires_at_unix_ms <= now_ms {
            return Ok(());
        }
        Err(RuntimeError::new(
            RuntimeErrorCode::AuthorizationDenied,
            format!(
                "Windows execution admission is fenced by active maintenance lease {} until {}",
                lease.maintenance_id, lease.expires_at_utc
            ),
            Some("execution.executionTarget"),
            false,
        ))
    }

    pub(crate) fn authorize_elevated_proposal(
        &self,
        proposal: &JobRunProposal,
    ) -> RuntimeResult<()> {
        if proposal.execution.execution_target != super::ExecutionTarget::WindowsNative {
            return Ok(());
        }
        let context = proposal
            .execution
            .windows_context
            .unwrap_or_else(|| proposal.execution.windows_authority.canonical_context());
        let selected = requested_privileged_profile(&proposal.execution.foreign_references)?;
        if context.privilege != WindowsPayloadPrivilege::Elevated {
            if selected.is_some() {
                return Err(RuntimeError::new(
                    RuntimeErrorCode::AuthorizationDenied,
                    "a privileged Windows profile may be selected only by elevated execution",
                    Some("execution.foreignReferences"),
                    false,
                ));
            }
            return Ok(());
        }
        if !proposal.execution.env.is_empty()
            || proposal
                .execution
                .steps
                .iter()
                .any(|step| !step.env.is_empty())
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                "elevated Windows profiles require the operator-controlled environment",
                Some("execution.env"),
                false,
            ));
        }
        let selected = selected.ok_or_else(|| {
            RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                "elevated Windows execution requires one operator-configured privileged profile",
                Some("execution.foreignReferences"),
                false,
            )
        })?;
        if selected.generation.is_some() || selected.digest.is_some() {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                "privileged profile references are operator policy selectors and must not carry caller generation or digest claims",
                Some("execution.foreignReferences"),
                false,
            ));
        }
        let profile = self
            .elevated_profiles
            .iter()
            .find(|profile| profile.id == selected.id)
            .ok_or_else(|| {
                RuntimeError::new(
                    RuntimeErrorCode::AuthorizationDenied,
                    "requested Windows privileged profile is not configured",
                    Some("execution.foreignReferences"),
                    false,
                )
            })?;
        if !profile
            .principals
            .iter()
            .any(|principal| principal == &proposal.principal)
        {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                "authenticated principal is not authorized for the requested Windows privileged profile",
                Some("execution.foreignReferences"),
                false,
            ));
        }
        let mut commands = Vec::with_capacity(1 + proposal.execution.steps.len());
        commands.push((
            proposal.execution.executable.as_str(),
            proposal.execution.args.as_slice(),
        ));
        commands.extend(
            proposal
                .execution
                .steps
                .iter()
                .map(|step| (step.executable.as_str(), step.args.as_slice())),
        );
        if commands.iter().any(|(executable, args)| {
            !profile
                .commands
                .iter()
                .any(|rule| command_matches_profile(executable, args, rule))
        }) {
            return Err(RuntimeError::new(
                RuntimeErrorCode::AuthorizationDenied,
                "elevated Windows command is outside the selected privileged profile",
                Some("execution.executable"),
                false,
            ));
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::{
        command_matches_profile, valid_privileged_profile_id, WindowsElevatedCommandProfile,
    };

    #[test]
    fn privilege_profile_id_is_not_a_wildcard() {
        assert!(valid_privileged_profile_id("operator:release-1"));
        assert!(!valid_privileged_profile_id(""));
        assert!(!valid_privileged_profile_id("id with spaces"));
        assert!(!valid_privileged_profile_id("*"));
    }

    #[test]
    fn command_prefix_requires_exact_arguments_unless_enabled() {
        let mut profile = WindowsElevatedCommandProfile {
            executable: r"C:\Windows\System32\cmd.exe".into(),
            argument_prefix: vec!["/c".into(), "echo".into()],
            allow_additional_arguments: false,
        };
        let exact = vec!["/c".into(), "echo".into()];
        let added = vec!["/c".into(), "echo".into(), "extra".into()];
        assert!(command_matches_profile(
            "c:/windows/system32/cmd.exe",
            &exact,
            &profile
        ));
        assert!(!command_matches_profile(
            "c:/windows/system32/cmd.exe",
            &added,
            &profile
        ));
        profile.allow_additional_arguments = true;
        assert!(command_matches_profile(
            "c:/windows/system32/cmd.exe",
            &added,
            &profile
        ));
    }
}
