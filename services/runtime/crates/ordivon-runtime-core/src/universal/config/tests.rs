//! Validate real native config capability, not source file placement.
use super::{UniversalExecErrorCode, UniversalExecutorConfig};
use std::path::PathBuf;

fn config(root: PathBuf) -> UniversalExecutorConfig {
    let runner = std::env::current_exe().unwrap();
    let executable_root = runner.parent().unwrap().to_path_buf();
    UniversalExecutorConfig {
        store_root: root,
        workspace_root: None,
        workspace_uid: None,
        workspace_gid: None,
        runner_path: Some(runner),
        allowed_executable_roots: vec![executable_root],
        max_runtime_ms: 10_000,
        max_output_bytes: 1024,
    }
}

#[test]
fn incomplete_native_task_identity_is_rejected_before_any_store_effect() {
    let root = std::env::temp_dir().join(format!(
        "runtime-native-config-no-effect-{}",
        uuid::Uuid::now_v7()
    ));
    let mut cfg = config(root.clone());
    cfg.workspace_uid = Some(65534);
    let err = cfg
        .ensure_store()
        .expect_err("UID without GID must not prepare stores");
    assert_eq!(err.code, UniversalExecErrorCode::InvalidRequest);
    assert_eq!(err.field.as_deref(), Some("workspaceUid"));
    assert!(
        !root.exists(),
        "invalid owner config must not mutate the filesystem"
    );
    cfg.workspace_gid = Some(65534);
    #[cfg(unix)]
    cfg.validate()
        .expect("complete nonroot identity can be qualified");
    #[cfg(not(unix))]
    {
        let error = cfg
            .ensure_store()
            .expect_err("Unix UID/GID must not qualify a non-Unix owner");
        assert_eq!(error.code, UniversalExecErrorCode::InvalidRequest);
        assert_eq!(error.field.as_deref(), Some("workspaceUid"));
        assert!(
            !root.exists(),
            "foreign owner config must not mutate the filesystem"
        );
    }
}

#[cfg(unix)]
#[test]
fn equivalent_physical_store_aliases_keep_one_workspace_tmp_namespace() {
    let root = std::env::temp_dir().join(format!("runtime-tmp-alias-{}", uuid::Uuid::now_v7()));
    let actual = root.join("store");
    let alias = root.join("same-physical-store");
    std::fs::create_dir_all(&actual).expect("own temporary store");
    std::os::unix::fs::symlink(&actual, &alias).expect("own temporary symlink alias");
    let direct = config(actual)
        .workspace_tmp_presentation_path("the-same-workspace")
        .unwrap();
    let via_alias = config(alias)
        .workspace_tmp_presentation_path("the-same-workspace")
        .unwrap();
    assert_eq!(
        direct, via_alias,
        "one physical owner cannot fork into two TMPDIR namespaces"
    );
    std::fs::remove_dir_all(&root).expect("clean only our temporary store");
}
