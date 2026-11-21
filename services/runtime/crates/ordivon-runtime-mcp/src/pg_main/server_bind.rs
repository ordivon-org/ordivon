//! Bind original authenticated ordinary and independent Harness Claim/Issuer ports.
use super::{config::required_env, pg_auth};
use ordivon_runtime_core::PgRuntime;
use ordivon_runtime_mcp::server::{ExecutionContext, PgReleaseOperatorConfig, PgRuntimeServer};
use std::path::PathBuf;

pub(super) fn bind_pg_runtime_servers(
    runtime: PgRuntime,
    harness_runtime: Option<PgRuntime>,
    contained_ordinary_only: bool,
    isolated_harness: &Option<(pg_auth::PgAuth, String, Option<String>)>,
) -> Result<(PgRuntimeServer, Option<PgRuntimeServer>), Box<dyn std::error::Error>> {
    let required = required_env;
    // The release interface remains absent unless the separate native
    // operator is explicitly installed/configured. PgRuntimeServer also
    // verifies actual live timer and independently qualified PG release stage.
    let release = std::env::var("ORDIVON_PG_RELEASE_SOURCE_REPO")
        .ok()
        .map(|source_repo| {
            Ok::<_, std::io::Error>(PgReleaseOperatorConfig {
                source_repo: PathBuf::from(source_repo),
                operator_executable: PathBuf::from(required("ORDIVON_PG_RELEASE_OPERATOR_BIN")?),
                receipt_root: PathBuf::from(required("ORDIVON_PG_RELEASE_RECEIPT_ROOT")?),
                dispatcher_timer: required("ORDIVON_PG_RELEASE_DISPATCH_TIMER")?,
            })
        })
        .transpose()?;
    let server = PgRuntimeServer::with_release(
        runtime,
        ExecutionContext {
            principal: required("ORDIVON_PG_PRINCIPAL")?,
            global_limit: 0,
        },
        release,
    );
    let server = if contained_ordinary_only {
        server.restrict_ordinary_jobs_to_contained()
    } else {
        server
    };
    // The ordinary /mcp route ALWAYS starts without Harness Claim release
    // authority. Missing/incomplete dedicated issuer configuration must fail
    // closed, not silently restore the raw early-release attack.
    // Existing ordinary-principal HELD Claims remain pinned; migration to the
    // dedicated issuer needs an exact, consumer-qualified original Run owner.
    let dedicated_server = match (harness_runtime, isolated_harness.as_ref()) {
        (Some(runtime), Some((_, principal, issuer_schema))) => {
            let dedicated = PgRuntimeServer::new(
                runtime,
                ExecutionContext {
                    principal: principal.clone(),
                    global_limit: 0,
                },
            );
            Some(if issuer_schema.is_some() {
                dedicated.for_authenticated_harness_finalizer()
            } else {
                dedicated.for_authenticated_claim_only_finalizer()
            })
        }
        (None, None) => None,
        _ => return Err("incomplete Harness Runtime source/ingress binding".into()),
    };
    Ok((server, dedicated_server))
}
