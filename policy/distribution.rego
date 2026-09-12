package ordivon.distribution

import rego.v1

# Input to this policy is normalized by scripts/admission.py.
# Provider-specific capability facts and effect classification are supplied by the
# bound provider observation; exact-effect authority is derived from a separately
# bound authority object. The policy contains no provider catalog or OAuth matrix.

default decision := {
  "action": "deny",
  "reason": "invalid-or-incomplete-normalized-input",
  "externalEffectPerformed": false,
}

effectful if {
  input.provider.effectMode == "write"
}

effectful if {
  input.provider.effectMode == "destructive"
}

artifact_release_eligible if {
  input.intent.artifact == null
}

artifact_release_eligible if {
  input.intent.artifact.releaseReady == true
}

decision := {
  "action": "capability_unavailable",
  "reason": "provider-does-not-support-effect",
  "externalEffectPerformed": false,
} if {
  input.provider.effectSupported == false
}

decision := {
  "action": "provider_access_required",
  "reason": "provider-reported-missing-requirements",
  "requirements": input.provider.missingProviderRequirements,
  "externalEffectPerformed": false,
} if {
  input.provider.effectSupported == true
  count(input.provider.missingProviderRequirements) > 0
}

decision := {
  "action": "user_action_required",
  "reason": "provider-reported-missing-per-effect-interaction",
  "requirements": input.provider.missingInteractions,
  "externalEffectPerformed": false,
} if {
  input.provider.effectSupported == true
  count(input.provider.missingProviderRequirements) == 0
  count(input.provider.missingInteractions) > 0
}

decision := {
  "action": "artifact_release_not_ready",
  "reason": "artifact-backed-effect-requires-release-ready-artifact",
  "externalEffectPerformed": false,
} if {
  input.provider.effectSupported == true
  count(input.provider.missingProviderRequirements) == 0
  count(input.provider.missingInteractions) == 0
  effectful
  input.intent.artifact != null
  input.intent.artifact.releaseReady != true
}

decision := {
  "action": "user_action_required",
  "reason": "bound-exact-effect-authority-required",
  "externalEffectPerformed": false,
} if {
  input.provider.effectSupported == true
  count(input.provider.missingProviderRequirements) == 0
  count(input.provider.missingInteractions) == 0
  effectful
  artifact_release_eligible
  input.authority.granted != true
}

decision := {
  "action": "user_action_required",
  "reason": "provider-requires-human-final-action",
  "externalEffectPerformed": false,
} if {
  input.provider.effectSupported == true
  count(input.provider.missingProviderRequirements) == 0
  count(input.provider.missingInteractions) == 0
  input.provider.executionMode == "human_handoff"
  not effectful
}

decision := {
  "action": "user_action_required",
  "reason": "provider-requires-human-final-action",
  "externalEffectPerformed": false,
} if {
  input.provider.effectSupported == true
  count(input.provider.missingProviderRequirements) == 0
  count(input.provider.missingInteractions) == 0
  input.provider.executionMode == "human_handoff"
  effectful
  artifact_release_eligible
  input.authority.granted == true
}

decision := {
  "action": "preflight_ready",
  "reason": "bound-external-substrate-preflight-satisfied",
  "externalEffectPerformed": false,
} if {
  input.provider.effectSupported == true
  count(input.provider.missingProviderRequirements) == 0
  count(input.provider.missingInteractions) == 0
  input.provider.executionMode != "human_handoff"
  not effectful
}

decision := {
  "action": "preflight_ready",
  "reason": "bound-external-substrate-preflight-satisfied",
  "externalEffectPerformed": false,
} if {
  input.provider.effectSupported == true
  count(input.provider.missingProviderRequirements) == 0
  count(input.provider.missingInteractions) == 0
  input.provider.executionMode != "human_handoff"
  effectful
  artifact_release_eligible
  input.authority.granted == true
}
