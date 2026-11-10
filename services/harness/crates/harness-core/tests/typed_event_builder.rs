use ordivon_harness_core::{canonical_bytes, digest_bytes, CanonicalDocument, CanonicalError};

#[test]
fn type_safe_event_payload_builder_matches_python_exact_bytes_and_hash() {
    let wide = "-184467440737095516170000000000000000000";
    let built = CanonicalDocument::object(vec![
        (
            "z".into(),
            CanonicalDocument::integer_from_decimal(wide).unwrap(),
        ),
        (
            "a".into(),
            CanonicalDocument::array(vec![
                CanonicalDocument::boolean(true),
                CanonicalDocument::object(vec![("city".into(), CanonicalDocument::string("東京"))])
                    .unwrap(),
            ])
            .unwrap(),
        ),
    ])
    .unwrap();
    let expected = r#"{"a":[true,{"city":"東京"}],"z":-184467440737095516170000000000000000000}"#;
    let bytes = canonical_bytes(&built);
    assert_eq!(bytes, expected.as_bytes());
    assert_eq!(
        digest_bytes(&bytes),
        "sha256:76812613bdefdc3c2715e600d2ccabb1af1b211f6a0924adbf289820ba7b0949"
    );
    assert_eq!(built.get("z").unwrap().as_integer_decimal(), Some(wide));
    assert_eq!(
        built
            .get("a")
            .and_then(|item| item.as_integer_decimal().map(str::to_string)),
        None
    );
}

#[test]
fn duplicate_and_malformed_inputs_are_not_constructible() {
    assert!(matches!(
        CanonicalDocument::object(vec![
            ("x".into(), CanonicalDocument::null()),
            ("x".into(), CanonicalDocument::boolean(true)),
        ]),
        Err(CanonicalError::DuplicateKey(key)) if key == "x"
    ));
    assert!(CanonicalDocument::integer_from_decimal("01").is_err());
    assert!(CanonicalDocument::integer_from_decimal("1e0").is_err());
    assert!(CanonicalDocument::integer_from_decimal("1.0").is_err());
    assert!(CanonicalDocument::integer_from_decimal("true").is_err());
    assert_eq!(
        CanonicalDocument::integer_from_decimal("-0")
            .unwrap()
            .as_integer_decimal(),
        Some("0")
    );
}

#[test]
fn builder_cannot_create_a_document_its_reader_would_reject() {
    let mut nested = CanonicalDocument::null();
    for _ in 0..995 {
        nested = CanonicalDocument::array(vec![nested]).unwrap();
    }
    assert_eq!(
        CanonicalDocument::array(vec![nested]),
        Err(CanonicalError::ExcessiveNesting)
    );
}
