# DW02 Threat Signal & Applicability Fusion R1

Date: 2026-10-01  
Work: `work:security:dwc-r21:dw02-threat-applicability:20261001`

## Decision

DW02 is a **thin, effect-free Security projection**, not a threat-feed platform.

It consumes provider-native artifacts acquired by an external acquisition owner, binds them to the exact DW01 `ordivon.security.dwc-subject-exposure-snapshot`, retains their native locator plus exact artifact digest, and emits only the minimum facts required by later DWC stages.

No Security-specific crawler, feed cache, CVE database, product ontology, or global risk score is introduced.

## Exact DW01 seam

DW01 landed while DW02 was being qualified, so R1 was rebased to the current subject contract rather than keeping a parallel subject shape.

DW02 now requires the real DW01 fields:

- `kind = ordivon.security.dwc-subject-exposure-snapshot`;
- `caseRef`, `epochRef`, and `subjectRef`;
- `snapshotDigest`;
- `evidenceRef = dwc-subject-exposure:<snapshotDigest>`;
- non-empty `requiredIdentityDimensions`;
- identity/exposure coverage, observation horizon, and mechanical binding standings.

Each applicability-bearing source carries a compact exact binding of `subjectRef + snapshotDigest + evidenceRef`. If DW01 identity coverage is not `COMPLETE`, DW02 refuses to emit a definitive `AFFECTED` or `NOT_AFFECTED` claim and remains `UNDER_INVESTIGATION`.

Exposure coverage is carried forward but does not itself decide vulnerability applicability; it belongs to later response-policy/attack-path reasoning.

## Standards / provider semantics

- CSAF 2.0 is the stable baseline. CSAF 2.1 CSD03 (2026-09-11) is observed as forward pressure only.
- CSAF product status is projected without replacing the document: affected buckets -> `AFFECTED`; fixed / known-not-affected -> `NOT_AFFECTED`; under-investigation / 2.1 unknown -> `UNDER_INVESTIGATION`.
- CycloneDX 1.7 VEX remains provider-native. Its exact component/service binding must already be validated before its analysis state can enter DW02.
- CISA KEV proves observed exploitation in the wild. It is a prioritization/threat signal, never local applicability.
- FIRST EPSS provides dated exploitation probability and percentile. It is never a PASS/FAIL or local applicability authority.

## Input envelope

Every evidence item carries:

- `evidenceRef`: task-local identity;
- `sourceKind`: vendor-advisory / csaf / cyclonedx-vex / local-observation / cisa-kev / first-epss;
- `providerNativeRef`: provider-native URL, JSON pointer, record ID, or other native locator;
- `artifactDigest`: exact `sha256:...` of the frozen source bytes;
- `vulnerabilityRef`: provider-native vulnerability identity (normally CVE here);
- `admission`: `ADMITTED` or `UNVERIFIED`;
- `currentness`: `CURRENT`, `STALE`, or `UNKNOWN`;
- exact DW01 `subjectBinding` for applicability-bearing sources;
- only the minimum projected signal required for composition.

Untrusted/unverified input is retained for attention but cannot mint an applicability claim.

## Fusion rules

1. **Exact real DW01 snapshot binding is mandatory** for vendor/CSAF/VEX/local applicability evidence.
2. DW01 identity coverage must be `COMPLETE` before any definitive applicability claim.
3. **KEV and EPSS never mint AFFECTED/NOT_AFFECTED.**
4. Current admitted AFFECTED evidence -> `AFFECTED`, unless a current admitted NOT_AFFECTED source contradicts it.
5. Current admitted AFFECTED + NOT_AFFECTED -> `UNDER_INVESTIGATION` with explicit contradiction.
6. `NOT_AFFECTED` is fail-closed: it requires current admitted clearance and no current investigation or stale/unknown adverse evidence.
7. Stale adverse evidence versus current clearance -> `UNDER_INVESTIGATION`, not silent clearance.
8. Stale clearance never weakens current adverse evidence.
9. No current admitted applicability evidence -> `UNDER_INVESTIGATION`.

## Historical Exchange replay

The replay fixture records and actually executes both historical source sets through the fuser:

- ProxyLogon: CVE-2021-26855, -26857, -26858, -27065.
- ProxyShell: CVE-2021-34473, -34523, -31207.

The fixture intentionally does **not** invent Exchange build ranges. Microsoft/CISA source evidence can establish vulnerability/chain/exploitation facts, but a real DW02 subject claim still requires a provider-native product identifier to bind to the exact DW01 subject snapshot.

This preserves the central safety property:

`historical threat truth != current local applicability`

## Acquisition owner

The current Ordivon authority map already assigns public-web acquisition to an external acquisition provider and keeps Security as the domain verifier. DW02 therefore does not add a network client. Machine-readable CSAF/KEV/EPSS artifacts should be fetched/frozen by the existing acquisition/data path (native API or web acquisition provider as appropriate), then admitted to Security by exact digest.

If that external path later proves inadequate for deterministic feed snapshots, the substitution failure must be demonstrated before a Security-specific adapter is considered.

## Downstream contract to DW03

DW03 receives separable fields:

- `claim`: AFFECTED / NOT_AFFECTED / UNDER_INVESTIGATION;
- the exact DW01 case/epoch/subject/snapshot binding and identity/exposure/horizon standings;
- applicability and evidence currentness;
- explicit conflicts;
- KEV `knownExploited` signal;
- dated EPSS probability/percentile;
- exact provider-native provenance refs.

DW03 may use those as policy inputs but must not collapse them into a universal numeric cyber-risk score or treat a deadline as authority.

## Qualification / negative controls

R1 includes tests for:

- the real DW01 `SubjectExposureSnapshot` contract;
- incomplete DW01 identity binding forcing `UNDER_INVESTIGATION`;
- CSAF and CycloneDX native state projection;
- full ProxyLogon and ProxyShell fixture replay across all seven listed CVEs;
- a benign current local `NOT_AFFECTED` control;
- KEV/EPSS-only evidence remaining `UNDER_INVESTIGATION`;
- current VEX/local contradiction;
- stale adverse feed versus current clearance;
- stale clearance versus current affected;
- unverified VEX unable to mint clearance;
- exact subject mismatch fail-closed;
- KEV unable to smuggle local applicability.

## Source anchors

- OASIS CSAF 2.0 / 2.1: https://docs.oasis-open.org/csaf/
- CycloneDX 1.7: https://cyclonedx.org/docs/1.7/
- CISA KEV: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- FIRST EPSS API: https://api.first.org/epss/
- Microsoft ProxyLogon disclosure: https://www.microsoft.com/en-us/security/blog/2021/03/02/hafnium-targeting-exchange-servers/
- Microsoft March 2021 Exchange mitigation guidance: https://www.microsoft.com/msrc/blog/2021/03/microsoft-exchange-server-vulnerabilities-mitigations-march-2021
- Microsoft ProxyShell Defender note: https://www.microsoft.com/en-us/wdsi/threats/malware-encyclopedia-description?Name=Exploit%3AWin32%2FCVE-2021-31207.A

## Truth boundary

DW02 does not prove that a target is patched, protected, uncompromised, remediated, or recovered. It only produces an evidence-currentness-, authority-, and DW01-identity-bounded applicability projection for one exact subject snapshot.
