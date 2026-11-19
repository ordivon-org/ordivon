//! The only Windows PG terminalization adapter, reusing the existing
//! native issuer witness, PostgreSQL Journal and terminal+Artifact CAS.
//!
//! Logic: result bytes -> original native owner -> durable kernel drain event
//! -> exact terminal decision. Capability: original PG writer & Artifacts.
//! This is not a second Windows registry, policy layer or PID-based kill loop.
use super::{
    inspect_windows_pg_bundle, read_raw_bounded, read_value, sha256, PgWindowsWitnessIdentity,
    PgWindowsWitnessObservation, PgWindowsWitnessPhase,
};
use crate::pg_admission::{PgArtifactRegistration, PgTerminalNoArtifacts};
use serde_json::Value;
use std::path::Path;

fn bounded_output_artifact(
    dir: &Path,
    attempt: &str,
    name: &str,
    result: &Value,
    finished: i64,
) -> Result<PgArtifactRegistration, String> {
    let path = format!("{name}.log");
    let output = result
        .get(name)
        .ok_or_else(|| format!("{name}: missing Windows native output"))?;
    if output.get("fileName").and_then(Value::as_str) != Some(path.as_str()) {
        return Err(format!("{name}: unexpected file name"));
    }
    let bytes = read_raw_bounded(&dir.join(&path))?;
    let digest = sha256(&bytes);
    if output.get("retainedBytes").and_then(Value::as_u64) != Some(bytes.len() as u64)
        || output.get("digest").and_then(Value::as_str) != Some(digest.as_str())
    {
        return Err(format!(
            "{name}: registered bytes do not match native Result"
        ));
    }
    let truncated = output
        .get("truncated")
        .and_then(Value::as_bool)
        .unwrap_or(false);
    Ok(PgArtifactRegistration {
        artifact_id: format!("{attempt}.{name}"),
        kind: name.to_owned(),
        relative_path: path,
        digest,
        media_type: "text/plain; charset=utf-8".into(),
        byte_length: i64::try_from(bytes.len()).map_err(|_| "unbounded Windows output")?,
        truncated,
        created_at_ms: finished,
    })
}

/// Pure evidence-to-transaction preparation; it cannot claim an OS process
/// exited and cannot perform a database write. The actual caller MUST first
/// independently qualify the native owner and a durable original-issuer event.
pub(crate) fn prepare_windows_terminal(
    dir: &Path,
    id: &PgWindowsWitnessIdentity,
    witness: &PgWindowsWitnessObservation,
    source_sha256: &str,
    expected_row_version: i64,
) -> Result<(PgTerminalNoArtifacts, Vec<PgArtifactRegistration>), String> {
    if witness.phase != PgWindowsWitnessPhase::ResultWitnessPendingOsReconciliation
        || witness.result_digest.is_none()
        || expected_row_version < 0
        || source_sha256.len() != 64
        || !source_sha256.bytes().all(|c| c.is_ascii_hexdigit())
    {
        return Err("unqualified native Windows terminal preparation".into());
    }
    let Some((raw, result_bytes)) = read_value(&dir.join("result.json"))? else {
        return Err("Windows Result is absent".into());
    };
    let actual_digest = sha256(&result_bytes);
    if witness.result_digest.as_deref() != Some(actual_digest.as_str()) {
        return Err("Windows Result changed after native witness".into());
    }
    let status = raw
        .get("status")
        .and_then(Value::as_str)
        .ok_or("missing Windows Result status")?;
    let timed_out = raw
        .get("timedOut")
        .and_then(Value::as_bool)
        .ok_or("missing Windows timeout evidence")?;
    let exit_code = raw
        .get("exitCode")
        .and_then(Value::as_i64)
        .map(i32::try_from)
        .transpose()
        .map_err(|_| "Windows exit code out of bounds")?;
    let (terminal, reason) = match (status, timed_out, exit_code) {
        ("COMPLETED", false, Some(0)) => ("succeeded", "WINDOWS_NATIVE_TARGET_SUCCEEDED"),
        ("FAILED", true, _) => ("timed_out", "WINDOWS_NATIVE_TARGET_TIMED_OUT"),
        ("FAILED", false, Some(_)) => ("failed", "WINDOWS_NATIVE_TARGET_FAILED"),
        ("CANCELLED", false, _) => ("cancelled", "WINDOWS_NATIVE_CANCELLED"),
        _ => return Err("contradictory Windows result status/timing/exit".into()),
    };
    let finished = raw
        .get("finishedUnixMs")
        .and_then(Value::as_i64)
        .filter(|ms| *ms > 0)
        .ok_or("Windows Result has no positive finish timestamp")?;
    let mut artifacts = vec![
        bounded_output_artifact(dir, &id.attempt_id, "stdout", &raw, finished)?,
        bounded_output_artifact(dir, &id.attempt_id, "stderr", &raw, finished)?,
    ];
    artifacts.push(PgArtifactRegistration {
        artifact_id: format!("{}.result", id.attempt_id),
        kind: "execution_result".into(),
        relative_path: "result.json".into(),
        digest: actual_digest.clone(),
        media_type: "application/json".into(),
        byte_length: i64::try_from(result_bytes.len()).map_err(|_| "unbounded Result")?,
        truncated: false,
        created_at_ms: finished,
    });
    Ok((
        PgTerminalNoArtifacts {
            attempt_id: id.attempt_id.clone(),
            expected_row_version,
            terminal_state: terminal.into(),
            result_digest: actual_digest,
            reason_code: reason.into(),
            exit_code,
            finished_at_ms: finished,
            expected_source_sha256: source_sha256.to_owned(),
        },
        artifacts,
    ))
}

