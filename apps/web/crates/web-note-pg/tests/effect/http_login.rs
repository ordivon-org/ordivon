use super::fixture::setup;
use axum::{
    Router,
    body::{Body, to_bytes},
    http::{HeaderMap, Request, StatusCode, header},
};
use ordivon_web_note_pg::{
    PgNoteStore,
    http::{LocalVerifier, LoginState, ReadState, login_router, read_router},
};
use serde_json::{Value, json};
use std::{path::PathBuf, time::Duration};
use tower::ServiceExt;
fn node() -> PathBuf {
    let out = std::process::Command::new(std::env::var("WEB_NOTE_TEST_NODE").unwrap())
        .args(["-p", "process.execPath"])
        .output()
        .unwrap();
    assert!(out.status.success());
    PathBuf::from(String::from_utf8(out.stdout).unwrap().trim())
}
fn fixture(args: &[&str]) -> Value {
    let out = std::process::Command::new(node())
        .arg(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/tests/assertion-fixture.mjs"
        ))
        .args(args)
        .output()
        .unwrap();
    assert!(
        out.status.success(),
        "{}",
        String::from_utf8_lossy(&out.stderr)
    );
    serde_json::from_slice(&out.stdout).unwrap()
}
fn store_for(name: &str) -> PgNoteStore {
    PgNoteStore::local(
        &PathBuf::from(std::env::var_os("WEB_NOTE_TEST_SOCKET").unwrap()),
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        name,
    )
    .unwrap()
}
fn verifier() -> LocalVerifier {
    LocalVerifier::new(
        &node(),
        &PathBuf::from(concat!(
            env!("CARGO_MANIFEST_DIR"),
            "/../../verifier/webauthn-login.ts"
        )),
        2,
        Duration::from_secs(5),
    )
    .unwrap()
}
async fn post(
    app: &Router,
    path: &str,
    input: Value,
    origin: &str,
    site: &str,
) -> (StatusCode, HeaderMap, Value) {
    let r = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri(path)
                .header(header::CONTENT_TYPE, "application/json")
                .header(header::ORIGIN, origin)
                .header("sec-fetch-site", site)
                .body(Body::from(input.to_string()))
                .unwrap(),
        )
        .await
        .unwrap();
    let status = r.status();
    let headers = r.headers().clone();
    let body = to_bytes(r.into_body(), 262144).await.unwrap();
    (
        status,
        headers,
        serde_json::from_slice(&body).unwrap_or(Value::Null),
    )
}
const OPTIONS: &str = "/api/auth/login/options";
const VERIFY: &str = "/api/auth/login/verify";
const ORIGIN: &str = "https://web.example";
#[tokio::test]
async fn actual_webauthn_signed_login_and_rejections() {
    let (store, peer) = setup("http_real_login").await;
    let key = fixture(&["key"]);
    let id = key["id"].as_str().unwrap();
    let bytes: Vec<u8> = serde_json::from_value(key["key"].clone()).unwrap();
    peer.execute("INSERT INTO webauthn_credentials SELECT $1,principal_id,$2,counter,transports_json,device_type,backed_up,created_at,last_used_at,revoked_at FROM webauthn_credentials WHERE credential_id='credential'",&[&id,&bytes]).await.unwrap();
    let app = login_router(
        LoginState::new(
            store_for("http_real_login"),
            verifier(),
            ORIGIN,
            "web.example",
            20,
            50,
            || 101,
        )
        .unwrap(),
    )
    .merge(read_router(
        ReadState::new(store_for("http_real_login"), 20, || 102).unwrap(),
    ));
    let private = key["private"].to_string();
    for (origin, site) in [
        ("https://evil.example", "same-origin"),
        (ORIGIN, "cross-site"),
    ] {
        let (s, h, _) = post(&app, OPTIONS, json!({"userName":"p"}), origin, site).await;
        assert_eq!(s, StatusCode::FORBIDDEN);
        assert!(!h.contains_key(header::SET_COOKIE));
    }
    for variant in ["signature", "origin", "rp", "uv", "challenge", "ok"] {
        let (status, _, o) = post(
            &app,
            OPTIONS,
            json!({"userName":"p"}),
            ORIGIN,
            "same-origin",
        )
        .await;
        assert_eq!(status, StatusCode::OK, "{o:?}");
        let challenge = o["options"]["challenge"].as_str().unwrap();
        let response = fixture(&[&private, challenge, variant]);
        let payload = json!({"challengeId":o["challengeId"],"response":response});
        let (status, h, body) = post(&app, VERIFY, payload.clone(), ORIGIN, "same-origin").await;
        if variant == "ok" {
            assert_eq!(status, StatusCode::OK, "{body:?}");
            let cookie = h[header::SET_COOKIE].to_str().unwrap();
            assert!(cookie.contains("; Secure; HttpOnly; SameSite=Lax;"));
            assert!(
                !body.to_string().contains(
                    cookie
                        .split(';')
                        .next()
                        .unwrap()
                        .trim_start_matches("__Host-session=")
                )
            );
            let read = app
                .clone()
                .oneshot(
                    Request::builder()
                        .uri("/api/me")
                        .header(header::COOKIE, cookie.split(';').next().unwrap())
                        .body(Body::empty())
                        .unwrap(),
                )
                .await
                .unwrap();
            assert_eq!(read.status(), StatusCode::OK);
            let view: Value =
                serde_json::from_slice(&to_bytes(read.into_body(), 262144).await.unwrap()).unwrap();
            assert_eq!(view["principal"]["principalId"], "p");
            assert_eq!(store.get_active_credential(id).await.unwrap().counter, 1);
        } else {
            assert_eq!(status, StatusCode::UNAUTHORIZED, "{variant}: {body:?}");
            assert!(!h.contains_key(header::SET_COOKIE));
            assert!(store.list_sessions("p").await.unwrap().is_empty());
        }
        let (retry, h, _) = post(&app, VERIFY, payload, ORIGIN, "same-origin").await;
        assert_eq!(retry, StatusCode::UNAUTHORIZED);
        assert!(!h.contains_key(header::SET_COOKIE));
    }
    let (_, _, o) = post(
        &app,
        OPTIONS,
        json!({"userName":"p"}),
        ORIGIN,
        "same-origin",
    )
    .await;
    let response = fixture(&[&private, o["options"]["challenge"].as_str().unwrap(), "ok"]);
    let (s, h, _) = post(
        &app,
        VERIFY,
        json!({"challengeId":o["challengeId"],"response":response}),
        ORIGIN,
        "same-origin",
    )
    .await;
    assert_eq!(s, StatusCode::UNAUTHORIZED);
    assert!(!h.contains_key(header::SET_COOKIE));
    println!(
        "real SimpleWebAuthn ES256 assertions; bad signature/origin/RP/UV/challenge rejected, consumed replay denied, counter replay rejected, actual PG session read"
    );
}

