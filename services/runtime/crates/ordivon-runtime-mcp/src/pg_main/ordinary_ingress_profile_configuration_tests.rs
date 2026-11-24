//! Real ordinary ingress profile configuration tests.rs behavioral tests.
use super::{ordinary_contained_only, require_ordinary_contained_owner};

#[test]
fn contained_ingress_must_have_real_nonroot_task_identity_at_startup() {
    assert!(require_ordinary_contained_owner(true, None).is_err());
    assert!(require_ordinary_contained_owner(true, Some((0, 65534))).is_err());
    assert!(require_ordinary_contained_owner(true, Some((65534, 0))).is_err());
    assert!(require_ordinary_contained_owner(true, Some((65534, 65534))).is_ok());
    assert!(require_ordinary_contained_owner(false, None).is_ok());
}

#[test]
fn only_an_explicit_operator_mode_can_restrict_ordinary_new_jobs() {
    assert_eq!(ordinary_contained_only(None), Ok(false));
    assert_eq!(ordinary_contained_only(Some("trusted_local")), Ok(false));
    assert_eq!(ordinary_contained_only(Some("contained_local")), Ok(true));
    for invalid in [
        "",
        "all",
        "TrustedLocal",
        "contained_local, trusted_local",
        "auto",
    ] {
        assert!(ordinary_contained_only(Some(invalid)).is_err(), "{invalid}");
    }
}
