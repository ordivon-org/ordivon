package ordivon.security.v2.response_policy

import rego.v1

reference_rows := [
	{
		"exploitation": "none",
		"systemExposure": "small",
		"automatable": "no",
		"humanImpact": "low",
		"actionClass": "defer",
	},
	{
		"exploitation": "none",
		"systemExposure": "open",
		"automatable": "yes",
		"humanImpact": "very-high",
		"actionClass": "out-of-cycle",
	},
	{
		"exploitation": "public-poc",
		"systemExposure": "small",
		"automatable": "yes",
		"humanImpact": "very-high",
		"actionClass": "scheduled",
	},
	{
		"exploitation": "public-poc",
		"systemExposure": "controlled",
		"automatable": "yes",
		"humanImpact": "very-high",
		"actionClass": "out-of-cycle",
	},
	{
		"exploitation": "active",
		"systemExposure": "open",
		"automatable": "yes",
		"humanImpact": "very-high",
		"actionClass": "immediate",
	},
]

base_policy := {
	"ownerRef": "policy-owner:test-only",
	"policyId": "response-policy:test",
	"policyVersion": "1",
	"decisionTableRef": "ssvc:DT_DP:1.0.0:test-subset",
	"decisionTableRows": reference_rows,
	"unknownActionClass": null,
	"deadlineBudgets": {},
}

base_threat_applicability := {
	"schemaVersion": 1,
	"kind": "ordivon.security.threat-applicability-fusion",
	"subject": {
		"subjectRef": "subject:test",
		"snapshotDigest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
	},
	"vulnerabilityRef": "CVE-TEST-0001",
	"claim": "AFFECTED",
	"currentness": {
		"evidenceStanding": "CURRENT",
		"applicabilityStanding": "CURRENT",
	},
	"threatSignals": {
		"knownExploited": null,
		"epss": [
			{
				"evidenceRef": "epss:test",
				"probability": 0.20,
				"percentile": 0.50,
				"date": "2026-10-01",
			},
		],
	},
	"conflicts": [],
}

base_case := {
	"caseRef": "case:test",
	"threatApplicability": base_threat_applicability,
	"exploitation": "none",
	"systemExposure": "open",
	"automatable": "yes",
	"humanImpact": "very-high",
}

input_for(case_overrides, policy_overrides) := {
	"case": object.union(base_case, case_overrides),
	"policy": object.union(base_policy, policy_overrides),
}

ta(overrides) := object.union(base_threat_applicability, overrides)

test_exact_dw02_table_match_is_action_only_without_owner_deadline if {
	d := decision with input as input_for({}, {})
	d.standing == "ACTION_ONLY"
	d.actionClass == "out-of-cycle"
	d.deadlineStatus == "UNSET"
	d.subject.snapshotDigest == base_threat_applicability.subject.snapshotDigest
	d.authorityGranted == false
}

test_owner_deadline_budget_is_projected_not_invented if {
	d := decision with input as input_for({}, {
		"deadlineBudgets": {
			"out-of-cycle": {
				"budgetRef": "policy-owner:test-only:budget:out-of-cycle",
				"maxSeconds": 7200,
			},
		},
	})
	d.standing == "DECIDED"
	d.deadlineBudget.maxSeconds == 7200
	d.deadlineBudget.budgetRef == "policy-owner:test-only:budget:out-of-cycle"
}

test_policy_identity_is_required if {
	d := decision with input as input_for({}, {"ownerRef": ""})
	d.standing == "INVALID_POLICY"
}

test_exact_dw01_subject_snapshot_binding_is_required if {
	broken_subject := {
		"subjectRef": "subject:test",
		"snapshotDigest": "sha256:not-a-real-digest",
	}
	d := decision with input as input_for(
		{
			"threatApplicability": ta({"subject": broken_subject}),
		},
		{},
	)
	d.standing == "INVALID_INPUT"
	"threatApplicability.binding" in d.invalidFields
}

