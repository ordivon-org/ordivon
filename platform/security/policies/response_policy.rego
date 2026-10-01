package ordivon.security.v2.response_policy

import rego.v1

valid_action_classes := {"defer", "scheduled", "out-of-cycle", "immediate"}
valid_applicability_claims := {"AFFECTED", "NOT_AFFECTED", "UNDER_INVESTIGATION"}
valid_exploitation := {"none", "public-poc", "active", "UNKNOWN"}
valid_exposure := {"small", "controlled", "open", "UNKNOWN"}
valid_automatable := {"no", "yes", "UNKNOWN"}
valid_human_impact := {"low", "medium", "high", "very-high", "UNKNOWN"}

case_obj := object.get(input, "case", {})
policy_obj := object.get(input, "policy", {})
threat_applicability := object.get(case_obj, "threatApplicability", {})
subject_obj := object.get(threat_applicability, "subject", {})
threat_signals := object.get(threat_applicability, "threatSignals", {})

applicability_claim := object.get(threat_applicability, "claim", "UNKNOWN")
raw_exploitation := object.get(case_obj, "exploitation", "UNKNOWN")
system_exposure := object.get(case_obj, "systemExposure", "UNKNOWN")
automatable := object.get(case_obj, "automatable", "UNKNOWN")
human_impact := object.get(case_obj, "humanImpact", "UNKNOWN")
known_exploited := object.get(threat_signals, "knownExploited", null)
epss_signals := object.get(threat_signals, "epss", [])

applicability := "affected" if {
	applicability_claim == "AFFECTED"
}

else := "not-affected" if {
	applicability_claim == "NOT_AFFECTED"
}

else := "under-investigation" if {
	applicability_claim == "UNDER_INVESTIGATION"
}

else := "UNKNOWN"

effective_exploitation := "active" if {
	known_exploited == true
}

else := raw_exploitation

nonempty_string(value) if {
	is_string(value)
	value != ""
}

sha256_digest(value) if {
	is_string(value)
	regex.match("^sha256:[0-9a-f]{64}$", value)
}

threat_applicability_identity_valid if {
	object.get(threat_applicability, "kind", null) == "ordivon.security.threat-applicability-fusion"
	nonempty_string(object.get(subject_obj, "subjectRef", null))
	sha256_digest(object.get(subject_obj, "snapshotDigest", null))
	nonempty_string(object.get(threat_applicability, "vulnerabilityRef", null))
}

epss_signals_valid if {
	is_array(epss_signals)
	every row in epss_signals {
		is_object(row)
		nonempty_string(object.get(row, "evidenceRef", null))
		is_number(object.get(row, "probability", null))
		object.get(row, "probability", -1) >= 0
		object.get(row, "probability", 2) <= 1
		is_number(object.get(row, "percentile", null))
		object.get(row, "percentile", -1) >= 0
		object.get(row, "percentile", 2) <= 1
		is_string(object.get(row, "date", null))
		regex.match("^\\d{4}-\\d{2}-\\d{2}$", object.get(row, "date", ""))
	}
}

policy_identity_valid if {
	nonempty_string(object.get(policy_obj, "ownerRef", null))
	nonempty_string(object.get(policy_obj, "policyId", null))
	nonempty_string(object.get(policy_obj, "policyVersion", null))
	nonempty_string(object.get(policy_obj, "decisionTableRef", null))
}

decision_table_valid if {
	rows := object.get(policy_obj, "decisionTableRows", [])
	is_array(rows)
	count(rows) > 0
	every row in rows {
		row.exploitation in {"none", "public-poc", "active"}
		row.systemExposure in {"small", "controlled", "open"}
		row.automatable in {"no", "yes"}
		row.humanImpact in {"low", "medium", "high", "very-high"}
		row.actionClass in valid_action_classes
	}
}

unknown_disposition_valid if {
	value := object.get(policy_obj, "unknownActionClass", null)
	value == null
}

else if {
	object.get(policy_obj, "unknownActionClass", null) in valid_action_classes
}

deadline_budgets := object.get(policy_obj, "deadlineBudgets", {})

deadline_budgets_valid if {
	is_object(deadline_budgets)
	every action_class, budget in deadline_budgets {
		action_class in valid_action_classes
		is_object(budget)
		nonempty_string(object.get(budget, "budgetRef", null))
		is_number(object.get(budget, "maxSeconds", null))
		object.get(budget, "maxSeconds", 0) > 0
	}
}

policy_valid if {
	policy_identity_valid
	decision_table_valid
	unknown_disposition_valid
	deadline_budgets_valid
}

invalid_fields contains "threatApplicability.binding" if {
	not threat_applicability_identity_valid
}

invalid_fields contains "threatApplicability.claim" if {
	not applicability_claim in valid_applicability_claims
}

invalid_fields contains "exploitation" if {
	not raw_exploitation in valid_exploitation
}

invalid_fields contains "systemExposure" if {
	not system_exposure in valid_exposure
}

invalid_fields contains "automatable" if {
	not automatable in valid_automatable
}

