package ordivon.security.v2.agent_admission

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
		"allowedActions": ["comment.read", "comment.create", "article.read"],
		"resourcePrefixes": ["/articles/", "/comments/"],
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

with_input(overrides) := object.union_n([base_input, overrides])

test_low_risk_delegated_agent_is_allowed if {
	decision.outcome == "ALLOW" with input as base_input
	decision.reason == "admitted" with input as base_input
}

test_unknown_or_unauthenticated_agent_is_denied if {
	x := object.union(base_input, {"agent": object.union(base_input.agent, {"authenticated": false})})
	decision.outcome == "DENY" with input as x
	decision.reason == "agent-not-authenticated" with input as x
}

test_grant_cannot_cross_principal if {
	x := object.union(base_input, {"grant": object.union(base_input.grant, {"principalId": "principal:other"})})
	decision.outcome == "DENY" with input as x
	decision.reason == "principal-grant-mismatch" with input as x
}

test_grant_cannot_cross_agent if {
	x := object.union(base_input, {"grant": object.union(base_input.grant, {"agentId": "agent:other"})})
	decision.outcome == "DENY" with input as x
	decision.reason == "agent-grant-mismatch" with input as x
}

test_expired_grant_is_denied if {
	x := object.union(base_input, {"grant": object.union(base_input.grant, {"expiresAtEpochSeconds": 1789930399})})
	decision.outcome == "DENY" with input as x
	decision.reason == "grant-expired" with input as x
}

test_action_must_be_explicitly_granted if {
	x := object.union(base_input, {"effect": object.union(base_input.effect, {"action": "article.delete"})})
	decision.outcome == "DENY" with input as x
	decision.reason == "action-not-granted" with input as x
}

test_resource_must_be_inside_grant_prefix if {
	x := object.union(base_input, {"effect": object.union(base_input.effect, {"resource": "/account/recovery"})})
	decision.outcome == "DENY" with input as x
	decision.reason == "resource-not-granted" with input as x
}

test_audience_must_match_grant if {
	x := object.union(base_input, {"effect": object.union(base_input.effect, {"audience": "https://evil.example/api"})})
	decision.outcome == "DENY" with input as x
	decision.reason == "audience-mismatch" with input as x
}

test_rate_budget_is_enforced if {
	x := object.union(base_input, {"grant": object.union(base_input.grant, {"remainingEffects": 0})})
	decision.outcome == "DENY" with input as x
	decision.reason == "effect-budget-exhausted" with input as x
}

test_risk_above_grant_ceiling_is_denied if {
	x := object.union(base_input, {"effect": object.union(base_input.effect, {"riskClass": "R5"})})
	decision.outcome == "DENY" with input as x
	decision.reason == "risk-exceeds-grant" with input as x
}

test_high_risk_effect_requires_effect_bound_step_up if {
	effect := object.union(base_input.effect, {"riskClass": "R4"})
	x := object.union(base_input, {"effect": effect})
	decision.outcome == "STEP_UP" with input as x
	decision.reason == "principal-step-up-required" with input as x
}

test_step_up_approval_must_bind_same_effect if {
	effect := object.union(base_input.effect, {"riskClass": "R4"})
	approval := {
		"verified": true,
		"principalId": base_input.principal.principalId,
		"effectId": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
		"method": "webauthn",
	}
	x := object.union_n([base_input, {"effect": effect}, {"approval": approval}])
	decision.outcome == "STEP_UP" with input as x
}

test_effect_bound_webauthn_step_up_allows_high_risk_effect if {
	effect := object.union(base_input.effect, {"riskClass": "R4"})
	approval := {
		"verified": true,
		"principalId": base_input.principal.principalId,
		"effectId": base_input.effect.effectId,
		"method": "webauthn",
	}
	x := object.union_n([base_input, {"effect": effect}, {"approval": approval}])
	decision.outcome == "ALLOW" with input as x
	decision.authorityProjection.actorId == base_input.agent.agentId with input as x
	decision.authorityProjection.authorityId == base_input.grant.grantId with input as x
	decision.authorityProjection.capability == base_input.effect.action with input as x
}
