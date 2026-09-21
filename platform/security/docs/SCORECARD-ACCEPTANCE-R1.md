# OpenSSF Scorecard acceptance R1

Date: 2026-09-12
Standing: `PROVIDER_EXECUTION_VERIFIED + EXACT_REPOSITORY_REVISION_BINDING`; no Ordivon repository admission claim yet.

## Provider

The acceptance used the official OpenSSF Scorecard image:

- image: `ghcr.io/ossf/scorecard:v5.5.0`;
- image digest observed after pull: `sha256:2ad2ced1cc8d080a589fac211944834c0da3dd82a4d7b0e70a642b6be76987d7`;
- Scorecard Git version: `v5.5.0`;
- Scorecard Git commit: `c395761df6afe1a69e476bc60a013a94bcbc153f`;
- platform: `linux/amd64`.

The local Go-module path was attempted first but failed before build because `proxy.golang.org` timed out over the current IPv6 path. No network configuration was changed. The official GHCR image was then used instead.

Podman could pull the image, but its default netavark bridge is unsupported by the current WSL2 kernel. Acceptance therefore used `--network=host` for this read-only public-repository scan rather than changing the host network substrate.

## Physical provider run

Provider target:

- repository: `github.com/ossf/scorecard`;
- exact scanned commit reported by Scorecard: `f92023a3f77879f96e0c9c1305f289d755be4bb6`;
- provider aggregate score: `8.9`;
- raw report SHA-256: `e20f9581e8fa5fbdf6d07ae74ea954fa86df52a4c3768221d12f929a090306a6`.

Examples from the same provider report:

- `Branch-Protection = 8`;
- `CI-Tests = 10`;
- `Code-Review = 10`;
- `Fuzzing = 10`;
- `Pinned-Dependencies = 9`;
- `Token-Permissions = 9`;
- `Vulnerabilities = 0`.

This is exactly why Security v2 does **not** define `aggregate score >= threshold` as authority. The aggregate is retained as provider metadata. Policy operates on named checks plus explicit applicability.

## Security v2 binding contract

`ordivon_security_v2.scorecard` now requires:

- exact provider-reported repository identity;
- exact provider-reported Git commit;
- unique named checks;
- provider-range check scores;
- any named checks required by the caller to be present.

Changed repository revision, duplicate check identity, or missing required check fails closed. The provider-native JSON is retained by digest; Security does not normalize Scorecard into a proprietary finding database.

The R1 provider run is a provider-integration acceptance against the official public Scorecard repository. It was **not** a security standing for the then-current standalone Security-v2 carrier at /root/projects/ordivon-security-v2; at the R1 observation boundary that carrier had no Git remote configured. This is historical target-identity evidence. Current Security source is owned under /root/projects/ordivon/platform/security. A future current repository standing still requires an owner-selected remotely addressable repository or an explicitly supported local-repository Scorecard path, exact applicability policy, and fresh evidence.
