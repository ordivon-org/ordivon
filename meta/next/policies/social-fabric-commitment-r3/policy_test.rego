package ordivon.social_commitment_r3

import rego.v1

base_input := {
	"policy": {
		"requiredSupportRoles": ["operations", "storage"],
		"requiredCandidateEvidencePrefixes": ["job:"],
		"blockingDamageReasonCodes": ["FILESYSTEM_UNSAFE"],
		"blockingModulatoryDimensions": ["storage-critical"],
	},
	"candidate": {
		"standing": "eligible_shadow",
		"supportRoles": ["operations", "storage"],
		"candidateEvidenceRefs": ["job:123"],
		"activeDamageReasonCodes": [],
		"activeModulatoryDimensions": [],
	},
}

test_explicit_requirements_satisfy_shadow_policy if {
	decision.satisfied with input as base_input
}

test_missing_required_role_is_not_satisfied if {
	not decision.satisfied with input as object.union(base_input, {
		"candidate": object.union(base_input.candidate, {"supportRoles": ["operations"]}),
	})
}

test_inhibited_candidate_is_not_satisfied if {
	not decision.satisfied with input as object.union(base_input, {
		"candidate": object.union(base_input.candidate, {"standing": "inhibited_shadow"}),
	})
}

test_blocking_damage_is_not_satisfied if {
	not decision.satisfied with input as object.union(base_input, {
		"candidate": object.union(base_input.candidate, {
			"activeDamageReasonCodes": ["FILESYSTEM_UNSAFE"],
		}),
	})
}

test_blocking_modulatory_signal_is_not_satisfied if {
	not decision.satisfied with input as object.union(base_input, {
		"candidate": object.union(base_input.candidate, {
			"activeModulatoryDimensions": ["storage-critical"],
		}),
	})
}
