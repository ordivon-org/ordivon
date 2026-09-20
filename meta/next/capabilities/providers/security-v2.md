# Provider: Security v2

- Source: `/root/projects/ordivon-security-v2`
- Observed revision: `17ebfb63f710`
- Role: security verification capability family
- Migration mode: metadata registration plus reusable evidence/authority lessons

## Provider composition

Current external providers include Gitleaks, Semgrep, OSV-Scanner, Trivy, Syft, OPA/Rego and OpenSSF Scorecard, with additional selected providers for threat modeling, ZAP, fuzzing, provenance and runtime detection.

Provider-native formats are retained where possible, including SARIF and CycloneDX, rather than normalized into an Ordivon proprietary finding ontology.

## Thin residual

Useful Ordivon-side metadata is limited to exact subject identity, evidence reference/digest, freshness/applicability, authority/admission context and bounded policy/standing projection.

## Activation

Load according to the security concerns of the current Entity of Interest. Security is not assumed to be a permanent topological subsystem.
