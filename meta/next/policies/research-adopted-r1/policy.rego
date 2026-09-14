package ordivon.research_adopted_r1

import rego.v1

# This package is a reference composition over OPA, not a new Ordivon policy language.
# Research evidence never appears as direct authorization input. A separate adopted
# decision must exist in PAP data before this PDP can allow an effect.
default allow := false

allow if {
	policy := data.ordivon.policy_administration.policies[input.policy_id]
	policy.status == "effective"
	policy.current == true
	policy.revoked == false

	decision := data.ordivon.policy_administration.decisions[policy.decision_ref]
	decision.status == "adopted"
	decision.policy_id == input.policy_id
	count(decision.source_research_refs) > 0

	input.delegation.current == true
	input.delegation.decision == "ALLOW"
	input.delegation.principal == input.principal

	some permission in policy.permissions
	permission.action == input.action
	startswith(input.resource, permission.resource_prefix)
}
