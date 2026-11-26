//! Qualification-only protected read composition, fixed artifact.read; no effect authority.
use crate::{
    artifact_stream::{Standing, Stream},
    logic::parse_execution_ref,
    owner_credential::read_fixture_bearer,
    owner_transport::{self, ReadFailure, ReadRequest},
};
use serde::Serialize;
use serde_json::{Value, json};
use std::{path::Path, time::Duration};

#[derive(Debug, Serialize)]
#[serde(tag = "outcome", rename_all = "snake_case")]
pub(crate) enum Outcome {
    Stream { evidence: Standing },
    OwnerFailure { failure: ReadFailure },
}
fn rejected(reason: &'static str) -> Outcome {
    Outcome::Stream {
        evidence: Standing::Rejected { reason },
    }
}

// Bound maximum raw bytes per request to leave space for JSON escape amplification
// in the existing 1 MiB transport frame. One lifecycle and total deadline.
const MAX_CHUNK: u64 = 128 * 1024;
pub(crate) async fn read_fixture(
    endpoint: &str,
    credential: &Path,
    legacy: bool,
    input: &Value,
) -> Outcome {
    let reference = input["operationRef"].as_str().unwrap_or_default();
    let Some(("runtime.linux", job_id)) = parse_execution_ref(reference) else {
        return rejected("invalid_operation_ref");
    };
    let Some(max_bytes) = input["maxTotalBytes"].as_u64() else {
        return rejected("stream_budget");
    };
    let Some(max_windows) = input["maxWindows"].as_u64() else {
        return rejected("stream_budget");
    };
    let Some(chunk) = input["chunkBytes"]
        .as_u64()
        .filter(|n| (4..=MAX_CHUNK).contains(n))
    else {
        return rejected("invalid_chunk_budget");
    };
    let mut state = match Stream::new(reference, &input["descriptor"], max_bytes, max_windows) {
        Ok(s) => s,
        Err(reason) => return rejected(reason),
    };
    let Some(url) = owner_transport::fixture_endpoint(endpoint) else {
        return rejected("unqualified_fixture_endpoint");
    };
    let Ok(token) = read_fixture_bearer(credential) else {
        return rejected("unqualified_fixture_credential");
    };
    let budget = Duration::from_secs(5);
    let outcome = tokio::time::timeout(budget, async {
        let client = match owner_transport::connect(url, budget, legacy, Some(token)).await {
            Ok(c) => c,
            Err(failure) => return Outcome::OwnerFailure { failure },
        };
        let mut failure = None;
        while state.can_read() {
            let offset = state.next();
            // Allow a small final request even for empty content; Owner controls exact EOF.
            let max_bytes = chunk.min(state.remaining().max(1));
            let request =
                json!({"artifactId":state.artifact_id(),"offset":offset,"maxBytes":max_bytes});
            let result = owner_transport::call_read(
                &client,
                ReadRequest::Artifact {
                    job_id,
                    artifact_id: state.artifact_id(),
                    offset,
                    max_bytes,
                },
            )
            .await;
            match result {
                Ok(value) => state.accept(&request, &value),
                Err(err) => {
                    failure = Some(err);
                    break;
                }
            }
        }
        let _ = client.cancel().await;
        if let Some(failure) = failure {
            Outcome::OwnerFailure { failure }
        } else {
            Outcome::Stream {
                evidence: state.standing(),
            }
        }
    })
    .await;
    outcome.unwrap_or_else(|_| rejected("stream_deadline"))
}
