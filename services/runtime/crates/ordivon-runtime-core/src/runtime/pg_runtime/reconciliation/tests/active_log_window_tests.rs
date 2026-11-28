//! Preserve real consumer behavior; test placement is not a production contract.
use super::*;
use std::io::Write;

#[test]
fn active_log_tail_and_incremental_offsets_preserve_observation_contract() {
    let path = std::env::temp_dir().join(format!("ordivon-pg-active-log-{}", uuid::Uuid::now_v7()));
    let mut initial = vec![b'x'; 1024 * 1024];
    initial.extend_from_slice(b"first");
    fs::write(&path, &initial).unwrap();
    let ceiling = (initial.len() + 16) as u64;

    let (tail, begin, end, available) =
        active_log_window(&path, ceiling, None, 5).unwrap().unwrap();
    assert_eq!(tail, b"first");
    assert_eq!(end, available);
    assert_eq!(end - begin, 5);

    let mut file = fs::OpenOptions::new().append(true).open(&path).unwrap();
    file.write_all(b"second").unwrap();
    drop(file);
    let (delta, delta_begin, delta_end, later) = active_log_window(&path, ceiling, Some(end), 16)
        .unwrap()
        .unwrap();
    assert_eq!(delta, b"second");
    assert_eq!(delta_begin, end);
    assert_eq!(delta_end, later);

    let (empty, start, next, total) = active_log_window(&path, ceiling, Some(later + 100), 16)
        .unwrap()
        .unwrap();
    assert!(empty.is_empty());
    assert_eq!((start, next, total), (later, later, later));

    assert!(active_log_window(&path, 16, None, 5).is_err());
    fs::remove_file(path).unwrap();
}

#[cfg(unix)]
#[test]
fn active_preview_rejects_link_instead_of_following_foreign_file() {
    let d = tempfile::TempDir::new().unwrap();
    let foreign = d.path().join("foreign.txt");
    let log = d.path().join("stdout.log");
    std::fs::write(&foreign, b"foreign").unwrap();
    std::os::unix::fs::symlink(&foreign, &log).unwrap();
    assert!(active_log_window(&log, 64, None, 64).is_err());
}

#[test]
fn active_preview_absent_leaf_is_distinct_from_unavailable_root() {
    let d = tempfile::TempDir::new().unwrap();
    assert!(
        active_log_window(&d.path().join("stdout.log"), 64, None, 64)
            .unwrap()
            .is_none()
    );
    assert!(active_log_window(&d.path().join("missing").join("stdout.log"), 64, None, 64).is_err());
}
