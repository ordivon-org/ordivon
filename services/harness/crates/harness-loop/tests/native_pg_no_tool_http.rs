//! Verified PG18 no-Tool contract -> Rust HTTP -> bounded native Loop.
//! Journal is test-only; this does NOT claim a production PG Provider writer.
use ordivon_harness_core::CanonicalDocument;
use ordivon_harness_loop::{
    native_loop::{
        AdmittedTool, DurableJournal, EffectReceiver, EffectResult, ModelDecision,
        ModelVisibleContent, NativeAgentLoop, RunFault, RunResult,
    },
    native_provider_http::HttpModelProvider,
    pg_domain_read::{inspect_pg_no_tool_run, ExpectedModel},
    tool_call::ModelToolCall,
};
use postgres::{Client, NoTls};
use serde_json::{json, Value};
use std::{
    fs,
    io::{Read, Write},
    net::TcpListener,
    thread,
    time::Duration,
};
struct Journal {
    claims: u32,
    proposals: u32,
}
impl DurableJournal for Journal {
    fn prepare_provider(&mut self, _: u32) -> Result<(), String> {
        self.claims += 1;
        Ok(())
    }
    fn complete_provider(&mut self, _: u32, _: &ModelDecision) -> Result<(), String> {
        Ok(())
    }
    fn admit_tool(&mut self, _: u32, _: &ModelToolCall) -> Result<AdmittedTool, String> {
        panic!("no-Tool PG Run must not authorize a Tool")
    }
    fn record_effect(
        &mut self,
        _: u32,
        _: &AdmittedTool,
        _: &EffectResult,
    ) -> Result<ModelVisibleContent, String> {
        panic!("no-Tool PG Run must not record Tool effects")
    }
    fn record_completion(&mut self, _: u32, _: &str) -> Result<(), String> {
        self.proposals += 1;
        Ok(())
    }
    fn record_pause(&mut self, _: u32) -> Result<(), String> {
        Ok(())
    }
}
struct NoEffect;
impl EffectReceiver for NoEffect {
    fn execute(&mut self, _: &AdmittedTool, _: &CanonicalDocument) -> EffectResult {
        panic!("no-Tool physically executed")
    }
}
fn server(response: &'static str) -> (String, thread::JoinHandle<()>) {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let url = format!(
        "http://{}/v1/chat/completions",
        listener.local_addr().unwrap()
    );
    let handle = thread::spawn(move || {
        let (mut sock, _) = listener.accept().unwrap();
        sock.set_read_timeout(Some(Duration::from_secs(5))).unwrap();
        let mut buffer = Vec::new();
        let mut part = [0u8; 8192];
        loop {
            let n = sock.read(&mut part).unwrap();
            if n == 0 {
                break;
            }
            buffer.extend_from_slice(&part[..n]);
            if let Some(at) = buffer.windows(4).position(|b| b == b"\r\n\r\n") {
                let head = String::from_utf8_lossy(&buffer[..at]);
                let size = head
                    .lines()
                    .find_map(|line| {
                        let (key, val) = line.split_once(':')?;
                        key.eq_ignore_ascii_case("content-length")
                            .then(|| val.trim().parse::<usize>().ok())
                            .flatten()
                    })
                    .unwrap();
                if buffer.len() >= at + 4 + size {
                    break;
                }
            }
        }
        let pos = buffer.windows(4).position(|b| b == b"\r\n\r\n").unwrap() + 4;
        let body: Value = serde_json::from_slice(&buffer[pos..]).unwrap();
        assert!(body.get("tools").is_none());
        assert!(body.get("tool_choice").is_none());
        assert_eq!(body["model"], json!("model:verified-source"));
        let msg=format!("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",response.len(),response);
        sock.write_all(msg.as_bytes()).unwrap();
    });
    (url, handle)
}
#[test]
#[ignore = "requires A-owned disposable PG18 Python no-Tool source fixture"]
fn native_pg_verifiable_provider_only_http_loop() {
    let dsn = std::env::var("HARNESS_RUST_TEST_PG_DSN").unwrap();
    let schema = std::env::var("HARNESS_RUST_TEST_SCHEMA").unwrap();
    let path = std::env::var("HARNESS_RUST_TEST_FIXTURE_PATH").unwrap();
    let fixture: Value = serde_json::from_slice(&fs::read(path).unwrap()).unwrap();
    let run = fixture["no_tool"]["runId"].as_str().unwrap();
    let mut db = Client::connect(&dsn, NoTls).unwrap();
    let expected = ExpectedModel {
        provider_id: "provider:verified-source",
        adapter_id: "adapter:verified-source",
        requested_model_id: "model:verified-source",
    };
    let verified = inspect_pg_no_tool_run(&mut db, &schema, run, expected).unwrap();
    assert_eq!(verified.model_visible_tool_count(), 0);
    assert_eq!(verified.status(), "created");
    for (response, should_complete) in [
        (
            r#"{"choices":[{"message":{"role":"assistant","content":"A useful answer"}}]}"#,
            true,
        ),
        (
            r#"{"choices":[{"message":{"role":"assistant","content":null,"tool_calls":[{"id":"call:forged","type":"function","function":{"name":"exec","arguments":"{}"}}]}}]}"#,
            false,
        ),
    ] {
        let (url, http) = server(response);
        let mut provider =
            HttpModelProvider::new_provider_only(&url, "test", "system", "question", &verified)
                .unwrap();
        let mut journal = Journal {
            claims: 0,
            proposals: 0,
        };
        let mut effect = NoEffect;
        let result = NativeAgentLoop::new_provider_only(
            &mut provider,
            &mut journal,
            &mut effect,
            &verified,
            1,
        )
        .unwrap()
        .run();
        if should_complete {
            assert_eq!(
                result,
                Ok(RunResult::CompletionProposal("A useful answer".into()))
            );
            assert_eq!(journal.proposals, 1);
        } else {
            assert_eq!(result, Err(RunFault::ToolNotGranted));
            assert_eq!(journal.proposals, 0);
        }
        assert_eq!(journal.claims, 1);
        http.join().unwrap();
    }
    println!("PG18_VERIFIED_NO_TOOL_REAL_HTTP_RUST_LOOP_PASS");
}