invalid_fields contains "humanImpact" if {
	not human_impact in valid_human_impact
}

invalid_fields contains "threatSignals.knownExploited" if {
	known_exploited != null
	known_exploited != true
}

invalid_fields contains "threatSignals.epss" if {
	not epss_signals_valid
}

unknown_fields contains "applicability" if {
	applicability == "under-investigation"
}

unknown_fields contains "exploitation" if {
	effective_exploitation == "UNKNOWN"
}

unknown_fields contains "systemExposure" if {
	system_exposure == "UNKNOWN"
}

unknown_fields contains "automatable" if {
	automatable == "UNKNOWN"
}

unknown_fields contains "humanImpact" if {
	human_impact == "UNKNOWN"
}

matching_rows := [row |
	some row in object.get(policy_obj, "decisionTableRows", [])
	row.exploitation == effective_exploitation
	row.systemExposure == system_exposure
	row.automatable == automatable
	row.humanImpact == human_impact
]

matching_row_count := count(matching_rows)

base_action_class := matching_rows[0].actionClass if {
	matching_row_count == 1
}

unknown_action_class := object.get(policy_obj, "unknownActionClass", null)

selected_action_class := unknown_action_class if {
	applicability != "not-affected"
	count(invalid_fields) == 0
	count(unknown_fields) > 0
	unknown_action_class in valid_action_classes
}

else := base_action_class if {
	applicability == "affected"
	count(invalid_fields) == 0
	count(unknown_fields) == 0
	matching_row_count == 1
}

selected_action_exists if {
	selected_action_class in valid_action_classes
}

deadline_budget := object.get(deadline_budgets, selected_action_class, null) if selected_action_exists

else := null

deadline_budget_valid if {
	is_object(deadline_budget)
	nonempty_string(object.get(deadline_budget, "budgetRef", null))
	is_number(object.get(deadline_budget, "maxSeconds", null))
	object.get(deadline_budget, "maxSeconds", 0) > 0
}

standing := "INVALID_POLICY" if {
	not policy_valid
}

else := "INVALID_INPUT" if {
	count(invalid_fields) > 0
}

else := "NOT_APPLICABLE" if {
	applicability == "not-affected"
}

else := "UNKNOWN_INPUT" if {
	count(unknown_fields) > 0
	not selected_action_exists
}

else := "POLICY_AMBIGUOUS" if {
	applicability == "affected"
	count(unknown_fields) == 0
	matching_row_count > 1
}

else := "POLICY_NO_MATCH" if {
	applicability == "affected"
	count(unknown_fields) == 0
	matching_row_count == 0
}

else := "DECIDED" if {
	selected_action_exists
	deadline_budget_valid
}

else := "ACTION_ONLY"

action_resolution := "owner-configured-unknown-disposition" if {
	selected_action_exists
	count(unknown_fields) > 0
}

else := "decision-table-exact-match" if {
	selected_action_exists
	count(unknown_fields) == 0
}

else := null

kev_effect := "promoted-exploitation-to-active" if {
	known_exploited == true
	raw_exploitation != "active"
}

else := "no-promotion"

deadline_status := "CONFIGURED" if deadline_budget_valid

else := "UNSET"

action_class_value := selected_action_class if selected_action_exists

else := null

deadline_budget_value := deadline_budget if deadline_budget_valid

else := null

decision := {
	"schemaVersion": 1,
	"kind": "ordivon.security.response-policy-decision",
	"caseRef": object.get(case_obj, "caseRef", null),
	"subject": {
		"subjectRef": object.get(subject_obj, "subjectRef", null),
		"snapshotDigest": object.get(subject_obj, "snapshotDigest", null),
	},
	"vulnerabilityRef": object.get(threat_applicability, "vulnerabilityRef", null),
	"policyOwnerRef": object.get(policy_obj, "ownerRef", null),
	"policyId": object.get(policy_obj, "policyId", null),
	"policyVersion": object.get(policy_obj, "policyVersion", null),
	"decisionTableRef": object.get(policy_obj, "decisionTableRef", null),
	"standing": standing,
	"actionClass": action_class_value,
	"actionResolution": action_resolution,
	"deadlineStatus": deadline_status,
	"deadlineBudget": deadline_budget_value,
	"authorityGranted": false,
	"inputs": {
		"applicabilityClaim": applicability_claim,
		"applicability": applicability,
		"rawExploitation": raw_exploitation,
		"effectiveExploitation": effective_exploitation,
		"systemExposure": system_exposure,
		"automatable": automatable,
		"humanImpact": human_impact,
		"knownExploited": known_exploited,
		"epss": epss_signals,
		"applicabilityCurrentness": object.get(
			object.get(threat_applicability, "currentness", {}),
			"applicabilityStanding",
			"UNKNOWN",
		),
	},
	"kevEffect": kev_effect,
	"unknownFields": sort([field | some field in unknown_fields]),
	"invalidFields": sort([field | some field in invalid_fields]),
	"matchingRowCount": matching_row_count,
}
