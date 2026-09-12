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

## R2 lifecycle expansion references

The R2 technology selection extends the original verification-focused baseline without replacing its provider-native evidence rules. The selected external references/providers are:

- OWASP Threat Modeling guidance and OWASP Threat Dragon for design-time threat models;
- MITRE CAPEC and CWE as referenced attack/weakness vocabularies rather than copied taxonomies;
- OpenSSF Scorecard for repository security-posture evidence;
- OWASP ZAP Automation Framework for authorized DAST/API testing;
- ClusterFuzzLite for CI continuous fuzzing, with OSS-Fuzz conditional for eligible public projects;
- SLSA v1.2 Build Provenance emitted by the real build owner and verified by Security;
- Falco as the default runtime detection provider, subject to host eBPF acceptance;
- Tetragon only when an explicit consumer needs kernel-inline enforcement and separate authority is proven.

These additions do not turn Security into the owner of repository hosting, build infrastructure, runtime execution, secret storage, or incident workflow durability. See `TECHNOLOGY-SELECTION-R2.md` for the ownership matrix and explicit non-selections.
