package ordivon.security.v2.agent_admission

import rego.v1

risk_rank := {
	"R0": 0,
	"R1": 1,
	"R2": 2,
	"R3": 3,
	"R4": 4,
	"R5": 5,
}

action_granted if {
	input.effect.action in input.grant.allowedActions
}

# Grant prefixes refer to path segments, not arbitrary string prefixes.
# "/articles" covers "/articles" and "/articles/42", not "/articles-private".
resource_granted if {
	some prefix in input.grant.resourcePrefixes
	input.effect.resource == prefix
}

resource_granted if {
	some prefix in input.grant.resourcePrefixes
	startswith(input.effect.resource, concat("", [trim_suffix(prefix, "/"), "/"]))
}

nonempty_string(value) if {
	is_string(value)
	value != ""
}

qualified_sha256(value) if {
	is_string(value)
	regex.match("^sha256:[0-9a-f]{64}$", value)
}

natural_number(value) if {
	is_number(value)
	value >= 0
	value == floor(value)
}

# A policy can also be evaluated directly by OPA, without the public Python
# JSON-Schema adapter. Direct policy evaluation must never interpret missing or
# mistyped security-critical fields as the absence of a denial reason.
decision_input_valid if {
	input.schemaVersion == 1
	object.keys(input) == {"schemaVersion", "nowEpochSeconds", "principal", "agent", "grant", "effect", "approval"}
	natural_number(input.nowEpochSeconds)
	is_object(input.principal)
	object.keys(input.principal) == {"principalId", "authenticated", "authnMethod"}
	nonempty_string(input.principal.principalId)
	is_boolean(input.principal.authenticated)
	input.principal.authnMethod in {"webauthn", "session", "federated"}
	is_object(input.agent)
	object.keys(input.agent) == {"agentId", "authenticated", "credentialKind"}
	nonempty_string(input.agent.agentId)
	is_boolean(input.agent.authenticated)
	input.agent.credentialKind in {"dpop-key", "spiffe-svid", "mtls", "gnap-key"}
	is_object(input.grant)
	object.keys(input.grant) == {"grantId", "grantDigest", "active", "principalId", "agentId", "audience", "allowedActions", "resourcePrefixes", "expiresAtEpochSeconds", "maxRiskClass", "stepUpAtOrAbove", "remainingEffects"}
	nonempty_string(input.grant.grantId)
	qualified_sha256(input.grant.grantDigest)
	is_boolean(input.grant.active)
	nonempty_string(input.grant.principalId)
	nonempty_string(input.grant.agentId)
	nonempty_string(input.grant.audience)
	is_array(input.grant.allowedActions)
	count(input.grant.allowedActions) > 0
	every action in input.grant.allowedActions { nonempty_string(action) }
	count({action | some action in input.grant.allowedActions}) == count(input.grant.allowedActions)
	is_array(input.grant.resourcePrefixes)
	count(input.grant.resourcePrefixes) > 0
	every prefix in input.grant.resourcePrefixes {
		is_string(prefix)
		startswith(prefix, "/")
	}
	count({prefix | some prefix in input.grant.resourcePrefixes}) == count(input.grant.resourcePrefixes)
	natural_number(input.grant.expiresAtEpochSeconds)
	input.grant.maxRiskClass in object.keys(risk_rank)
	input.grant.stepUpAtOrAbove in object.keys(risk_rank)
	natural_number(input.grant.remainingEffects)
	is_object(input.effect)
	object.keys(input.effect) == {"effectId", "effectDigest", "action", "resource", "audience", "riskClass", "effectType"}
	qualified_sha256(input.effect.effectId)
	qualified_sha256(input.effect.effectDigest)
	nonempty_string(input.effect.action)
	nonempty_string(input.effect.resource)
	startswith(input.effect.resource, "/")
	nonempty_string(input.effect.audience)
	input.effect.riskClass in object.keys(risk_rank)
	nonempty_string(input.effect.effectType)
	is_object(input.approval)
	valid_approval_keys
	is_boolean(input.approval.verified)
	valid_approval_principal
	valid_approval_effect_id
	valid_approval_effect_digest
	input.approval.method in {null, "webauthn"}
}

valid_approval_keys if {
	object.keys(input.approval) == {"verified", "principalId", "effectId", "method"}
}

valid_approval_keys if {
	object.keys(input.approval) == {"verified", "principalId", "effectId", "effectDigest", "method"}
}

valid_approval_effect_id if { input.approval.effectId == null }
valid_approval_effect_id if { qualified_sha256(input.approval.effectId) }

valid_approval_effect_digest if {
	object.get(input.approval, "effectDigest", null) == null
}
valid_approval_effect_digest if {
	qualified_sha256(input.approval.effectDigest)
}

valid_approval_principal if { input.approval.principalId == null }
valid_approval_principal if { nonempty_string(input.approval.principalId) }



risk_within_grant if {
	risk_rank[input.effect.riskClass] <= risk_rank[input.grant.maxRiskClass]
}

