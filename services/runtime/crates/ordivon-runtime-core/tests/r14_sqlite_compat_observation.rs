#![cfg(feature = "transactional-runtime")]
use rusqlite::{backup::Backup, Connection, OpenFlags};
use sha2::{Digest, Sha256};
use std::time::Duration;
#[test]
#[ignore = "requires explicit immutable historical snapshot and expected projection digest"]
fn archived_sqlite_projection_matches_expected_digest() {
    let path = std::path::PathBuf::from(
        std::env::var_os("ORDIVON_RUNTIME_SQLITE_SNAPSHOT")
            .expect("explicit historical snapshot required"),
    );
    assert!(
        path.is_absolute() && path.is_file(),
        "explicit absolute snapshot path"
    );
    let path = path.canonicalize().unwrap();
    let mut wal = path.as_os_str().to_os_string();
    wal.push("-wal");
    match std::fs::metadata(&wal) {
        Ok(m) => assert_eq!(m.len(), 0, "uncheckpointed WAL"),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
        Err(e) => panic!("WAL identity unavailable: {e}"),
    }
    let expected = std::env::var("ORDIVON_RUNTIME_SQLITE_SAMPLE_SHA256")
        .expect("expected sampled projection digest");
    assert_eq!(expected.len(), 64);
    assert!(expected.bytes().all(|b| b.is_ascii_hexdigit()));
    let before = std::fs::metadata(&path).unwrap();
    let path_text = path.to_str().expect("UTF-8 snapshot path");
    let encoded = path_text
        .bytes()
        .map(|b| {
            if b.is_ascii_alphanumeric() || b"/-._~:".contains(&b) {
                (b as char).to_string()
            } else {
                format!("%{b:02X}")
            }
        })
        .collect::<String>();
    let db = Connection::open_with_flags(
        format!("file:{encoded}?mode=ro&immutable=1"),
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_URI,
    )
    .unwrap();
    db.pragma_update(None, "query_only", true).unwrap();
    let version: String = db
        .query_row("SELECT sqlite_version()", [], |r| r.get(0))
        .unwrap();
    let mut digest = Sha256::new();
    let mut counts = Vec::new();
    for q in [
        "SELECT json_array(job_id,resolution,created_at_ms,current_attempt_id,row_version) FROM jobs ORDER BY job_id LIMIT 1024",
        "SELECT json_array(attempt_id,job_id,state,exit_code,started_at_ms,finished_at_ms) FROM attempts ORDER BY attempt_id LIMIT 1024",
        "SELECT json_array(artifact_id,job_id,attempt_id,kind,digest,byte_length,truncated) FROM artifacts ORDER BY artifact_id LIMIT 1024",
        "SELECT json_array(event_id,job_id,attempt_id,event_sequence,event_type,reason_code,detail_digest) FROM job_events ORDER BY event_id LIMIT 1024",
    ] {
        let mut stmt=db.prepare(q).unwrap();
        let mut rows=stmt.query([]).unwrap();
        let mut n=0u64;
        while let Some(row)=rows.next().unwrap() {
            let s:String=row.get(0).unwrap();
            digest.update((s.len() as u64).to_le_bytes()); digest.update(s.as_bytes()); n+=1;
        }
        assert_eq!(n,1024); counts.push(n);
    }
    drop(db);
    let after = std::fs::metadata(&path).unwrap();
    assert_eq!(before.len(), after.len());
    assert_eq!(before.modified().unwrap(), after.modified().unwrap());
    let actual = hex::encode(digest.finalize());
    assert_eq!(
        actual,
        expected.to_ascii_lowercase(),
        "historical sampled projection differs"
    );
    println!("SQLITE_SAMPLE version={version} sample={counts:?} digest={actual}");
}

#[test]
fn native_backup_preserves_binary_null_empty_and_unicode() {
    let src = Connection::open_in_memory().unwrap();
    src.execute_batch("CREATE TABLE t(id INTEGER PRIMARY KEY,v BLOB,n TEXT); INSERT INTO t VALUES(1,x'0000ff',NULL),(2,x'01',''),(3,x'00','日本語');").unwrap();
    let mut dst = Connection::open_in_memory().unwrap();
    Backup::new(&src, &mut dst)
        .unwrap()
        .run_to_completion(1, Duration::ZERO, None)
        .unwrap();
    let read = |c: &Connection| {
        c.query_row(
            "SELECT json_group_array(json_array(id,hex(v),n)) FROM (SELECT * FROM t ORDER BY id)",
            [],
            |r| r.get::<_, String>(0),
        )
        .unwrap()
    };
    assert_eq!(read(&src), read(&dst));
    assert_eq!(
        dst.query_row("PRAGMA integrity_check", [], |r| r.get::<_, String>(0))
            .unwrap(),
        "ok"
    );
}
