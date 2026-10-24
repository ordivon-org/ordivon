use std::collections::HashSet;

use uuid::Uuid;

#[test]
fn durable_id_v7_roundtrips_through_string_and_json() {
    let id = Uuid::now_v7();
    assert_eq!(id.get_version_num(), 7);
    assert_eq!(Uuid::parse_str(&id.to_string()).unwrap(), id);

    let encoded = serde_json::to_string(&id).unwrap();
    let decoded: Uuid = serde_json::from_str(&encoded).unwrap();
    assert_eq!(decoded, id);
}

#[test]
fn independent_runtime_ids_do_not_collide_in_a_local_batch() {
    let mut seen = HashSet::new();
    for _ in 0..256 {
        let id = Uuid::now_v7();
        assert_eq!(id.get_version_num(), 7);
        assert!(seen.insert(id), "duplicate runtime UUIDv7 in batch");
    }
}
