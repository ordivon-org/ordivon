//! Bind actual Security decision projections to the exact native request.
use crate::effect::{EffectRequest, GrantSnapshot};
use serde_json::{Value, json};
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(super) enum Decision {
    Allow,
    StepUp,
    Deny,
}
pub(super) fn input(
    now: i64,
    g: &GrantSnapshot,
    r: &EffectRequest,
    risk: &str,
    approved: bool,
) -> Value {
    let approval = if approved {
        json!({"verified":true,"principalId":g.principal_id,"effectId":r.effect_id,"effectDigest":r.effect_digest,"method":"webauthn"})
    } else {
        json!({"verified":false,"principalId":null,"effectId":null,"effectDigest":null,"method":null})
    };
    json!({"schemaVersion":1,"nowEpochSeconds":now,
 "principal":{"principalId":g.principal_id,"authenticated":true,"authnMethod":"webauthn"},
 "agent":{"agentId":r.agent_id,"authenticated":true,"credentialKind":"dpop-key"},
 "grant":{"grantId":g.grant_id,"grantDigest":g.grant_digest,"active":g.active,"principalId":g.principal_id,"agentId":g.agent_id,"audience":g.audience,"allowedActions":g.allowed_actions,"resourcePrefixes":g.resource_prefixes,"expiresAtEpochSeconds":g.expires_at_epoch_seconds,"maxRiskClass":g.max_risk_class,"stepUpAtOrAbove":g.step_up_at_or_above,"remainingEffects":g.remaining_effects},
 "effect":{"effectId":r.effect_id,"effectDigest":r.effect_digest,"action":r.action,"resource":r.resource,"audience":r.audience,"riskClass":risk,"effectType":r.effect_type},"approval":approval})
}
pub(super) fn check(v: &Value, g: &GrantSnapshot, r: &EffectRequest) -> Option<Decision> {
    if v["schemaVersion"] != 1 || v["kind"] != "ordivon.security.agent-admission-chain" {
        return None;
    }
    let a = &v["agent"];
    let e = &v["effect"];
    if a["schemaVersion"] != 1
        || a["kind"] != "ordivon.security.agent-admission"
        || a["principalId"] != g.principal_id
        || a["agentId"] != r.agent_id
        || a["grantId"] != g.grant_id
        || a["effectId"] != r.effect_id
    {
        return None;
    }
    match a["outcome"].as_str()? {
        "ALLOW" => {
            let exact = json!({"requestId":r.effect_id,"requestDigest":r.effect_digest,"actorId":r.agent_id,"authorityId":g.grant_id,"authorityDigest":g.grant_digest,"zoneRef":g.audience,"capability":r.action,"effectType":r.effect_type});
            if a["reason"] != "admitted"
                || a["authorityProjection"] != exact
                || e["kind"] != "ordivon.security.effect-admission"
                || e["schemaVersion"] != 1
                || e["inputContractVersion"] != 2
                || e["authorityDigestBound"] != true
                || e["admitted"] != true
                || e["reason"] != "admitted"
            {
                return None;
            }
            for (key, value) in exact.as_object()? {
                if e[key] != *value {
                    return None;
                }
            }
            Some(Decision::Allow)
        }
        "STEP_UP"
            if a["reason"] == "principal-step-up-required"
                && a.get("authorityProjection") == Some(&Value::Null)
                && v.get("effect") == Some(&Value::Null) =>
        {
            Some(Decision::StepUp)
        }
        "DENY"
            if a["reason"].is_string()
                && a.get("authorityProjection") == Some(&Value::Null)
                && v.get("effect") == Some(&Value::Null) =>
        {
            Some(Decision::Deny)
        }
        _ => None,
    }
}
