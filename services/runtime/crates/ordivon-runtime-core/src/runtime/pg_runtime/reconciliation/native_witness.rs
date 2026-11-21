//! Native PID-namespace identity and final Runner-result evidence.
use super::*;

/// NSpid lists kernel PIDs in nested namespaces, from the namespace of the
/// host procfs mount through the innermost namespace. A private systemd
/// PID namespace changes the Runner's getpid() without changing the kernel
/// process starttime. Reject malformed, duplicated, or mismatched host
/// identities rather than trusting a supplied namespace PID alone.
fn namespace_pid_from_host_status(status: &str, host_pid: u32) -> Option<u32> {
    if host_pid == 0 {
        return None;
    }
    let mut namespace_pid = None;
    for line in status.lines() {
        let Some(value) = line.strip_prefix("NSpid:") else {
            continue;
        };
        if namespace_pid.is_some() {
            return None;
        }
        let values: Option<Vec<u32>> = value
            .split_whitespace()
            .map(|part| part.parse::<u32>().ok().filter(|pid| *pid != 0))
            .collect();
        let values = values?;
        if values.first().copied() != Some(host_pid) {
            return None;
        }
        namespace_pid = values.last().copied();
    }
    namespace_pid
}

pub(super) fn observed_namespace_pid(host_pid: u32) -> Option<u32> {
    let status = std::fs::read_to_string(format!("/proc/{host_pid}/status")).ok()?;
    namespace_pid_from_host_status(&status, host_pid)
}

/// One native observation binds the Manager's host PID to the Runner's
/// namespace-local PID and the same kernel process starttime. Keep the
/// three dependent facts together rather than accepting free-floating PIDs.
pub(super) struct NativePidReadback<'a> {
    pub(super) host_pid: Option<u32>,
    pub(super) namespace_pid: Option<u32>,
    pub(super) process_start: Option<&'a str>,
}

/// Project RUNNING only from a positively bound Linux Runner plus the
/// kernel supervisor's host PID, the same kernel process starttime, and its
/// namespace-local PID. An issued dispatch, partial stdout, or the mere
/// presence of runner-start.json is insufficient.
pub(super) fn native_running_witness(
    start: &RunnerStartEvidence,
    native: &std::collections::BTreeMap<String, String>,
    job: &str,
    attempt: &str,
    launch_digest: &str,
    observed: NativePidReadback<'_>,
    provider_digest: &str,
) -> bool {
    let expected_unit = format!("ordivon-pg-{attempt}.service");
    start.schema_version == 1
        && start.job_id == job
        && start.attempt_id == attempt
        && start.launch_token_digest == launch_digest
        && start.unit_name == expected_unit
        && start.control_group == format!("/system.slice/{expected_unit}")
        && start.namespace_pid != 0
        && !start.namespace_process_start_identity.is_empty()
        && observed.host_pid.is_some_and(|pid| pid != 0)
        && observed.namespace_pid == Some(start.namespace_pid)
        && observed.process_start == Some(start.namespace_process_start_identity.as_str())
        && start.observed_unix_ms > 0
        && start.runner_executable_digest.as_deref() == Some(provider_digest)
        && native.get("LoadState").map(String::as_str) == Some("loaded")
        && native.get("ActiveState").map(String::as_str) == Some("active")
        && native.get("InvocationID").map(String::as_str) == Some(start.invocation_id.as_str())
        && !start.invocation_id.is_empty()
        && native.get("ControlGroup").map(String::as_str) == Some(start.control_group.as_str())
        && native
            .get("MainPID")
            .and_then(|pid| pid.parse::<u32>().ok())
            == observed.host_pid
}

pub(super) fn runner_result_still_absent(path: &Path) -> RuntimeResult<bool> {
    match fs::symlink_metadata(path.join("result.json")) {
        Err(err) if err.kind() == std::io::ErrorKind::NotFound => Ok(true),
        Ok(metadata) if metadata.file_type().is_file() => Ok(false),
        Ok(_) => Err(error("Runner result path is not a regular file")),
        Err(err) => Err(io(err)),
    }
}

