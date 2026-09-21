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

resource_granted if {
	some prefix in input.grant.resourcePrefixes
	startswith(input.effect.resource, prefix)
}

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
}

reason := "principal-not-authenticated" if {
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
