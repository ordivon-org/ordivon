//! Native test fixture lifetime, independent of the product lifecycle policy.
//! Failed/unknown carriers are retained; this module never resets other Units.
use postgres::Client;
use std::{
    fs, io,
    os::unix::fs::{MetadataExt, PermissionsExt},
    path::{Path, PathBuf},
    process::{Child, Command, ExitStatus},
    thread,
    time::{Duration, Instant},
};
use uuid::Uuid;

pub(super) const SCOPE_ENV: &str = "ORDIVON_NATIVE_MCP_FIXTURE_ROOT";

pub(super) fn new_root() -> io::Result<PathBuf> {
    let parent = match std::env::var_os(SCOPE_ENV) {
        None => PathBuf::from("/var/tmp"),
        Some(raw) => {
            let path = PathBuf::from(raw);
            let meta = fs::symlink_metadata(&path)?;
            let uid = fs::metadata("/proc/self")?.uid();
            if path.parent() != Some(Path::new("/var/tmp"))
                || !path
                    .file_name()
                    .and_then(|s| s.to_str())
                    .is_some_and(|s| s.starts_with("od-mcp-"))
                || !meta.file_type().is_dir()
                || meta.uid() != uid
                || meta.mode() & 0o777 != 0o755
                || path.canonicalize()? != path
            {
                return Err(io::Error::new(
                    io::ErrorKind::InvalidInput,
                    "unqualified native fixture scope",
                ));
            }
            path
        }
    };
    let root = parent.join(format!("runtime-pg-mcp-{}", Uuid::now_v7().simple()));
    fs::create_dir(&root)?;
    fs::set_permissions(&root, fs::Permissions::from_mode(0o777))?;
    Ok(root)
}

// Own the actual child as soon as spawn succeeds, including constructor
// failure before Fixture is fully constructed. Fast PostgreSQL shutdown
// waits for workers and preserves native failure evidence; no global kill.
pub(super) struct PgProcess {
    child: Child,
    stopped: bool,
    stop_attempted: bool,
}

impl PgProcess {
    pub(super) fn new(child: Child) -> Self {
        Self {
            child,
            stopped: false,
            stop_attempted: false,
        }
    }

    pub(super) fn try_wait(&mut self) -> io::Result<Option<ExitStatus>> {
        self.child.try_wait()
    }

    pub(super) fn stop(&mut self) -> Result<(), String> {
        if self.stopped {
            return Ok(());
        }
        if self.stop_attempted {
            return Err("PG shutdown already unqualified".into());
        }
        self.stop_attempted = true;
        if let Some(status) = self.child.try_wait().map_err(|e| e.to_string())? {
            self.stopped = status.success();
            return if self.stopped {
                Ok(())
            } else {
                Err(format!("PG exited {status}"))
            };
        }
        let pid = self.child.id().to_string();
        let status = Command::new("/usr/bin/kill")
            .args(["-INT", &pid])
            .status()
            .map_err(|e| e.to_string())?;
        if !status.success() {
            return Err(format!("PG fast shutdown signal {status}"));
        }
        let deadline = Instant::now() + Duration::from_secs(8);
        loop {
            if let Some(status) = self.child.try_wait().map_err(|e| e.to_string())? {
                self.stopped = status.success();
                return if self.stopped {
                    Ok(())
                } else {
                    Err(format!("PG exited {status}"))
                };
            }
            if Instant::now() >= deadline {
                return Err(format!("PG fast shutdown unobserved pid={pid}"));
            }
            thread::sleep(Duration::from_millis(25));
        }
    }
}

impl Drop for PgProcess {
    fn drop(&mut self) {
        if !self.stop_attempted {
            if let Err(err) = self.stop() {
                eprintln!("NATIVE_FIXTURE_PG_UNQUALIFIED: {err}");
            }
        }
    }
}