step_up_required if {
	risk_rank[input.effect.riskClass] >= risk_rank[input.grant.stepUpAtOrAbove]
}

effect_bound_approval if {
	input.approval.verified
	input.approval.method == "webauthn"
	input.approval.principalId == input.principal.principalId
	input.approval.effectId == input.effect.effectId
	input.approval.effectDigest == input.effect.effectDigest
}

reason := "invalid-input" if {
	not decision_input_valid
}
else := "principal-not-authenticated" if {
	not input.principal.authenticated
}

else := "agent-not-authenticated" if {
	input.principal.authenticated
	not input.agent.authenticated
}

else := "grant-inactive" if {
	input.principal.authenticated
	input.agent.authenticated
	not input.grant.active
}

else := "principal-grant-mismatch" if {
	input.principal.authenticated
	input.agent.authenticated
	input.grant.active
	input.grant.principalId != input.principal.principalId
}

else := "agent-grant-mismatch" if {
	input.principal.authenticated
	input.agent.authenticated
	input.grant.active
	input.grant.principalId == input.principal.principalId
	input.grant.agentId != input.agent.agentId
}

else := "grant-expired" if {
	input.principal.authenticated
	input.agent.authenticated
	input.grant.active
	input.grant.principalId == input.principal.principalId
	input.grant.agentId == input.agent.agentId
	input.nowEpochSeconds >= input.grant.expiresAtEpochSeconds
}

else := "audience-mismatch" if {
	input.principal.authenticated
	input.agent.authenticated
	input.grant.active
	input.grant.principalId == input.principal.principalId
	input.grant.agentId == input.agent.agentId
	input.nowEpochSeconds < input.grant.expiresAtEpochSeconds
	input.effect.audience != input.grant.audience
}

else := "action-not-granted" if {
	input.principal.authenticated
	input.agent.authenticated
	input.grant.active
	input.grant.principalId == input.principal.principalId
	input.grant.agentId == input.agent.agentId
	input.nowEpochSeconds < input.grant.expiresAtEpochSeconds
	input.effect.audience == input.grant.audience
	not action_granted
}

else := "resource-not-granted" if {
	input.principal.authenticated
	input.agent.authenticated
	input.grant.active
	input.grant.principalId == input.principal.principalId
	input.grant.agentId == input.agent.agentId
	input.nowEpochSeconds < input.grant.expiresAtEpochSeconds
	input.effect.audience == input.grant.audience
	action_granted
	not resource_granted
}

else := "effect-budget-exhausted" if {
	input.principal.authenticated
	input.agent.authenticated
	input.grant.active
	input.grant.principalId == input.principal.principalId
	input.grant.agentId == input.agent.agentId
	input.nowEpochSeconds < input.grant.expiresAtEpochSeconds
	input.effect.audience == input.grant.audience
	action_granted
	resource_granted
	input.grant.remainingEffects <= 0
}

else := "risk-exceeds-grant" if {
	input.principal.authenticated
	input.agent.authenticated
	input.grant.active
	input.grant.principalId == input.principal.principalId
	input.grant.agentId == input.agent.agentId
	input.nowEpochSeconds < input.grant.expiresAtEpochSeconds
	input.effect.audience == input.grant.audience
	action_granted
	resource_granted
	input.grant.remainingEffects > 0
	not risk_within_grant
}

else := "principal-step-up-required" if {
	input.principal.authenticated
	input.agent.authenticated
	input.grant.active
	input.grant.principalId == input.principal.principalId
	input.grant.agentId == input.agent.agentId
	input.nowEpochSeconds < input.grant.expiresAtEpochSeconds
	input.effect.audience == input.grant.audience
	action_granted
	resource_granted
	input.grant.remainingEffects > 0
	risk_within_grant
	step_up_required
	not effect_bound_approval
}

else := "admitted"

outcome := "ALLOW" if {
	reason == "admitted"
}

outcome := "STEP_UP" if {
	reason == "principal-step-up-required"
}

outcome := "DENY" if {
	reason != "admitted"
	reason != "principal-step-up-required"
}

authority_projection := {
	"requestId": input.effect.effectId,
	"requestDigest": input.effect.effectDigest,
	"actorId": input.agent.agentId,
	"authorityId": input.grant.grantId,
	"authorityDigest": input.grant.grantDigest,
	"zoneRef": input.grant.audience,
	"capability": input.effect.action,
	"effectType": input.effect.effectType,
} if {
	reason == "admitted"
}

authority_projection := null if {
	reason != "admitted"
}

decision := {
	"schemaVersion": 1,
	"kind": "ordivon.security.agent-admission",
	"principalId": input.principal.principalId,
	"agentId": input.agent.agentId,
	"grantId": input.grant.grantId,
	"effectId": input.effect.effectId,
	"outcome": outcome,
	"reason": reason,
	"authorityProjection": authority_projection,
}
