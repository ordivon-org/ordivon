package ordivon.security.v2

import rego.v1

complete_evidence := [
  {"provider":"gitleaks","sha256":"sha256:a","byte_length":1},
  {"provider":"semgrep","sha256":"sha256:b","byte_length":1},
  {"provider":"trivy","sha256":"sha256:c","byte_length":1},
  {"provider":"syft","sha256":"sha256:d","byte_length":1},
  {"provider":"osv-scanner","sha256":"sha256:e","byte_length":1},
]

complete_results := [
  {"provider":"gitleaks","mechanicalSuccess":true,"blocking":false},
  {"provider":"semgrep","mechanicalSuccess":true,"blocking":false},
  {"provider":"trivy","mechanicalSuccess":true,"blocking":false},
  {"provider":"syft","mechanicalSuccess":true,"blocking":false},
  {"provider":"osv-scanner","mechanicalSuccess":true,"blocking":false},
]

base_input := {
  "authority":"security-verification",
  "subjectRevision":"rev:a",
  "observedSubjectRevision":"rev:a",
  "evidenceRefs":complete_evidence,
  "providerResults":complete_results,
}

test_rejects_missing_provider if {
  not allow with input as {
    "authority":"security-verification",
    "subjectRevision":"rev:a",
    "observedSubjectRevision":"rev:a",
    "evidenceRefs":[{"provider":"gitleaks","sha256":"sha256:x","byte_length":1}],
    "providerResults":[],
  }
}

test_accepts_complete_clean_provider_set if {
  allow with input as base_input
}

test_blocks_provider_finding_without_calling_it_execution_failure if {
  decision.standing == "BLOCKED" with input as object.union(base_input, {
    "providerResults":array.concat(array.slice(complete_results,0,4), [{"provider":"osv-scanner","mechanicalSuccess":true,"blocking":true}]),
  })
}

test_distinguishes_provider_error if {
  decision.standing == "PROVIDER_ERROR" with input as object.union(base_input, {
    "providerResults":array.concat(array.slice(complete_results,0,4), [{"provider":"osv-scanner","mechanicalSuccess":false,"blocking":false}]),
  })
}

test_rejects_stale_provider_evidence_before_using_findings if {
  decision.standing == "STALE_EVIDENCE" with input as object.union(base_input, {
    "observedSubjectRevision":"rev:older",
    "providerResults":array.concat(array.slice(complete_results,0,4), [{"provider":"osv-scanner","mechanicalSuccess":true,"blocking":true}]),
  })
}