#[tokio::test]
async fn verifier_failure_and_commit_unknown_never_release_cookie() {
    let (store, peer) = setup("http_verifier_failure").await;
    let key = fixture(&["key"]);
    let id = key["id"].as_str().unwrap();
    let bytes: Vec<u8> = serde_json::from_value(key["key"].clone()).unwrap();
    peer.execute("INSERT INTO webauthn_credentials SELECT $1,principal_id,$2,counter,transports_json,device_type,backed_up,created_at,last_used_at,revoked_at FROM webauthn_credentials WHERE credential_id='credential'",&[&id,&bytes]).await.unwrap();
    let good = login_router(
        LoginState::new(
            store_for("http_verifier_failure"),
            verifier(),
            ORIGIN,
            "web.example",
            20,
            50,
            || 101,
        )
        .unwrap(),
    );
    let private = key["private"].to_string();
    for rp in [
        "hang.example",
        "oversize.example",
        "bad.example",
        "exit.example",
    ] {
        let (_, _, o) = post(
            &good,
            OPTIONS,
            json!({"userName":"p"}),
            ORIGIN,
            "same-origin",
        )
        .await;
        let response = fixture(&[&private, o["options"]["challenge"].as_str().unwrap(), "ok"]);
        let payload = json!({"challengeId":o["challengeId"],"response":response});
        let bad = LocalVerifier::new(
            &node(),
            &PathBuf::from(concat!(
                env!("CARGO_MANIFEST_DIR"),
                "/tests/verifier-failure.mjs"
            )),
            1,
            Duration::from_secs(1),
        )
        .unwrap();
        let app = login_router(
            LoginState::new(
                store_for("http_verifier_failure"),
                bad,
                ORIGIN,
                rp,
                20,
                50,
                || 101,
            )
            .unwrap(),
        );
        let (status, h, b) = post(&app, VERIFY, payload.clone(), ORIGIN, "same-origin").await;
        assert_eq!(status, StatusCode::SERVICE_UNAVAILABLE, "{rp}: {b:?}");
        assert!(!h.contains_key(header::SET_COOKIE));
        assert!(store.list_sessions("p").await.unwrap().is_empty());
        let (status, h, _) = post(&good, VERIFY, payload, ORIGIN, "same-origin").await;
        assert_eq!(status, StatusCode::UNAUTHORIZED);
        assert!(!h.contains_key(header::SET_COOKIE));
    }
    // Native wire cut during Challenge consume, before verifier or completion.
    let (_, _, o) = post(
        &good,
        OPTIONS,
        json!({"userName":"p"}),
        ORIGIN,
        "same-origin",
    )
    .await;
    let response = fixture(&[&private, o["options"]["challenge"].as_str().unwrap(), "ok"]);
    let payload = json!({"challengeId":o["challengeId"],"response":response});
    let proxy = PgNoteStore::local(
        &PathBuf::from(std::env::var_os("WEB_HTTP_LOGIN_TEST_ACK_PROXY").unwrap()),
        std::env::var("WEB_NOTE_TEST_PORT")
            .unwrap()
            .parse()
            .unwrap(),
        &std::env::var("WEB_NOTE_TEST_USER").unwrap(),
        "http_verifier_failure",
    )
    .unwrap();
    let app = login_router(
        LoginState::new(proxy, verifier(), ORIGIN, "web.example", 20, 50, || 101).unwrap(),
    );
    let (status, h, _) = post(&app, VERIFY, payload.clone(), ORIGIN, "same-origin").await;
    assert_eq!(status, StatusCode::SERVICE_UNAVAILABLE);
    assert!(!h.contains_key(header::SET_COOKIE));
    assert!(store.list_sessions("p").await.unwrap().is_empty());
    assert_eq!(store.get_active_credential(id).await.unwrap().counter, 0);
    assert_eq!(
        post(&good, VERIFY, payload, ORIGIN, "same-origin").await.0,
        StatusCode::UNAUTHORIZED
    );
    println!(
        "real carrier timeout/oversize/malformed/nonzero exit and native Challenge COMMIT ACK loss: no session/cookie, retry denied"
    );
}

