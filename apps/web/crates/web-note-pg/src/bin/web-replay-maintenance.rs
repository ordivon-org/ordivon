//! Explicit one-shot local maintenance. The scheduler is external.
//! No automatic retries, hidden task, production discovery or secret output.
use ordivon_web_note_pg::{PgNoteStore, maintenance::ReplayMaintenance};
use std::{
    path::Path,
    process::ExitCode,
    time::{SystemTime, UNIX_EPOCH},
};

#[tokio::main(flavor = "current_thread")]
async fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let [socket, port, user, database, batch, max_batches] = args.as_slice() else {
        eprintln!("usage: web-replay-maintenance SOCKET PORT USER DATABASE BATCH_SIZE MAX_BATCHES");
        return ExitCode::from(2);
    };
    let (Ok(port), Ok(batch), Ok(max_batches)) = (
        port.parse::<u16>(),
        batch.parse::<u32>(),
        max_batches.parse::<u32>(),
    ) else {
        eprintln!("invalid maintenance configuration");
        return ExitCode::from(2);
    };
    if !Path::new(socket).is_absolute() || port == 0 || user.is_empty() || database.is_empty() {
        eprintln!("explicit local owner coordinate required");
        return ExitCode::from(2);
    }
    let Ok(runner) = ReplayMaintenance::new(batch, max_batches) else {
        eprintln!("invalid maintenance budget");
        return ExitCode::from(2);
    };
    let Ok(store) = PgNoteStore::local(Path::new(socket), port, user, database) else {
        eprintln!("invalid owner connection configuration");
        return ExitCode::from(2);
    };
    let Some(now) = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .ok()
        .and_then(|d| i64::try_from(d.as_secs()).ok())
    else {
        eprintln!("trusted time unavailable");
        return ExitCode::FAILURE;
    };
    match runner.run_once(&store, now).await {
        Ok(report) => {
            println!(
                "{}",
                serde_json::json!({"status":"confirmed","deleted":report.deleted,"batches":report.batches,"shortBatch":report.short_batch})
            );
            ExitCode::SUCCESS
        }
        Err(failure) => {
            // Error details may contain database or request coordinates.
            // An unknown last batch is not included in confirmed counts.
            println!(
                "{}",
                serde_json::json!({"status":"not-confirmed","confirmedDeleted":failure.committed_deleted,"confirmedBatches":failure.committed_batches})
            );
            ExitCode::FAILURE
        }
    }
}
