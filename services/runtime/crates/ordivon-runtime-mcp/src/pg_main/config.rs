//! Original operator environment, exact Harness route/UID and native PG Runtime config.
use super::pg_auth;
use ordivon_runtime_core::{PgRuntimeConfig, UniversalExecutorConfig};
use std::{net::SocketAddr, path::PathBuf};

pub(super) struct PgStartup {
    pub(super) bind: SocketAddr,
    pub(super) auth: pg_auth::PgAuth,
    pub(super) contained_ordinary_only: bool,
    pub(super) isolated_harness: Option<(pg_auth::PgAuth, String, Option<String>)>,
    pub(super) config: PgRuntimeConfig,
    pub(super) issuer_runtime_config: Option<PgRuntimeConfig>,
}

pub(super) fn required_env(key: &str) -> Result<String, std::io::Error> {
    std::env::var(key).map_err(|_| std::io::Error::other(format!("{key} required")))
}

pub(super) fn parse_pg_headroom_pair(
    path_key: &str,
    minimum_key: &str,
    path: Option<String>,
    minimum: Option<String>,
) -> Result<Option<ordivon_runtime_core::WorkspaceHeadroomConfig>, Box<dyn std::error::Error>> {
    match (path, minimum) {
        (None, None) => Ok(None),
        (Some(path), Some(minimum)) => Ok(Some(ordivon_runtime_core::WorkspaceHeadroomConfig {
            path: std::path::PathBuf::from(path),
            minimum_free_bytes: minimum.parse()?,
        })),
        _ => Err(std::io::Error::other(format!(
            "{path_key} and {minimum_key} must be configured together"
        ))
        .into()),
    }
}

/// Explicit operator cutover for ordinary Agent Job admission. This policy
/// is bound to the authenticated MCP server, never submitted by the Agent.
pub(super) fn ordinary_contained_only(raw: Option<&str>) -> Result<bool, &'static str> {
    match raw {
        None | Some("trusted_local") => Ok(false), // legacy administrator compatibility
        Some("contained_local") => Ok(true),
        Some(_) => {
            Err("ORDIVON_PG_ORDINARY_EXECUTION_PROFILE must be trusted_local or contained_local")
        }
    }
}

// Do not start a Runtime that advertises contained-only Jobs while the
// system has no operator-owned Unix task identity to execute them.
// Unlike per-Job rejection, service startup failure cannot advertise a
// usable Agent execution capability that does not exist.
pub(super) fn require_ordinary_contained_owner(
    restricted: bool,
    owner: Option<(u32, u32)>,
) -> Result<(), &'static str> {
    if restricted && !matches!(owner, Some((uid, gid)) if uid != 0 && gid != 0) {
        return Err("contained-only ordinary ingress requires nonroot Workspace UID and GID");
    }
    Ok(())
}

#[cfg(windows)]
#[path = "config_workspace_root.rs"]
mod config_workspace_root;

