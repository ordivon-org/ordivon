// Real file and loaded native Manager behavior, not source-file path assertions.
use super::*;

use super::*;

#[test]
fn linked_systemd_unit_outside_scanned_roots_is_not_safe_to_ignore() {
    let temp = TestUnitRoot::new();
    let root = temp.path().join("units");
    let external = temp.path().join("external");
    fs::create_dir_all(&root).unwrap();
    fs::create_dir_all(&external).unwrap();
    let source = external.join("remote.service");
    fs::write(
        &source,
        "[Service]\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-linked\n",
    )
    .unwrap();
    let link = root.join("remote.service");
    symlink(&source, &link).unwrap();
    let result = installed_systemd_workspace_consumers("ws-linked", &[&root]);
    assert!(
        result.is_err() || !result.unwrap().is_empty(),
        "CANDIDATE_FALSE_GREEN: systemctl link supports an external service file"
    );
}

#[test]
fn instantiated_systemd_unit_specifier_is_not_safe_to_treat_as_absent() {
    let temp = TestUnitRoot::new();
    let root = temp.path().join("units");
    let wanted = root.join("multi-user.target.wants");
    fs::create_dir_all(&wanted).unwrap();
    let source = root.join("agent@.service");
    fs::write(
        &source,
        "[Service]\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/%i\n",
    )
    .unwrap();
    symlink(&source, wanted.join("agent@ws-instance.service")).unwrap();
    let result = installed_systemd_workspace_consumers("ws-instance", &[&root]);
    assert!(
        result.is_err() || !result.unwrap().is_empty(),
        "CANDIDATE_FALSE_GREEN: systemd template %i can resolve to the live workspace"
    );
}
#[test]
fn unescaped_instance_specifier_is_a_workspace_consumer() {
    let temp = TestUnitRoot::new();
    let root = temp.path().join("units");
    let wants = root.join("multi-user.target.wants");
    fs::create_dir_all(&wants).unwrap();
    let template = root.join("agent@.service");
    fs::write(
        &template,
        "[Service]\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/%I\n",
    )
    .unwrap();
    symlink(&template, wants.join("agent@ws-raw.service")).unwrap();
    let found = installed_systemd_workspace_consumers("ws-raw", &[&root]).unwrap();
    assert_eq!(
        found,
        vec![wants.join("agent@ws-raw.service").display().to_string()]
    );
}

use std::os::unix::fs::symlink;
struct TestUnitRoot(std::path::PathBuf);

impl TestUnitRoot {
    fn new() -> Self {
        let nonce = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let root = std::env::temp_dir().join(format!(
            "ordivon-systemd-consumer-{}-{nonce}",
            std::process::id()
        ));
        fs::create_dir(&root).unwrap();
        Self(root)
    }

    fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TestUnitRoot {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

#[test]
fn installed_consumer_matches_exact_workspace_not_comments_or_prefix_aliases() {
    let temp = TestUnitRoot::new();
    let root = temp.path().join("units");
    fs::create_dir(&root).unwrap();
    let service = root.join("durable.service");
    fs::write(
        &service,
        "# WorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-target\n\
             WorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-target-copy\n",
    )
    .unwrap();
    assert!(installed_systemd_workspace_consumers("ws-target", &[&root])
        .unwrap()
        .is_empty());
    fs::write(
        &service,
        "WorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-target\n",
    )
    .unwrap();
    assert_eq!(
        installed_systemd_workspace_consumers("ws-target", &[&root]).unwrap(),
        vec![service.display().to_string()]
    );
    let err = ensure_no_installed_systemd_consumer("ws-target", &[&root]).unwrap_err();
    assert_eq!(err.code, UniversalExecErrorCode::WorkspaceStateMismatch);
    assert!(err.message.contains("durable.service"));
    assert!(err.retryable);
    fs::remove_file(&service).unwrap();
    ensure_no_installed_systemd_consumer("ws-target", &[&root]).unwrap();
}

#[test]
fn installed_service_dropin_is_consumer_and_symlink_is_not_followed() {
    let temp = TestUnitRoot::new();
    let root = temp.path().join("units");
    let dropin = root.join("durable.service.d");
    fs::create_dir_all(&dropin).unwrap();
    let file = dropin.join("30-override.conf");
    fs::write(
        &file,
        "ExecStartPre=/usr/bin/test -d /var/lib/ordivon/runtime/workspaces/ws-root/.git\n",
    )
    .unwrap();
    let symlink_path = root.join("old.service");
    symlink(&file, &symlink_path).unwrap();
    assert_eq!(
        installed_systemd_workspace_consumers("ws-root", &[&root]).unwrap(),
        vec![file.display().to_string()]
    );
    assert!(installed_systemd_workspace_consumers("ws-other", &[&root])
        .unwrap()
        .is_empty());
}

#[test]
fn unrelated_broken_unit_link_must_not_block_every_workspace_close() {
    // A missing unrelated source cannot currently load a Workspace.
    // Absence in this filesystem readset is not proof of the live manager.
    let temp = TestUnitRoot::new();
    let root = temp.path().join("units");
    fs::create_dir(&root).unwrap();
    let absent = temp.path().join("no-such-unrelated.service");
    symlink(&absent, root.join("unrelated.service")).unwrap();
    assert!(
        ensure_no_installed_systemd_consumer("ws-target", &[&root]).is_ok(),
        "broken unrelated systemd alias globally blocked clean closure",
    );
    // A dangling link to a DIFFERENT workspace whose name has this
    // Workspace as a prefix is not a consumer of this Workspace.
    let different = root.join("similar-name.service");
    symlink(
        "/var/lib/ordivon/runtime/workspaces/ws-target-copy/linked.service",
        &different,
    )
    .unwrap();
    assert!(
        ensure_no_installed_systemd_consumer("ws-target", &[&root]).is_ok(),
        "a different Workspace prefix alias must not block close",
    );
    let link = root.join("target.service");
    symlink(
        "/var/lib/ordivon/runtime/workspaces/ws-target/linked.service",
        &link,
    )
    .unwrap();
    assert!(
        ensure_no_installed_systemd_consumer("ws-target", &[&root]).is_err(),
        "even a broken symlink explicitly pointing to this Workspace is a consumer root",
    );
}

#[test]
fn oversized_or_symlinked_unit_roots_fail_closed() {
    let temp = TestUnitRoot::new();
    let root = temp.path().join("units");
    fs::create_dir(&root).unwrap();
    fs::write(root.join("oversize.service"), vec![b'a'; 1024 * 1024 + 1]).unwrap();
    let err = installed_systemd_workspace_consumers("ws-target", &[&root]).unwrap_err();
    assert_eq!(err.code, UniversalExecErrorCode::WorkspaceStateMismatch);
    assert!(err.message.contains("inspection bound"));
    let alias = temp.path().join("alias");
    symlink(&root, &alias).unwrap();
    let err = installed_systemd_workspace_consumers("ws-target", &[&alias]).unwrap_err();
    assert!(err.message.contains("not a regular directory"));
}
#[test]
fn loaded_transient_unit_retains_workspace_even_without_installed_unit_file() {
    let temp = TestUnitRoot::new();
    let root = temp.path().join("units");
    fs::create_dir(&root).unwrap();
    assert!(installed_systemd_workspace_consumers("ws-live", &[&root])
        .unwrap()
        .is_empty());
    let names = vec!["transient.service".to_string()];
    let show = "Id=transient.service\nLoadState=loaded\nWorkingDirectory=/var/lib/ordivon/runtime/workspaces/ws-live\n\n";
    assert_eq!(
        manager_unit_consumers(show, "ws-live", &names).unwrap(),
        names
    );
    assert!(manager_unit_consumers(show, "ws-live-copy", &names)
        .unwrap()
        .is_empty());
}

#[test]
fn changing_or_partial_manager_snapshot_is_not_a_negative_consumer_proof() {
    let names = vec!["one.service".to_string(), "two.scope".to_string()];
    let one = "Id=one.service\nLoadState=loaded\nWorkingDirectory=\n\n";
    assert!(manager_unit_consumers(one, "ws-root", &names).is_err());
    let missing = "Id=one.service\nLoadState=not-found\nWorkingDirectory=\n\n";
    assert!(manager_unit_consumers(missing, "ws-root", &names[..1])
        .unwrap()
        .is_empty());
    let masked = "Id=one.service\nLoadState=masked\nWorkingDirectory=\n\n";
    assert!(manager_unit_consumers(masked, "ws-root", &names[..1])
        .unwrap()
        .is_empty());
    let unknown = "Id=one.service\nLoadState=future-unknown\nWorkingDirectory=\n\n";
    assert!(manager_unit_consumers(unknown, "ws-root", &names[..1]).is_err());
    assert!(manager_unit_consumers(&format!("{one}{one}"), "ws-root", &names[..1]).is_err());
}

#[test]
fn systemd_manager_real_readonly_query_is_not_vacuous_when_booted() {
    if !Path::new("/run/systemd/system").is_dir() {
        return; // Non-systemd CI has no PID1 system manager to query.
    }
    let list = manager_read_only_query(&[
        "list-units",
        "--all",
        "--plain",
        "--no-legend",
        "--no-pager",
    ])
    .expect("real systemd manager unit inventory");
    assert!(!list.trim().is_empty(), "real manager must expose units");
    // The real manager commonly includes a unit named '-.mount';
    // the exact native probe must handle names beginning with a dash.
    ensure_no_loaded_manager_consumer("ws-nonexistent-ordivon-gpt6-probe-20261101")
        .expect("no unrelated loaded manager consumer");
}

#[test]
fn pg_native_workspace_consumer_uses_bound_path_and_exact_instance() {
    let temp = TestUnitRoot::new();
    let root = temp.path().join("units");
    fs::create_dir_all(&root).unwrap();
    let expected = Path::new("/var/lib/ordivon/pg-candidate/workspaces/ws-pg");
    let neighbor = Path::new("/var/lib/ordivon/pg-candidate/workspaces/ws-pg-copy");
    let service = root.join("pg-runner.service");
    fs::write(
        &service,
        format!("[Service]\nWorkingDirectory={neighbor:?}\n"),
    )
    .unwrap();
    assert!(installed_systemd_workspace_consumers_at(expected, &[&root])
        .unwrap()
        .is_empty());
    fs::write(
        &service,
        format!(
            "[Service]\nExecStart=/bin/sh {}/run.sh\n",
            expected.display()
        ),
    )
    .unwrap();
    let hits = installed_systemd_workspace_consumers_at(expected, &[&root]).unwrap();
    assert_eq!(hits, vec![service.display().to_string()]);
    assert!(ensure_no_installed_systemd_consumer_at(expected, &[&root]).is_err());
    let names = vec!["transient-pg.service".to_string()];
    let manager = format!(
        "Id=transient-pg.service\nLoadState=loaded\nWorkingDirectory={}\n\n",
        expected.display()
    );
    assert_eq!(
        manager_unit_consumers_at(&manager, expected, &names).unwrap(),
        names
    );
    assert!(manager_unit_consumers_at(&manager, neighbor, &names)
        .unwrap()
        .is_empty());
    let template = root.join("runner@ws-pg.service");
    fs::write(
        &template,
        "[Service]\nWorkingDirectory=/var/lib/ordivon/pg-candidate/workspaces/%i\n",
    )
    .unwrap();
    assert!(installed_systemd_workspace_consumers_at(expected, &[&root])
        .unwrap()
        .contains(&template.display().to_string()));
}

#[test]
fn loaded_manager_properties_cover_scope_environment_and_exec() {
    let names = vec!["one.scope".to_string(), "two.service".to_string()];
    let show = "Id=one.scope\nLoadState=loaded\nEnvironment=ROOT=/var/lib/ordivon/runtime/workspaces/ws-scope/bin\n\nId=two.service\nLoadState=loaded\nExecStart={ path=/bin/sh ; argv[]=/bin/sh /var/lib/ordivon/runtime/workspaces/ws-scope/job; }\n\n";
    assert_eq!(
        manager_unit_consumers(show, "ws-scope", &names).unwrap(),
        names
    );
    assert!(manager_unit_consumers(show, "ws-other", &names)
        .unwrap()
        .is_empty());
}
