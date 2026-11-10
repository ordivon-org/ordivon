use ordivon_harness_core::{canonical_bytes_from_json, canonical_digest_from_json};

#[test]
fn python_315_canonical_v1_bytes_and_rejection_parity() {
    // Captured by invoking the actual anc_canonical.loads_strict/canonical_bytes
    // in Python 3.15.1, not fabricated by the Rust implementation.
    let corpus: serde_json::Value =
        serde_json::from_str(include_str!("python_canonical_v1_vectors.json"))
            .expect("Python-generated source fixture is valid JSON");
    assert_eq!(corpus["python"], "3.15.1");
    assert_eq!(corpus["int_max_str_digits"], 4300);
    let cases = corpus["cases"].as_array().expect("cases array");
    assert!(cases.len() >= 30);
    for case in cases {
        let source = case["input"].as_str().expect("input");
        let name = case["name"].as_str().expect("case name");
        if case["accept"] == true {
            let bytes = canonical_bytes_from_json(source)
                .unwrap_or_else(|err| panic!("{name}: unexpected Rust rejection: {err}"));
            assert_eq!(
                hex::encode(&bytes),
                case["canonical_hex"].as_str().unwrap(),
                "{name}: bytes"
            );
            assert_eq!(
                canonical_digest_from_json(source).expect("valid source"),
                case["digest"].as_str().unwrap(),
                "{name}: sha256"
            );
        } else {
            assert!(
                canonical_bytes_from_json(source).is_err(),
                "{name}: expected Python rejection, Rust accepted it"
            );
        }
    }
}
