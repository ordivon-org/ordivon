//! Real headroom configuration tests.rs behavioral tests.
use super::parse_pg_headroom_pair;

#[test]
fn pg_native_entry_rejects_unpaired_or_non_numeric_guest_capacity() {
    let parse = |path: Option<&str>, bytes: Option<&str>| {
        parse_pg_headroom_pair(
            "ORDIVON_WORKSPACE_GUEST_HEADROOM_PATH",
            "ORDIVON_WORKSPACE_GUEST_MIN_FREE_BYTES",
            path.map(str::to_owned),
            bytes.map(str::to_owned),
        )
    };
    assert!(parse(Some("/var/lib/ordivon"), None).is_err());
    assert!(parse(None, Some("21474836480")).is_err());
    assert!(parse(Some("/var/lib/ordivon"), Some("twenty-gb")).is_err());
    assert!(parse(None, None).unwrap().is_none());
    let valid = parse(Some("/var/lib/ordivon"), Some("21474836480"))
        .unwrap()
        .unwrap();
    assert_eq!(valid.path, std::path::PathBuf::from("/var/lib/ordivon"));
    assert_eq!(valid.minimum_free_bytes, 21474836480);
}
