//! Rust-native PostgreSQL Run commands, never a Python process.
#![forbid(unsafe_code)]
use ordivon_harness_core::loads_strict;
use ordivon_harness_pg::{create_run, read_run_readonly};
use postgres::{Client, NoTls};
use serde_json::json;
use std::{env, error::Error, fs, process::ExitCode};

fn execute() -> Result<(), Box<dyn Error>> {
    let mut args = env::args().skip(1);
    let action = args
        .next()
        .ok_or("usage: ordivon-harness <create CONTRACT_FILE|status RUN_ID|inspect RUN_ID>")?;
    if !matches!(action.as_str(), "create" | "status" | "inspect") {
        return Err(format!("unknown native Harness command: {action}").into());
    }
    let input = args.next().ok_or("missing command argument")?;
    if input.is_empty() || args.next().is_some() {
        return Err("expected exactly one argument".into());
    }
    let dsn = env::var("HARNESS_PG_DSN")?;
    let schema = env::var("HARNESS_PG_SCHEMA").unwrap_or_else(|_| "harness".into());
    let mut db = Client::connect(&dsn, NoTls)?;
    if action == "create" {
        let contract = loads_strict(&fs::read_to_string(&input)?)?;
        let outcome = create_run(&mut db, &schema, &contract)?;
        println!(
            "{}",
            serde_json::to_string(&json!({
                "admission":format!("{outcome:?}").to_lowercase(),
                "runId":contract.field("harnessRunId").and_then(|v|v.as_str())
            }))?
        );
        return Ok(());
    }
    let result = read_run_readonly(&mut db, &schema, &input)?;
    let p = result.projection;
    let mut obj = json!({
      "runId":p.harness_run_id,"revision":p.revision,"status":p.status,
      "contractDigest":p.contract_digest,"eventCount":result.events.len(),
      "terminalEventId":p.terminal_event_id
    });
    if action == "inspect" {
        obj["events"] = serde_json::Value::Array(
            result
                .events
                .iter()
                .map(|e| {
                    json!({
                        "eventId":e.event_id,"sequence":e.sequence,"revision":e.run_revision,
                        "kind":e.event_kind,"payloadDigest":e.payload_digest
                    })
                })
                .collect(),
        );
    }
    println!("{}", serde_json::to_string(&obj)?);
    Ok(())
}
fn main() -> ExitCode {
    match execute() {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("ordivon-harness: {e}");
            ExitCode::FAILURE
        }
    }
}
