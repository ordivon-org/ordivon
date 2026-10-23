#![cfg(feature = "transactional-runtime")]

use rusqlite::{params, Connection};

#[test]
fn unsigned_sqlite_integer_mapping_is_lossless_only_inside_signed_64_bit_range() {
    let conn = Connection::open_in_memory().expect("in-memory database");
    conn.execute("CREATE TABLE counter(value INTEGER)", [])
        .expect("create counter table");

    for value in [0_u64, 1, i64::MAX as u64] {
        conn.execute("INSERT INTO counter(value) VALUES (?1)", params![value])
            .expect("in-range unsigned value must persist");
        let restored: u64 = conn
            .query_row(
                "SELECT value FROM counter ORDER BY rowid DESC LIMIT 1",
                [],
                |row| row.get(0),
            )
            .expect("in-range unsigned value must load");
        assert_eq!(restored, value);
    }

    let too_large = conn.execute("INSERT INTO counter(value) VALUES (?1)", params![u64::MAX]);
    assert!(
        too_large.is_err(),
        "SQLite INTEGER cannot store full u64 range"
    );

    let negative_as_unsigned = conn.query_row("SELECT -1", [], |row| row.get::<_, u64>(0));
    assert!(
        negative_as_unsigned.is_err(),
        "negative SQL INTEGER is not u64"
    );
}
