package ordivon.distribution.reconciliation_test

import rego.v1

# Exhaust the exact finite enum universe declared by the v2 Reconciliation
# input schema. This is a policy-model proof, not provider-side effect proof.
dispatch_states := data.properties.dispatchStanding.enum
provider_readbacks := data.properties.providerReadback.enum
retry_proofs := data.properties.retryProof.enum

# The sole three combinations that may safely retry a possibly emitted effect.
safe_retry_states := {
	["ambiguous", "unknown", "provider_idempotency"],
	["ambiguous", "absent", "provider_idempotency"],
	["ambiguous", "absent", "authoritative_absence"],
}

# Fail closed if the actual provider input-schema enum is missing or narrowed
# so far that the proof could pass vacuously.
test_exact_owner_schema_domains_exist if {
	count(dispatch_states) > 0
	count(provider_readbacks) > 0
	count(retry_proofs) > 0
	"ambiguous" in dispatch_states
	"unknown" in provider_readbacks
	"present" in provider_readbacks
	"authoritative_absence" in retry_proofs
}

test_retry_permission_iff_exact_provider_proof if {
	every dispatch in dispatch_states {
		every readback in provider_readbacks {
			every proof in retry_proofs {
				input_case := {
					"dispatchStanding": dispatch,
					"providerReadback": readback,
					"retryProof": proof,
				}
				result := data.ordivon.distribution.reconciliation.decision with input as input_case
				expected_retry := [dispatch, readback, proof] in safe_retry_states
				result.retryPermitted == expected_retry
			}
		}
	}
}

test_ambiguous_effect_always_has_explicit_recovery_disposition if {
	every readback in provider_readbacks {
		every proof in retry_proofs {
			input_case := {
				"dispatchStanding": "ambiguous",
				"providerReadback": readback,
				"retryProof": proof,
			}
			result := data.ordivon.distribution.reconciliation.decision with input as input_case
			result.action != "hold"
		}
	}
}

test_effect_confirmed_iff_positive_provider_readback if {
	every dispatch in dispatch_states {
		every readback in provider_readbacks {
			every proof in retry_proofs {
				input_case := {
					"dispatchStanding": dispatch,
					"providerReadback": readback,
					"retryProof": proof,
				}
				result := data.ordivon.distribution.reconciliation.decision with input as input_case
				is_confirmed := result.action == "effect_confirmed"
				has_readback := readback == "present"
				is_confirmed == has_readback
			}
		}
	}
}
