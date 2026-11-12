//! One existing PostgreSQL cluster, one source Run serialization cut, and
//! one Runtime Job admission transaction. No new Store/authority table.
//!
//! This is an OPTIONAL admission-current policy. It neither authenticates
//! arbitrary foreignReferences without an issuer PG read nor claims that
//! source authority remains current at a later systemd-run spawn.
use super::{PgAdmissionError, PgAdmissionInput};
use postgres::Transaction;
use serde_json::Value;
use sha2::{Digest, Sha256};

fn stale() -> PgAdmissionError {
    PgAdmissionError::IssuerNotCurrent
}

fn exact_digest(raw: &[u8], claimed: &str) -> bool {
    format!("sha256:{}", hex::encode(Sha256::digest(raw))) == claimed
}

fn doc(raw: &[u8], claimed: &str) -> Result<Value, PgAdmissionError> {
    if !exact_digest(raw, claimed) {
        return Err(stale());
    }
    // A digest-correct but ambiguous JSON document cannot confer authority.
    let json = std::str::from_utf8(raw).map_err(|_| stale())?;
    if !super::unambiguous_json_object(json) {
        return Err(stale());
    }
    serde_json::from_str(json).map_err(|_| stale())
}

pub(super) fn require_current_harness_issuer_for_new_job(
    tx: &mut Transaction<'_>,
    i: &PgAdmissionInput,
    issuer_schema: &str,
) -> Result<(), PgAdmissionError> {
    // The caller cannot choose this schema. The configured service endpoint
    // uses its existing SAME-PG connection and operator-qualified SQL role.
    // The query identifier has already passed exact_schema.
    if !super::exact_schema(issuer_schema) {
        return Err(stale());
    }
    let plan: Value = serde_json::from_str(&i.execution_plan_json).map_err(|_| stale())?;
    let refs = plan
        .get("foreignReferences")
        .and_then(Value::as_array)
        .ok_or_else(stale)?;
    let mut run_ref = None;
    let mut fence_ref = None;
    for reference in refs {
        if reference.get("namespace").and_then(Value::as_str) != Some("ordivon.harness") {
            continue;
        }
        match reference.get("type").and_then(Value::as_str) {
            Some("harness_run") => {
                if run_ref.replace(reference).is_some() {
                    return Err(stale());
                }
            }
            Some("dispatch_fence") if fence_ref.is_some() => return Err(stale()),
            Some("dispatch_fence") => fence_ref = Some(reference),
            _ => (),
        }
    }
    let run_id = run_ref
        .and_then(|v| v.get("id"))
        .and_then(Value::as_str)
        .filter(|v| v.starts_with("harness-run:"))
        .ok_or_else(stale)?;
    let fence_ref = fence_ref.ok_or_else(stale)?;
    let fence_id = fence_ref
        .get("id")
        .and_then(Value::as_str)
        .filter(|v| v.starts_with("harness-dispatch-fence:"))
        .ok_or_else(stale)?;
    let fence_digest = fence_ref
        .get("digest")
        .and_then(Value::as_str)
        .filter(|v| v.len() == 71 && v.starts_with("sha256:"))
        .ok_or_else(stale)?;
    let generation = fence_ref
        .get("generation")
        .and_then(Value::as_str)
        .and_then(|v| v.parse::<i64>().ok())
        .filter(|v| *v > 0)
        .ok_or_else(stale)?;

    // SECURITY DEFINER locks the issuer Run row for the duration of this
    // same-PG serializable Runtime Job transaction. The Runtime role has only
    // EXECUTE on the source function, not write/read access to private tables.
    // Canonical CAS/Intent verification below is independently Rust-owned.
    let q = format!("SELECT * FROM \"{issuer_schema}\".harness_current_dispatch_cut($1,$2,$3)");
    let row = tx
        .query_opt(&q, &[&run_id, &generation, &fence_digest])?
        .ok_or_else(stale)?;
    let event_kind: String = row.get(0);
    let payload_digest: String = row.get(1);
    let payload_kind: String = row.get(2);
    let payload_size: i64 = row.get(3);
    let payload_raw: Vec<u8> = row.get(4);
    let fence_kind: String = row.get(5);
    let fence_size: i64 = row.get(6);
    let fence_raw: Vec<u8> = row.get(7);
    let intent_object_digest: String = row.get(8);
    let intent_kind: String = row.get(9);
    let intent_len: i64 = row.get(10);
    let intent_raw: Vec<u8> = row.get(11);
    if event_kind != "harness.tool-step-prepared"
        || payload_kind != "ordivon.harness-run-event-payload"
        || fence_kind != "harness-dispatch-fence"
        || payload_size != payload_raw.len() as i64
        || fence_size != fence_raw.len() as i64
        || intent_kind != "harness-tool-step-intent"
        || intent_len != intent_raw.len() as i64
    {
        return Err(stale());
    }
    let payload = doc(&payload_raw, &payload_digest)?;
    let fence = doc(&fence_raw, fence_digest)?;
    let intent = doc(&intent_raw, &intent_object_digest)?;
    let data = payload.get("data").ok_or_else(stale)?;
    if payload.get("schemaVersion").and_then(Value::as_i64) != Some(1)
        || payload.get("eventKind").and_then(Value::as_str) != Some("harness.tool-step-prepared")
        || payload.get("kind").and_then(Value::as_str) != Some("ordivon.harness-run-event-payload")
        || data.get("dispatchFenceDigest").and_then(Value::as_str) != Some(fence_digest)
        || data
            .get("dispatchFenceObjectDigest")
            .and_then(Value::as_str)
            != Some(fence_digest)
        || data.get("toolStepIntentDigest").and_then(Value::as_str)
            != fence.get("intentDigest").and_then(Value::as_str)
        || fence.get("schemaVersion").and_then(Value::as_i64) != Some(2)
        || fence.get("kind").and_then(Value::as_str) != Some("ordivon.harness-dispatch-fence")
        || fence.get("fenceId").and_then(Value::as_str) != Some(fence_id)
        || fence.get("harnessRunId").and_then(Value::as_str) != Some(run_id)
        || fence.get("runRevision").and_then(Value::as_i64) != Some(generation)
        || fence.get("clientRequestId").and_then(Value::as_str)
            != Some(i.client_request_id.as_str())
        || fence.get("runtimeOperation").and_then(Value::as_str) != Some("workspace.exec")
        || data
            .get("toolStepIntentObjectDigest")
            .and_then(Value::as_str)
            != Some(intent_object_digest.as_str())
        || intent.get("schemaVersion").and_then(Value::as_i64) != Some(1)
        || intent.get("kind").and_then(Value::as_str) != Some("ordivon.harness-tool-step-intent")
        || intent.get("harnessRunId").and_then(Value::as_str) != Some(run_id)
        || intent.get("runtimeOperation").and_then(Value::as_str) != Some("workspace.exec")
        || intent
            .get("runtimeArgumentsDigest")
            .and_then(Value::as_str)
            .is_none_or(|v| !v.starts_with("sha256:") || v.len() != 71)
        || intent.get("clientRequestId").and_then(Value::as_str)
            != Some(i.client_request_id.as_str())
    {
        return Err(stale());
    }

    // Never persist source tool inputs/env as raw CAS: metadata-only Harness
    // privacy contracts explicitly prohibit their durable materialization.
    // Its canonical physical execution digest is part of the SAME immutable
    // Tool-prepared Journal Event, which is row-locked and CAS-verified above.
    // Reconstruct the complete physical representation from the actual
    // Owner-resolved execution plan, without trusting caller-supplied hashes.
    let physical_digest = data
        .get("physicalExecutionDigest")
        .and_then(Value::as_str)
        .filter(|v| v.starts_with("sha256:") && v.len() == 71)
        .ok_or_else(stale)?;
    let refs_original = plan
        .get("foreignReferences")
        .and_then(Value::as_array)
        .ok_or_else(stale)?;
    if refs_original.is_empty()
        || refs_original.last() != Some(fence_ref)
        || !plan
            .get("steps")
            .is_none_or(|v| v.as_array().is_some_and(Vec::is_empty))
        || !plan
            .get("hostDependencies")
            .is_none_or(|v| v.as_array().is_some_and(Vec::is_empty))
        || plan.get("executionProfile").and_then(Value::as_str) != Some("trusted_local")
        || plan.get("executionTarget").and_then(Value::as_str) != Some("local_linux")
    {
        return Err(stale());
    }
    let workspace_path = plan
        .get("workspacePath")
        .and_then(Value::as_str)
        .ok_or_else(stale)?;
    let actual_cwd = plan.get("cwd").and_then(Value::as_str).ok_or_else(stale)?;
    let relative_cwd = std::path::Path::new(actual_cwd)
        .strip_prefix(std::path::Path::new(workspace_path))
        .map_err(|_| stale())?;
    let relative_cwd = if relative_cwd.as_os_str().is_empty() {
        ".".to_string()
    } else {
        relative_cwd.to_str().ok_or_else(stale)?.to_string()
    };
    let physical_execution = serde_json::json!({
        "workspaceId": plan.get("workspaceId").ok_or_else(stale)?,
        "executable": plan.get("executable").ok_or_else(stale)?,
        "args": plan.get("args").ok_or_else(stale)?,
        "cwdRelative": relative_cwd,
        "env": plan.get("env").ok_or_else(stale)?,
        "timeoutMs": plan.get("timeoutMs").ok_or_else(stale)?,
        "stdoutLimitBytes": plan.get("stdoutLimitBytes").ok_or_else(stale)?,
        "stderrLimitBytes": plan.get("stderrLimitBytes").ok_or_else(stale)?,
        "foreignReferences": &refs_original[..refs_original.len() - 1],
    });
    let canonical = serde_json::to_vec(&physical_execution).map_err(|_| stale())?;
    if !exact_digest(&canonical, physical_digest) {
        return Err(stale());
    }

    // Source-generated issue time/expiry are constrained by this PG cluster's
    // clock, not the untrusted request or an arbitrary agent-supplied now_ms.
    let now_ms: i64 = tx
        .query_one(
            "SELECT floor(extract(epoch FROM clock_timestamp()) * 1000)::bigint",
            &[],
        )?
        .get(0);
    let issued = fence
        .get("issuedAtMs")
        .and_then(Value::as_i64)
        .ok_or_else(stale)?;
    let expiry = fence
        .get("expiresAtMs")
        .and_then(Value::as_i64)
        .ok_or_else(stale)?;
    if issued > now_ms || expiry <= now_ms || issued >= expiry {
        return Err(stale());
    }
    Ok(())
}