#[tokio::test]
async fn actual_session_bound_csrf_and_logout() {
    use ordivon_web_note_pg::{
        http::{SessionWriteState, session_write_router},
        identity::PreparedSession,
    };
    use std::sync::{
        Arc,
        atomic::{AtomicI64, Ordering},
    };
    let (store, _) = setup("http_csrf").await;
    let p = PreparedSession::new("p", 100, 20, 50, None).unwrap();
    let q = PreparedSession::new("q", 100, 20, 50, None).unwrap();
    store.issue_session(&p).await.unwrap();
    store.issue_session(&q).await.unwrap();
    let clock = Arc::new(AtomicI64::new(101));
    let c = clock.clone();
    let app = session_write_router(
        SessionWriteState::new(store_for("http_csrf"), ORIGIN, 20, move || {
            c.load(Ordering::SeqCst)
        })
        .unwrap(),
    );
    async fn csrf(app: &Router, session: &str) -> String {
        let r = app
            .clone()
            .oneshot(
                Request::builder()
                    .uri("/api/session/csrf")
                    .header(header::COOKIE, format!("__Host-session={session}"))
                    .header("sec-fetch-site", "same-origin")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(r.status(), StatusCode::OK);
        assert_eq!(r.headers()[header::CACHE_CONTROL], "no-store");
        let v: Value =
            serde_json::from_slice(&to_bytes(r.into_body(), 10000).await.unwrap()).unwrap();
        v["token"].as_str().unwrap().into()
    }
    async fn logout(
        app: &Router,
        session: &str,
        csrf: Option<&str>,
        origin: &str,
        site: &str,
    ) -> (StatusCode, HeaderMap) {
        let mut b = Request::builder()
            .method("POST")
            .uri("/api/session/logout")
            .header(header::COOKIE, format!("__Host-session={session}"))
            .header(header::ORIGIN, origin)
            .header("sec-fetch-site", site);
        if let Some(csrf) = csrf {
            b = b.header("x-csrf-token", csrf)
        }
        let r = app
            .clone()
            .oneshot(b.body(Body::empty()).unwrap())
            .await
            .unwrap();
        (r.status(), r.headers().clone())
    }
    let token = csrf(&app, p.token()).await;
    let foreign = csrf(&app, q.token()).await;
    assert_ne!(token, foreign);
    clock.store(102, Ordering::SeqCst);
    for (csrf, origin, site) in [
        (None, ORIGIN, "same-origin"),
        (Some(foreign.as_str()), ORIGIN, "same-origin"),
        (Some("wrong"), ORIGIN, "same-origin"),
        (Some(token.as_str()), "https://evil.example", "same-origin"),
        (Some(token.as_str()), ORIGIN, "cross-site"),
    ] {
        let (status, h) = logout(&app, p.token(), csrf, origin, site).await;
        assert_eq!(status, StatusCode::FORBIDDEN);
        assert!(!h.contains_key(header::SET_COOKIE));
        assert_eq!(store.list_sessions("p").await.unwrap()[0].last_seen_at, 101);
        assert!(
            store.list_sessions("p").await.unwrap()[0]
                .revoked_at
                .is_none()
        );
    }
    let restarted = session_write_router(
        SessionWriteState::new(store_for("http_csrf"), ORIGIN, 20, || 102).unwrap(),
    );
    assert_eq!(
        logout(&restarted, p.token(), Some(&token), ORIGIN, "same-origin")
            .await
            .0,
        StatusCode::FORBIDDEN
    );
    let (status, h) = logout(&app, p.token(), Some(&token), ORIGIN, "same-origin").await;
    assert_eq!(status, StatusCode::OK);
    assert!(
        h[header::SET_COOKIE]
            .to_str()
            .unwrap()
            .contains("Max-Age=0")
    );
    assert_eq!(
        store.list_sessions("p").await.unwrap()[0].revoked_at,
        Some(102)
    );
    assert!(
        store.list_sessions("q").await.unwrap()[0]
            .revoked_at
            .is_none()
    );
    assert_eq!(
        logout(&app, p.token(), Some(&token), ORIGIN, "same-origin")
            .await
            .0,
        StatusCode::UNAUTHORIZED
    );
    println!(
        "session-bound CSRF and native logout: absent/foreign/tampered token, cross-origin/site, restart invalidation, no denied touch, own session only"
    );
}
