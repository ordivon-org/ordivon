package ordivon.security.v2

import rego.v1

default allow := false

required_providers := {"gitleaks", "semgrep", "trivy", "syft", "osv-scanner"}

present_providers contains p if {
  some evidence in input.evidenceRefs
  p := evidence.provider
}

missing_providers := required_providers - present_providers

allow if {
  input.authority == "security-verification"
  count(missing_providers) == 0
  every evidence in input.evidenceRefs {
    startswith(evidence.sha256, "sha256:")
    evidence.byte_length > 0
  }
}

decision := {
  "allow": allow,
  "standing": standing,
  "missingProviders": sort([p | some p in missing_providers]),
}

standing := "CURRENT" if allow
standing := "INCOMPLETE_EVIDENCE" if not allow
