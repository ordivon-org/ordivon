//! Validate real native config capability, not source file placement.
use super::{UniversalExecErrorCode, UniversalExecutorConfig};
use std::path::PathBuf;

fn config(root: PathBuf) -> UniversalExecutorConfig {
    UniversalExecutorConfig {
        store_root: root,
        workspace_root: None,
        workspace_uid: None,
        workspace_gid: None,
        runner_path: Some(PathBuf::from("/usr/bin/true")),
        allowed_executable_roots: vec![PathBuf::from("/usr/bin")],
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
    cfg.validate()
        .expect("complete nonroot identity can be qualified");
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

#[cfg(windows)]
#[test]
fn windows_explicit_presentation_root_preserves_operator_acl_and_private_store() {
    use std::process::Command;
    let fixture = tempfile::tempdir().unwrap();
    let store = fixture.path().join("private");
    let workspace = fixture.path().join("presentation");
    std::fs::create_dir(&store).unwrap();
    std::fs::create_dir(&workspace).unwrap();
    let mut cfg = config(store.clone());
    cfg.allowed_executable_roots = vec![fixture.path().to_path_buf()];
    cfg.runner_path = None;
    cfg.workspace_root = Some(workspace.clone());
    crate::windows_security::protect_private_directory(&workspace).unwrap();
    let icacls = PathBuf::from(std::env::var_os("SystemRoot").unwrap())
        .join("System32")
        .join("icacls.exe");
    // Synthetic directory only. Local authenticated-user SID, no production
    // desktop identity, and no inherited rights. This ACE used to disappear
    // on the first normal Workspace ensure_store call.
    let grant = Command::new(&icacls)
        .arg(&workspace)
        .args(["/grant", "*S-1-5-11:(RX)"])
        .output()
        .unwrap();
    assert!(grant.status.success(), "{:?}", grant);
    let acl = |path: &std::path::Path| {
        let output = Command::new(&icacls).arg(path).output().unwrap();
        assert!(output.status.success(), "{:?}", output);
        output.stdout
    };
    let before = acl(&workspace);
    cfg.ensure_store().unwrap();
    cfg.ensure_store().unwrap();
    assert_eq!(
        acl(&workspace),
        before,
        "ordinary repeated ensure_store must preserve the operator DACL"
    );
    assert!(cfg.workspace_records_root().is_dir());
    assert!(cfg.job_credentials_root().is_dir());
    // A physically nested or missing presentation must fail before creation.
    let nested = store.join("nested");
    std::fs::create_dir(&nested).unwrap();
    cfg.workspace_root = Some(nested);
    assert!(cfg.ensure_store().is_err());
    cfg.workspace_root = Some(fixture.path().join("missing"));
    assert!(cfg.ensure_store().is_err());
    assert!(!fixture.path().join("missing").exists());
}
