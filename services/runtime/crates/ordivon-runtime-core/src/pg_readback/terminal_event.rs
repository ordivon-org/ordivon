use super::types::PgJobSnapshot;
use crate::pg_admission::{
    PgAdmissionError, PgArtifactRegistration, pg_artifact_manifest_digest, valid_pg_artifacts,
};
use postgres::Transaction;
use sha2::{Digest, Sha256};

/// Check terminal event digests in the same repeatable-read snapshot.
/// This qualifies recorded evidence only, never a physical effect.
pub(super) fn terminal_events_coherent(
    tx: &mut Transaction<'_>,
    snapshot: &PgJobSnapshot,
) -> Result<bool, PgAdmissionError> {
    let Some(resolution) = snapshot.resolution.as_deref() else {
        return Ok(true);
    };
    // ReleaseEffect has an independently privileged *operator* and its own
    // receipt. It is not a systemd Runner process; forging PROCESS_EXITED
    // would violate the physical-evidence model. Admit a distinct, digest-
    // bound operator terminal event only when this Job has committed release
    // side truth. The filesystem receipt is separately verified by
    // ReleaseStateContract on release.get.
    let release = tx.query_opt(
        "SELECT effect_id,request_digest FROM job_runtime_release_effects WHERE job_id=$1",
        &[&snapshot.job_id],
    )?;
    let event_query = if release.is_some() {
        "SELECT event_type,origin,new_state,detail_json,detail_digest,event_sequence FROM job_events WHERE job_id=$1 AND attempt_id=$2 AND event_type IN ('RELEASE_EFFECT_RECEIPTED','JOB_TERMINAL') ORDER BY event_sequence"
    } else {
        "SELECT event_type,origin,new_state,detail_json,detail_digest,event_sequence FROM job_events WHERE job_id=$1 AND attempt_id=$2 AND event_type IN ('PROCESS_EXITED','NATIVE_HANDOFF_PREVENTED','JOB_TERMINAL') ORDER BY event_sequence"
    };
    let rows = tx.query(event_query, &[&snapshot.job_id, &snapshot.attempt_id])?;
    if rows.len() != 2 {
        return Ok(false);
    }
    // All terminal writers append the original source witness followed by
    // JOB_TERMINAL as consecutive events in the same transaction. Digest
    // validity alone cannot qualify a reversed or separated causal pair.
    let source_sequence: i64 = rows[0].get(5);
    let derived_sequence: i64 = rows[1].get(5);
    if source_sequence <= 0
        || source_sequence.checked_add(1) != Some(derived_sequence)
        || rows[0].get::<_, String>(0) == "JOB_TERMINAL"
        || rows[1].get::<_, String>(0) != "JOB_TERMINAL"
    {
        return Ok(false);
    }
    let artifact_rows = tx.query(
        "SELECT job_id,artifact_id,kind,relative_path,digest,media_type,byte_length,truncated,created_at_ms FROM artifacts WHERE attempt_id=$1 ORDER BY artifact_id",
        &[&snapshot.attempt_id],
    )?;
    let mut artifacts = Vec::with_capacity(artifact_rows.len());
    for row in artifact_rows {
        if row.get::<_, String>(0) != snapshot.job_id {
            return Ok(false);
        }
        artifacts.push(PgArtifactRegistration {
            artifact_id: row.get(1),
            kind: row.get(2),
            relative_path: row.get(3),
            digest: row.get(4),
            media_type: row.get(5),
            byte_length: row.get(6),
            truncated: row.get(7),
            created_at_ms: row.get(8),
        });
    }
    if !valid_pg_artifacts(&artifacts) {
        return Ok(false);
    }
    let expected_manifest = if artifacts.is_empty() {
        None
    } else {
        Some(pg_artifact_manifest_digest(&artifacts))
    };
    // A structured installer owns its receipt, not a native Runner Artifact.
    // Unexpected generic Artifacts invalidate its dedicated terminal proof.
    if release.is_some() && !artifacts.is_empty() {
        return Ok(false);
    }
    let mut terminal_source_observed = false;
    let mut terminal_recorded = false;
    for row in rows {
        let event_type: String = row.get(0);
        let origin: String = row.get(1);
        let state: Option<String> = row.get(2);
        let detail_json: String = row.get(3);
        let digest: String = row.get(4);
        if format!(
            "sha256:{}",
            hex::encode(Sha256::digest(detail_json.as_bytes()))
        ) != digest
            || state.as_deref() != Some(resolution)
        {
            return Ok(false);
        }
        let Ok(detail) = serde_json::from_str::<serde_json::Value>(&detail_json) else {
            return Ok(false);
        };
        match event_type.as_str() {
            "RELEASE_EFFECT_RECEIPTED" if origin == "OPERATOR_OBSERVED" && release.is_some() => {
                let authority = release.as_ref().expect("guarded release binding");
                let bound_effect: String = authority.get(0);
                let bound_request: String = authority.get(1);
                if terminal_source_observed
                    || detail.get("resultDigest").and_then(|v| v.as_str())
                        != snapshot.result_digest.as_deref()
                    || detail.get("receiptDigest").and_then(|v| v.as_str())
                        != snapshot.result_digest.as_deref()
                    || detail.get("effectId").and_then(|v| v.as_str())
                        != Some(bound_effect.as_str())
                    || detail.get("requestDigest").and_then(|v| v.as_str())
                        != Some(bound_request.as_str())
                {
                    return Ok(false);
                }
                terminal_source_observed = true;
            }
            "NATIVE_HANDOFF_PREVENTED"
                if origin == "SYSTEM_DERIVED"
                    && release.is_none()
                    && resolution == "cancelled"
                    && snapshot.desired_state == "cancelled"
                    && artifacts.is_empty() =>
            {
                // This is a positive issuer-before-OS-call cancellation,
                // deliberately NOT a PROCESS_EXITED or systemd Manager ACK.
                // Source code's at-most-once physical handoff ordering is
                // needed in addition to these durable PG events.
                if terminal_source_observed
                    || detail.get("resultDigest").and_then(|v| v.as_str())
                        != snapshot.result_digest.as_deref()
                    || detail.get("nativeCallIssued").and_then(|v| v.as_bool()) != Some(false)
                    || detail.get("dispatchIssued").and_then(|v| v.as_bool()) != Some(true)
                {
                    return Ok(false);
                }
                let issued: i64 = tx.query_one(
                    "SELECT COUNT(*) FROM job_events WHERE job_id=$1 AND attempt_id=$2                      AND event_type='DISPATCH_ISSUED' AND origin='SYSTEM_DERIVED'                      AND reason_code='AT_MOST_ONCE_BOUNDARY_COMMITTED'",
                    &[&snapshot.job_id, &snapshot.attempt_id],
                )?.get(0);
                let stopped: i64 = tx.query_one(
                    "SELECT COUNT(*) FROM job_events WHERE job_id=$1 AND attempt_id=$2                      AND event_type='STOP_REQUESTED'",
                    &[&snapshot.job_id, &snapshot.attempt_id],
                )?.get(0);
                let runner_bound: i64 = tx.query_one(
                    "SELECT COUNT(*) FROM job_events WHERE job_id=$1 AND attempt_id=$2                      AND event_type='RUNNER_BOUND'",
                    &[&snapshot.job_id, &snapshot.attempt_id],
                )?.get(0);
                if issued != 1 || stopped != 1 || runner_bound != 0 {
                    return Ok(false);
                }
                terminal_source_observed = true;
            }
            "PROCESS_EXITED" if origin == "SYSTEM_OBSERVED" => {
                if terminal_source_observed
                    || detail.get("resultDigest").and_then(|v| v.as_str())
                        != snapshot.result_digest.as_deref()
                    || detail.get("artifactSetDigest").and_then(|v| v.as_str())
                        != expected_manifest.as_deref()
                {
                    return Ok(false);
                }
                terminal_source_observed = true;
            }
            "JOB_TERMINAL" if origin == "SYSTEM_DERIVED" => {
                if terminal_recorded
                    || detail.get("resolution").and_then(|v| v.as_str()) != Some(resolution)
                {
                    return Ok(false);
                }
                terminal_recorded = true;
            }
            _ => return Ok(false),
        }
    }
    Ok(terminal_source_observed && terminal_recorded)
}
