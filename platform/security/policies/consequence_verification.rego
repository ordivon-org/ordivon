package ordivon.security.v2.consequence

import rego.v1

# This is a content-consistency policy, NOT an observation-authentication
# service. A caller-supplied plane == "world-truth" is a claim, not proof that
# an independent observer signed or supplied these bytes. Until a trusted
# observation-issuer consumer is wired, no input can yield VERIFIED_CONSEQUENCE.
admitted if {
  input.admission.admitted == true
}

execution_present if {
  is_object(input.executionReceipt)
}

observation_present if {
  is_object(input.observation)
}

valid_sha256(value) if {
  is_string(value)
  regex.match("^sha256:[0-9a-f]{64}$", value)
}

execution_binding_ok if {
  execution_present
  input.executionReceipt.requestId == input.admission.requestId
}

execution_receipt_valid if {
  execution_binding_ok
  input.executionReceipt.effectExecuted == true
  input.executionReceipt.worldEffectVerified == false
  valid_sha256(input.executionReceipt.stateDigestAfterWrite)
}

# "world-truth" is a historical format coordinate; it remains UNTRUSTED.
# Checking the format and digest cannot authenticate the source.
observation_content_qualified if {
  observation_present
  input.observation.plane == "world-truth"
  is_object(input.observation.payload)
  valid_sha256(input.observation.payload.stateDigest)
}

consequence_matches if {
  execution_receipt_valid
  observation_content_qualified
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
  not observation_content_qualified
}
else := "CONSEQUENCE_MISMATCH" if {
  admitted
  execution_receipt_valid
  observation_content_qualified
  not consequence_matches
}
else := "CONTENT_MATCHED_UNVERIFIED"

execution_bound_value := true if execution_binding_ok else := false
execution_receipt_valid_value := true if execution_receipt_valid else := false
observation_content_qualified_value := true if observation_content_qualified else := false
consequence_matches_value := true if consequence_matches else := false

decision := {
  "standing": standing,
  "admissionRequestId": input.admission.requestId,
  "executionBound": execution_bound_value,
  "executionReceiptValid": execution_receipt_valid_value,
  "observationContentQualified": observation_content_qualified_value,
  "observationAuthoritative": false,
  "consequenceMatches": consequence_matches_value,
  "verifiedConsequence": null,
}