pub(super) fn load_pg_startup() -> Result<PgStartup, Box<dyn std::error::Error>> {
    let required = required_env;
    let bind: SocketAddr = required("ORDIVON_PG_BIND")?.parse()?;
    if !bind.ip().is_loopback() {
        return Err("PG vertical requires an explicit loopback bind".into());
    }
    #[cfg(windows)]
    let token = {
        if std::env::var_os("ORDIVON_PG_TOKEN").is_some() {
            return Err("native Windows PG requires private bearer file, not inline token".into());
        }
        pg_auth::read_private_token(std::path::Path::new(&required(
            "ORDIVON_BEARER_TOKEN_FILE",
        )?))?
    };
    #[cfg(not(windows))]
    let token = required("ORDIVON_PG_TOKEN")?;
    if token.len() < 32 {
        return Err("ORDIVON_PG_TOKEN requires at least 32 characters".into());
    }
    let auth = pg_auth::PgAuth::from_env(&token)?;
    // Existing deployments retain the exact trusted_local behavior until
    // operators qualify the contained consumer and intentionally cut over.
    let contained_ordinary_only = ordinary_contained_only(
        pg_auth::optional_env("ORDIVON_PG_ORDINARY_EXECUTION_PROFILE")?.as_deref(),
    )?;
    #[cfg(windows)]
    if contained_ordinary_only {
        return Err("native Windows PG does not implement Linux contained_local".into());
    }
    let issuer_schema = pg_auth::optional_env("ORDIVON_PG_HARNESS_ISSUER_SCHEMA")?;
    let harness_bearer_file = pg_auth::optional_env("ORDIVON_PG_HARNESS_TOKEN_FILE")?;
    let harness_principal = pg_auth::optional_env("ORDIVON_PG_HARNESS_PRINCIPAL")?;
    // The dedicated profile must be complete. Bare issuer_schema retains the
    // already-tested, isolated legacy all-Job mode; it must not be installed
    // on a shared endpoint that also accepts ordinary execution requests.
    let isolated_harness = match (harness_bearer_file, harness_principal) {
        (None, None) => None,
        (Some(file), Some(principal)) => {
            if principal == required("ORDIVON_PG_PRINCIPAL")?
                || principal.is_empty()
                || principal.trim() != principal
                || principal.len() > 256
            {
                return Err("Harness principal must be distinct, nonempty and trimmed".into());
            }
            // A dedicated Claim finalizer needs original Runtime PG Workspace
            // ownership only, NOT the optional same-DB Harness Job issuer.
            // With an issuer schema the existing R16 Job source-currentness
            // contract remains exactly as before.
            let dedicated = auth.dedicated_harness_from_file(std::path::Path::new(&file))?;
            Some((dedicated, principal, issuer_schema.clone()))
        }
        _ => {
            return Err(
                "dedicated Harness token file and principal must be configured together".into(),
            )
        }
    };
    // The PG native binary must consume the same two carrier budgets as the
    // legacy entrypoint. Never mistake a legacy MCP compile for PG coverage.
    let headroom_pair = |path_key: &str, minimum_key: &str| {
        parse_pg_headroom_pair(
            path_key,
            minimum_key,
            pg_auth::optional_env(path_key)?,
            pg_auth::optional_env(minimum_key)?,
        )
    };
    let workspace_headroom = [
        headroom_pair(
            "ORDIVON_WORKSPACE_HEADROOM_PATH",
            "ORDIVON_WORKSPACE_MIN_FREE_BYTES",
        )?,
        headroom_pair(
            "ORDIVON_WORKSPACE_GUEST_HEADROOM_PATH",
            "ORDIVON_WORKSPACE_GUEST_MIN_FREE_BYTES",
        )?,
    ]
    .into_iter()
    .flatten()
    .collect();
    // Optional operator-owned Unix payload owner. Ordinary callers never set
    // it. A contained Job requires both nonzero IDs; otherwise admission
    // fails closed rather than running the task as host UID 0.
    let contained_workspace_owner = match (
        pg_auth::optional_env("ORDIVON_PG_WORKSPACE_UID")?,
        pg_auth::optional_env("ORDIVON_PG_WORKSPACE_GID")?,
    ) {
        (None, None) => None,
        (Some(uid), Some(gid)) => {
            let uid = uid.parse::<u32>()?;
            let gid = gid.parse::<u32>()?;
            if uid == 0 || gid == 0 {
                return Err("contained Workspace payload owner must be nonroot".into());
            }
            Some((uid, gid))
        }
        _ => return Err("PG Workspace UID and GID must be configured together".into()),
    };
    require_ordinary_contained_owner(contained_ordinary_only, contained_workspace_owner)?;
    #[cfg(windows)]
    if issuer_schema.is_some() || isolated_harness.is_some() || contained_workspace_owner.is_some()
    {
        return Err("native Windows PG has no qualified Linux issuer/UID transport".into());
    }
    let store_root = PathBuf::from(required("ORDIVON_PG_STORE_ROOT")?);
    #[cfg(windows)]
    let workspace_root = Some(config_workspace_root::windows_workspace_root(
        &store_root,
        &PathBuf::from(required("ORDIVON_PG_WORKSPACE_ROOT")?),
    )?);
    #[cfg(not(windows))]
    let workspace_root = None;
    let config = PgRuntimeConfig {
        #[cfg(windows)]
        windows: windows_config(PathBuf::from(required("ORDIVON_PG_RUNNER")?))?,
        dsn: required("ORDIVON_PG_DSN")?,
        schema: required("ORDIVON_PG_SCHEMA")?,
        source_sha256: required("ORDIVON_PG_SOURCE_SHA256")?,
        // A dedicated authenticated Harness route uses its own cloned
        // PgRuntime configuration (same source/database/Runner, one scheduler).
        // Normal /mcp Job admissions retain their original execution contract.
        harness_issuer_schema: if isolated_harness.is_none() {
            issuer_schema.clone()
        } else {
            None
        },
        harness_dispatch_issuer: isolated_harness
            .as_ref()
            .and_then(|(_, principal, schema)| {
                schema
                    .as_ref()
                    .map(|schema| (principal.clone(), schema.clone()))
            }),
        workspace_headroom,
        executor: UniversalExecutorConfig {
            store_root,
            workspace_root,
            workspace_uid: contained_workspace_owner.map(|(uid, _)| uid),
            workspace_gid: contained_workspace_owner.map(|(_, gid)| gid),
            runner_path: Some(PathBuf::from(required("ORDIVON_PG_RUNNER")?)),
            allowed_executable_roots: serde_json::from_str(&required(
                "ORDIVON_PG_EXECUTABLE_ROOTS_JSON",
            )?)?,
            max_runtime_ms: 30 * 60 * 1000,
            max_output_bytes: 4 * 1024 * 1024,
        },
    };
    let issuer_runtime_config = isolated_harness
        .as_ref()
        .map(|(_, _, schema)| PgRuntimeConfig {
            // Claim-only path shares the existing physical PG owner and
            // never reads an unrelated Harness database/issuer function.
            harness_issuer_schema: schema.clone(),
            harness_dispatch_issuer: None,
            ..config.clone()
        });
    Ok(PgStartup {
        bind,
        auth,
        contained_ordinary_only,
        isolated_harness,
        config,
        issuer_runtime_config,
    })
}

