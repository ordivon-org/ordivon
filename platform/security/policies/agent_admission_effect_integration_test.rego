package ordivon.security.v2.agent_admission_effect_integration

import rego.v1

base_input := {
	"schemaVersion": 1,
	"nowEpochSeconds": 1789930400,
	"principal": {
		"principalId": "principal:user-123",
		"authenticated": true,
		"authnMethod": "webauthn",
	},
	"agent": {
		"agentId": "agent:ordivon/research-17",
		"authenticated": true,
		"credentialKind": "dpop-key",
	},
	"grant": {
		"grantId": "grant:research-17-v1",
		"grantDigest": "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
		"active": true,
		"principalId": "principal:user-123",
		"agentId": "agent:ordivon/research-17",
		"audience": "https://www.example.test/api",
		"allowedActions": ["comment.create"],
		"resourcePrefixes": ["/comments/"],
		"expiresAtEpochSeconds": 1790016800,
		"maxRiskClass": "R4",
		"stepUpAtOrAbove": "R4",
		"remainingEffects": 3,
	},
	"effect": {
		"effectId": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
		"effectDigest": "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
		"action": "comment.create",
		"resource": "/comments/article-42",
		"audience": "https://www.example.test/api",
		"riskClass": "R2",
		"effectType": "website.comment.create",
	},
	"approval": {
		"verified": false,
		"principalId": null,
		"effectId": null,
		"method": null,
	},
}

test_allowed_agent_projection_is_accepted_by_existing_effect_admission if {
	agent_decision := data.ordivon.security.v2.agent_admission.decision with input as base_input
	agent_decision.outcome == "ALLOW"

	projection := agent_decision.authorityProjection
	effect_input := {
		"actorIds": [projection.actorId],
		"authorities": [{
			"authorityId": projection.authorityId,
			"actorId": projection.actorId,
			"zoneRefs": [projection.zoneRef],
			"capabilities": [projection.capability],
			"authorityDigest": projection.authorityDigest,
		}],
		"request": projection,
	}

	effect_decision := data.ordivon.security.v2.effect_admission.decision with input as effect_input
	effect_decision.admitted
	effect_decision.reason == "admitted"
	effect_decision.requestId == base_input.effect.effectId
	effect_decision.requestDigest == base_input.effect.effectDigest
}

test_step_up_does_not_emit_effect_authority if {
	high_risk := object.union(base_input.effect, {"riskClass": "R4"})
	x := object.union(base_input, {"effect": high_risk})
	agent_decision := data.ordivon.security.v2.agent_admission.decision with input as x
	agent_decision.outcome == "STEP_UP"
	agent_decision.authorityProjection == null
}