test_under_investigation_is_not_silently_coerced if {
	d := decision with input as input_for(
		{
			"threatApplicability": ta({"claim": "UNDER_INVESTIGATION"}),
		},
		{},
	)
	d.standing == "UNKNOWN_INPUT"
	d.actionClass == null
	"applicability" in d.unknownFields
}

test_owner_can_explicitly_route_unknown_without_granting_authority if {
	d := decision with input as input_for(
		{
			"threatApplicability": ta({"claim": "UNDER_INVESTIGATION"}),
		},
		{
			"unknownActionClass": "out-of-cycle",
		},
	)
	d.standing == "ACTION_ONLY"
	d.actionClass == "out-of-cycle"
	d.actionResolution == "owner-configured-unknown-disposition"
	d.authorityGranted == false
}

test_current_kev_signal_from_dw02_promotes_exploitation if {
	signals := object.union(base_threat_applicability.threatSignals, {"knownExploited": true})
	d := decision with input as input_for(
		{
			"threatApplicability": ta({"threatSignals": signals}),
		},
		{},
	)
	d.inputs.rawExploitation == "none"
	d.inputs.effectiveExploitation == "active"
	d.kevEffect == "promoted-exploitation-to-active"
	d.actionClass == "immediate"
}

test_absent_current_kev_signal_does_not_invent_exploitation if {
	d := decision with input as input_for({}, {})
	d.inputs.knownExploited == null
	d.inputs.effectiveExploitation == "none"
	d.kevEffect == "no-promotion"
	d.actionClass == "out-of-cycle"
}

test_exposure_change_can_change_action_class_through_table if {
	small := decision with input as input_for(
		{
			"exploitation": "public-poc",
			"systemExposure": "small",
		},
		{},
	)
	controlled := decision with input as input_for(
		{
			"exploitation": "public-poc",
			"systemExposure": "controlled",
		},
		{},
	)
	small.actionClass == "scheduled"
	controlled.actionClass == "out-of-cycle"
}

test_epss_change_alone_does_not_create_hidden_threshold if {
	low_epss := [{
		"evidenceRef": "epss:low",
		"probability": 0.01,
		"percentile": 0.10,
		"date": "2026-10-01",
	}]
	high_epss := [{
		"evidenceRef": "epss:high",
		"probability": 0.99,
		"percentile": 0.99,
		"date": "2026-10-01",
	}]
	low_signals := object.union(base_threat_applicability.threatSignals, {"epss": low_epss})
	high_signals := object.union(base_threat_applicability.threatSignals, {"epss": high_epss})
	lower := decision with input as input_for(
		{
			"threatApplicability": ta({"threatSignals": low_signals}),
		},
		{},
	)
	higher := decision with input as input_for(
		{
			"threatApplicability": ta({"threatSignals": high_signals}),
		},
		{},
	)
	lower.actionClass == "out-of-cycle"
	higher.actionClass == "out-of-cycle"
	lower.inputs.epss[0].probability == 0.01
	higher.inputs.epss[0].probability == 0.99
}

test_invalid_epss_probability_fails_closed if {
	bad_epss := [{
		"evidenceRef": "epss:bad",
		"probability": 1.5,
		"percentile": 0.99,
		"date": "2026-10-01",
	}]
	signals := object.union(base_threat_applicability.threatSignals, {"epss": bad_epss})
	d := decision with input as input_for(
		{
			"threatApplicability": ta({"threatSignals": signals}),
		},
		{},
	)
	d.standing == "INVALID_INPUT"
	"threatSignals.epss" in d.invalidFields
}

test_not_affected_has_no_remediation_action if {
	d := decision with input as input_for(
		{
			"threatApplicability": ta({"claim": "NOT_AFFECTED"}),
		},
		{},
	)
	d.standing == "NOT_APPLICABLE"
	d.actionClass == null
}

test_duplicate_matching_rows_are_ambiguous if {
	duplicated := array.concat(reference_rows, [reference_rows[1]])
	d := decision with input as input_for({}, {"decisionTableRows": duplicated})
	d.standing == "POLICY_AMBIGUOUS"
	d.matchingRowCount == 2
}
