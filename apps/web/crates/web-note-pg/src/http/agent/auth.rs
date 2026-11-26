//! Security-owned verifier adapter and native durable replay obligation.

use super::AgentState;
use crate::OwnerError;
use axum::http::{HeaderMap, StatusCode};
use serde::Deserialize;
use serde_json::json;

#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
pub(super) struct Agent {
    pub agent_id: String,
    client_id: String,
    subject: String,
}
#[derive(Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Replay {
    proof_id: String,
    verified_at: i64,
    ttl_seconds: i64,
}
#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
enum Reply {
    Candidate { agent: Agent, replay: Replay },
    Denied,
}
pub(super) fn header<'a>(headers: &'a HeaderMap, name: &str) -> Option<&'a str> {
    let mut values = headers.get_all(name).iter();
    let v = values.next()?.to_str().ok()?;
    if values.next().is_some() || v.is_empty() || v.len() > 16384 || v.contains(',') {
        return None;
    }
    Some(v)
}
type Rejection = (StatusCode, &'static str);
fn denied() -> Rejection {
    (
        StatusCode::UNAUTHORIZED,
        "agent-request-verification-failed",
    )
}
pub(super) async fn authenticate(
    s: &AgentState,
    headers: &HeaderMap,
    path: &str,
) -> Result<Agent, Rejection> {
    let authorization = header(headers, "authorization").ok_or_else(denied)?;
    let proof = header(headers, "dpop").ok_or_else(denied)?;
    if !authorization.starts_with("DPoP ") {
        return Err(denied());
    }
    let now = (s.clock)();
    let result=s.verifier.call::<Reply>(json!({"issuer":s.issuer.as_ref(),"audience":s.origin.as_ref(),"allowInsecure":s.allow_insecure,"path":path,"authorization":authorization,"dpop":proof,"now":now})).await;
    let (agent, replay) = match result {
        Ok(Reply::Candidate { agent, replay }) => (agent, replay),
        Ok(Reply::Denied) => return Err(denied()),
        Err(_) => {
            return Err((
                StatusCode::SERVICE_UNAVAILABLE,
                "agent-verifier-unavailable",
            ));
        }
    };
    let after = (s.clock)();
    if replay.verified_at != now
        || replay.ttl_seconds != 600
        || after < now
        || after - now > 30
        || agent.client_id.is_empty()
        || agent.client_id.len() > 128
        || agent.subject.is_empty()
        || agent.subject.len() > 2048
        || agent.agent_id != format!("oauth-client:{}", agent.client_id)
        || agent.agent_id.contains('\0')
        || agent.subject.contains('\0')
    {
        return Err(denied());
    }
    // A callback in another process is only an obligation. No grant or effect
    // access until the actual owner has acknowledged this single-use claim.
    match s
        .store
        .consume_dpop_proof(&replay.proof_id, after, replay.ttl_seconds)
        .await
    {
        Ok(()) => Ok(agent),
        Err(OwnerError::DpopReplayed | OwnerError::DpopInvalid) => Err(denied()),
        Err(_) => Err((StatusCode::SERVICE_UNAVAILABLE, "agent-replay-unavailable")),
    }
}