/// Single repeated observation, no new Attempt and no re-spawn.
///
/// During original Launcher lifetime: validate mutable result bytes, prove
/// native JobObject Empty via the kernel-peered pipe, COMMIT its unique event
/// in existing PG Job Journal, ACK so original Launcher can exit.
///
/// After original Launcher exit: read the SAME digest-bound result again;
/// require original-issuer durable event and named JobObject destroyed, then
/// let the one existing PostgreSQL CAS atomically terminalize Job, Attempt,
/// reservation and registered stdout/stderr/Result Artifacts.
///
/// Missing or ambiguous OS data -> Ok(false) (unknown). Inconsistent/broken
/// original identity -> Err without terminal. Safe for repeated reconcile.
#[cfg(windows)]
pub(crate) fn reconcile_windows_native_terminal(
    store: &mut crate::pg_admission::PgAdmissionStore,
    dir: &Path,
    id: &PgWindowsWitnessIdentity,
    source_sha256: &str,
    expected_row_version: i64,
) -> Result<bool, String> {
    use super::{
        inspect_windows_pg_job_object, inspect_windows_pg_os_owner, native_terminal_gate,
        PgWindowsJobObjectState, PgWindowsOwnerState,
    };
    use crate::pg_admission::PgNativeWindowsDrainInput;
    let witness = inspect_windows_pg_bundle(dir, id)?;
    if witness.phase != PgWindowsWitnessPhase::ResultWitnessPendingOsReconciliation {
        return Ok(false);
    }
    match inspect_windows_pg_os_owner(&witness) {
        PgWindowsOwnerState::Alive => {
            // Parent's original process is still alive: commit the native
            // positive event while the ORIGINAL Job Object handle exists.
            native_terminal_gate::record_verified_native_drain(
                store,
                source_sha256,
                expected_row_version,
                id,
                &witness,
            )?;
            Ok(false)
        }
        PgWindowsOwnerState::Exited | PgWindowsOwnerState::PidAbsent => {
            // The named JobObject must be physically GONE after the original
            // Launcher exits. Empty with foreign handles is insufficient.
            if inspect_windows_pg_job_object(&witness) != PgWindowsJobObjectState::NotFound {
                return Ok(false);
            }
            let event = PgNativeWindowsDrainInput {
                job_id: id.job_id.clone(),
                attempt_id: id.attempt_id.clone(),
                expected_row_version,
                expected_source_sha256: source_sha256.to_owned(),
                launch_token_digest: id.launch_token_digest.clone(),
                request_digest: id.request_digest.clone(),
                result_digest: witness
                    .result_digest
                    .clone()
                    .ok_or("Result digest absent")?,
                launcher_process_id: witness
                    .launcher_process_id
                    .ok_or("original Launcher PID absent")?
                    .try_into()
                    .map_err(|_| "Launcher PID out of range")?,
                launcher_creation_file_time: witness
                    .launcher_creation_file_time
                    .ok_or("original Launcher creation time absent")?,
                // Reader validates the ORIGINAL persisted event timestamp and
                // identity, not this caller's new wall-clock observation.
                observed_at_ms: 0,
            };
            if !store
                .qualified_native_windows_drain(&event)
                .map_err(|e| format!("PG original drain event qualification: {e:?}"))?
            {
                return Ok(false);
            }
            let (terminal, artifacts) =
                prepare_windows_terminal(dir, id, &witness, source_sha256, expected_row_version)?;
            store
                .commit_terminal_with_artifacts(&terminal, &artifacts)
                .map_err(|e| format!("PG native Windows terminal+Artifact CAS: {e:?}"))?;
            Ok(true)
        }
        PgWindowsOwnerState::Unknown | PgWindowsOwnerState::IdentityConflict => Ok(false),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use tempfile::TempDir;

    fn fixtures() -> (
        TempDir,
        PgWindowsWitnessIdentity,
        PgWindowsWitnessObservation,
    ) {
        let dir = TempDir::new().unwrap();
        let id = PgWindowsWitnessIdentity {
            job_id: "job-native-win".into(),
            attempt_id: "attempt-native-win".into(),
            launch_token_digest: format!("sha256:{}", "a".repeat(64)),
            request_digest: format!("sha256:{}", "b".repeat(64)),
            launcher_image_digest: format!("sha256:{}", "c".repeat(64)),
        };
        let put = |file: &str, value: &Value| {
            std::fs::write(dir.path().join(file), serde_json::to_vec(value).unwrap()).unwrap();
        };
        put(
            "windows-launcher-start.json",
            &json!({
                "schemaVersion":1,"jobId":id.job_id,"attemptId":id.attempt_id,
                "launchTokenDigest":id.launch_token_digest,"requestDigest":id.request_digest,
                "jobName":"Ordivon.attempt-native-win","launcherImageDigest":id.launcher_image_digest,
                "launcherProcessId":111,"launcherProcessCreationTimeFileTime":222,"observedUnixMs":1
            }),
        );
        put(
            "windows-start.json",
            &json!({
                "schemaVersion":1,"jobId":id.job_id,"attemptId":id.attempt_id,
                "launchTokenDigest":id.launch_token_digest,"requestDigest":id.request_digest,
                "jobName":"Ordivon.attempt-native-win","launcherImageDigest":id.launcher_image_digest,
                "launcherProcessId":111,"launcherProcessCreationTimeFileTime":222,"observedUnixMs":2,
                "processId":333,"processCreationTimeFileTime":444
            }),
        );
        std::fs::write(dir.path().join("stdout.log"), b"HELLO_WIN_NATIVE").unwrap();
        std::fs::write(dir.path().join("stderr.log"), b"").unwrap();
        put(
            "result.json",
            &json!({
                "schemaVersion":1,"jobId":id.job_id,"attemptId":id.attempt_id,"taskId":id.attempt_id,
                "launchTokenDigest":id.launch_token_digest,"status":"COMPLETED","exitCode":0,
                "timedOut":false,"startedUnixMs":5,"finishedUnixMs":6,
                "stdout":{"fileName":"stdout.log","digest":sha256(b"HELLO_WIN_NATIVE"),"retainedBytes":16,"truncated":false},
                "stderr":{"fileName":"stderr.log","digest":sha256(b""),"retainedBytes":0,"truncated":false}
            }),
        );
        let witness = inspect_windows_pg_bundle(dir.path(), &id).unwrap();
        (dir, id, witness)
    }
    #[test]
    fn result_preparation_is_not_a_terminal_and_has_three_digest_bound_artifacts() {
        let (d, id, w) = fixtures();
        let (t, artifacts) =
            prepare_windows_terminal(d.path(), &id, &w, &"d".repeat(64), 2).unwrap();
        assert_eq!(t.terminal_state, "succeeded");
        assert_eq!(t.exit_code, Some(0));
        assert_eq!(artifacts.len(), 3);
        assert_eq!(artifacts[0].kind, "stdout");
        assert_eq!(artifacts[0].byte_length, 16);
        assert_eq!(artifacts[1].kind, "stderr");
        assert_eq!(artifacts[2].kind, "execution_result");
        assert!(!w.terminal_proven);
        assert!(!t.result_digest.is_empty());
    }
    #[test]
    fn terminal_preparation_rejects_changed_output_and_result() {
        let (d, id, w) = fixtures();
        std::fs::write(d.path().join("stdout.log"), b"MUTATED").unwrap();
        assert!(prepare_windows_terminal(d.path(), &id, &w, &"d".repeat(64), 2).is_err());
        std::fs::write(d.path().join("stdout.log"), b"HELLO_WIN_NATIVE").unwrap();
        let mut raw: Value =
            serde_json::from_slice(&std::fs::read(d.path().join("result.json")).unwrap()).unwrap();
        raw["finishedUnixMs"] = json!(999);
        std::fs::write(
            d.path().join("result.json"),
            serde_json::to_vec(&raw).unwrap(),
        )
        .unwrap();
        assert!(prepare_windows_terminal(d.path(), &id, &w, &"d".repeat(64), 2).is_err());
    }
}
