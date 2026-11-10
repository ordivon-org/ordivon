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
		"effectDigest": null,
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
		"effectDigest": base_input.effect.effectDigest,
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
		"effectDigest": base_input.effect.effectDigest,
		"method": "webauthn",
	}
	x := object.union_n([base_input, {"effect": effect}, {"approval": approval}])
	decision.outcome == "ALLOW" with input as x
	decision.authorityProjection.actorId == base_input.agent.agentId with input as x
	decision.authorityProjection.authorityId == base_input.grant.grantId with input as x
	decision.authorityProjection.capability == base_input.effect.action with input as x
}

test_step_up_approval_rejects_same_id_changed_effect_content if {
  effect := object.union(base_input.effect, {"riskClass": "R4"})
  approval := {
    "verified": true,
    "principalId": base_input.principal.principalId,
    "effectId": base_input.effect.effectId,
    "effectDigest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "method": "webauthn",
  }
  x := object.union_n([base_input, {"effect": effect}, {"approval": approval}])
  decision.outcome == "STEP_UP" with input as x
  decision.reason == "principal-step-up-required" with input as x
}

test_legacy_id_only_high_risk_approval_is_not_content_bound if {
  effect := object.union(base_input.effect, {"riskClass": "R4"})
  approval := {
    "verified": true,
    "principalId": base_input.principal.principalId,
    "effectId": base_input.effect.effectId,
    "method": "webauthn",
  }
  x := object.union_n([base_input, {"effect": effect}, {"approval": approval}])
  decision.outcome == "STEP_UP" with input as x
}

# Resource scope is an exact canonical path segment relation, not startswith.
# These are the actual false ALLOW inputs observed before the source fix.
test_resource_scope_rejects_adjacent_name if {
  not scope_contains("/comments", "/comments-evil")
  scope_contains("/comments", "/comments")
  scope_contains("/comments", "/comments/article-42")
}

test_resource_scope_rejects_encoded_or_dot_traversal if {
  not scope_contains("/comments/", "/comments/../account/recovery")
  not scope_contains("/comments/", "/comments/%2e%2e/account")
  not scope_contains("/comments/", "/comments/./article-42")
  not scope_contains("/comments/", "/comments//article-42")
  not scope_contains("/comments/", "/comments/..")
}

test_resource_scope_rejects_noncanonical_delimiters if {
  not scope_contains("/comments/", "/comments\\..\\secret")
  not scope_contains("/comments/", "/comments/article-42?admin=true")
  not scope_contains("/comments/", "/comments/article-42#fragment")
  not scope_contains("/comments/", "/comments/\nadmin")
}

test_resource_scope_rejects_malformed_grants if {
  not scope_contains("/comments/../", "/comments/article-42")
  not scope_contains("/comments%", "/comments/article-42")
  not scope_contains("comments/", "/comments/article-42")
  not scope_contains("/comments//", "/comments/article-42")
}

test_resource_scope_denies_real_admission_neighbor if {
  scope_grant := object.union(base_input.grant, {"resourcePrefixes": ["/comments"]})
  scope_effect := object.union(base_input.effect, {"resource": "/comments-evil"})
  candidate := object.union_n([base_input, {"grant": scope_grant}, {"effect": scope_effect}])
  decision.outcome == "DENY" with input as candidate
  decision.reason == "resource-not-granted" with input as candidate
}

test_resource_scope_denies_real_admission_traversal if {
  scope_effect := object.union(base_input.effect, {"resource": "/comments/../account/recovery"})
  candidate := object.union(base_input, {"effect": scope_effect})
  decision.outcome == "DENY" with input as candidate
  decision.reason == "resource-not-granted" with input as candidate
}

test_resource_scope_preserves_existing_canonical_grants if {
  decision.outcome == "ALLOW" with input as base_input
  scope_contains("/comments/", "/comments/article-42")
  scope_contains("/", "/comments/article-42")
  not scope_contains("/comments/", "/comments")
}
