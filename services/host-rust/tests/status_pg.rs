//! A read-only real PostgreSQL 18 check, never pointed at production DSN.
//! Run with HOST_RUST_TEST_DSN pointing to disposable schema13:
//! cargo test --test status_pg -- --ignored
use ordivon_host_rust::pg::{HostPg, REQUIRED_SCHEMA};

#[tokio::test]
#[ignore = "requires a disposable PostgreSQL 18 database with Host schema 13"]
async fn summary_comes_from_same_real_postgres_authority() {
    let dsn = std::env::var("HOST_RUST_TEST_DSN")
        .expect("HOST_RUST_TEST_DSN is required for isolated PG test");
    assert!(
        dsn.contains("127.0.0.1") || dsn.contains("localhost"),
        "test DSN must point to isolated loopback PG"
    );
    let pg = HostPg::new(dsn);
    assert_eq!(pg.check_schema().await.expect("PG schema"), REQUIRED_SCHEMA);
    let summary = pg.summary().await.expect("Host summary");
    assert_eq!(summary.authority.journal_schema, REQUIRED_SCHEMA);
    assert_eq!(summary.authority.journal_backend, "postgresql");
    assert_eq!(summary.kind, "ordivon.host-status");
    assert_eq!(
        summary.authority.works,
        summary.authority.works_by_state.values().sum::<i64>()
    );
    assert_eq!(summary.detail, "summary");
    assert!(summary.doctor.is_none());
}