// The database is the fixture's private PG, not production. Unit names are
// derived independently and every exact native carrier must be absent.
// A failure retained by CollectMode=inactive is intentionally NOT reset.
pub(super) fn verify_units_absent(db: &mut Client, root: &Path) -> Result<(), String> {
    let mut tx = db.transaction().map_err(|e| e.to_string())?;
    tx.batch_execute("SET LOCAL statement_timeout='2000ms'; SET LOCAL lock_timeout='1000ms'; SET TRANSACTION READ ONLY")
        .map_err(|e| e.to_string())?;
    let rows = tx
        .query(
            "SELECT attempt_id,unit_name,bundle_path FROM fresh.attempts ORDER BY attempt_id",
            &[],
        )
        .map_err(|e| e.to_string())?;
    tx.commit().map_err(|e| e.to_string())?;
    for row in rows {
        let attempt: String = row.try_get(0).map_err(|e| e.to_string())?;
        let unit: String = row.try_get(1).map_err(|e| e.to_string())?;
        let bundle: String = row.try_get(2).map_err(|e| e.to_string())?;
        validate_binding(root, &attempt, &unit, &bundle)?;
        let deadline = Instant::now() + Duration::from_secs(2);
        loop {
            let out = Command::new("/usr/bin/timeout")
                .args([
                    "3s",
                    "systemctl",
                    "show",
                    &unit,
                    "--no-pager",
                    "-p",
                    "LoadState",
                    "-p",
                    "ActiveState",
                    "-p",
                    "MainPID",
                    "-p",
                    "ControlGroup",
                ])
                .output()
                .map_err(|e| e.to_string())?;
            let raw = String::from_utf8(out.stdout).map_err(|e| e.to_string())?;
            if !out.status.success() {
                return Err(format!("Unit readback failed {unit}: {}", out.status));
            }
            if absent(&raw) {
                break;
            }
            if Instant::now() >= deadline {
                return Err(format!("Unit not absent {unit}: {raw}"));
            }
            thread::sleep(Duration::from_millis(50));
        }
    }
    Ok(())
}

fn validate_binding(root: &Path, attempt: &str, unit: &str, bundle: &str) -> Result<(), String> {
    let id = attempt
        .strip_prefix("attempt-")
        .ok_or("invalid Attempt prefix")?;
    // Synthetic test attempts also use safe literal suffixes. Never allow
    // path separators, whitespace or option-like unit names.
    if id.is_empty()
        || !id
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
        || unit != format!("ordivon-pg-{attempt}.service")
        || Path::new(bundle) != root.join("store/pg-attempts").join(attempt)
    {
        return Err(format!(
            "foreign or malformed fixture binding {attempt} {unit} {bundle}"
        ));
    }
    Ok(())
}

fn absent(raw: &str) -> bool {
    let mut values = std::collections::BTreeMap::new();
    for line in raw.lines() {
        let Some((k, v)) = line.split_once('=') else {
            return false;
        };
        if values.insert(k, v).is_some() {
            return false;
        }
    }
    values.len() == 4
        && values.get("LoadState") == Some(&"not-found")
        && values.get("ActiveState") == Some(&"inactive")
        && values.get("MainPID") == Some(&"0")
        && values.get("ControlGroup") == Some(&"")
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn exact_absence_is_not_failed_or_inactive_unit() {
        let absent_report = "LoadState=not-found\nActiveState=inactive\nMainPID=0\nControlGroup=\n";
        assert!(absent(absent_report));
        for (from, to) in [
            ("not-found", "loaded"),
            ("inactive", "failed"),
            ("MainPID=0", "MainPID=42"),
            ("ControlGroup=", "ControlGroup=/system.slice/foreign"),
            ("MainPID=0\n", ""),
        ] {
            assert!(!absent(&absent_report.replace(from, to)), "{from}");
        }
        assert!(!absent(&format!("{absent_report}MainPID=0\n")));
    }
    #[test]
    fn exact_fixture_binding_rejects_foreign_or_traversal() {
        let root = Path::new("/var/tmp/od-mcp-example/runtime-pg-mcp-a");
        let bundle = root.join("store/pg-attempts/attempt-a");
        assert!(validate_binding(
            root,
            "attempt-a",
            "ordivon-pg-attempt-a.service",
            bundle.to_str().unwrap()
        )
        .is_ok());
        for (attempt, unit, path) in [
            (
                "attempt-a",
                "ordivon-pg-attempt-b.service",
                bundle.to_str().unwrap(),
            ),
            (
                "attempt-a",
                "ordivon-pg-attempt-a.service",
                "/var/tmp/foreign",
            ),
            (
                "attempt-../foreign",
                "ordivon-pg-attempt-../foreign.service",
                bundle.to_str().unwrap(),
            ),
        ] {
            assert!(validate_binding(root, attempt, unit, path).is_err());
        }
    }
}
