//! Physical local HTTP → Rust Loop → test-only Owner → HTTP completion.
//! The journal and effect receiver here are explicit test doubles; NOT PG or
//! proof of installed production Runtime Tool authorization.
use ordivon_harness_core::{digest_bytes, loads_strict, CanonicalDocument};
use ordivon_harness_loop::{
    native_loop::{
        AdmittedTool, DurableJournal, EffectReceiver, EffectResult, ModelDecision, NativeAgentLoop,
        RunResult,
    },
    native_provider_http::HttpModelProvider,
    tool_call::ModelToolCall,
    tool_surface::project_domain_tool_surface,
};
use serde_json::{json, Value};
use std::{
    io::{Read, Write},
    net::TcpListener,
    thread,
    time::Duration,
};

#[derive(Default)]
struct TestJournal(Vec<&'static str>);
impl DurableJournal for TestJournal {
    fn prepare_provider(&mut self, _: u32) -> Result<(), String> {
        self.0.push("provider-prepared");
        Ok(())
    }
    fn complete_provider(&mut self, _: u32, _: &ModelDecision) -> Result<(), String> {
        self.0.push("provider-recorded");
        Ok(())
    }
    fn admit_tool(&mut self, _: u32, call: &ModelToolCall) -> Result<AdmittedTool, String> {
        self.0.push("tool-admitted");
        Ok(AdmittedTool::after_committed_intent(call))
    }
    fn record_effect(&mut self, _: u32, _: &AdmittedTool, _: &EffectResult) -> Result<(), String> {
        self.0.push("owner-effect-recorded");
        Ok(())
    }
    fn record_completion(&mut self, _: u32, _: &str) -> Result<(), String> {
        self.0.push("completion-proposed");
        Ok(())
    }
    fn record_pause(&mut self, _: u32) -> Result<(), String> {
        self.0.push("paused");
        Ok(())
    }
}
#[derive(Default)]
struct TestReceiver(usize);
impl EffectReceiver for TestReceiver {
    fn execute(&mut self, grant: &AdmittedTool, _: &CanonicalDocument) -> EffectResult {
        assert_eq!(grant.name(), "search");
        assert_eq!(grant.call_id(), "call:1");
        self.0 += 1;
        EffectResult::Observed {
            owner_receipt_digest: digest_bytes(b"physical-test-owner-receipt"),
        }
    }
}
fn response(index: usize) -> &'static str {
    match index {
        0 => {
            r#"{"choices":[{"message":{"role":"assistant","content":null,"tool_calls":[{"id":"call:1","type":"function","function":{"name":"search","arguments":"{}"}}]}}]}"#
        }
        _ => r#"{"choices":[{"message":{"role":"assistant","content":"candidate-complete"}}]}"#,
    }
}
#[test]
fn native_http_loop_full_two_turn_owner_receipt() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let url = format!(
        "http://{}/v1/chat/completions",
        listener.local_addr().unwrap()
    );
    let server = thread::spawn(move || {
        for index in 0..2 {
            let (mut conn, _) = listener.accept().unwrap();
            conn.set_read_timeout(Some(Duration::from_secs(5))).unwrap();
            let mut received = Vec::new();
            let mut data = [0u8; 8192];
            loop {
                let n = conn.read(&mut data).unwrap();
                if n == 0 {
                    break;
                }
                received.extend_from_slice(&data[..n]);
                if let Some(at) = received.windows(4).position(|w| w == b"\r\n\r\n") {
                    let h = String::from_utf8_lossy(&received[..at]);
                    let length = h
                        .lines()
                        .find_map(|line| {
                            let (name, value) = line.split_once(':')?;
                            name.eq_ignore_ascii_case("content-length")
                                .then(|| value.trim().parse::<usize>().ok())
                                .flatten()
                        })
                        .expect("request Content-Length");
                    if received.len() >= at + 4 + length {
                        break;
                    }
                }
            }
            let start = received.windows(4).position(|w| w == b"\r\n\r\n").unwrap() + 4;
            let body: Value = serde_json::from_slice(&received[start..]).unwrap();
            let messages = body.get("messages").and_then(Value::as_array).unwrap();
            if index == 0 {
                assert!(!messages
                    .iter()
                    .any(|m| m.get("role") == Some(&json!("tool"))));
            } else {
                assert!(messages
                    .iter()
                    .any(|m| m.get("role") == Some(&json!("tool"))
                        && m.get("content")
                            .and_then(Value::as_str)
                            .is_some_and(|s| s.contains("sha256:"))));
                assert!(messages
                    .iter()
                    .any(|m| m.get("role") == Some(&json!("assistant"))
                        && m.get("tool_calls").is_some()));
            }
            let text = response(index);
            let packet=format!("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",text.len(),text);
            conn.write_all(packet.as_bytes()).unwrap();
        }
    });
    let catalog=loads_strict(r#"{"schemaVersion":1,"kind":"ordivon.domain-tool-catalog","domainId":"domain:smoke","revision":"v1","tools":[{"name":"search","description":"Search owner","inputSchema":{"type":"object"}}]}"#).unwrap();
    let surface = project_domain_tool_surface(&catalog, &["search"]).unwrap();
    let mut provider = HttpModelProvider::new(
        &url,
        "model",
        "test",
        "instruction",
        "question",
        &catalog,
        &surface,
    )
    .unwrap();
    let mut journal = TestJournal::default();
    let mut effect = TestReceiver::default();
    let result = NativeAgentLoop::new(
        &mut provider,
        &mut journal,
        &mut effect,
        &catalog,
        &surface,
        3,
        1,
    )
    .unwrap()
    .run()
    .unwrap();
    assert_eq!(
        result,
        RunResult::CompletionProposal("candidate-complete".to_owned())
    );
    assert_eq!(effect.0, 1);
    assert_eq!(
        journal.0,
        vec![
            "provider-prepared",
            "provider-recorded",
            "tool-admitted",
            "owner-effect-recorded",
            "provider-prepared",
            "provider-recorded",
            "completion-proposed"
        ]
    );
    server.join().unwrap();
}