#[cfg(windows)]
fn windows_config(
    launcher_path: PathBuf,
) -> Result<ordivon_runtime_core::WindowsExecutionConfig, Box<dyn std::error::Error>> {
    use ordivon_runtime_core::{WindowsExecutionConfig, WindowsPrivilegedBrokerConfig};
    use pg_auth::optional_env;
    let privileged_broker = match (
        optional_env("ORDIVON_WINDOWS_PRIVILEGED_BROKER_PATH")?,
        optional_env("ORDIVON_WINDOWS_PRIVILEGED_BROKER_PIPE")?,
    ) {
        (None, None) => None,
        (Some(path), Some(pipe_name)) => Some(WindowsPrivilegedBrokerConfig {
            executable_path: path.into(),
            pipe_name,
        }),
        _ => return Err("Windows broker path and pipe must be configured together".into()),
    };
    Ok(WindowsExecutionConfig {
        launcher_path,
        privileged_broker,
        elevated_principals: optional_env("ORDIVON_WINDOWS_ELEVATED_PRINCIPALS_JSON")?
            .map(|v| serde_json::from_str(&v))
            .transpose()?
            .unwrap_or_default(),
        elevated_profiles: optional_env("ORDIVON_WINDOWS_ELEVATED_PROFILES_JSON")?
            .map(|v| serde_json::from_str(&v))
            .transpose()?
            .unwrap_or_default(),
        maintenance_lease_path: optional_env("ORDIVON_WINDOWS_MAINTENANCE_LEASE_PATH")?
            .map(Into::into),
    })
}
