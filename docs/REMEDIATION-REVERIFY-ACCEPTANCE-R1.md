# Remediation and fresh re-verification acceptance R1

Date: 2026-09-12
Standing: `BASELINE_VULNERABILITIES_CLEARED_ON_FRESH_EVIDENCE` for the bounded fixture; no autonomous mutation authority claim.

## Ownership

Security discovers and verifies. It does not silently mutate repository dependencies.

For a GitHub repository, Dependabot is a mature provider for automated security/version-update pull requests. Renovate is a mature cross-platform/self-hosted alternative where repository owners need broader control. Either mutation path belongs to the repository/Engineer owner. Security consumes the resulting new revision/artifact and fresh evidence.

The target lifecycle is:

`finding -> VEX/triage -> repository-owner update -> build -> fresh SBOM -> fresh scan -> Security reverify`

## Physical R1 fixture

R1 used the locally cached Trivy vulnerability database and provider-native Syft/Trivy evidence.

Before:

- manifest: `setuptools==65.5.0`;
- Trivy findings for setuptools: 4;
- `CVE-2022-40897` HIGH, fixed at `65.5.1`;
- `CVE-2024-6345` HIGH, fixed at `70.0.0`;
- `CVE-2025-47273` HIGH, fixed at `78.1.1`;
- `CVE-2026-59890` MEDIUM, fixed at `83.0.0`.

After the acceptance fixture changed the manifest to `setuptools==83.0.0`, a **new** Syft CycloneDX SBOM and **new** Trivy SBOM scan reported zero setuptools vulnerabilities from the same local DB.

Observed digests:

- before manifest: `71ee904968ab7efb11b09e3ed1b9b865ef064e56facd79f3452178da992eeea3`;
- before SBOM: `bc7125dbc1d0d1eae32feff754167384f621b011ea63059ae745be62bedc74d1`;
- before Trivy report: `7e209e3941902cc1fa0cf42a538d2278525eb243871a22fe01fbb8e66f0783f0`;
- after manifest: `4723b97f4d3f3c1d817e4896c0f7d59642e326ad891c7037482d2455b8a6bb4c`;
- after SBOM: `cd476ace40d5e774be9c501c64bffdef85e9e44c16b8d9c81f3a176af68bf065`;
- after Trivy report: `08fb52731bf3ed587bda885d6d4650eddb025eed7b3366a83d96f37fe5b942b3`.

The observed delta was `4 -> 0`.

## Residual Security contract

`ordivon_security_v2.remediation` does not implement a package updater. It verifies:

- before evidence actually contains vulnerabilities for the requested package;
- after evidence comes from a changed/fresh SBOM rather than replaying the old inventory;
- Trivy evidence on both sides is explicitly CycloneDX-SBOM based;
- every baseline vulnerability identity is absent from the after scan;
- any remaining/new after findings remain visible rather than being hidden by a successful delta.

A real release still requires the normal Artifact build/provenance and Security admission chain. R1 proves the remediation/re-observation contract, not production release readiness.
