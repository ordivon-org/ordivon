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

test_admitted_is_not_executed if {
  decision.standing == "ADMITTED_NOT_EXECUTED" with input as {
    "admission": admission,
    "executionReceipt": null,
    "observation": null,
  }
}

test_execution_receipt_is_not_world_truth if {
  decision.standing == "EXECUTED_UNVERIFIED" with input as {
    "admission": admission,
    "executionReceipt": receipt,
    "observation": null,
  }
}

test_matching_world_truth_observation_verifies_consequence if {
  decision.standing == "VERIFIED_CONSEQUENCE" with input as {
    "admission": admission,
    "executionReceipt": receipt,
    "observation": observation,
  }
}

test_executor_cannot_self_promote_receipt_to_world_truth if {
  decision.standing == "EXECUTION_RECEIPT_INVALID" with input as {
    "admission": admission,
    "executionReceipt": object.union(receipt, {"worldEffectVerified": true}),
    "observation": observation,
  }
}

test_sensor_plane_is_not_authoritative_consequence if {
  decision.standing == "OBSERVATION_NOT_AUTHORITATIVE" with input as {
    "admission": admission,
    "executionReceipt": receipt,
    "observation": object.union(observation, {"plane":"sensor"}),
  }
}

test_state_digest_mismatch_fails_closed if {
  decision.standing == "CONSEQUENCE_MISMATCH" with input as {
    "admission": admission,
    "executionReceipt": receipt,
    "observation": object.union(observation, {"payload":{"quarantined":true,"stateDigest":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}}),
  }
}

test_request_binding_mismatch_fails_closed if {
  decision.standing == "EXECUTION_BINDING_ERROR" with input as {
    "admission": admission,
    "executionReceipt": object.union(receipt, {"requestId":"range-effect-request:other"}),
    "observation": observation,
  }
}

test_rejected_admission_never_advances if {
  decision.standing == "NOT_ADMITTED" with input as {
    "admission": object.union(admission, {"admitted":false}),
    "executionReceipt": receipt,
    "observation": observation,
  }
}
