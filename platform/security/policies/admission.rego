package ordivon.security.v2

import rego.v1

# Provider-native reports are the evidence; this decision only checks the
# exact configured product profile. It does not independently authenticate
# externally supplied status JSON or rehash referenced files.
default allow := false
default evidence_complete := false
default results_complete := false

required_providers := {"gitleaks", "semgrep", "trivy", "syft", "osv-scanner"}

evidence_formats := {
  "gitleaks": "sarif",
  "semgrep": "sarif",
  "trivy": "sarif",
  "syft": "cyclonedx-json",
  "osv-scanner": "json",
  "ordivon-runner": "json",
}

allowed_evidence_providers := required_providers | {"ordivon-runner"}

present_evidence_providers contains provider if {
  some evidence in input.evidenceRefs
  provider := evidence.provider
}

present_result_providers contains provider if {
  some result in input.providerResults
  provider := result.provider
}

missing_evidence_providers := required_providers - present_evidence_providers
missing_result_providers := required_providers - present_result_providers

valid_evidence_reference(evidence) if {
  is_object(evidence)
  evidence.provider in allowed_evidence_providers
  is_string(evidence.format)
  evidence.format == evidence_formats[evidence.provider]
  is_string(evidence.path)
  evidence.path != ""
  is_string(evidence.sha256)
  regex.match("^sha256:[0-9a-f]{64}$", evidence.sha256)
  is_number(evidence.byte_length)
  evidence.byte_length > 0
  evidence.byte_length == floor(evidence.byte_length)
}

evidence_complete if {
  is_array(input.evidenceRefs)
  count(input.evidenceRefs) >= count(required_providers)
  count(input.evidenceRefs) <= count(required_providers) + 1
  every evidence in input.evidenceRefs {
    valid_evidence_reference(evidence)
  }
  # Set cardinality equals array cardinality only for unique providers.
  count(present_evidence_providers) == count(input.evidenceRefs)
  count(missing_evidence_providers) == 0
}

# Provider-specific exit classification matches scan_product.sh's native CLI.
# Gitleaks is invoked with --exit-code 10 to distinguish leaks from its
# ambiguous default exit 1 (leaks OR execution error). OSV exit codes above 1
# are conservatively not treated as successful scans; Syft emits no findings.
scan_result_consistent(result) if {
  result.provider != "gitleaks"
  result.exitCode == 0
  result.mechanicalSuccess == true
  result.blocking == false
}

scan_result_consistent(result) if {
  result.provider != "gitleaks"
  result.exitCode == 1
  result.mechanicalSuccess == true
  result.blocking == true
}

scan_result_consistent(result) if {
  result.provider != "gitleaks"
  result.exitCode > 1
  result.mechanicalSuccess == false
  result.blocking == false
}

scan_result_consistent(result) if {
  result.provider == "gitleaks"
  result.exitCode == 0
  result.mechanicalSuccess == true
  result.blocking == false
}

scan_result_consistent(result) if {
  result.provider == "gitleaks"
  result.exitCode == 10
  result.mechanicalSuccess == true
  result.blocking == true
}

scan_result_consistent(result) if {
  result.provider == "gitleaks"
  result.exitCode != 0
  result.exitCode != 10
  result.mechanicalSuccess == false
  result.blocking == false
}

provider_result_consistent(result) if {
  result.provider != "syft"
  scan_result_consistent(result)
}

provider_result_consistent(result) if {
  result.provider == "syft"
  result.exitCode == 0
  result.mechanicalSuccess == true
  result.blocking == false
}

provider_result_consistent(result) if {
  result.provider == "syft"
  result.exitCode > 0
  result.mechanicalSuccess == false
  result.blocking == false
}

valid_provider_result(result) if {
  is_object(result)
  result.provider in required_providers
  is_number(result.exitCode)
  result.exitCode >= 0
  result.exitCode == floor(result.exitCode)
  is_boolean(result.mechanicalSuccess)
  is_boolean(result.blocking)
  provider_result_consistent(result)
}

results_complete if {
  is_array(input.providerResults)
  count(input.providerResults) == count(required_providers)
  every result in input.providerResults {
    valid_provider_result(result)
  }
  present_result_providers == required_providers
}

mechanical_error_providers contains provider if {
  some result in input.providerResults
  result.provider in required_providers
  result.mechanicalSuccess == false
  provider := result.provider
}

blocking_providers contains provider if {
  some result in input.providerResults
  result.provider in required_providers
  result.blocking == true
  provider := result.provider
}

mechanically_sound if {
  results_complete
  count(mechanical_error_providers) == 0
}

valid_revision(value) if {
  is_string(value)
  regex.match("^([0-9a-f]{40}|[0-9a-f]{64})$", value)
}

revision_current if {
  valid_revision(input.subjectRevision)
  valid_revision(input.observedSubjectRevision)
  input.observedSubjectRevision == input.subjectRevision
}

allow if {
  input.authority == "security-verification"
  evidence_complete
  mechanically_sound
  revision_current
  count(blocking_providers) == 0
}

standing := "CURRENT" if allow
else := "INCOMPLETE_EVIDENCE" if {
  not evidence_complete
}
else := "INCOMPLETE_EVIDENCE" if {
  not results_complete
}
else := "PROVIDER_ERROR" if {
  input.authority == "security-verification"
  evidence_complete
  results_complete
  count(mechanical_error_providers) > 0
}
else := "STALE_EVIDENCE" if {
  input.authority == "security-verification"
  evidence_complete
  mechanically_sound
  not revision_current
}
else := "BLOCKED" if {
  input.authority == "security-verification"
  evidence_complete
  mechanically_sound
  revision_current
  count(blocking_providers) > 0
}
else := "INCOMPLETE_EVIDENCE"

decision := {
  "allow": allow,
  "standing": standing,
  "subjectRevision": input.subjectRevision,
  "observedSubjectRevision": input.observedSubjectRevision,
  "missingEvidenceProviders": sort([p | some p in missing_evidence_providers]),
  "missingResultProviders": sort([p | some p in missing_result_providers]),
  "mechanicalErrorProviders": sort([p | some p in mechanical_error_providers]),
  "blockingProviders": sort([p | some p in blocking_providers]),
  "evidenceComplete": evidence_complete,
  "resultsComplete": results_complete,
}
