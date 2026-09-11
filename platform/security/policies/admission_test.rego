package ordivon.security.v2

import rego.v1

test_rejects_missing_provider if {
  not allow with input as {
    "authority": "security-verification",
    "evidenceRefs": [{"provider": "gitleaks", "sha256": "sha256:x", "byte_length": 1}],
  }
}

test_accepts_complete_provider_set if {
  allow with input as {
    "authority": "security-verification",
    "evidenceRefs": [
      {"provider": "gitleaks", "sha256": "sha256:a", "byte_length": 1},
      {"provider": "semgrep", "sha256": "sha256:b", "byte_length": 1},
      {"provider": "trivy", "sha256": "sha256:c", "byte_length": 1},
      {"provider": "syft", "sha256": "sha256:d", "byte_length": 1},
      {"provider": "osv-scanner", "sha256": "sha256:e", "byte_length": 1},
    ],
  }
}
