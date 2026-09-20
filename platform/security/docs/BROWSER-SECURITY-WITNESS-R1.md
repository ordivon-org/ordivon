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


## Live Harness r2 LKG

The first repeatable live collector baseline is sealed separately from the historical R1/R2 research fixture:

```text
fixtures/browser-security/harness-r2-live-lkg-carrier11-manifest.json
fixtures/browser-security/harness-r2-live-lkg-carrier11-bundle.json
```

It was produced by Harness detector version `harness-browser-security-r2` from `chatgpt-carrier-11` without visiting ChatGPT. Two consecutive live observations compared with zero infrastructure, detector, family, or public-field drift. The LKG binds the exact current Chromium binary, Network-v2 authority, Browserless image, and normalized 36-entry effective Chromium launch argv. Ephemeral remote-debugging port values are normalized before the control-layer digest.

This fixture is a regression baseline, not a provider-admissibility baseline and not a causal claim about any challenge.

## Live Harness r2 pool LKG

The production Browserless pool now has one neutral/read-only LKG per persistent carrier:

```text
fixtures/browser-security/harness-r2-live-lkg-carrier11-manifest.json
fixtures/browser-security/harness-r2-live-lkg-carrier11-bundle.json
fixtures/browser-security/harness-r2-live-lkg-carrier12-manifest.json
fixtures/browser-security/harness-r2-live-lkg-carrier12-bundle.json
fixtures/browser-security/harness-r2-live-lkg-carrier13-manifest.json
fixtures/browser-security/harness-r2-live-lkg-carrier13-bundle.json
fixtures/browser-security/harness-r2-live-lkg-pool-index.json
```

The pool index binds each carrier identity to its manifest/bundle digest, browser binary digest, detector version, Network-v2 authority, and control-layer endpoint identity.

The comparison law is subject-scoped:

```text
same carrier candidate vs same carrier LKG -> allowed drift comparison
cross-carrier comparison                  -> descriptive differential only
cross carrier as one subject drift        -> forbidden
```

This prevents profile-local state or endpoint identity differences between carrier-11/12/13 from being misclassified as time drift. A pool-wide incident can instead be diagnosed by comparing each current carrier against its own LKG and then intersecting the changed CF families.

## Pool drift classification

`compare_browser_security_pool()` compares each persistent carrier only against its own LKG and then aggregates the same-subject comparisons across the pool.

```text
NO_OBSERVED_DRIFT
  no changed CF family and no infrastructure change on any carrier

DETECTOR_DRIFT
  detector version/coverage or detector-set shape changed on any carrier;
  subject classification is suppressed fail-closed

OBSERVATION_INVALID
  one or more public observations are not valid subject evidence because the observer or detector
  reported an explicit unavailable/error/failed standing; subject classification is suppressed
  fail-closed and the result routes to observation-validity instead of a CF-family repair owner

GLOBAL_DRIFT
  at least one identical CF-family or infrastructure signal changed on every carrier,
  with no carrier-local residual

CARRIER_LOCAL_DRIFT
  observed changes exist only on a strict subset of carriers or differ by signal

MIXED_DRIFT
  shared pool-wide signal(s) and additional carrier-local signal(s) coexist
```

The result preserves every per-carrier bundle comparison, the shared intersection, carrier-local residuals, changed challenge standings as outcome metadata, and repair routes. It always leaves `rootCauseEstablished=false`; pool co-movement is localization evidence, not provider-authoritative causality.

CLI input is an explicit comparison manifest:

```json
{
  "schemaVersion": 1,
  "carriers": [
    {
      "carrierId": "chatgpt-carrier-11",
      "baselineBundle": "carrier11-lkg.json",
      "candidateBundle": "carrier11-current.json"
    }
  ]
}
```

At least two carriers are required. Cross-carrier bundles are not compared as if they represented one subject.


## Pool LKG reseal authority

Security-v2 owns promotion of a newly qualified Browserless pool observation into the per-carrier LKG. Harness may supply a durable post-change pool-run directory, but its classification is not trusted as the reseal decision.

```text
Harness post-change pool run
        -> candidate manifests + bundles + pool-run receipt
Security-v2 reseal
        -> verify old index digest / Harness revision / Security revision
        -> rebuild every candidate bundle from its source manifest
        -> reload old same-carrier LKG bundles
        -> recompute compare_browser_security_pool()
        -> require Harness classification == Security recomputation
        -> allow only NO_OBSERVED_DRIFT or shared browserBinary/controlLayer drift
        -> atomically replace per-carrier fixtures + pool index
```

The reseal command is:

```text
PYTHONPATH=src:. python scripts/promote_browser_security_pool_lkg.py \
  <post-change-run-root> \
  --expected-harness-revision <40-hex-commit> \
  --expected-old-index-sha256 sha256:<64hex>
```

Reseal is fail-closed. It rejects detector drift, any CF02-CF07 subject drift, challenge-standing drift, carrier-local infrastructure drift, Network-v2 authority drift, a stale old-index digest, candidate artifact digest mismatch, a candidate bundle that differs from Security-v2's own canonical rebuild, or disagreement between the Harness receipt and Security-v2's recomputed pool classification. A different Browserless/Chromium image may therefore become a new LKG only when the observable detector surface remains unchanged and the only shared infrastructure identity change is `browserBinary` and/or `controlLayer`.

The generated pool index retains the stable production pool identity and comparison law, but carries a `reseal` provenance object binding the previous index digest, source pool-run receipt digest, source Harness revision, pre-commit Security revision, observed standing, and explicitly allowed infrastructure-change set. The command intentionally stops at `LKG_RESEALED_PENDING_COMMIT`; Git review/commit remains a separate owner authority. It never deploys Browserless, changes Agent Automation admission, visits a protected provider challenge, or crosses SEND.


## Observation validity gate

Browser Security distinguishes **the subject changed** from **the observation failed**. Existing bundle schema v1 is retained: collector-side failure sentinels remain public observations, while Security-v2 interprets explicit `standing` values during comparison.

```text
standing=OBSERVED (or no failure sentinel)
        -> VALID
        -> eligible for subject drift comparison

standing=UNAVAILABLE
        -> OBSERVER_UNAVAILABLE
        -> not subject evidence

standing=ERROR / FAILED
        -> DETECTOR_FAILED
        -> not subject evidence
```

The classifier is recursive, so an unavailable nested observer such as `CF06.network` invalidates that detector observation without pretending that the browser/timezone/font subject changed. Invalid detector rows are marked `OBSERVATION_INVALID`; they do not contribute to `changedFamilies`, `publicObservationChanges`, or CF-family repair routes.

At pool level, any invalid carrier observation yields:

```text
standing = OBSERVATION_INVALID
subjectClassificationSuppressed = true
repairRoutes = ["observation-validity"]
rootCauseEstablished = false
```

Detector-shape/version drift still takes precedence as `DETECTOR_DRIFT`. This gate is intentionally fail-closed: an unavailable observer cannot make a release qualify as `NO_OBSERVED_DRIFT`, but it also cannot be mislabeled as CF02/CF06 subject drift.

The 2026-09-18 Network-v2 forwarding incident is the motivating regression case. With host `net.ipv4.ip_forward=0`, the Browserless namespace retained routes and WireGuard TX increased, while `tls.peet.ws` and Cloudflare trace became unavailable. The historical candidate bundles now replay as `OBSERVATION_INVALID` for CF02/CF06 rather than `GLOBAL_DRIFT`; after forwarding recovery, the same pool returns `NO_OBSERVED_DRIFT`.
