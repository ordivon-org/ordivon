//! Preserve real consumer behavior; test placement is not a production contract.
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
