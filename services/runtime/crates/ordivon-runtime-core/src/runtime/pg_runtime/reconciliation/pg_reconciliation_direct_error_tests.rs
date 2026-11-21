//! Original PG Runtime behavior regression tests; source location is not a contract.
use super::*;

/// Exercise actual PostgreSQL, not a fabricated SQLSTATE.
#[test]
#[ignore = "requires explicitly disposable ORDIVON_PG_TEST_DSN and #2123 typed mapper"]
fn native_postgres_recovery_keeps_server_transaction_abort_sqlstate() {
    let dsn = std::env::var("ORDIVON_PG_TEST_DSN")
        .expect("dedicated disposable PostgreSQL cluster is required");
    let mut db = postgres::Client::connect(&dsn, postgres::NoTls).unwrap();
    for (state, busy) in [("40001", true), ("40P01", true), ("23505", false)] {
        let source_error = db
            .batch_execute(&format!(
                "DO $$ BEGIN RAISE EXCEPTION SQLSTATE '{state}'; END $$;"
            ))
            .unwrap_err();
        let projected = pg_read_error(source_error);
        assert_eq!(
            projected.code,
            if busy {
                RuntimeErrorCode::RegistryBusy
            } else {
                RuntimeErrorCode::RegistryUnavailable
            },
            "SQLSTATE {state} must retain typed classification"
        );
        assert_eq!(projected.retryable, busy);
        if busy {
            assert_eq!(projected.retry_after_ms, Some(250));
        }
    }
}
