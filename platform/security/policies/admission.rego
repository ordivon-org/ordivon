package ordivon.security.v2

import rego.v1

default allow := false

required_providers := {"gitleaks", "semgrep", "trivy", "syft", "osv-scanner"}

present_evidence_providers contains p if {
  some evidence in input.evidenceRefs
  p := evidence.provider
}

present_result_providers contains p if {
  some result in input.providerResults
  p := result.provider
}

missing_evidence_providers := required_providers - present_evidence_providers
missing_result_providers := required_providers - present_result_providers

mechanical_error_providers contains p if {
  some result in input.providerResults
  result.provider in required_providers
  result.mechanicalSuccess == false
  p := result.provider
}

blocking_providers contains p if {
  some result in input.providerResults
  result.provider in required_providers
  result.blocking == true
  p := result.provider
}

evidence_complete if {
  count(missing_evidence_providers) == 0
  every evidence in input.evidenceRefs {
    startswith(evidence.sha256, "sha256:")
    evidence.byte_length > 0
  }
}

results_complete if {
  count(missing_result_providers) == 0
}

mechanically_sound if {
  results_complete
  count(mechanical_error_providers) == 0
}

allow if {
  input.authority == "security-verification"
  evidence_complete
  mechanically_sound
  count(blocking_providers) == 0
}

standing := "CURRENT" if allow
else := "BLOCKED" if {
  input.authority == "security-verification"
  evidence_complete
  mechanically_sound
  count(blocking_providers) > 0
}
else := "PROVIDER_ERROR" if {
  input.authority == "security-verification"
  evidence_complete
  results_complete
  count(mechanical_error_providers) > 0
}
else := "INCOMPLETE_EVIDENCE"

decision := {
  "allow": allow,
  "standing": standing,
  "missingEvidenceProviders": sort([p | some p in missing_evidence_providers]),
  "missingResultProviders": sort([p | some p in missing_result_providers]),
  "mechanicalErrorProviders": sort([p | some p in mechanical_error_providers]),
  "blockingProviders": sort([p | some p in blocking_providers]),
}