#[cfg(test)]
mod native_runner_start_tests {
    use super::*;
    use std::collections::BTreeMap;

    fn native_running_witness(
        start: &RunnerStartEvidence,
        native: &BTreeMap<String, String>,
        job: &str,
        attempt: &str,
        launch_digest: &str,
        provider_digest: &str,
    ) -> bool {
        super::native_running_witness(
            start,
            native,
            job,
            attempt,
            launch_digest,
            NativePidReadback {
                host_pid: Some(1234),
                namespace_pid: Some(start.namespace_pid),
                process_start: Some(start.namespace_process_start_identity.as_str()),
            },
            provider_digest,
        )
    }

    #[test]
    fn namespace_status_binding_never_synthesizes_host_or_inner_pid() {
        assert_eq!(
            super::namespace_pid_from_host_status("Name:\trunner\nNSpid:\t54321\t1\n", 54321),
            Some(1)
        );
        assert_eq!(
            super::namespace_pid_from_host_status("NSpid:\t1234\n", 1234),
            Some(1234)
        );
        for broken in [
            "Name:\trunner\n",
            "NSpid:\t54321\t0\n",
            "NSpid:\t54321\tinvalid\n",
            "NSpid:\t54321\t1\nNSpid:\t54321\t1\n",
            "NSpid:\t54322\t1\n",
        ] {
            assert_eq!(super::namespace_pid_from_host_status(broken, 54321), None);
        }
    }

    #[test]
    fn private_pid_namespace_witness_preserves_host_manager_binding() {
        let mut start = start();
        start.namespace_pid = 1;
        let mut native = unit();
        native.insert("MainPID".into(), "54321".into());
        let provider = start.runner_executable_digest.as_deref().unwrap();
        let check = |host_pid, inner_pid, started| {
            super::native_running_witness(
                &start,
                &native,
                "job-a",
                "attempt-a",
                &start.launch_token_digest,
                NativePidReadback {
                    host_pid,
                    namespace_pid: inner_pid,
                    process_start: started,
                },
                provider,
            )
        };
        assert!(check(Some(54321), Some(1), Some("start-1234")));
        assert!(!check(Some(54321), None, Some("start-1234")));
        assert!(!check(Some(54321), Some(54321), Some("start-1234")));
        assert!(!check(Some(54322), Some(1), Some("start-1234")));
        assert!(!check(Some(54321), Some(1), Some("stale-starttime")));
    }

    #[test]
    fn running_witness_rejects_pid_reuse_and_unobserved_kernel_start_identity() {
        let start = start();
        let native = unit();
        let provider = start.runner_executable_digest.as_deref().unwrap();
        for stale in [None, Some("different-kernel-starttime")] {
            assert!(
                !super::native_running_witness(
                    &start,
                    &native,
                    "job-a",
                    "attempt-a",
                    &start.launch_token_digest,
                    NativePidReadback {
                        host_pid: Some(1234),
                        namespace_pid: Some(start.namespace_pid),
                        process_start: stale,
                    },
                    provider
                ),
                "PID-only proof wrongly qualified a replaced or unobserved process"
            );
        }
    }

