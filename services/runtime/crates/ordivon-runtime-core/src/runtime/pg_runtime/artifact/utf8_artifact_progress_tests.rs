//! Test original sealed Artifact and UTF-8 consumer behavior, not source file layout.
use super::*;

#[test]
fn pg_artifact_integrity_mismatch_is_not_a_registry_failure() {
    let committed = b"initial sealed receipt";
    let digest = universal::sha256_bytes(committed);
    require_pg_artifact_identity(committed, committed.len() as i64, &digest).unwrap();
    for (bytes, expected_length) in [
        (
            b"initial sealed receipt".as_slice(),
            committed.len() as i64 + 1,
        ),
        (b"initial sealed receipT".as_slice(), committed.len() as i64),
    ] {
        let err = require_pg_artifact_identity(bytes, expected_length, &digest).unwrap_err();
        assert_eq!(err.code, RuntimeErrorCode::ArtifactIdentityConflict);
        assert_eq!(err.field.as_deref(), Some("artifactId"));
        assert!(!err.retryable);
    }
}

#[test]
fn pg_artifact_page_rejects_zero_progress_in_the_middle_of_utf8() {
    let source = "A中文B🙂C\n";
    for (offset, max_bytes) in [(1, 1), (1, 2), (8, 1), (8, 2), (8, 3)] {
        let failure = artifact_utf8_window(source, offset, max_bytes).unwrap_err();
        assert_eq!(failure.field.as_deref(), Some("maxBytes"));
    }
}

#[test]
fn pg_artifact_page_preserves_valid_byte_cursor_boundaries() {
    let source = "A中文B🙂C\n";
    for (offset, max_bytes, expected) in [
        (0, 5, (0, 4)),
        (4, 4, (4, 8)),
        (8, 4, (8, 12)),
        (12, 2, (12, 14)),
        (14, 1, (14, 14)),
    ] {
        let (begin, end) = artifact_utf8_window(source, offset, max_bytes).unwrap();
        assert_eq!((begin, end), expected);
    }
    let failure = artifact_utf8_window(source, 2, 4).unwrap_err();
    assert_eq!(failure.field.as_deref(), Some("offset"));
}
