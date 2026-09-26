package ordivon.social_commitment_r3

import rego.v1

# OPA evaluates explicit commitment requirements only. This package does not
# authorize execution, rank candidates, or interpret support count as a vote.

candidate_evidence_has_prefix(prefix) if {
	some ref in input.candidate.candidateEvidenceRefs
	startswith(ref, prefix)
}

unmet contains {"code": "CANDIDATE_NOT_ELIGIBLE_SHADOW", "value": input.candidate.standing} if {
	input.candidate.standing != "eligible_shadow"
}

unmet contains {"code": "MISSING_SUPPORT_ROLE", "value": role} if {
	some role in input.policy.requiredSupportRoles
	not role in input.candidate.supportRoles
}

unmet contains {"code": "MISSING_CANDIDATE_EVIDENCE_PREFIX", "value": prefix} if {
	some prefix in input.policy.requiredCandidateEvidencePrefixes
	not candidate_evidence_has_prefix(prefix)
}

unmet contains {"code": "BLOCKED_DAMAGE_REASON", "value": reason} if {
	some reason in input.candidate.activeDamageReasonCodes
	reason in input.policy.blockingDamageReasonCodes
}

unmet contains {"code": "BLOCKED_MODULATORY_DIMENSION", "value": dimension} if {
	some dimension in input.candidate.activeModulatoryDimensions
	dimension in input.policy.blockingModulatoryDimensions
}

decision := {
	"satisfied": count(unmet) == 0,
	"unmet": sort(unmet),
	"effectAuthorityGranted": false,
	"externalEffectPerformed": false,
}
