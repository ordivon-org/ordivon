# Ordivon Security v2

External-first security verification substrate with a deliberately thin Ordivon semantic waist.

## Ownership boundary

External tools own scanning, package discovery, vulnerability data, and policy execution. Ordivon owns only:

- exact subject identity;
- evidence references and digests;
- evidence freshness/applicability metadata supplied by the caller or provider;
- authority/admission context;
- policy decision and standing projection.

Current implemented provider/integration set: Gitleaks, Semgrep, OSV-Scanner, Trivy, Syft, OPA/Rego, and OpenSSF Scorecard evidence binding. Scorecard R1 has a real provider acceptance but no Ordivon-repository admission standing yet.

The selected lifecycle expansion is recorded in [`docs/TECHNOLOGY-SELECTION-R2.md`](docs/TECHNOLOGY-SELECTION-R2.md). P0 additions are OWASP Threat Model Library TM-BOM with Threat Dragon as editor/viewer, OpenSSF Scorecard, OWASP ZAP Automation Framework, ClusterFuzzLite, and SLSA v1.2 Build Provenance. Falco is the selected P1 runtime-detection provider; Tetragon is conditional for consumers that actually require kernel-inline enforcement. Selection does not imply installation or production admission.

## Artifact contract

Provider-native formats are retained instead of normalized into a proprietary finding model:

- Gitleaks / Semgrep / Trivy -> SARIF
- Syft -> CycloneDX JSON
- OSV-Scanner -> provider-native JSON
- OPA -> JSON decision

`ordivon_security_v2.evidence` creates only digest-bound `EvidenceRef` records over those artifacts and assembles a small policy input.
