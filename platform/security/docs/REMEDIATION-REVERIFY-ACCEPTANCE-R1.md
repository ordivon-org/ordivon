# Remediation and fresh re-verification acceptance R1

Date: 2026-09-12
Historical recorded standing (2026-09-12): `BASELINE_VULNERABILITIES_CLEARED_ON_FRESH_EVIDENCE` for that bounded observation only. Not the current CLI contract or a current vulnerability verdict.

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
- the supplied after SBOM bytes differ from the before SBOM bytes; scan-input binding is not established by this comparison;
- Trivy evidence on both sides is explicitly CycloneDX-SBOM based;
- every baseline vulnerability identity is absent from the after scan;
- any remaining/new after findings remain visible rather than being hidden by a successful delta.

A real release still requires the normal Artifact build/provenance and Security admission chain. R1 proves the remediation/re-observation contract, not production release readiness.


## Current report-delta contract (supersedes the old generic standing)

The historical fixture standing above includes a real observed scan sequence. The
standalone verifier cannot establish that sequence merely by comparing four
supplied files. It returns `BASELINE_VULNERABILITY_IDS_ABSENT_IN_SUPPLIED_REPORTS`
with `scanInputBinding=UNKNOWN` and `authenticated=false`. A changed SBOM digest
is not a scanner receipt. Missing Results is not accepted as an observed empty
array in this profile. Consumers needing fresh remediation acceptance must
independently qualify the exact scan inputs, producer and coverage; this CLI
does not manufacture that evidence.

## R14 native consumer and temporal validity observation (2026-11-26)

The historical 4-to-0 observation is not a permanent regression oracle.
Native Syft 1.55.0 / CycloneDX 1.7 and Trivy 0.76.2 used isolated requirements
manifests (setuptools 65.5.0 and 83.0.0), not installed packages. A vulnerability
database was downloaded into a private temporary cache; both native scans
used that cache with updates disabled. Unique package vulnerability-ID counts
were 5 and 1, with one shared ID. The existing CLI rejected baseline clearance.
Runtime Job `job-01a214ad-aa9a-70fc-a16c-e2b1c647e73d` exited 1 at the verifier;
both native scans completed. Observed SHA-256 values:

| Input | Digest (hex) |
|---|---|
| Before SBOM | 26c6a70bfb06a0688c5efb9ea836bfd4d861f856a22f3cb505b9527d93c50f56 |
| After SBOM | 890fd2fb7e43ab3c5744bfa307264d18e5fbed205d9a22973665c551f287b819 |
| Before report | b3396c1d17452279ee7645b200bd8d505ab8dd25e8fbe83f6b53554da973cb15 |
| After report | 06d218edb8c5e42de8efcdcca394f92d23116194a7868b25be778e24f885224e |

These are bounded observations, not retained signed scan receipts. Exact DB
bytes and metadata were not captured; Trivy warned third-party SBOMs can affect
accuracy. Scratch inputs and DB were ephemeral. No current verdict for any
installed Ordivon dependency follows. Authenticated qualification must retain
actual scan-input and report identities, provider/database identity, coverage,
execution observation and independent consumer acceptance.

`tests/test_remediation_cli.py` exercises actual stdout JSON, all four digests,
unbound/unauthenticated standing and explicit rejection of missing Results.
This synthetic first-party consumer does not establish external migration.
Tracked source search outside Security found inventory references only;
dynamic or external consumer compatibility remains UNKNOWN.

Preserve native Syft/Trivy and the existing report-delta contract. Qualify
native coverage and authenticated receipts with the build/scan owner before
new clearance claims. Do not build another scanner or normalize unknown to
clearance. Use existing SLSA/in-toto verification only where subject and
verifier semantics are satisfied; a signature alone does not prove coverage.

## R15 evidence identity operator and release gate (2026-11-26)

The opaque SBOM digest operator consumes the native Python hashlib.file_digest
streaming primitive rather than materializing the entire file. The report
parser deliberately still captures and hashes the same JSON bytes; do not
replace that binding with an independent reopen. The opaque digest alone
does not establish immutability, scanner input, source trust or completeness.

On a synthetic 64 MiB binary file, actual existing eager-read and standard
streaming carriers each produced the independently accumulated SHA-256
in all three observations. Existing median 87.315 ms and traced Python
allocation peak 67,109,138 bytes; streaming median 43.187 ms and traced peak
394,369 bytes. Job `job-01a214b3-d4b0-717c-b7e9-52b2a3cba044`.
This is a bounded local synthetic comparison, not a production latency,
resident memory, concurrent mutation or scanner benchmark. The owner test
covers exact-byte parity on empty, binary and multi-buffer inputs. No new
dependency, custom hashing implementation or evidence schema.

The independent native database identity experiment did not complete:
Trivy's fresh private DB download exceeded the 65-second execution bound
(job `job-01a214b3-1d31-7376-9a1e-aa463f6e7282`). No new DB continuity
or cross-SBOM-provider qualification follows. Future native qualification
must retain actual DB/metadata identity and exact input/output observations
and distinguish an unavailable provider from a clean result.

Release qualification remains independent of evidence integrity. The
existing Gitleaks history gate detected a finding in #2808 CI. Keep the
normal gate and distinguish detector observation, genuine secret exposure,
credential-owner remediation, historical source scope and release standing.
Do not treat lack of a verified credential or an unavailable Git object as
a clean result. Use only redacted finding metadata in coordination.
