package ordivon.security.v2

import rego.v1

complete_evidence := [
  {"provider":"gitleaks","format":"sarif","path":"gitleaks.sarif","sha256":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","byte_length":1},
  {"provider":"semgrep","format":"sarif","path":"semgrep.sarif","sha256":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","byte_length":1},
  {"provider":"trivy","format":"sarif","path":"trivy.sarif","sha256":"sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","byte_length":1},
  {"provider":"syft","format":"cyclonedx-json","path":"sbom.cdx.json","sha256":"sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","byte_length":1},
  {"provider":"osv-scanner","format":"json","path":"osv.json","sha256":"sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee","byte_length":1},
]

complete_results := [
  {"provider":"gitleaks","exitCode":0,"mechanicalSuccess":true,"blocking":false},
  {"provider":"semgrep","exitCode":0,"mechanicalSuccess":true,"blocking":false},
  {"provider":"trivy","exitCode":0,"mechanicalSuccess":true,"blocking":false},
  {"provider":"syft","exitCode":0,"mechanicalSuccess":true,"blocking":false},
  {"provider":"osv-scanner","exitCode":0,"mechanicalSuccess":true,"blocking":false},
]

base_input := {
  "authority": "security-verification",
  "subjectRevision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "observedSubjectRevision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "evidenceRefs": complete_evidence,
  "providerResults": complete_results,
}

test_accepts_complete_clean_provider_set if {
  decision.standing == "CURRENT" with input as base_input
  decision.allow == true with input as base_input
}

test_accepts_runner_receipt_as_optional_sixth_reference if {
  runner := {"provider": "ordivon-runner", "format": "json", "path": "provider-status.json", "sha256": "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "byte_length": 8}
  decision.standing == "CURRENT" with input as object.union(base_input, {
    "evidenceRefs": array.concat(complete_evidence, [runner]),
  })
}

test_rejects_missing_provider if {
  result := decision with input as object.union(base_input, {
    "evidenceRefs": array.slice(complete_evidence, 0, 4),
    "providerResults": array.slice(complete_results, 0, 4),
  })
  not result.allow
  result.standing == "INCOMPLETE_EVIDENCE"
}

test_rejects_missing_mechanical_success_not_clean if {
  malformed := {"provider":"gitleaks","exitCode":0,"blocking":false}
  decision.standing == "INCOMPLETE_EVIDENCE" with input as object.union(base_input, {
    "providerResults": array.concat([malformed], array.slice(complete_results, 1, 5)),
  })
}

test_rejects_missing_blocking_status_not_clean if {
  malformed := {"provider":"gitleaks","exitCode":0,"mechanicalSuccess":true}
  not allow with input as object.union(base_input, {
    "providerResults": array.concat([malformed], array.slice(complete_results, 1, 5)),
  })
}

test_rejects_missing_exit_code if {
  malformed := {"provider":"gitleaks","mechanicalSuccess":true,"blocking":false}
  not allow with input as object.union(base_input, {
    "providerResults": array.concat([malformed], array.slice(complete_results, 1, 5)),
  })
}

test_rejects_string_instead_of_boolean if {
  malformed := {"provider":"gitleaks","exitCode":0,"mechanicalSuccess":"true","blocking":false}
  not allow with input as object.union(base_input, {
    "providerResults": array.concat([malformed], array.slice(complete_results, 1, 5)),
  })
}

test_rejects_inconsistent_exit_code_status if {
  malformed := {"provider":"gitleaks","exitCode":2,"mechanicalSuccess":true,"blocking":false}
  not allow with input as object.union(base_input, {
    "providerResults": array.concat([malformed], array.slice(complete_results, 1, 5)),
  })
}

test_rejects_duplicate_provider_result if {
  not allow with input as object.union(base_input, {
    "providerResults": array.concat(complete_results, [complete_results[0]]),
  })
}

test_rejects_duplicate_evidence_provider if {
  not allow with input as object.union(base_input, {
    "evidenceRefs": array.concat(complete_evidence, [complete_evidence[0]]),
  })
}

test_rejects_unknown_provider_result if {
  injected := {"provider":"unknown-provider","exitCode":0,"mechanicalSuccess":true,"blocking":false}
  not allow with input as object.union(base_input, {
    "providerResults": array.concat(array.slice(complete_results, 0, 4), [injected]),
  })
}

test_rejects_fake_short_digest if {
  malformed := object.union(complete_evidence[0], {"sha256": "sha256:a"})
  not allow with input as object.union(base_input, {
    "evidenceRefs": array.concat([malformed], array.slice(complete_evidence, 1, 5)),
  })
}

test_rejects_evidence_wrong_provider_format if {
  malformed := object.union(complete_evidence[0], {"format":"json"})
  not allow with input as object.union(base_input, {
    "evidenceRefs": array.concat([malformed], array.slice(complete_evidence, 1, 5)),
  })
}

test_gitleaks_custom_findings_exit_is_blocked if {
  changed := {"provider":"gitleaks","exitCode":10,"mechanicalSuccess":true,"blocking":true}
  decision.standing == "BLOCKED" with input as object.union(base_input, {
    "providerResults": array.concat([changed], array.slice(complete_results, 1, 5)),
  })
}

test_gitleaks_default_ambiguous_exit_is_not_accepted_as_findings if {
  ambiguous := {"provider":"gitleaks","exitCode":1,"mechanicalSuccess":true,"blocking":true}
  not allow with input as object.union(base_input, {
    "providerResults": array.concat([ambiguous], array.slice(complete_results, 1, 5)),
  })
}

test_rejects_non_commit_subject_revision if {
  not allow with input as object.union(base_input, {
    "subjectRevision": "rev:a",
    "observedSubjectRevision": "rev:a",
  })
}

test_blocks_provider_finding_without_calling_it_execution_failure if {
  changed := {"provider":"osv-scanner","exitCode":1,"mechanicalSuccess":true,"blocking":true}
  decision.standing == "BLOCKED" with input as object.union(base_input, {
    "providerResults": array.concat(array.slice(complete_results, 0, 4), [changed]),
  })
}

test_distinguishes_provider_error if {
  changed := {"provider":"osv-scanner","exitCode":2,"mechanicalSuccess":false,"blocking":false}
  decision.standing == "PROVIDER_ERROR" with input as object.union(base_input, {
    "providerResults": array.concat(array.slice(complete_results, 0, 4), [changed]),
  })
}

test_rejects_stale_provider_evidence_before_using_findings if {
  changed := {"provider":"osv-scanner","exitCode":1,"mechanicalSuccess":true,"blocking":true}
  decision.standing == "STALE_EVIDENCE" with input as object.union(base_input, {
    "observedSubjectRevision": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "providerResults": array.concat(array.slice(complete_results, 0, 4), [changed]),
  })
}
