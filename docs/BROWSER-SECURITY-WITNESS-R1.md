# Browser Security Witness R1

Status: experimental Security-v2 evidence waist.

## Purpose

Browser/provider incidents must be diagnosed from versioned detector witnesses rather than a protected provider challenge alone. The witness model separates subject drift from detector drift and routes changed observable families to the owning repair surface.

Supported families:

- `CF02` network / TLS / transport;
- `CF03` HTTP request presentation;
- `CF04` browser launch / page-visible presentation;
- `CF05` automation-control / execution-context observability;
- `CF06` cross-layer consistency;
- `CF07` profile / session lifecycle;
- `CF08` challenge standing as an outcome observation only.

A witness deliberately contains detector observation digests rather than raw credentials, cookies, session tokens, provider secrets, or unrestricted browser dumps.

## Invariant

```text
protected challenge outcome != detector oracle
```

`protectedChallengeUsedAsDetectorOracle` must be exactly `false`. A challenge standing may be recorded as an outcome, but `compare_browser_security_witnesses()` never reports that a changed challenge standing establishes root cause.

## Detector drift

A detector version change is classified as `DETECTOR_DRIFT`, not as a changed browser-security family. This prevents a detector implementation update from being mistaken for provider/browser drift.

## Repair routing

Observed family drift maps to bounded repair ownership:

```text
CF02 -> network/provider-path
CF03 -> http-request-presentation
CF04 -> browser-launch-js-presentation
CF05 -> automation-control-layer
CF06 -> cross-layer-consistency
CF07 -> profile-session-lifecycle
CF08 -> provider-policy-drift-attribution-only
```

The router identifies where to investigate; it does not claim causality.

## CLI

```text
PYTHONPATH=src python scripts/compare_browser_security_witnesses.py baseline.json candidate.json
```

The output contains infrastructure changes, per-detector status, changed families, detector-version drift, repair routes, challenge-standing change, and `rootCauseEstablished=false`.


## Collector bundle

Security-v2 now owns the canonicalization/redaction/digest boundary as well as comparison. Browser, Network, Harness, or another provider adapter supplies declared JSON observations; Security does not acquire browser authority merely by accepting those observations.

Collector manifest shape:

```json
{
  "schemaVersion": 1,
  "witnessId": "browserless-prod-r2-20260918",
  "browserBinaryDigest": "sha256:...",
  "controlLayer": {"routeFamily": "browserless/chromium"},
  "networkAuthority": {"kind": "network-v2", "name": "browserless-prod"},
  "readings": [
    {
      "detectorId": "cf04-browser-js-presentation",
      "family": "CF04",
      "detectorVersion": "r2-20260918",
      "coverage": "page-visible browser identity and automation presentation",
      "publicObservation": {"navigatorWebdriver": true}
    }
  ],
  "challengeStanding": "CHALLENGE_GATED"
}
```

`controlLayer` and `networkAuthority` are canonicalized and retained only as SHA-256 identities in the emitted witness. Each `publicObservation` remains visible in the bundle for field-level drift diagnosis, but its digest is revalidated on bundle load. Secret-shaped fields such as password, authorization, token, cookie value, or private-key values are rejected recursively before a bundle can be built.

The bundle therefore separates:

```text
provider observation authority
        -> declared public readings
Security canonicalization/redaction/digest authority
        -> canonical witness bundle
comparison
        -> detector drift vs subject drift vs infrastructure drift
```

A detector coverage declaration change is detector drift. It is not silently treated as subject/browser drift.

## Collector CLI

Build a canonical bundle:

```text
PYTHONPATH=src python scripts/build_browser_security_witness.py \
  manifest.json --output witness.json
```

Compare bundles with field-level changed paths:

```text
PYTHONPATH=src python scripts/compare_browser_security_bundles.py \
  baseline.json candidate.json
```

The bundle comparator retains all R1 invariants and additionally reports `publicObservationChanges`, for example:

```json
{
  "detectorId": "cf04-browser-js-presentation",
  "changedPaths": ["$.navigatorWebdriver", "$.window.innerWidth"]
}
```

It reports paths, not a causal verdict. `rootCauseEstablished` remains `false`.

## R2 reference fixture

The repository carries a reference manifest and its deterministic canonical bundle derived from the 2026-09-18 R1/R2 browser-security experiments:

```text
fixtures/browser-security/r2-reference-manifest.json
fixtures/browser-security/r2-reference-bundle.json
```

It covers CF02 through CF08 with the measured normalized transport, request-header order, browser-JS presentation, partial control observability, consistency/font/geometry observations, non-secret profile metadata, and provider outcome. It is a regression/reference artifact, not a claim that any observed field causes a protected-provider challenge.
