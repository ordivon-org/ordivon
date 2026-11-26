use super::super::problem;
use super::{
    AgentState,
    admission::{self, Decision},
    auth,
};
use crate::{
    OwnerError,
    effect::{EffectOperation, EffectReceipt, EffectRequest, PendingOutcome},
};
use axum::{
    Json,
    extract::{OriginalUri, Path, State},
    http::{HeaderMap, StatusCode},
    response::{IntoResponse, Response},
};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use uuid::Uuid;
fn error(e: OwnerError) -> Response {
    let status = match e {
        OwnerError::ActorMismatch
        | OwnerError::GrantUnavailable
        | OwnerError::Binding
        | OwnerError::Fence => StatusCode::FORBIDDEN,
        OwnerError::Conflict
        | OwnerError::GrantChanged
        | OwnerError::GrantAmbiguous
        | OwnerError::ApprovalBinding
        | OwnerError::PendingConflict
        | OwnerError::NotPublishable => StatusCode::CONFLICT,
        OwnerError::Busy
        | OwnerError::Pool(_)
        | OwnerError::AuthorityCommitUnknown { .. }
        | OwnerError::CommitUnknown { .. }
        | OwnerError::RollbackUnknown { .. } => StatusCode::SERVICE_UNAVAILABLE,
        OwnerError::Invalid => StatusCode::UNPROCESSABLE_ENTITY,
        _ => StatusCode::INTERNAL_SERVER_ERROR,
    };
    problem(status, e.code())
}
fn receipt(r: EffectReceipt, replayed: bool, fresh: StatusCode) -> Response {
    let Ok(result) = serde_json::from_str::<Value>(&r.result_json) else {
        return problem(StatusCode::INTERNAL_SERVER_ERROR, "effect-corrupt");
    };
    (if replayed{StatusCode::OK}else{fresh},Json(json!({"receipt":{"effectId":r.effect_id,"effectDigest":r.effect_digest,"principalId":r.principal_id,"agentId":r.agent_id,"grantId":r.grant_id,"action":r.action,"resource":r.resource,"result":result,"committedAt":r.committed_at},"replayed":replayed}))).into_response()
}
fn effect_id(h: &HeaderMap) -> Option<String> {
    let v = auth::header(h, "x-ordivon-effect-id")?;
    let hex = v.strip_prefix("sha256:")?;
    (hex.len() == 64
        && hex
            .bytes()
            .all(|b| b.is_ascii_digit() || matches!(b, b'a'..=b'f')))
    .then(|| v.to_owned())
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub(super) struct CreateInput {
    content: String,
}
#[derive(Serialize)]
struct CreateDigest<'a> {
    action: &'a str,
    resource: &'a str,
    content: &'a str,
}
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct PublishDigest<'a> {
    action: &'a str,
    resource: &'a str,
    note_id: &'a str,
}
fn digest(v: &impl Serialize) -> String {
    let bytes = serde_json::to_vec(v).expect("fixed string digest input");
    {
        use std::fmt::Write;
        let mut out = String::from("sha256:");
        for b in Sha256::digest(bytes) {
            write!(&mut out, "{b:02x}").expect("String write");
        }
        out
    }
}
pub(super) async fn create(
    State(s): State<AgentState>,
    OriginalUri(uri): OriginalUri,
    headers: HeaderMap,
    Json(input): Json<CreateInput>,
) -> Response {
    let path = "/api/agent/canary/notes";
    if uri.path_and_query().map(|v| v.as_str()) != Some(path)
        || input.content.is_empty()
        || input.content.encode_utf16().count() > 2000
        || input.content.contains('\0')
    {
        return problem(StatusCode::UNPROCESSABLE_ENTITY, "invalid-input");
    }
    let Some(id) = effect_id(&headers) else {
        return problem(StatusCode::UNPROCESSABLE_ENTITY, "effect-id-invalid");
    };
    let agent = match auth::authenticate(&s, &headers, path).await {
        Ok(a) => a,
        Err((status, code)) => return problem(status, code),
    };
    let (action, resource) = ("canary.note.create", "/canary/notes");
    let r = EffectRequest {
        effect_id: id,
        effect_digest: digest(&CreateDigest {
            action,
            resource,
            content: &input.content,
        }),
        agent_id: agent.agent_id,
        audience: s.origin.to_string(),
        action: action.into(),
        resource: resource.into(),
        effect_type: "website.canary.note.create".into(),
    };
    execute(
        &s,
        r,
        EffectOperation::Create {
            note_id: Uuid::new_v4(),
            content: input.content,
        },
        false,
    )
    .await
}
pub(super) async fn publish(
    State(s): State<AgentState>,
    OriginalUri(uri): OriginalUri,
    Path(note): Path<String>,
    headers: HeaderMap,
) -> Response {
    if Uuid::parse_str(&note)
        .ok()
        .is_none_or(|u| u.to_string() != note)
    {
        return problem(StatusCode::UNPROCESSABLE_ENTITY, "invalid-note-id");
    }
    let path = format!("/api/agent/canary/notes/{note}/publish");
    if uri.path_and_query().map(|v| v.as_str()) != Some(&path) {
        return problem(StatusCode::UNPROCESSABLE_ENTITY, "invalid-input");
    }
    let Some(id) = effect_id(&headers) else {
        return problem(StatusCode::UNPROCESSABLE_ENTITY, "effect-id-invalid");
    };
    let agent = match auth::authenticate(&s, &headers, &path).await {
        Ok(a) => a,
        Err((status, code)) => return problem(status, code),
    };
    let action = "canary.note.publish";
    let resource = format!("/canary/notes/{note}");
    let r = EffectRequest {
        effect_id: id,
        effect_digest: digest(&PublishDigest {
            action,
            resource: &resource,
            note_id: &note,
        }),
        agent_id: agent.agent_id,
        audience: s.origin.to_string(),
        action: action.into(),
        resource,
        effect_type: "website.canary.note.publish".into(),
    };
    execute(&s, r, EffectOperation::Publish { note_id: note }, true).await
}
async fn execute(s: &AgentState, r: EffectRequest, op: EffectOperation, publish: bool) -> Response {
    let fresh = if publish {
        StatusCode::OK
    } else {
        StatusCode::CREATED
    };
    match s.store.observe_effect(&r).await {
        Ok(Some(v)) => return receipt(v, true, fresh),
        Ok(None) => {}
        Err(e) => return error(e),
    }
    let now = (s.clock)();
    let g = match s
        .store
        .resolve_grant(&r.agent_id, &r.audience, &r.action, &r.resource, now)
        .await
    {
        Ok(g) => g,
        Err(e) => return error(e),
    };
    // Only Publish consumes an approval in the native effect kernel. Do not
    // present a Create approval as sufficient to OPA or reuse it indefinitely.
    let approved = if publish {
        match s.store.observe_authority(&g.principal_id, &r).await {
            Ok(v) => {
                if let Some(receipt_value) = v.receipt {
                    return receipt(receipt_value, true, fresh);
                }
                v.approval.is_some_and(|a| {
                    a.consumed_at.is_none() && a.expires_at > now && a.verified_at <= now
                })
            }
            Err(e) => return error(e),
        }
    } else {
        false
    };
    let input = admission::input(now, &g, &r, if publish { "R4" } else { "R2" }, approved);
    let output = s.admission.call::<Value>(input).await;
    let decision = match output
        .ok()
        .as_ref()
        .and_then(|v| admission::check(v, &g, &r))
    {
        Some(d) => d,
        None => {
            return problem(
                StatusCode::SERVICE_UNAVAILABLE,
                "security-admission-unavailable",
            );
        }
    };
    match s.store.observe_effect(&r).await {
        Ok(Some(v)) => return receipt(v, true, fresh),
        Ok(None) => {}
        Err(e) => return error(e),
    }
    let at = (s.clock)();
    if at < now || at - now > 30 {
        return problem(StatusCode::SERVICE_UNAVAILABLE, "admission-stale");
    }
    match decision {
        Decision::Deny => problem(StatusCode::FORBIDDEN, "agent-effect-denied"),
        Decision::StepUp if publish => {
            let Some(expires) = at.checked_add(300) else {
                return problem(StatusCode::SERVICE_UNAVAILABLE, "admission-stale");
            };
            match s.store.register_selected_pending(&g.fence(),&r,&op,at,expires).await{
    Ok(PendingOutcome::AlreadyCommitted(v))=>receipt(v,true,fresh),
    Ok(PendingOutcome::Registered(_))=>(StatusCode::PRECONDITION_REQUIRED,[(axum::http::header::CONTENT_TYPE,"application/problem+json")],Json(json!({"status":428,"title":"Principal approval required","effectId":r.effect_id,"effectDigest":r.effect_digest}))).into_response(),
    Err(e)=>error(e),
   }
        }
        Decision::StepUp => problem(StatusCode::FORBIDDEN, "create-step-up-not-supported"),
        Decision::Allow if publish && !approved => {
            problem(StatusCode::FORBIDDEN, "effect-fence-rejected")
        }
        Decision::Allow => match s
            .store
            .commit_selected_effect(&g.fence(), &r, &op, Uuid::new_v4(), at)
            .await
        {
            Ok(v) => receipt(v.receipt, v.replayed, fresh),
            Err(e) => error(e),
        },
    }
}
