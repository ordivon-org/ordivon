//! Runtime-owned contained execution environment: reject caller overrides.
use super::super::{RuntimeError, RuntimeResult};
use std::collections::BTreeMap;

const CONTAINED_RUNTIME_ENVIRONMENT: [&str; 15] = [
    "HOME",
    "TMPDIR",
    "XDG_CACHE_HOME",
    "CARGO_TARGET_DIR",
    "UV_CACHE_DIR",
    "PIP_CACHE_DIR",
    "npm_config_cache",
    "PNPM_HOME",
    "COREPACK_HOME",
    "BUN_INSTALL_CACHE_DIR",
    "GOMODCACHE",
    "GOCACHE",
    "GIT_OPTIONAL_LOCKS",
    "ORDIVON_PAYLOAD_UID",
    "ORDIVON_PAYLOAD_GID",
];

pub(super) fn validate_contained_environment(
    environment: &BTreeMap<String, String>,
    field: &str,
) -> RuntimeResult<()> {
    if let Some(name) = CONTAINED_RUNTIME_ENVIRONMENT
        .iter()
        .find(|name| environment.contains_key(**name))
    {
        let environment_field = format!("{field}.{name}");
        return Err(RuntimeError::invalid(
            format!("{name} is owned by the contained-local Runtime profile"),
            &environment_field,
        ));
    }
    Ok(())
}

#[cfg(test)]
mod behavior_tests {
    use super::validate_contained_environment;
    use crate::runtime::RuntimeErrorCode;
    use std::collections::BTreeMap;

    #[test]
    fn contained_execution_owns_its_control_environment_but_accepts_user_data() {
        for key in [
            "HOME",
            "TMPDIR",
            "CARGO_TARGET_DIR",
            "ORDIVON_PAYLOAD_UID",
            "ORDIVON_PAYLOAD_GID",
            "GIT_OPTIONAL_LOCKS",
            "PNPM_HOME",
        ] {
            let environment = BTreeMap::from([(key.to_string(), "caller-value".to_string())]);
            let error = validate_contained_environment(&environment, "execution.env").unwrap_err();
            assert_eq!(error.code, RuntimeErrorCode::InvalidRequest, "{key}");
            assert_eq!(
                error.field.as_deref(),
                Some(format!("execution.env.{key}").as_str())
            );
        }

        let ordinary_input = BTreeMap::from([
            ("AGENT_TASK_LABEL".to_string(), "value".to_string()),
            ("LANG".to_string(), "C.UTF-8".to_string()),
        ]);
        validate_contained_environment(&ordinary_input, "execution.env")
            .expect("a caller's ordinary data must not be denied as a Runtime-owned control");
    }
}
