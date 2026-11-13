//! Rust-native Harness canonical document kernel.
#![forbid(unsafe_code)]

mod document;
mod encode;
mod error;
mod parse;

pub use document::{CanonicalDocument, CanonicalRef};
pub use encode::{
    canonical_bytes, canonical_bytes_from_json, canonical_digest_from_json, digest_bytes,
};
pub use error::CanonicalError;
pub use parse::loads_strict;

#[cfg(test)]
mod unit_tests {
    use super::*;

    #[test]
    fn rejects_duplicate_unescaped_key() {
        assert_eq!(
            loads_strict(r#"{"z":1,"\u007a":2}"#),
            Err(CanonicalError::DuplicateKey("z".into()))
        );
    }

    #[test]
    fn no_floating_point_or_nonfinite() {
        for source in ["3.1", "3e2", "-0.0", "NaN", "Infinity", "-Infinity"] {
            assert!(loads_strict(source).is_err(), "{source}");
        }
    }
}
