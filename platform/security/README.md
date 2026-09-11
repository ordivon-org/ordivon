# Ordivon Security v2

External-first security verification substrate with a deliberately thin Ordivon semantic waist.

## Ownership boundary

External tools own scanning, package discovery, vulnerability data, and policy execution. Ordivon owns only:

- exact subject identity;
- evidence references and digests;
- evidence freshness/applicability metadata supplied by the caller or provider;
- authority/admission context;
- policy decision and standing projection.

Current provider set: Gitleaks, Semgrep, OSV-Scanner, Trivy, Syft, OPA/Rego.

## Artifact contract

Provider-native formats are retained instead of normalized into a proprietary finding model:

- Gitleaks / Semgrep / Trivy -> SARIF
- Syft -> CycloneDX JSON
- OSV-Scanner -> provider-native JSON
- OPA -> JSON decision

`ordivon_security_v2.evidence` creates only digest-bound `EvidenceRef` records over those artifacts and assembles a small policy input.
