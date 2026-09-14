package ordivon.research_adopted_r1

import rego.v1

base_input := {
	"policy_id": "policy:game:synthetic-structural-evaluation:r1",
	"principal": "agent:game",
	"action": "game.claim.evaluate.synthetic",
	"resource": "game:station-zero:structural-claim:visibility",
	"consequence_class": "high",
	"epistemic_context": {"standing": "UNKNOWN"},
	"delegation": {
		"current": true,
		"decision": "ALLOW",
		"principal": "agent:game",
		"authority_ref": "provider-iam://game-agent/current"
	}
}

test_effective_adopted_policy_plus_current_delegation_allows if {
	allow with input as base_input
}

test_research_standing_alone_cannot_mint_permission if {
	not allow with input as object.union(base_input, {
		"policy_id": "policy:missing:not-adopted",
		"research_standing": "SUPPORTED"
	})
}

test_missing_current_delegation_denies_effect if {
	not allow with input as object.union(base_input, {
		"delegation": {
			"current": false,
			"decision": "ALLOW",
			"principal": "agent:game",
			"authority_ref": "provider-iam://game-agent/stale"
		}
	})
}

test_provider_delegation_deny_is_preserved if {
	not allow with input as object.union(base_input, {
		"delegation": {
			"current": true,
			"decision": "DENY",
			"principal": "agent:game",
			"authority_ref": "provider-iam://game-agent/current"
		}
	})
}

test_high_consequence_and_unknown_are_not_automatic_human_gate if {
	allow with input as base_input
}

test_action_scope_cannot_be_widened if {
	not allow with input as object.union(base_input, {"action": "game.product.commit"})
}

test_resource_scope_cannot_be_widened if {
	not allow with input as object.union(base_input, {"resource": "finance:capital:live"})
}

test_adoption_record_is_required if {
	not allow with input as base_input with data.ordivon.policy_administration.decisions as {}
}
