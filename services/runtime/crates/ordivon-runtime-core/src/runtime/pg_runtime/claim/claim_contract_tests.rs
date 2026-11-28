//! Tests of actual Runtime Claim input and behavior, not the location of product files.
use super::*;
#[test]
fn invalid_identity_cannot_reach_pg_or_git() {
    assert!(validate_key(2, "principal", "request").is_err());
    assert!(validate_key(1, "", "request").is_err());
    assert!(validate_key(1, "principal", "bad\nrequest").is_err());
}