    fn start() -> RunnerStartEvidence {
        RunnerStartEvidence {
            schema_version: 1,
            job_id: "job-a".into(),
            attempt_id: "attempt-a".into(),
            launch_token_digest: format!("sha256:{}", "a".repeat(64)),
            unit_name: "ordivon-pg-attempt-a.service".into(),
            invocation_id: "invocation-1".into(),
            control_group: "/system.slice/ordivon-pg-attempt-a.service".into(),
            namespace_pid: 1234,
            namespace_process_start_identity: "start-1234".into(),
            payload_uid: None,
            payload_gid: None,
            observed_workspace_source_digest: None,
            runner_executable_digest: Some(format!("sha256:{}", "d".repeat(64))),
            observed_unix_ms: 1000,
        }
    }
    fn unit() -> BTreeMap<String, String> {
        BTreeMap::from([
            ("LoadState".into(), "loaded".into()),
            ("ActiveState".into(), "active".into()),
            ("InvocationID".into(), "invocation-1".into()),
            (
                "ControlGroup".into(),
                "/system.slice/ordivon-pg-attempt-a.service".into(),
            ),
            ("MainPID".into(), "1234".into()),
        ])
    }
    #[test]
    fn runner_running_witness_requires_bound_live_native_identity() {
        let start = start();
        let properties = unit();
        let provider = start.runner_executable_digest.as_deref().unwrap();
        assert!(native_running_witness(
            &start,
            &properties,
            "job-a",
            "attempt-a",
            &start.launch_token_digest,
            provider
        ));
        for (name, wrong) in [
            ("ActiveState", "activating"),
            ("LoadState", "not-found"),
            ("InvocationID", "reused"),
            ("ControlGroup", "/system.slice/wrong.service"),
            ("MainPID", "3456"),
        ] {
            let mut bad = properties.clone();
            bad.insert(name.into(), wrong.into());
            assert!(
                !native_running_witness(
                    &start,
                    &bad,
                    "job-a",
                    "attempt-a",
                    &start.launch_token_digest,
                    provider
                ),
                "{name}"
            );
        }
        let mut missing = start.clone();
        missing.namespace_process_start_identity.clear();
        assert!(!native_running_witness(
            &missing,
            &properties,
            "job-a",
            "attempt-a",
            &start.launch_token_digest,
            provider
        ));
        missing = start.clone();
        missing.runner_executable_digest = None;
        assert!(!native_running_witness(
            &missing,
            &properties,
            "job-a",
            "attempt-a",
            &start.launch_token_digest,
            provider
        ));
        assert!(!native_running_witness(
            &start,
            &properties,
            "job-other",
            "attempt-a",
            &start.launch_token_digest,
            provider
        ));
        assert!(!native_running_witness(
            &start,
            &properties,
            "job-a",
            "attempt-other",
            &start.launch_token_digest,
            provider
        ));
        assert!(!native_running_witness(
            &start,
            &properties,
            "job-a",
            "attempt-a",
            "sha256:wrong",
            provider
        ));
        assert!(!native_running_witness(
            &start,
            &properties,
            "job-a",
            "attempt-a",
            &start.launch_token_digest,
            "sha256:wrong"
        ));
    }
}

#[cfg(test)]
mod late_runner_result_tests {
    use super::*;

    #[test]
    fn post_quiescence_recheck_prevents_false_os_only_lost() {
        // A first probe sees no result; the actual Runner writes it while
        // an independent systemctl/cgroup probe is in flight. The final
        // negative-evidence gate MUST reject LOST in that second state.
        let root =
            std::env::temp_dir().join(format!("ordivon-pg-late-result-{}", uuid::Uuid::now_v7()));
        fs::create_dir(&root).unwrap();
        assert!(runner_result_still_absent(&root).unwrap());
        fs::write(root.join("result.json"), b"native runner terminal bytes").unwrap();
        assert!(!runner_result_still_absent(&root).unwrap());
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn post_quiescence_missing_result_still_allows_native_lost() {
        let root =
            std::env::temp_dir().join(format!("ordivon-pg-absent-result-{}", uuid::Uuid::now_v7()));
        fs::create_dir(&root).unwrap();
        assert!(runner_result_still_absent(&root).unwrap());
        fs::remove_dir_all(root).unwrap();
    }

    #[cfg(target_family = "unix")]
    #[test]
    fn suspicious_runner_result_path_fails_closed() {
        let root = std::env::temp_dir().join(format!(
            "ordivon-pg-result-topology-{}",
            uuid::Uuid::now_v7()
        ));
        fs::create_dir(&root).unwrap();
        fs::create_dir(root.join("result.json")).unwrap();
        assert!(runner_result_still_absent(&root).is_err());
        fs::remove_dir(root.join("result.json")).unwrap();
        std::os::unix::fs::symlink("/dev/null", root.join("result.json")).unwrap();
        assert!(runner_result_still_absent(&root).is_err());
        fs::remove_dir_all(root).unwrap();
    }
}
