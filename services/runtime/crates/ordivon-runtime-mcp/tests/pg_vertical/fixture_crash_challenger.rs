//! Actual SIGKILL challenge for a private PostgreSQL Fixture.
//! Never a generic recovery tool; the parent owns the precise spawned child
//! and receives a one-use readiness identity before performing the fault.
use super::{new_root, Fixture};
use postgres::{Client, NoTls};
use serde_json::{json, Value};
use std::{
    fs,
    os::unix::{
        fs::MetadataExt,
        process::{CommandExt, ExitStatusExt},
    },
    path::{Path, PathBuf},
    process::{Child, Command, ExitStatus, Stdio},
    thread,
    time::{Duration, Instant},
};
const CHILD_ENV: &str = "ORDIVON_NATIVE_FIXTURE_KILL_CHILD";
const CASE: &str =
    "fixture_crash_challenger::native_pg_fixture_sigkill_recovers_exact_private_postmaster";

struct OwnedChild(Child);
impl Drop for OwnedChild {
    fn drop(&mut self) {
        if self.0.try_wait().ok().flatten().is_none() {
            let _ = self.0.kill();
            let _ = self.0.wait();
        }
    }
}

fn proc_start(pid: u32) -> String {
    let stat = fs::read_to_string(format!("/proc/{pid}/stat")).unwrap();
    stat.rsplit_once(") ")
        .unwrap()
        .1
        .split_whitespace()
        .nth(19)
        .unwrap()
        .to_owned()
}

fn pg_pid(root: &Path) -> u32 {
    let raw = fs::read_to_string(root.join("data/postmaster.pid")).unwrap();
    let mut lines = raw.lines();
    let pid: u32 = lines.next().unwrap().parse().unwrap();
    assert!(pid > 1);
    assert_eq!(Path::new(lines.next().unwrap()), root.join("data"));
    pid
}

fn cluster_id(db: &mut Client, root: &Path) -> String {
    let row = db.query_one("SELECT system_identifier::text, current_setting('data_directory') FROM pg_control_system()", &[]).unwrap();
    assert_eq!(Path::new(&row.get::<_, String>(1)), root.join("data"));
    row.get(0)
}

fn pg_ctl(root: &Path, args: &[&str]) -> ExitStatus {
    let mut c = Command::new("/usr/bin/timeout");
    c.args(["12s", "pg_ctl", "-D"])
        .arg(root.join("data"))
        .args(args)
        .env_remove("PGDATA")
        .stdout(Stdio::null())
        .stderr(Stdio::inherit());
    if fs::metadata("/proc/self").unwrap().uid() == 0 {
        c.uid(65534).gid(65534);
    }
    c.status().unwrap()
}

#[test]
#[ignore = "requires actual disposable PostgreSQL and Linux SIGKILL"]
fn native_pg_fixture_sigkill_recovers_exact_private_postmaster() {
    if let Some(marker) = std::env::var_os(CHILD_ENV) {
        let marker = PathBuf::from(marker);
        // This branch only constructs a private Fixture and writes into its
        // parent's newly allocated handshake directory; no recovery effects.
        assert_eq!(marker.file_name().unwrap(), "ready.json");
        let mut fixture = Fixture::new();
        let pid = pg_pid(&fixture.root);
        let system_id = cluster_id(&mut fixture.db, &fixture.root);
        let ready = json!({"root":fixture.root,"pid":pid,"start":proc_start(pid),
            "systemId":system_id,"child":std::process::id()});
        let pending = marker.with_extension("pending");
        fs::write(&pending, serde_json::to_vec(&ready).unwrap()).unwrap();
        fs::rename(pending, marker).unwrap();
        // A bounded fallback prevents an abandoned challenger from running
        // forever. The parent must prove the actual SIGKILL before recovery.
        thread::sleep(Duration::from_secs(30));
        panic!("fault challenger parent failed to deliver SIGKILL");
    }
    let handshake = new_root().unwrap();
    let marker = handshake.join("ready.json");
    let log = fs::File::create(handshake.join("child.log")).unwrap();
    let mut child = OwnedChild(
        Command::new(std::env::current_exe().unwrap())
            .args(["--ignored", "--exact", CASE, "--nocapture"])
            .env(CHILD_ENV, &marker)
            .stdout(log.try_clone().unwrap())
            .stderr(log)
            .spawn()
            .unwrap(),
    );
    let deadline = Instant::now() + Duration::from_secs(12);
    while !marker.is_file() {
        assert!(
            child.0.try_wait().unwrap().is_none(),
            "child ended before readiness"
        );
        assert!(
            Instant::now() < deadline,
            "child readiness deadline; retained {}",
            handshake.display()
        );
        thread::sleep(Duration::from_millis(25));
    }
    let ready: Value = serde_json::from_slice(&fs::read(&marker).unwrap()).unwrap();
    assert_eq!(ready["child"].as_u64().unwrap(), u64::from(child.0.id()));
    let root = PathBuf::from(ready["root"].as_str().unwrap());
    assert_eq!(root.parent(), handshake.parent());
    assert_ne!(root, handshake);
    assert!(root
        .file_name()
        .unwrap()
        .to_str()
        .unwrap()
        .starts_with("runtime-pg-mcp-"));
    assert_eq!(root.canonicalize().unwrap(), root);
    let pid = u32::try_from(ready["pid"].as_u64().unwrap()).unwrap();
    let start = ready["start"].as_str().unwrap();
    let system_id = ready["systemId"].as_str().unwrap();
    assert_eq!(pg_pid(&root), pid);
    assert_eq!(proc_start(pid), start);
    assert_eq!(
        fs::read_link(format!("/proc/{pid}/cwd")).unwrap(),
        root.join("data")
    );
    assert_eq!(pg_ctl(&root, &["status"]).code(), Some(0));
    child.0.kill().unwrap();
    assert_eq!(child.0.wait().unwrap().signal(), Some(9));
    // Rust Drop never ran. The PG is actually still alive and attributable.
    assert!(root.is_dir());
    assert_eq!(pg_pid(&root), pid);
    assert_eq!(proc_start(pid), start);
    assert_eq!(pg_ctl(&root, &["status"]).code(), Some(0));
    let mut db = Client::connect(
        &format!(
            "host={} user=postgres dbname=postgres connect_timeout=2",
            root.display()
        ),
        NoTls,
    )
    .unwrap();
    assert_eq!(cluster_id(&mut db, &root), system_id);
    assert_eq!(
        db.query_one("SELECT count(*) FROM fresh.attempts", &[])
            .unwrap()
            .get::<_, i64>(0),
        0,
        "this challenge owns a PG-only Fixture, no external Runner"
    );
    drop(db);
    println!("SIGKILL_RETAINED_LIVE_PG pid={pid} cluster={system_id}");
    // Last exact identity observations before the native operation. This
    // private no-writer test is not a general PID-reuse or concurrency fence.
    assert_eq!(pg_pid(&root), pid);
    assert_eq!(proc_start(pid), start);
    assert!(pg_ctl(&root, &["-m", "fast", "-w", "-t", "8", "stop"]).success());
    assert_eq!(pg_ctl(&root, &["status"]).code(), Some(3));
    assert!(!root.join("data/postmaster.pid").exists());
    assert!(!root.join(".s.PGSQL.5432").exists());
    // Retire only our exact two directories after native evidence.
    fs::remove_dir_all(&root).unwrap();
    fs::remove_dir_all(&handshake).unwrap();
    assert!(!root.exists() && !handshake.exists());
    println!("SIGKILL_EXACT_PRIVATE_PG_RECOVERED");
}
