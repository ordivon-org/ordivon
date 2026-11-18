package ordivon.security.v2.consequence

import rego.v1

admission := {
  "requestId": "range-effect-request:test",
  "admitted": true,
}

receipt := {
  "requestId": "range-effect-request:test",
  "effectExecuted": true,
  "worldEffectVerified": false,
  "stateDigestAfterWrite": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
}

observation := {
  "plane": "world-truth",
  "payload": {
    "quarantined": true,
    "stateDigest": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  },
}

case_input(adm, rec, obs) := {"admission": adm, "executionReceipt": rec, "observation": obs}

test_admitted_is_not_executed if {
  decision.standing == "ADMITTED_NOT_EXECUTED" with input as case_input(admission, null, null)
}

test_execution_receipt_is_not_world_truth if {
  decision.standing == "EXECUTED_UNVERIFIED" with input as case_input(admission, receipt, null)
}

test_matching_untrusted_observation_is_not_verified_consequence if {
  result := decision with input as case_input(admission, receipt, observation)
  result.standing == "CONTENT_MATCHED_UNVERIFIED"
  result.consequenceMatches == true
  result.observationContentQualified == true
  result.observationAuthoritative == false
  result.verifiedConsequence == null
}

test_untrusted_claims_cannot_upgrade_consequence if {
  claimed := object.union(observation, {
    "verified": true,
    "issuer": "trusted",
    "signed": true,
  })
  result := decision with input as case_input(admission, receipt, claimed)
  result.standing == "CONTENT_MATCHED_UNVERIFIED"
  result.verifiedConsequence == null
}

test_executor_cannot_self_promote_receipt_to_world_truth if {
  decision.standing == "EXECUTION_RECEIPT_INVALID" with input as case_input(
    admission, object.union(receipt, {"worldEffectVerified": true}), observation,
  )
}

test_sensor_plane_is_not_authoritative_consequence if {
  decision.standing == "OBSERVATION_NOT_AUTHORITATIVE" with input as case_input(
    admission, receipt, object.union(observation, {"plane": "sensor"}),
  )
}

test_malformed_observation_digest_not_accepted if {
  malformed := object.union(observation, {"payload": {
    "stateDigest": "sha256:incomplete",
  }})
  result := decision with input as case_input(admission, receipt, malformed)
  result.standing == "OBSERVATION_NOT_AUTHORITATIVE"
  result.verifiedConsequence == null
}

test_malformed_executor_digest_rejected if {
  malformed := object.union(receipt, {"stateDigestAfterWrite": "sha256:incomplete"})
  decision.standing == "EXECUTION_RECEIPT_INVALID" with input as case_input(
    admission, malformed, observation,
  )
}

test_state_digest_mismatch_fails_closed if {
  changed := object.union(observation, {"payload": {
    "quarantined": true,
    "stateDigest": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  }})
  decision.standing == "CONSEQUENCE_MISMATCH" with input as case_input(admission, receipt, changed)
}

test_request_binding_mismatch_fails_closed if {
  decision.standing == "EXECUTION_BINDING_ERROR" with input as case_input(
    admission, object.union(receipt, {"requestId": "range-effect-request:other"}), observation,
  )
}

test_rejected_admission_never_advances if {
  decision.standing == "NOT_ADMITTED" with input as case_input(
    object.union(admission, {"admitted": false}), receipt, observation,
  )
}
