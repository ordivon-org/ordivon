//! Preserve real consumer behavior; test placement is not a production contract.
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
