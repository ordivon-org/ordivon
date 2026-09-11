# Security v2 standards baseline

Status: adopted design baseline, not a conformance claim.

Security v2 uses external standards as the vocabulary and interchange layer. Ordivon does not replace these formats with a proprietary security finding ontology.

## Current authoritative baseline

- NIST SP 800-218, Secure Software Development Framework (SSDF) v1.1 — secure-development practice vocabulary and lifecycle baseline.
- OpenSSF Open Source Project Security (OSPS) Baseline v2026.08.28 — current open-source project security control baseline.
- OASIS SARIF v2.1.0 with Approved Errata 01 — static-analysis result interchange.
- OWASP CycloneDX v1.7 — current stable BOM standard; Security v2 uses CycloneDX JSON for SBOM output and will prefer native VEX/citation capabilities rather than inventing a parallel format.
- SLSA v1.2 — current approved supply-chain security specification; future provenance and verification-summary work should use SLSA/in-toto attestations rather than custom build provenance.

## Current ownership split

External systems own scanning, package discovery, vulnerability data, and policy evaluation:

- Gitleaks -> secret detection / SARIF
- Semgrep -> SAST / SARIF
- Trivy -> vulnerability and secret scanning / SARIF
- Syft -> SBOM / CycloneDX JSON
- OSV-Scanner -> dependency-vulnerability evidence / provider-native JSON
- OPA/Rego -> policy execution

Ordivon retains only the thin semantic waist required to bind those artifacts to an exact subject and decision:

- subject identity and revision;
- evidence references and exact digests;
- provider mechanical success versus security finding;
- currentness/applicability;
- authority;
- policy decision and standing.

## Standing semantics currently implemented

- `CURRENT`: complete mechanically valid evidence, exact current revision, no blocking provider verdict.
- `BLOCKED`: evidence is current and mechanically valid, but at least one provider returns a blocking verdict.
- `PROVIDER_ERROR`: required evidence exists but one or more required providers did not execute successfully.
- `STALE_EVIDENCE`: evidence was produced for a different or unknown subject revision; provider findings are not promoted to current standing.
- `INCOMPLETE_EVIDENCE`: required evidence/result coverage is missing.

This file records the baseline only. It does not claim NIST, OSPS, SLSA, or other compliance.
