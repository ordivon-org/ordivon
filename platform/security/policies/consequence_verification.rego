package ordivon.security.v2.consequence

import rego.v1

admitted if {
  input.admission.admitted == true
}

execution_present if {
  is_object(input.executionReceipt)
}

observation_present if {
  is_object(input.observation)
}

execution_binding_ok if {
  execution_present
  input.executionReceipt.requestId == input.admission.requestId
}

execution_receipt_valid if {
  execution_binding_ok
  input.executionReceipt.effectExecuted == true
  input.executionReceipt.worldEffectVerified == false
  is_string(input.executionReceipt.stateDigestAfterWrite)
  startswith(input.executionReceipt.stateDigestAfterWrite, "sha256:")
}

observation_authoritative if {
  observation_present
  input.observation.plane == "world-truth"
  is_object(input.observation.payload)
  is_string(input.observation.payload.stateDigest)
  startswith(input.observation.payload.stateDigest, "sha256:")
}

consequence_matches if {
  execution_receipt_valid
  observation_authoritative
  input.executionReceipt.stateDigestAfterWrite == input.observation.payload.stateDigest
}

standing := "NOT_ADMITTED" if {
  not admitted
}
else := "ADMITTED_NOT_EXECUTED" if {
  admitted
  not execution_present
}
else := "EXECUTION_BINDING_ERROR" if {
  admitted
  execution_present
  not execution_binding_ok
}
else := "EXECUTION_RECEIPT_INVALID" if {
  admitted
  execution_binding_ok
  not execution_receipt_valid
}
else := "EXECUTED_UNVERIFIED" if {
  admitted
  execution_receipt_valid
  not observation_present
}
else := "OBSERVATION_NOT_AUTHORITATIVE" if {
  admitted
  execution_receipt_valid
  observation_present
  not observation_authoritative
}
else := "CONSEQUENCE_MISMATCH" if {
  admitted
  execution_receipt_valid
  observation_authoritative
  not consequence_matches
}
else := "VERIFIED_CONSEQUENCE"

execution_bound_value := true if execution_binding_ok else := false
execution_receipt_valid_value := true if execution_receipt_valid else := false
observation_authoritative_value := true if observation_authoritative else := false
consequence_matches_value := true if consequence_matches else := false

verified_consequence := input.observation.payload if {
  standing == "VERIFIED_CONSEQUENCE"
}
else := null

decision := {
  "standing": standing,
  "admissionRequestId": input.admission.requestId,
  "executionBound": execution_bound_value,
  "executionReceiptValid": execution_receipt_valid_value,
  "observationAuthoritative": observation_authoritative_value,
  "consequenceMatches": consequence_matches_value,
  "verifiedConsequence": verified_consequence,
}
