use super::fixture::{reference, setup};
use axum::{
    Router,
    body::{Body, to_bytes},
    http::{Request, StatusCode, header},
};
use ordivon_web_note_pg::{
    PgNoteStore,
    http::{ReadState, read_router},
    identity::PreparedSession,
};
use serde_json::{Value, json};
use std::sync::{
    Arc,
    atomic::{AtomicI64, Ordering},
};
use tower::ServiceExt;
use uuid::Uuid;
async fn call(
    app: &Router,
    method: &str,
    path: &str,
    token: Option<&str>,
    site: Option<&str>,
) -> (StatusCode, Value) {
    let mut builder = Request::builder().method(method).uri(path);
    if let Some(t) = token {
        builder = builder.header(header::COOKIE, format!("__Host-session={t}"))
    }
    if let Some(s) = site {
        builder = builder.header("sec-fetch-site", s)
    }
    let response = app
        .clone()
        .oneshot(builder.body(Body::empty()).unwrap())
        .await
        .unwrap();
    assert_eq!(response.headers()[header::CACHE_CONTROL], "no-store");
    assert_eq!(response.headers()[header::VARY], "Cookie");
    assert!(!response.headers().contains_key(header::SET_COOKIE));
    let status = response.status();
    let bytes = to_bytes(response.into_body(), 1_000_000).await.unwrap();
    (
        status,
        serde_json::from_slice(&bytes).unwrap_or(Value::Null),
    )
}
fn store_for(db: &str) -> PgNoteStore {
    PgNoteStore::local(
        &std::path::PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap()),
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        db,
    )
    .unwrap()
}
#[tokio::test]
async fn actual_axum_owner_reads_and_denials() {
    let (store, peer) = setup("http_reads").await;
    let p = PreparedSession::new("p", 100, 20, 50, None).unwrap();
    let q = PreparedSession::new("q", 100, 20, 50, None).unwrap();
    store.issue_session(&p).await.unwrap();
    store.issue_session(&q).await.unwrap();
    let time = Arc::new(AtomicI64::new(101));
    let clock = time.clone();
    let app = read_router(
        ReadState::new(store_for("http_reads"), 20, move || {
            clock.load(Ordering::SeqCst)
        })
        .unwrap(),
    );
    let paths = [
        "/api/me",
        "/api/security/sessions",
        "/api/security/passkeys",
        "/api/security/agents/grants",
    ];
    for path in paths {
        let (status, _) = call(&app, "GET", path, None, None).await;
        assert_eq!(status, StatusCode::UNAUTHORIZED);
        let (status, _) = call(&app, "GET", path, Some(p.token()), Some("cross-site")).await;
        assert_eq!(status, StatusCode::FORBIDDEN);
    }
    assert_eq!(store.list_sessions("p").await.unwrap()[0].last_seen_at, 100);
    let (status, me) = call(&app, "GET", "/api/me", Some(p.token()), Some("same-origin")).await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(
        me,
        json!({"principal":store.get_principal("p").await.unwrap(),"session":store.list_sessions("p").await.unwrap()[0]})
    );
    assert!(me.get("tokenHash").is_none());
    let (_, sessions) = call(&app, "GET", "/api/security/sessions", Some(p.token()), None).await;
    assert_eq!(
        sessions,
        json!({"currentSessionId":p.session_id(),"sessions":store.list_sessions("p").await.unwrap()})
    );
    let (_, passkeys) = call(&app, "GET", "/api/security/passkeys", Some(p.token()), None).await;
    assert_eq!(
        passkeys,
        json!({"credentials":[{"credentialId":"credential","deviceType":"singleDevice","backedUp":false,"transports":[],"createdAt":1,"lastUsedAt":1,"revokedAt":null}]})
    );
    let (_, grants) = call(
        &app,
        "GET",
        "/api/security/agents/grants?principalId=q",
        Some(p.token()),
        None,
    )
    .await;
    assert_eq!(
        grants,
        json!({"principalId":"p","displayName":"p","observedAt":101,"grants":store.list_grants("p").await.unwrap()})
    );
    let (_, other) = call(
        &app,
        "GET",
        "/api/security/agents/grants?principalId=p",
        Some(q.token()),
        None,
    )
    .await;
    assert_eq!(
        other,
        json!({"principalId":"q","displayName":"q","observedAt":101,"grants":[]})
    );
    let (_, other_passkeys) =
        call(&app, "GET", "/api/security/passkeys", Some(q.token()), None).await;
    assert_eq!(other_passkeys, json!({"credentials":[]}));
    // Exact older SQLite producer, not a second Rust projection oracle.
    let old = reference()["source"].clone();
    assert_eq!(
        old["agent_grants"]["rows"].as_array().unwrap().len(),
        grants["grants"].as_array().unwrap().len()
    );
    time.store(102, Ordering::SeqCst);
    let duplicate = app
        .clone()
        .oneshot(
            Request::builder()
                .uri("/api/me")
                .header(
                    header::COOKIE,
                    format!("__Host-session={}; __Host-session={}", p.token(), q.token()),
                )
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(duplicate.status(), StatusCode::UNAUTHORIZED);
    let (status, _) = call(&app, "HEAD", "/api/me", Some(p.token()), None).await;
    assert_eq!(status, StatusCode::METHOD_NOT_ALLOWED);
    let (status, _) = call(&app, "POST", "/api/me", Some(p.token()), None).await;
    assert_eq!(status, StatusCode::METHOD_NOT_ALLOWED);
    assert_eq!(store.list_sessions("p").await.unwrap()[0].last_seen_at, 101);
    peer.execute(
        "UPDATE agent_grants SET allowed_actions_json='{}' WHERE grant_id='g1'",
        &[],
    )
    .await
    .unwrap();
    let (status, body) = call(
        &app,
        "GET",
        "/api/security/agents/grants",
        Some(p.token()),
        None,
    )
    .await;
    assert_eq!(status, StatusCode::INTERNAL_SERVER_ERROR);
    assert_eq!(body["code"], "owner-integrity-failure");
    assert!(body.get("grants").is_none());
    store
        .revoke_session("p", p.session_id(), Uuid::new_v4(), 103)
        .await
        .unwrap();
    time.store(104, Ordering::SeqCst);
    for path in paths {
        let (status, _) = call(&app, "GET", path, Some(p.token()), None).await;
        assert_eq!(status, StatusCode::UNAUTHORIZED)
    }
    time.store(150, Ordering::SeqCst);
    let (status, _) = call(&app, "GET", "/api/me", Some(q.token()), None).await;
    assert_eq!(status, StatusCode::UNAUTHORIZED);
    println!(
        "four real Tower/Axum PG read consumers, identity isolation, projected passkeys, duplicate cookie, cross-site, method, corruption, revoke and expiry denial"
    );
}

#[tokio::test]
async fn actual_http_socket_session_consumer() {
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    let (store, _) = setup("http_socket").await;
    let p = PreparedSession::new("p", 100, 20, 50, None).unwrap();
    store.issue_session(&p).await.unwrap();
    let app = read_router(ReadState::new(store_for("http_socket"), 20, || 101).unwrap());
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let (stop, stopped) = tokio::sync::oneshot::channel();
    let server = tokio::spawn(async move {
        axum::serve(listener, app)
            .with_graceful_shutdown(async {
                let _ = stopped.await;
            })
            .await
            .unwrap()
    });
    let mut stream = tokio::net::TcpStream::connect(address).await.unwrap();
    stream.write_all(format!("GET /api/security/agents/grants HTTP/1.1\r\nHost: localhost\r\nCookie: __Host-session={}\r\nSec-Fetch-Site: same-origin\r\nConnection: close\r\n\r\n",p.token()).as_bytes()).await.unwrap();
    let mut bytes = Vec::new();
    tokio::time::timeout(
        std::time::Duration::from_secs(5),
        stream.read_to_end(&mut bytes),
    )
    .await
    .unwrap()
    .unwrap();
    let wire = String::from_utf8(bytes).unwrap();
    let (headers, body) = wire.split_once("\r\n\r\n").unwrap();
    assert!(headers.starts_with("HTTP/1.1 200"));
    assert!(
        headers
            .to_ascii_lowercase()
            .contains("cache-control: no-store")
    );
    let response: Value = serde_json::from_str(body).unwrap();
    assert_eq!(response["principalId"], "p");
    assert_eq!(
        response["grants"],
        json!(store.list_grants("p").await.unwrap())
    );
    assert!(!wire.contains(p.token()));
    stop.send(()).unwrap();
    tokio::time::timeout(std::time::Duration::from_secs(5), server)
        .await
        .unwrap()
        .unwrap();
    println!(
        "real loopback HTTP/1.1 request -> Axum -> native PG Session -> Grant -> JSON, graceful shutdown"
    );
}
