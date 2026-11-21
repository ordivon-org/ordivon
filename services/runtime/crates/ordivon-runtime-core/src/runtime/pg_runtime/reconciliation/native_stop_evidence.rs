//! Lost-result evidence for a quiescent exact systemd Runner/Attempt.
//! No terminal transition is inferred from merely missing result.json.
use super::*;

impl PgRuntime {
    pub(super) fn reconcile_absent_runner_result(
        &self,
        db: &mut PgAdmissionStore,
        job: &str,
        a: &AttemptRecord,
        provider: &serde_json::Value,
        path: &Path,
    ) -> RuntimeResult<()> {
        // The kernel may have terminated the systemd-owned process tree
        // before Runner could write result.json. A missing result file is
        // not evidence that the process is still alive. Observe the exact
        // native Unit and its cgroup instead of inventing PID-tree logic.
        if a.unit_name != format!("ordivon-pg-{}.service", a.attempt_id) {
            return Err(error("Attempt native unit identity mismatch"));
        }
        let properties = super::platform::systemctl_show(&a.unit_name)?;
        if super::platform::unit_is_active(&properties)
            || super::platform::unit_has_pending_job(&properties)
        {
            return Ok(());
        }
        let start_path = path.join("runner-start.json");
        let (runner_start, runner_start_digest): (Option<RunnerStartEvidence>, String) =
            if start_path.exists() {
                let bytes = fs::read(&start_path).map_err(io)?;
                let start: RunnerStartEvidence = serde_json::from_slice(&bytes).map_err(io)?;
                if start.control_group != format!("/system.slice/{}", a.unit_name)
                    || start.job_id != job
                    || start.attempt_id != a.attempt_id
                    || start.launch_token_digest != a.launch_token_digest
                    || start.unit_name != a.unit_name
                    || start.invocation_id.is_empty()
                {
                    return Err(error("Runner identity mismatch during native cancellation"));
                }
                if super::platform::nonempty_property(&properties, "InvocationID")
                    .is_some_and(|observed| observed != start.invocation_id)
                {
                    return Err(error("Native Unit invocation changed during cancellation"));
                }
                (Some(start), universal::sha256_bytes(&bytes))
            } else {
                // A transient Unit can be absent while systemd-run has not
                // finished dispatch. Without a bound Runner start, its
                // absence cannot fence a late physical launch.
                return Ok(());
            };
        let observed_cgroup = super::platform::nonempty_property(&properties, "ControlGroup");
        let cgroup = runner_start
            .as_ref()
            .map(|start| start.control_group.as_str())
            .or(observed_cgroup.as_deref());
        let Some(cgroup) = cgroup else {
            return Ok(());
        };
        let population = super::platform::cgroup_population(cgroup)?;
        let removed = population == super::platform::CgroupPopulation::Removed;
        if !matches!(
            properties.get("ActiveState").map(String::as_str),
            Some("inactive" | "failed")
        ) || !matches!(
            properties.get("LoadState").map(String::as_str),
            Some("loaded" | "not-found")
        ) || runner_start
            .as_ref()
            .and_then(|start| start.runner_executable_digest.as_deref())
            != provider["executionProvider"]["executableDigest"].as_str()
        {
            return Ok(());
        }
        // CollectMode=inactive retains a *failed* transient even after
        // systemd has killed its cgroup. Do not reset-failed first: its
        // invocation identity is valuable evidence until PG commits LOST.
        // Only the exact Runner start + same systemd InvocationID + no
        // MainPID can authorize the failed/removed classification.
        let bound_failed_unit = runner_start.as_ref().is_some_and(|start| {
            super::native_stop::failed_unit_matches_runner(
                properties.get("LoadState").map(String::as_str),
                properties.get("ActiveState").map(String::as_str),
                properties.get("InvocationID").map(String::as_str),
                &start.invocation_id,
                properties.get("MainPID").map(String::as_str),
            )
        });
        if super::native_stop::decide_native_stop(
            super::platform::unit_is_active(&properties),
            super::platform::unit_has_pending_job(&properties),
            properties
                .get("LoadState")
                .is_some_and(|state| state == "not-found"),
            bound_failed_unit,
            runner_start.is_some(),
            population,
        ) != super::native_stop::NativeStopDecision::CommitLost
        {
            return Ok(());
        }
        // A failed-but-retained Unit can be queried again while the cgroup
        // is gone. Confirm it still owns the same invocation and is still
        // failed, not a different process launched under the same name.
        if bound_failed_unit {
            let recheck = super::platform::systemctl_show(&a.unit_name)?;
            if !super::native_stop::failed_unit_matches_runner(
                recheck.get("LoadState").map(String::as_str),
                recheck.get("ActiveState").map(String::as_str),
                recheck.get("InvocationID").map(String::as_str),
                runner_start
                    .as_ref()
                    .map(|start| start.invocation_id.as_str())
                    .unwrap_or(""),
                recheck.get("MainPID").map(String::as_str),
            ) || super::platform::unit_has_pending_job(&recheck)
                || super::platform::cgroup_population(cgroup)?
                    != super::platform::CgroupPopulation::Removed
            {
                return Ok(());
            }
        }
        // Kernel cgroup quiescence proves the bound process tree is gone.
        // Without a Runner result the execution outcome remains LOST,
        // not a fabricated successful cancellation or external effect.
        let (terminal_state, reason_code) = ("lost", "NATIVE_CGROUP_QUIESCENT_NO_TERMINAL_RESULT");
        let native_receipt = json!({
            "schemaVersion": 1,
            "jobId": job,
            "attemptId": a.attempt_id,
            "unitName": a.unit_name,
            "activeState": properties.get("ActiveState"),
            "loadState": properties.get("LoadState"),
            "controlGroup": cgroup,
            "runnerStartObserved": runner_start.is_some(),
            "runnerStartDigest": runner_start_digest,
            "nativeCgroupState": population.as_str(),
            "failedUnitInvocationBound": bound_failed_unit,
            "nativeUnitResult": properties.get("Result"),
            "kernelCgroupPopulated": population.observed_population(),
            "kernelCgroupRemoved": removed,
            "finishedAtMs": now()?,
            "terminalState": terminal_state
        });
        let proposed_bytes = serde_json::to_vec(&native_receipt).map_err(io)?;
        let receipt_path = path.join("native-stop-evidence.json");
        let receipt_lock = fs::OpenOptions::new()
            .create(true)
            .truncate(false)
            .write(true)
            .open(path.join("native-stop-evidence.lock"))
            .map_err(io)?;
        // Rust std locks this File as flock(LOCK_EX) on Unix and
        // LockFileEx on Windows. Keep the exclusive guard alive until
        // the native receipt and PG terminal+Artifact CAS are resolved.
        // The lock is relinquished automatically when File is dropped.
        receipt_lock.lock().map_err(io)?;
        // A result that arrived while systemctl/cgroup was being queried
        // must take the existing digest/identity-verified result path on
        // the *next* reconciliation. Do not commit an irreversible LOST
        // terminal when that stronger Runner receipt is now available.
        // At this point the bound native cgroup is already quiescent, so
        // the Runner cannot subsequently publish this file from the
        // same owned process tree.
        if !runner_result_still_absent(&path)? {
            return Ok(());
        }
        let receipt_bytes = if receipt_path.exists() {
            // A PG COMMIT acknowledgement can be lost after immutable
            // native evidence was written. Native Unit LoadState may
            // subsequently change from inactive to not-found: do not
            // re-author the original evidence or make a retry impossible.
            // Recheck kernel quiescence above and then replay the original
            // receipt only for the same exact Attempt/Runner identity.
            let retained = fs::read(&receipt_path).map_err(io)?;
            let prior: serde_json::Value = serde_json::from_slice(&retained).map_err(io)?;
            if prior["schemaVersion"].as_u64() != Some(1)
                || prior["jobId"].as_str() != Some(job)
                || prior["attemptId"].as_str() != Some(a.attempt_id.as_str())
                || prior["unitName"].as_str() != Some(a.unit_name.as_str())
                || prior["controlGroup"].as_str() != Some(cgroup)
                || prior["runnerStartDigest"].as_str() != Some(runner_start_digest.as_str())
                || prior["runnerStartObserved"].as_bool() != Some(true)
                || !matches!(
                    prior["nativeCgroupState"].as_str(),
                    Some("unpopulated" | "removed")
                )
                || prior["terminalState"].as_str() != Some(terminal_state)
            {
                return Err(error("native stop evidence identity mismatch"));
            }
            retained
        } else {
            universal::write_bytes_atomic(&receipt_path, &proposed_bytes).map_err(io)?;
            proposed_bytes
        };
        let receipt_digest = universal::sha256_bytes(&receipt_bytes);
        let retained: serde_json::Value = serde_json::from_slice(&receipt_bytes).map_err(io)?;
        let finished_at_ms = retained["finishedAtMs"]
            .as_i64()
            .ok_or_else(|| error("native stop receipt omitted finish time"))?;
        let terminal = PgTerminalNoArtifacts {
            attempt_id: a.attempt_id.clone(),
            expected_row_version: a.row_version as i64,
            terminal_state: terminal_state.to_string(),
            result_digest: receipt_digest.clone(),
            reason_code: reason_code.to_string(),
            exit_code: None,
            finished_at_ms,
            expected_source_sha256: self.config.source_sha256.clone(),
        };
        let artifact = PgArtifactRegistration {
            artifact_id: format!("artifact-{}-native-stop", a.attempt_id),
            kind: "native_stop_evidence".to_string(),
            relative_path: "native-stop-evidence.json".to_string(),
            digest: receipt_digest,
            media_type: "application/json".to_string(),
            byte_length: i64::try_from(receipt_bytes.len()).map_err(io)?,
            truncated: false,
            created_at_ms: finished_at_ms,
        };
        // Reuse the existing PG atomic terminal/reservation/Artifact
        // transaction. Kernel process absence is evidence of liveness,
        // not proof of a successful arbitrary external effect.
        db.commit_terminal_with_artifacts(&terminal, &[artifact])
            .map_err(pg)?;
        // Only now may systemd forget a failed transient. This ordering
        // keeps its positive failure/InvocationID evidence available for
        // the irreversible LOST decision and its durable receipt.
        super::platform::release_terminal_unit(&a.unit_name);
        Ok(())
    }
}
