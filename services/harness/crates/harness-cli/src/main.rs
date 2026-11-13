//! Native Run inspection: no Python process, no fallback to SQLite and no second Store.
#![forbid(unsafe_code)]

use ordivon_harness_pg::read_run_readonly;
use postgres::{Client, NoTls};
use serde_json::json;
use std::{env, error::Error, process::ExitCode};

fn execute() -> Result<(), Box<dyn Error>> {
    let mut args = env::args().skip(1);
    let action = args
        .next()
        .ok_or("usage: ordivon-harness <status|inspect> RUN_ID")?;
    if action != "status" && action != "inspect" {
        return Err(format!("unknown Harness operation: {action}").into());
    }
    let run_id = args.next().ok_or("missing RUN_ID")?;
    if run_id.is_empty() || args.next().is_some() {
        return Err("expected exactly one nonempty RUN_ID".into());
    }
    let dsn = env::var("HARNESS_PG_DSN")?;
    let schema = env::var("HARNESS_PG_SCHEMA").unwrap_or_else(|_| "harness".to_owned());
    let mut connection = Client::connect(&dsn, NoTls)?;
    let evidence = read_run_readonly(&mut connection, &schema, &run_id)?;
    let p = evidence.projection;
    let mut output = json!({
        "runId": p.harness_run_id,
        "revision": p.revision,
        "status": p.status,
        "contractDigest": p.contract_digest,
        "eventCount": evidence.events.len(),
        "terminalEventId": p.terminal_event_id
    });
    if action == "inspect" {
        output["events"] = serde_json::Value::Array(
            evidence
                .events
                .iter()
                .map(|event| {
                    json!({
                        "eventId": event.event_id,
                        "sequence": event.sequence,
                        "revision": event.run_revision,
                        "kind": event.event_kind,
                        "payloadDigest": event.payload_digest
                    })
                })
                .collect(),
        );
    }
    println!("{}", serde_json::to_string(&output)?);
    Ok(())
}

fn main() -> ExitCode {
    match execute() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("ordivon-harness: {error}");
            ExitCode::FAILURE
        }
    }
}
