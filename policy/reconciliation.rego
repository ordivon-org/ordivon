package ordivon.distribution.reconciliation

import rego.v1

# Input is normalized evidence. This policy never infers provider idempotency or
# authoritative absence itself; those facts must come from a bound provider adapter.
default decision := {
  "action": "hold",
  "retryPermitted": false,
  "reason": "insufficient-reconciliation-evidence",
}

decision := {
  "action": "effect_confirmed",
  "retryPermitted": false,
  "reason": "provider-native-readback-present",
} if {
  input.providerReadback == "present"
}

decision := {
  "action": "no_effect_confirmed",
  "retryPermitted": false,
  "reason": "provider-definitely-rejected-before-effect",
} if {
  input.dispatchStanding == "definitely_rejected"
  input.providerReadback != "present"
}

decision := {
  "action": "reconcile_required",
  "retryPermitted": false,
  "reason": "ambiguous-effect-without-safe-retry-proof",
} if {
  input.dispatchStanding == "ambiguous"
  input.providerReadback != "present"
  input.retryProof == "none"
}

decision := {
  "action": "retry_permitted",
  "retryPermitted": true,
  "reason": "bound-provider-idempotency-proof",
} if {
  input.dispatchStanding == "ambiguous"
  input.providerReadback != "present"
  input.retryProof == "provider_idempotency"
}

decision := {
  "action": "retry_permitted",
  "retryPermitted": true,
  "reason": "bound-authoritative-absence-proof",
} if {
  input.dispatchStanding == "ambiguous"
  input.providerReadback == "absent"
  input.retryProof == "authoritative_absence"
}

decision := {
  "action": "reconcile_required",
  "retryPermitted": false,
  "reason": "provider-acknowledged-but-readback-not-yet-present",
} if {
  input.dispatchStanding == "provider_acknowledged"
  input.providerReadback == "unknown"
}

decision := {
  "action": "manual_review_required",
  "retryPermitted": false,
  "reason": "provider-acknowledged-but-authoritative-readback-absent",
} if {
  input.dispatchStanding == "provider_acknowledged"
  input.providerReadback == "absent"
}
