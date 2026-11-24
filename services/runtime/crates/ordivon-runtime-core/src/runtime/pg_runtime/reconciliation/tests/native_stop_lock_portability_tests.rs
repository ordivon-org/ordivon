//! Preserve real consumer behavior; test placement is not a production contract.
#[test]
fn native_stop_receipt_lock_excludes_an_independent_writer_until_drop() {
    let temporary = tempfile::tempdir().expect("isolated native stop lock fixture");
    let path = temporary.path().join("native-stop-evidence.lock");
    let first = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
        .unwrap();
    let second = std::fs::OpenOptions::new().write(true).open(&path).unwrap();
    first.lock().expect("first exclusive lock");
    assert!(
        matches!(second.try_lock(), Err(std::fs::TryLockError::WouldBlock)),
        "a second handle cannot publish a conflicting native stop receipt"
    );
    drop(first);
    second
        .try_lock()
        .expect("dropping the first File must release its lock");
}
